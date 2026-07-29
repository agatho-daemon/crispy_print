"""Disposable-site fixtures for core v1 business-format browser acceptance."""

from __future__ import annotations

from typing import Any

import frappe

from crispy_print.api.v1.sample_formats import create_format_from_sample
from crispy_print.business_format_acceptance import CORE_V1_BUSINESS_FORMATS
from crispy_print.dev_utils.rtl_e2e import _ensure_test_user

FORMAT_PREFIX = "Crispy V1 E2E"
POS_FIXTURE_REMARK = "Crispy V1 E2E disposable POS fixture"
POS_FIXTURE_ITEM = "Crispy V1 E2E POS Item"
CASH_FIXTURE_REMARK = "Crispy V1 E2E disposable cash/petty-cash fixture"


def seed(test_user_password: str | None = None) -> dict[str, Any]:
	"""Create deterministic format copies and return available source records."""
	frappe.only_for("System Manager")
	company = frappe.defaults.get_user_default("Company") or frappe.db.get_single_value(
		"Global Defaults", "default_company"
	)
	if not company:
		frappe.throw("Set a Default Company before seeding business-format acceptance.")

	documents = {
		"payment_receive": _latest("Payment Entry", {"payment_type": "Receive"}),
		"payment_pay": _latest("Payment Entry", {"payment_type": "Pay"}),
		"stock_entry": _latest("Stock Entry"),
		"material_request": _latest("Material Request"),
		"journal_entry": _latest("Journal Entry"),
		"journal_entry_cash": _latest("Journal Entry", {"voucher_type": "Cash Entry"}),
		"pos_invoice": _latest("POS Invoice"),
	}
	if not documents["journal_entry_cash"]["available"]:
		documents["journal_entry_cash"] = _seed_cash_journal_entry()
	if not documents["pos_invoice"]["available"]:
		documents["pos_invoice"] = _seed_pos_invoice()

	formats: dict[str, str] = {}
	for index, spec in enumerate(CORE_V1_BUSINESS_FORMATS, start=1):
		name = f"{FORMAT_PREFIX} {index:02d} {spec.sample_id}"
		if frappe.db.exists("Crispy Format", name):
			frappe.delete_doc("Crispy Format", name, ignore_permissions=True, force=True)
		target_company = _company_for_sample(spec.sample_id, documents, company)
		result = create_format_from_sample(spec.sample_id, target_company, name=name)
		formats[spec.sample_id] = result["name"]
	test_user = _ensure_test_user(test_user_password) if test_user_password else None
	frappe.db.commit()
	return {
		"company": company,
		"formats": formats,
		"documents": documents,
		"test_user": test_user.name if test_user else None,
		"disposable_site_only": True,
	}


def cleanup() -> dict[str, Any]:
	"""Remove only formats created by this disposable acceptance seed."""
	frappe.only_for("System Manager")
	names = frappe.get_all(
		"Crispy Format",
		filters={"name": ["like", f"{FORMAT_PREFIX}%"]},
		pluck="name",
	)
	for name in names:
		frappe.delete_doc("Crispy Format", name, ignore_permissions=True, force=True)
	pos_names = frappe.get_all(
		"POS Invoice",
		filters={"docstatus": 0, "remarks": POS_FIXTURE_REMARK},
		pluck="name",
	)
	for name in pos_names:
		frappe.delete_doc("POS Invoice", name, ignore_permissions=True, force=True)
	cash_names = frappe.get_all(
		"Journal Entry",
		filters={"docstatus": 0, "user_remark": CASH_FIXTURE_REMARK},
		pluck="name",
	)
	for name in cash_names:
		frappe.delete_doc("Journal Entry", name, ignore_permissions=True, force=True)
	item_names = frappe.get_all(
		"Item",
		filters={"item_name": POS_FIXTURE_ITEM},
		pluck="name",
	)
	deleted_items: list[str] = []
	for name in item_names:
		try:
			frappe.delete_doc("Item", name, ignore_permissions=True, force=True)
			deleted_items.append(name)
		except frappe.LinkExistsError:
			# A retained document may still reference the fixture. Never delete
			# through links during cleanup.
			continue
	frappe.db.commit()
	return {
		"deleted_formats": names,
		"deleted_pos_invoices": pos_names,
		"deleted_cash_entries": cash_names,
		"deleted_items": deleted_items,
	}


def _latest(doctype: str, filters: dict[str, Any] | None = None) -> dict[str, Any]:
	effective_filters = {"docstatus": ["<", 2], **(filters or {})}
	row = frappe.db.get_value(
		doctype,
		effective_filters,
		["name", "company"],
		as_dict=True,
		order_by="modified desc",
	)
	if not row:
		return {"available": False}
	return {"available": True, "docname": row.name, "company": row.company}


def _seed_pos_invoice() -> dict[str, Any]:
	"""Use ERPNext's maintained test factory for a disposable draft POS Invoice."""
	try:
		from erpnext.accounts.doctype.pos_invoice.test_pos_invoice import create_pos_invoice
		from erpnext.accounts.doctype.pos_opening_entry.test_pos_opening_entry import (
			create_opening_entry,
		)
		from erpnext.accounts.doctype.pos_profile.test_pos_profile import make_pos_profile

		from crispy_print.dev_utils.erpnext_test_seed import run as seed_erpnext_prerequisites

		seed_erpnext_prerequisites(
			cleanup=0,
			seed_core=1,
			seed_supplier=0,
			seed_address_geo=0,
		)
		if not frappe.db.exists("Price List", "_Test Price List"):
			frappe.get_doc(
				{
					"doctype": "Price List",
					"price_list_name": "_Test Price List",
					"currency": "INR",
					"selling": 1,
					"buying": 1,
					"enabled": 1,
				}
			).insert(ignore_permissions=True)
		item_name = frappe.db.get_value("Item", {"item_name": POS_FIXTURE_ITEM}, "name")
		if not item_name:
			item = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": POS_FIXTURE_ITEM,
					"item_name": POS_FIXTURE_ITEM,
					"description": "Disposable Crispy Print v1 POS acceptance item",
					"item_group": "Products",
					"stock_uom": "Nos",
					"is_stock_item": 0,
					"is_sales_item": 1,
				}
			).insert(ignore_permissions=True)
			item_name = item.name
			frappe.db.commit()
		frappe.clear_document_cache("Item", item_name)
		pos_profile = make_pos_profile()
		pos_profile.save()
		if not frappe.db.exists(
			"POS Opening Entry",
			{"pos_profile": pos_profile.name, "docstatus": 1, "status": "Open"},
		):
			create_opening_entry(pos_profile, "Administrator")
		doc = create_pos_invoice(
			do_not_submit=1,
			remarks=POS_FIXTURE_REMARK,
			item_code=item_name,
			pos_profile=pos_profile.name,
			qty=2,
			rate=12.5,
		)
		return {
			"available": True,
			"docname": doc.name,
			"company": doc.company,
			"seeded": True,
		}
	except Exception as exc:
		frappe.log_error(
			title="Crispy V1 POS acceptance fixture",
			message=frappe.get_traceback(),
		)
		return {"available": False, "reason": str(exc)}


def _seed_cash_journal_entry() -> dict[str, Any]:
	"""Create a disposable Cash Entry variant from a valid existing voucher."""
	source = frappe.db.get_value(
		"Journal Entry",
		{"docstatus": ["<", 2]},
		"name",
		order_by="modified desc",
	)
	if not source:
		return {"available": False, "reason": "No Journal Entry is available to copy."}
	try:
		doc = frappe.copy_doc(frappe.get_doc("Journal Entry", source))
		doc.voucher_type = "Cash Entry"
		doc.user_remark = CASH_FIXTURE_REMARK
		doc.docstatus = 0
		doc.insert(ignore_permissions=True)
		return {
			"available": True,
			"docname": doc.name,
			"company": doc.company,
			"seeded": True,
		}
	except Exception as exc:
		frappe.log_error(
			title="Crispy V1 cash/petty-cash acceptance fixture",
			message=frappe.get_traceback(),
		)
		return {"available": False, "reason": str(exc)}


def _company_for_sample(
	sample_id: str,
	documents: dict[str, dict[str, Any]],
	fallback: str,
) -> str:
	fixture_key = {
		"payment-entry-voucher": "payment_receive",
		"remittance-advice": "payment_pay",
		"stock-entry-movement": "stock_entry",
		"material-request-requisition": "material_request",
		"journal-entry-voucher": "journal_entry",
		"pos-invoice-thermal": "pos_invoice",
		"pos-invoice-a4": "pos_invoice",
	}.get(sample_id)
	row = documents.get(fixture_key or "") or {}
	return str(row.get("company") or fallback)
