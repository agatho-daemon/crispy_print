from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime


@dataclass(frozen=True)
class TemplateRenderContext:
	source_doctype: str | None = None
	source_docname: str | None = None
	source_report: str | None = None
	source_contract: str | None = None
	company: str | None = None
	template: str | None = None
	template_name: str | None = None


def get_active_templates_for_context(context: TemplateRenderContext) -> list[dict[str, Any]]:
	validate_template_render_context(context)
	target_filters = template_target_filters(context)
	effective_company = resolve_template_company(context)
	rows = _get_active_template_rows({**target_filters, "status": "Approved", "is_active": 1})
	applicable = [
		active_template_list_payload(row, effective_company)
		for row in rows
		if _is_applicable_template_row(row, effective_company)
	]
	return sort_active_template_payloads(applicable, effective_company)


def resolve_active_template_for_context(context: TemplateRenderContext) -> dict[str, Any]:
	effective_company = resolve_template_company(context)
	if context.template:
		doc = frappe.get_doc("Crispy Template", context.template)
		doc.check_permission("read")
		validate_resolved_template_target(doc, context, company=effective_company)
		return template_resolution_payload(doc, effective_company, "explicit")

	validate_template_render_context(context)
	target_filters = template_target_filters(context, include_template_name=True)
	if not target_filters.get("crispy_format_type"):
		frappe.throw(_("Template target is required."))

	base_filters = {
		**target_filters,
		"status": "Approved",
		"is_active": 1,
	}

	if effective_company:
		doc = get_latest_active_template({**base_filters, "company": effective_company})
		if doc:
			return template_resolution_payload(doc, effective_company, "company")

	doc = get_latest_active_template(base_filters, expected_company="")
	if doc:
		return template_resolution_payload(doc, effective_company, "global")

	frappe.throw(_("No active Crispy Template found for this document context."))


def validate_template_render_context(context: TemplateRenderContext) -> None:
	target_count = sum(
		bool(value) for value in (context.source_doctype, context.source_report, context.source_contract)
	)
	if target_count != 1:
		frappe.throw(_("Exactly one template render target is required."))


def template_target_filters(
	context: TemplateRenderContext,
	*,
	include_template_name: bool = False,
) -> dict[str, str]:
	filters = {}
	if context.source_doctype:
		filters.update({"crispy_format_type": "DocType", "source_doctype": context.source_doctype})
	elif context.source_report:
		filters.update({"crispy_format_type": "Report", "source_report": context.source_report})
	elif context.source_contract:
		filters.update({"crispy_format_type": "Contract", "source_contract": context.source_contract})
	if include_template_name and context.template_name:
		filters["template_name"] = context.template_name
	return filters


def resolve_template_company(context: TemplateRenderContext) -> str | None:
	from crispy_print.api.v1.company_context import resolve_effective_company

	return resolve_effective_company(
		source_doctype=context.source_doctype,
		source_docname=context.source_docname,
		explicit_company=context.company,
		allow_global_fallback=False,
	)


def get_latest_active_template(
	filters: dict[str, Any],
	expected_company: str | None = None,
):
	rows = _get_active_template_rows(filters)
	if expected_company is not None:
		rows = [row for row in rows if _clean(row.get("company")) == _clean(expected_company)]
	rows = [row for row in rows if is_effective_template_row(row)]
	if not rows:
		return None
	rows = sort_active_template_rows(rows)
	return frappe.get_doc("Crispy Template", rows[0].get("name"))


def validate_resolved_template_target(
	doc,
	context: TemplateRenderContext,
	company: str | None = None,
) -> None:
	if doc.status != "Approved" or not doc.is_active:
		frappe.throw(_("Selected Crispy Template is not an active approved template."))
	if context.source_doctype and doc.source_doctype != context.source_doctype:
		frappe.throw(_("Selected Crispy Template does not match the source DocType."))
	if context.source_report and doc.source_report != context.source_report:
		frappe.throw(_("Selected Crispy Template does not match the source Report."))
	if context.source_contract and doc.source_contract != context.source_contract:
		frappe.throw(_("Selected Crispy Template does not match the source Contract."))
	if doc.company and company and doc.company != company:
		frappe.throw(_("Selected Crispy Template does not belong to company {0}.").format(company))


def active_template_list_payload(row: dict[str, Any], effective_company: str | None) -> dict[str, Any]:
	row_company = _clean(row.get("company"))
	return {
		"name": row.get("name"),
		"template_name": row.get("template_name"),
		"template_id": row.get("name"),
		"company": row.get("company"),
		"company_abbr": get_company_abbr(row.get("company")),
		"version": row.get("version"),
		"effective_from": row.get("effective_from"),
		"effective_to": row.get("effective_to"),
		"source_branding_profile": row.get("source_branding_profile"),
		"snapshot_hash": row.get("snapshot_hash"),
		"snapshot_hash_version": row.get("snapshot_hash_version"),
		"zebra_version": row.get("zebra_version"),
		"barcode_symbology": row.get("barcode_symbology"),
		"scope": "Company" if row_company else "Global",
	}


def template_resolution_payload(
	doc,
	effective_company: str | None,
	resolution_reason: str,
) -> dict[str, Any]:
	presentation_settings = doc.presentation_settings_json
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"template_id": doc.name,
		"company": doc.company,
		"company_abbr": get_company_abbr(doc.company),
		"effective_company": effective_company,
		"scope": "Company" if doc.company else "Global",
		"version": doc.version,
		"resolution_reason": resolution_reason,
		"source_crispy_format": doc.source_crispy_format,
		"source_branding_profile": doc.source_branding_profile,
		"crispy_format_type": doc.crispy_format_type,
		"source_doctype": doc.source_doctype,
		"source_report": doc.source_report,
		"source_contract": doc.source_contract,
		"pdf_standard": doc.pdf_standard,
		"raw_typst": bool(doc.raw_typst),
		"compact_item_print": doc.compact_item_print,
		"print_uom_after_quantity": doc.print_uom_after_quantity,
		"print_taxes_with_zero_amount": doc.print_taxes_with_zero_amount,
		"layout_json": doc.layout_json,
		"presentation_settings": presentation_settings,
		"doc_header": doc.doc_header,
		"doc_footer": doc.doc_footer,
		"typst_preamble": doc.typst_preamble,
		"typst_code": doc.typst_code,
		"snapshot_hash": doc.snapshot_hash,
		"snapshot_hash_version": doc.snapshot_hash_version,
		"zebra_version": doc.zebra_version,
		"barcode_symbology": doc.barcode_symbology,
		"render_payload": {
			"name": doc.source_crispy_format or doc.name,
			"doc_type": doc.source_doctype,
			"crispy_format_type": doc.crispy_format_type,
			"company": doc.company,
			"effective_company": effective_company,
			"layout_json": doc.layout_json,
			"presentation_settings": presentation_settings,
			"doc_header": doc.doc_header,
			"doc_footer": doc.doc_footer,
			"typst_preamble": doc.typst_preamble,
			"typst_code": doc.typst_code,
			"pdf_standard": doc.pdf_standard,
			"raw_typst": 1 if doc.raw_typst else 0,
			"compact_item_print": doc.compact_item_print,
			"print_uom_after_quantity": doc.print_uom_after_quantity,
			"print_taxes_with_zero_amount": doc.print_taxes_with_zero_amount,
			"crispy_template": doc.name,
			"crispy_template_version": doc.version,
			"template_hash": doc.snapshot_hash,
			"snapshot_hash_version": doc.snapshot_hash_version,
			"zebra_version": doc.zebra_version,
			"barcode_symbology": doc.barcode_symbology,
		},
	}


def sort_active_template_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
	rows = list(rows)
	rows.sort(key=lambda row: str(row.get("name") or ""))
	rows.sort(key=lambda row: parse_version(row.get("version")), reverse=True)
	rows.sort(key=lambda row: str(row.get("effective_from") or ""), reverse=True)
	return rows


def sort_active_template_payloads(
	rows: list[dict[str, Any]],
	effective_company: str | None,
) -> list[dict[str, Any]]:
	rows = list(rows)
	rows.sort(key=lambda row: str(row.get("template_name") or ""))
	rows.sort(key=lambda row: parse_version(row.get("version")), reverse=True)
	rows.sort(key=lambda row: str(row.get("effective_from") or ""), reverse=True)
	rows.sort(key=lambda row: 0 if _clean(row.get("company")) == _clean(effective_company) else 1)
	return rows


def is_effective_template_row(row: dict[str, Any], now=None) -> bool:
	now = now or now_datetime()
	if row.get("effective_from") and row.get("effective_from") > now:
		return False
	if row.get("effective_to") and row.get("effective_to") < now:
		return False
	return True


def get_company_abbr(company: str | None) -> str:
	if not company:
		return ""
	return _clean(frappe.db.get_value("Company", company, "abbr")) or _clean(company)


def parse_version(value: Any) -> tuple[int, int]:
	major_raw, _, minor_raw = str(value or "0.0").partition(".")
	try:
		major = int(major_raw)
	except (TypeError, ValueError):
		major = 0
	try:
		minor = int(minor_raw or 0)
	except (TypeError, ValueError):
		minor = 0
	return major, minor


def _get_active_template_rows(filters: dict[str, Any]) -> list[dict[str, Any]]:
	return frappe.get_all(
		"Crispy Template",
		filters={key: value for key, value in filters.items() if value not in (None, "")},
		fields=[
			"name",
			"template_name",
			"company",
			"version",
			"effective_from",
			"effective_to",
			"source_branding_profile",
			"snapshot_hash",
			"snapshot_hash_version",
			"zebra_version",
			"barcode_symbology",
		],
	)


def _is_applicable_template_row(row: dict[str, Any], effective_company: str | None) -> bool:
	row_company = _clean(row.get("company"))
	if row_company and row_company != _clean(effective_company):
		return False
	return is_effective_template_row(row)


def _clean(value: Any) -> str:
	return str(value or "").strip()
