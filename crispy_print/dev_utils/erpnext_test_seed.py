"""Helpers to prepare ERPNext company test fixtures on a shared dev site.

Usage:
    bench --site fdev.local execute crispy_print.dev_utils.erpnext_test_seed.run
"""

from __future__ import annotations

from typing import Any

import frappe
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

		frappe.db.sql("delete from `tabMode of Payment Account` where company = %s", company)

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

	# Ensure this session has the expected cache keys before _make_test_records calls.
	if not hasattr(frappe.local, "test_objects") or frappe.local.test_objects is None:
		frappe.local.test_objects = {}

	for doctype in ("Company", "Cost Center", "Department", "Account"):
		frappe.local.test_objects.setdefault(doctype, [])
		make_test_records_for_doctype(doctype, force=True, commit=True)

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
		"snapshots": snapshots,
	}


def _ensure_test_companies_exist() -> int:
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
		"state_created": state_created,
		"city_created": city_created,
	}


def _ensure_named_doc(doctype: str, name: str, values: dict[str, Any]) -> bool:
	if frappe.db.exists(doctype, name):
		return False

	doc = frappe.new_doc(doctype)
	for fieldname, value in values.items():
		doc.set(fieldname, value)
	doc.insert(ignore_permissions=True)
	return True
