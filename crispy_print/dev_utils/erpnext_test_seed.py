"""Helpers to prepare ERPNext company test fixtures on a shared dev site.

Usage:
    bench --site fdev.local execute crispy_print.dev_utils.erpnext_test_seed.run
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import frappe
from frappe.utils import getdate, today

try:
	from frappe.tests.utils.generators import make_test_objects, make_test_records_for_doctype
except ImportError:  # Frappe v15
	from frappe.test_runner import make_test_objects, make_test_records_for_doctype

TEST_COMPANIES: dict[str, str] = {
	"_Test Company": "_TC",
	"_Test Company 1": "_TC1",
	"_Test Company with perpetual inventory": "TCP1",
}

TEMP_COMPANY_NAMES: set[str] = {
	"COA from Existing Company",
	"Canada - Plan comptable pour les provinces francophones",
}


def run(
	cleanup: int = 1,
	seed_core: int = 1,
	seed_supplier: int = 1,
	seed_address_geo: int = 1,
) -> dict[str, Any]:
	"""Prepare test fixtures for ERPNext Company tests on a shared site.

	This command intentionally focuses on prerequisites and cleanup only.
	It does not run tests and does not change ERPNext source code.
	"""

	frappe.set_user("Administrator")
	result: dict[str, Any] = {
		"cleanup": {},
		"seed": {},
	}

	if cleanup:
		result["cleanup"] = _cleanup_leftover_company_test_artifacts()
		result["cleanup"]["test_record_log"] = _clear_persistent_test_record_log()

	if seed_core:
		result["seed"]["core"] = _seed_core_company_prereqs()

	if seed_supplier:
		result["seed"]["supplier"] = _ensure_demo_supplier()

	if seed_address_geo:
		result["seed"]["geo"] = _ensure_address_geo_prereqs()

	frappe.db.commit()
	frappe.logger().info("erpnext_test_seed: completed with summary=%s", result)
	return result


def _cleanup_leftover_company_test_artifacts() -> dict[str, Any]:
	cleaned_profiles = 0
	deleted_companies = 0
	skipped_companies: list[dict[str, str]] = []
	target_companies = _collect_cleanup_target_companies()

	for company in sorted(target_companies):
		if not frappe.db.exists("Company", company):
			continue

		for profile_name in frappe.get_all(
			"Crispy Branding Profile", filters={"company": company}, pluck="name"
		):
			frappe.delete_doc(
				"Crispy Branding Profile",
				profile_name,
				ignore_permissions=True,
				force=True,
			)
			cleaned_profiles += 1

		frappe.db.sql("delete from `tabMode of Payment Account` where company = %s", (company,))

		try:
			frappe.delete_doc("Company", company, ignore_permissions=True, force=True)
			deleted_companies += 1
		except Exception as exc:  # pragma: no cover - environment-specific links
			skipped_companies.append({"company": company, "reason": str(exc)})

	return {
		"target_companies": sorted(target_companies),
		"cleaned_profiles": cleaned_profiles,
		"deleted_companies": deleted_companies,
		"skipped_companies": skipped_companies,
	}


def _clear_persistent_test_record_log() -> dict[str, Any]:
	log_path = Path(frappe.get_site_path(".test_records.jsonl"))
	if not log_path.exists():
		return {"cleared": False, "path": str(log_path)}

	log_path.unlink()
	return {"cleared": True, "path": str(log_path)}


def _collect_cleanup_target_companies() -> set[str]:
	target = set(TEMP_COMPANY_NAMES)

	# Company names created by test_company.py
	target.update(
		frappe.get_all(
			"Company",
			filters={"name": ["like", "COA from %"]},
			pluck="name",
		)
	)

	# Demo-company residue from erpnext.setup.demo.create_demo_company.
	target.update(
		frappe.get_all(
			"Company",
			filters={"name": ["like", "%(Demo)"]},
			pluck="name",
		)
	)

	try:
		from erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts import (
			get_charts_for_country,
		)

		for country in ("Canada", "Germany", "France"):
			target.update(get_charts_for_country(country) or [])
	except Exception:
		# Keep cleanup resilient even if ERPNext chart helper import changes.
		pass

	return target


def _seed_core_company_prereqs() -> dict[str, Any]:
	created_companies = _ensure_test_companies_exist()
	updated_abbr = _ensure_test_company_abbrs()
	fiscal_years = _ensure_current_fiscal_year_for_test_companies()
	defaults = _ensure_test_global_defaults()
	parties = _ensure_basic_party_prereqs()
	price_lists = _ensure_price_list_prereqs()
	warehouses = _ensure_leaf_test_warehouses()
	stock_settings = _ensure_stock_settings_default_warehouse()

	_make_core_test_records()

	snapshots = []
	for company, abbr in TEST_COMPANIES.items():
		snapshots.append(
			{
				"company": company,
				"abbr": frappe.db.get_value("Company", company, "abbr"),
				"bank_root_exists": bool(frappe.db.exists("Account", f"Bank Accounts - {abbr}")),
				"cost_centers": frappe.db.count("Cost Center", {"company": company}),
				"departments": frappe.db.count("Department", {"company": company}),
				"accounts": frappe.db.count("Account", {"company": company}),
			}
		)

	return {
		"created_companies": created_companies,
		"updated_abbr": updated_abbr,
		"fiscal_years": fiscal_years,
		"defaults": defaults,
		"parties": parties,
		"price_lists": price_lists,
		"warehouses": warehouses,
		"stock_settings": stock_settings,
		"snapshots": snapshots,
	}


def _ensure_test_companies_exist() -> int:
	if all(frappe.db.exists("Company", company) for company in TEST_COMPANIES):
		return 0

	company_records = frappe.get_test_records("Company")
	selected = [record for record in company_records if record.get("company_name") in TEST_COMPANIES]
	if not selected:
		raise RuntimeError("Company test_records not found for required _Test Company entries")

	created_docs = make_test_objects("Company", selected, commit=True)
	return len(created_docs)


def _ensure_test_company_abbrs() -> int:
	updates = 0
	for company, expected_abbr in TEST_COMPANIES.items():
		if not frappe.db.exists("Company", company):
			raise RuntimeError(f"Required company missing after seed step: {company}")

		current_abbr = frappe.db.get_value("Company", company, "abbr")
		if current_abbr != expected_abbr:
			frappe.db.set_value("Company", company, "abbr", expected_abbr)
			updates += 1
	return updates


def _ensure_current_fiscal_year_for_test_companies() -> list[dict[str, Any]]:
	current_date = getdate(today())
	if not current_date:
		raise RuntimeError("Could not resolve current date for ERPNext test seed")
	current_year = str(current_date.year)
	results = [_ensure_fiscal_year_for_test_companies(current_year)]

	test_fiscal_year = f"_Test Fiscal Year {current_year}"
	if frappe.db.exists("Fiscal Year", test_fiscal_year):
		results.append(_ensure_fiscal_year_for_test_companies(test_fiscal_year))

	return results


def _ensure_fiscal_year_for_test_companies(fiscal_year_name: str) -> dict[str, Any]:
	current_date = getdate(today())
	if not current_date:
		raise RuntimeError("Could not resolve current date for ERPNext test seed")
	current_year = str(current_date.year)
	created = False
	companies_added: list[str] = []

	if frappe.db.exists("Fiscal Year", fiscal_year_name):
		fiscal_year = frappe.get_doc("Fiscal Year", fiscal_year_name)
	else:
		fiscal_year = frappe.get_doc(
			{
				"doctype": "Fiscal Year",
				"year": fiscal_year_name,
				"year_start_date": f"{current_year}-01-01",
				"year_end_date": f"{current_year}-12-31",
				"disabled": 0,
			}
		)
		created = True

	fiscal_year.set("disabled", 0)
	fiscal_year.set("year_start_date", f"{current_year}-01-01")
	fiscal_year.set("year_end_date", f"{current_year}-12-31")
	existing_companies = {row.company for row in fiscal_year.get("companies", []) or [] if row.company}
	for company in TEST_COMPANIES:
		if company not in existing_companies:
			fiscal_year.append("companies", {"company": company})
			companies_added.append(company)

	if created:
		fiscal_year.insert(ignore_permissions=True)
	else:
		fiscal_year.save(ignore_permissions=True)

	return {
		"name": fiscal_year.name,
		"created": created,
		"companies_added": companies_added,
	}


def _ensure_test_global_defaults() -> dict[str, Any]:
	previous_db_default = frappe.db.get_default("company")
	previous_global_default = frappe.db.get_single_value("Global Defaults", "default_company")
	previous_customer_naming = frappe.db.get_default("cust_master_name")
	previous_supplier_naming = frappe.db.get_default("supp_master_name")
	frappe.db.set_default("company", "_Test Company")
	frappe.db.set_default("cust_master_name", "Customer Name")
	frappe.db.set_default("supp_master_name", "Supplier Name")
	frappe.db.set_single_value("Global Defaults", "default_company", "_Test Company")
	return {
		"previous_db_default": previous_db_default,
		"previous_global_default": previous_global_default,
		"previous_customer_naming": previous_customer_naming,
		"previous_supplier_naming": previous_supplier_naming,
		"company": "_Test Company",
	}


def _ensure_basic_party_prereqs() -> dict[str, Any]:
	created = []
	for name in ("_Test Customer Group", "_Test Customer Group 1"):
		if _ensure_named_doc(
			"Customer Group",
			name,
			{
				"customer_group_name": name,
				"is_group": 0,
				"parent_customer_group": "All Customer Groups",
			},
		):
			created.append({"doctype": "Customer Group", "name": name})

	if _ensure_named_doc(
		"Territory",
		"_Test Territory",
		{
			"territory_name": "_Test Territory",
			"is_group": 0,
			"parent_territory": "All Territories",
		},
	):
		created.append({"doctype": "Territory", "name": "_Test Territory"})

	for name in ("_Test Customer", "_Test Customer 1", "_Test Customer 2", "_Test Customer 3"):
		if _ensure_named_doc(
			"Customer",
			name,
			{
				"customer_name": name,
				"customer_type": "Individual",
				"customer_group": "_Test Customer Group",
				"territory": "_Test Territory",
			},
		):
			created.append({"doctype": "Customer", "name": name})

	if _ensure_named_doc(
		"Supplier Group",
		"_Test Supplier Group",
		{
			"supplier_group_name": "_Test Supplier Group",
			"parent_supplier_group": "All Supplier Groups",
		},
	):
		created.append({"doctype": "Supplier Group", "name": "_Test Supplier Group"})

	for name in ("_Test Supplier", "_Test Supplier 1", "_Test Supplier 2"):
		if _ensure_named_doc(
			"Supplier",
			name,
			{
				"supplier_name": name,
				"supplier_group": "_Test Supplier Group",
			},
		):
			created.append({"doctype": "Supplier", "name": name})

	return {"created": created}


def _ensure_price_list_prereqs() -> dict[str, Any]:
	"""Align price-list rows with ERPNext bootstrap's duplicate check.

	ERPNext test bootstrap checks Price List existence by
	(price_list_name, enabled, selling, buying, currency). On dev sites where
	Standard Buying/Selling already exist in the site currency, bootstrap misses
	them and then collides on the primary key while inserting INR versions.
	"""
	updates = []
	for name, selling, buying in (
		("Standard Buying", 0, 1),
		("Standard Selling", 1, 0),
	):
		if not frappe.db.exists("Price List", name):
			continue

		current = {
			"price_list_name": frappe.db.get_value("Price List", name, "price_list_name"),
			"enabled": frappe.db.get_value("Price List", name, "enabled"),
			"selling": frappe.db.get_value("Price List", name, "selling"),
			"buying": frappe.db.get_value("Price List", name, "buying"),
			"currency": frappe.db.get_value("Price List", name, "currency"),
		}
		expected = {
			"price_list_name": name,
			"enabled": 1,
			"selling": selling,
			"buying": buying,
			"currency": "INR",
		}
		if any(current.get(field) != value for field, value in expected.items()):
			for field, value in expected.items():
				frappe.db.set_value("Price List", name, field, value, update_modified=False)
			updates.append({"name": name, "previous": current, "updated": expected})

	return {"updated": updates}


def _make_core_test_records() -> None:
	# Ensure this session has the expected cache keys before _make_test_records calls.
	if not hasattr(frappe.local, "test_objects") or frappe.local.test_objects is None:
		frappe.local.test_objects = {}

	from frappe.model.document import Document

	original_get_value = frappe.db.get_value
	original_insert = Document.insert

	def get_value_with_test_warehouse(doctype, filters=None, fieldname="name", *args, **kwargs):
		if doctype == "Warehouse" and filters == {"warehouse_name": "Stores"}:
			return "_Test Warehouse - _TC"
		return original_get_value(doctype, filters, fieldname, *args, **kwargs)

	def insert_ignoring_existing_test_record(doc, *args, **kwargs):
		try:
			return original_insert(doc, *args, **kwargs)
		except frappe.DuplicateEntryError:
			if doc.name and frappe.db.exists(doc.doctype, doc.name):
				return frappe.get_doc(doc.doctype, doc.name)
			raise

	frappe.db.get_value = get_value_with_test_warehouse  # type: ignore[method-assign]
	Document.insert = insert_ignoring_existing_test_record  # type: ignore[method-assign]
	try:
		for doctype in ("Company", "Cost Center", "Department", "Account"):
			frappe.local.test_objects.setdefault(doctype, [])
			make_test_records_for_doctype(doctype, force=True, commit=True)
	finally:
		frappe.db.get_value = original_get_value  # type: ignore[method-assign]
		Document.insert = original_insert  # type: ignore[method-assign]


def _ensure_leaf_test_warehouses() -> dict[str, Any]:
	return {
		"test_warehouses": [
			_ensure_leaf_warehouse("_Test Warehouse", "_Test Company", "All Warehouses - _TC"),
			_ensure_leaf_warehouse("Stores", "_Test Company", "All Warehouses - _TC"),
		],
		"ambiguous_stores_groups": _ensure_stores_named_warehouses_are_leaf(),
	}


def _ensure_leaf_warehouse(
	warehouse_name: str,
	company: str,
	parent_warehouse: str | None = None,
) -> dict[str, Any]:
	abbr = TEST_COMPANIES[company]
	name = f"{warehouse_name} - {abbr}"
	created = False
	updates: dict[str, Any] = {}

	if frappe.db.exists("Warehouse", name):
		warehouse = frappe.get_doc("Warehouse", name)
	else:
		warehouse = frappe.get_doc(
			{
				"doctype": "Warehouse",
				"warehouse_name": warehouse_name,
				"company": company,
				"is_group": 0,
			}
		)
		if parent_warehouse and frappe.db.exists("Warehouse", parent_warehouse):
			warehouse.set("parent_warehouse", parent_warehouse)
		created = True

	if warehouse.get("is_group"):
		warehouse.set("is_group", 0)
		updates["is_group"] = 0
	if not warehouse.get("company"):
		warehouse.set("company", company)
		updates["company"] = company
	if (
		parent_warehouse
		and frappe.db.exists("Warehouse", parent_warehouse)
		and not warehouse.get("parent_warehouse")
	):
		warehouse.set("parent_warehouse", parent_warehouse)
		updates["parent_warehouse"] = parent_warehouse

	if created:
		warehouse.insert(ignore_permissions=True)
	elif updates:
		warehouse.save(ignore_permissions=True)

	return {"name": warehouse.name, "created": created, "updates": updates}


def _ensure_stores_named_warehouses_are_leaf() -> list[str]:
	"""Prevent ERPNext test bootstrap from selecting a group Stores warehouse.

	ERPNext's test bootstrap resolves Stock Settings.default_warehouse with an
	unqualified lookup by warehouse_name = "Stores". On shared dev sites, any
	company-specific group warehouse also named "Stores" can be returned first and
	then fail stock ledger validation. Normalize those ambiguous rows for this dev
	test site so the bootstrap remains deterministic.
	"""
	updated = []
	for warehouse in frappe.get_all(
		"Warehouse",
		filters={"warehouse_name": "Stores", "is_group": 1},
		pluck="name",
	):
		frappe.db.set_value("Warehouse", warehouse, "is_group", 0)
		updated.append(warehouse)
	return updated


def _ensure_stock_settings_default_warehouse() -> dict[str, Any]:
	preferred_warehouse = "_Test Warehouse - _TC"
	if not frappe.db.exists("Warehouse", preferred_warehouse):
		raise RuntimeError(f"Required test warehouse missing after seed step: {preferred_warehouse}")

	is_group = frappe.db.get_value("Warehouse", preferred_warehouse, "is_group")
	if is_group:
		frappe.db.set_value("Warehouse", preferred_warehouse, "is_group", 0)

	stock_settings = frappe.get_single("Stock Settings")
	previous_warehouse = stock_settings.get("default_warehouse")
	previous_valuation_method = stock_settings.get("valuation_method")
	changed = previous_warehouse != preferred_warehouse or previous_valuation_method != "FIFO"
	if changed:
		frappe.db.set_single_value("Stock Settings", "default_warehouse", preferred_warehouse)
		frappe.db.set_single_value("Stock Settings", "valuation_method", "FIFO")

	return {
		"previous_warehouse": previous_warehouse,
		"default_warehouse": preferred_warehouse,
		"previous_valuation_method": previous_valuation_method,
		"valuation_method": "FIFO",
		"changed": changed,
	}


def _ensure_demo_supplier() -> dict[str, Any]:
	supplier_name = "Zuckerman Security Ltd."
	existing = frappe.db.get_value("Supplier", {"supplier_name": supplier_name}, "name")
	if existing:
		return {"created": False, "name": existing}

	naming_series = (
		frappe.db.get_value(
			"Property Setter",
			{
				"doc_type": "Supplier",
				"field_name": "naming_series",
				"property": "default",
			},
			"value",
		)
		or "SUP-.YYYY.-"
	)

	supplier = frappe.get_doc(
		{
			"doctype": "Supplier",
			"supplier_name": supplier_name,
			"supplier_type": "Company",
			"supplier_group": frappe.db.get_value("Supplier Group", {}, "name") or "All Supplier Groups",
			"territory": frappe.db.get_value("Territory", {}, "name") or "All Territories",
			"naming_series": naming_series,
		}
	)
	supplier.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"created": True, "name": supplier.name}


def _ensure_address_geo_prereqs() -> dict[str, Any]:
	if not _doctype_is_loadable("FUA State") or not _doctype_is_loadable("FUA City"):
		return {"skipped": True, "reason": "FUA State/FUA City DocType controller is not loadable"}

	state_created = _ensure_named_doc("FUA State", "Maharashtra", {"state_name": "Maharashtra"})
	city_created = _ensure_named_doc(
		"FUA City",
		"Mumbai",
		{
			"city_name": "Mumbai",
			"state": "Maharashtra",
			"country": "India",
		},
	)
	return {
		"skipped": False,
		"state_created": state_created,
		"city_created": city_created,
	}


def _doctype_is_loadable(doctype: str) -> bool:
	if not frappe.db.exists("DocType", doctype):
		return False
	try:
		frappe.get_controller(doctype)
	except Exception:
		return False
	return True


def _ensure_named_doc(doctype: str, name: str, values: dict[str, Any]) -> bool:
	if frappe.db.exists(doctype, name):
		return False

	doc = frappe.new_doc(doctype)
	doc.name = name
	for fieldname, value in values.items():
		doc.set(fieldname, value)
	doc.insert(ignore_permissions=True)
	return True
