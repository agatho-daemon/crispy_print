from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	_supersede_previous_active_templates,
	build_template_id,
	get_company_abbr,
	get_publish_preview,
	publish_crispy_template,
	resolve_active_crispy_template,
)

from .company_context import resolve_effective_company
from .formats import _format_data_from_doc, _insert_format_duplicate_for_company
from .security import ensure_doctype_read_permission

JSONDict = dict[str, Any]
ALLOWED_TEMPLATE_DUPLICATE_MODES = {"snapshot", "current_format"}


def get_crispy_template_publish_preview(
	source_crispy_format: str,
	version_bump: str = "minor",
	company: str | None = None,
) -> JSONDict:
	return get_publish_preview(source_crispy_format, version_bump=version_bump, company=company)


def get_active_crispy_templates_for_document(
	source_doctype: str,
	source_docname: str | None = None,
	company: str | None = None,
) -> list[JSONDict]:
	return get_active_crispy_templates_for_render(
		source_doctype=source_doctype,
		source_docname=source_docname,
		company=company,
	)


def get_active_crispy_templates_for_render(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
) -> list[JSONDict]:
	_validate_template_render_context(
		source_doctype=source_doctype,
		source_report=source_report,
		source_contract=source_contract,
	)
	target_filters = _template_target_filters(
		source_doctype=source_doctype,
		source_report=source_report,
		source_contract=source_contract,
	)
	effective_company = _resolve_render_company(
		source_doctype=source_doctype,
		source_docname=source_docname,
		company=company,
	)
	return _get_active_templates(target_filters, effective_company)


def get_resolved_crispy_template_for_document(
	source_doctype: str,
	source_docname: str | None = None,
	company: str | None = None,
	template: str | None = None,
	template_name: str | None = None,
) -> JSONDict:
	return get_resolved_crispy_template_for_render(
		source_doctype=source_doctype,
		source_docname=source_docname,
		company=company,
		template=template,
		template_name=template_name,
	)


def get_resolved_crispy_template_for_render(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
	template: str | None = None,
	template_name: str | None = None,
) -> JSONDict:
	_validate_template_render_context(
		source_doctype=source_doctype,
		source_report=source_report,
		source_contract=source_contract,
	)
	return resolve_active_crispy_template(
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_report=source_report,
		source_contract=source_contract,
		company=company,
		template=template,
		template_name=template_name,
	)


def _get_active_templates(target_filters: dict[str, Any], effective_company: str | None) -> list[JSONDict]:
	now = now_datetime()
	filters: dict[str, Any] = {
		**target_filters,
		"status": "Approved",
		"is_active": 1,
	}
	rows = frappe.get_all(
		"Crispy Template",
		filters=filters,
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

	applicable = []
	for row in rows:
		row_company = _clean(row.get("company"))
		if row_company and row_company != _clean(effective_company):
			continue
		if row.get("effective_from") and row.get("effective_from") > now:
			continue
		if row.get("effective_to") and row.get("effective_to") < now:
			continue
		applicable.append(
			{
				"name": row.get("name"),
				"template_name": row.get("template_name"),
				"template_id": build_template_id(
					row.get("template_name") or "",
					row.get("company"),
					row.get("version") or "",
				),
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
		)

	applicable.sort(key=lambda row: str(row.get("template_name") or ""))
	applicable.sort(key=lambda row: _parse_version(row.get("version")), reverse=True)
	applicable.sort(key=lambda row: str(row.get("effective_from") or ""), reverse=True)
	applicable.sort(key=lambda row: 0 if _clean(row.get("company")) == _clean(effective_company) else 1)
	return applicable


def _validate_template_render_context(
	source_doctype: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
) -> None:
	target_count = sum(bool(value) for value in (source_doctype, source_report, source_contract))
	if target_count != 1:
		frappe.throw("Exactly one template render target is required.")
	if source_doctype:
		ensure_doctype_read_permission(source_doctype)
		return
	if source_report:
		ensure_doctype_read_permission("Report")
		return
	ensure_doctype_read_permission("Crispy Template")


def _template_target_filters(
	source_doctype: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
) -> dict[str, str]:
	if source_doctype:
		return {"crispy_format_type": "DocType", "source_doctype": source_doctype}
	if source_report:
		return {"crispy_format_type": "Report", "source_report": source_report}
	return {"crispy_format_type": "Contract", "source_contract": source_contract or ""}


def _resolve_render_company(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	company: str | None = None,
) -> str | None:
	return resolve_effective_company(
		source_doctype=source_doctype,
		source_docname=source_docname,
		explicit_company=company,
		allow_global_fallback=False,
	)


def publish_template_from_crispy_format(
	source_crispy_format: str,
	version_bump: str = "minor",
	make_active: int | bool = 1,
	effective_from: str | None = None,
	notes: str | None = None,
	company: str | None = None,
) -> JSONDict:
	if isinstance(make_active, str):
		make_active_value = make_active.strip().lower() in {"1", "true", "yes"}
	else:
		make_active_value = bool(make_active)
	return publish_crispy_template(
		source_crispy_format=source_crispy_format,
		version_bump=version_bump,
		make_active=make_active_value,
		effective_from=effective_from,
		notes=notes,
		company=company,
	)


def duplicate_crispy_template_for_company(
	source_template: str,
	target_company: str,
	clone_mode: str = "snapshot",
	make_active: int | bool = 0,
	version_bump: str = "minor",
) -> JSONDict:
	if not source_template:
		frappe.throw(_("Source Crispy Template is required."))
	target_company = _require_target_company(target_company)
	clone_mode = _normalize_template_clone_mode(clone_mode)
	make_active_value = _truthy(make_active)

	source = frappe.get_doc("Crispy Template", source_template)
	source.check_permission("read")
	if _clean(source.company) == target_company:
		frappe.throw(_("Target company must be different from the source company."))

	if clone_mode == "current_format":
		return _duplicate_template_from_current_format(
			source,
			target_company=target_company,
			make_active=make_active_value,
			version_bump=version_bump,
		)
	return _duplicate_template_from_snapshot(
		source,
		target_company=target_company,
		make_active=make_active_value,
		version_bump=version_bump,
	)


def _duplicate_template_from_current_format(
	source,
	*,
	target_company: str,
	make_active: bool,
	version_bump: str,
) -> JSONDict:
	if not source.source_crispy_format:
		frappe.throw(_("Source Crispy Template is not linked to a Crispy Format."))
	source_format = frappe.get_doc("Crispy Format", source.source_crispy_format)
	source_format.check_permission("read")
	cloned_format, warnings = _insert_format_duplicate_for_company(
		_format_data_from_doc(source_format),
		target_company=target_company,
		source_name=source_format.name,
		set_default=0,
		name=None,
		name_strategy="copy",
	)
	result = publish_crispy_template(
		source_crispy_format=cloned_format.name,
		version_bump=version_bump,
		make_active=make_active,
		company=target_company,
	)
	return _template_duplicate_payload(
		result,
		source_template=source.name,
		cloned_format=cloned_format.name,
		clone_mode="current_format",
		warnings=warnings,
	)


def _duplicate_template_from_snapshot(
	source,
	*,
	target_company: str,
	make_active: bool,
	version_bump: str,
) -> JSONDict:
	format_data = _snapshot_format_data(source)
	cloned_format, warnings = _insert_format_duplicate_for_company(
		format_data,
		target_company=target_company,
		source_name=source.template_name or source.name,
		set_default=0,
		name=None,
		name_strategy="copy",
	)
	doc = frappe.get_doc(
		{
			"doctype": "Crispy Template",
			"template_name": source.template_name,
			"source_crispy_format": cloned_format.name,
			"company": target_company,
			"status": "Approved",
			"is_active": 1 if make_active else 0,
			"effective_from": now_datetime(),
			"notes": _("Duplicated from {0}.").format(source.name),
			"typst_version": source.typst_version,
			"zebra_version": source.zebra_version,
			"barcode_symbology": source.barcode_symbology,
		}
	)
	doc.flags.template_version_bump = version_bump
	doc.flags.skip_active_template_uniqueness = bool(make_active)
	doc.insert(ignore_permissions=True)
	if make_active:
		_supersede_previous_active_templates(doc)
	return _template_duplicate_payload(
		_template_result_payload(doc),
		source_template=source.name,
		cloned_format=cloned_format.name,
		clone_mode="snapshot",
		warnings=warnings,
	)


def _snapshot_format_data(source) -> dict[str, Any]:
	format_data: dict[str, Any] = {
		"name": source.template_name or source.name,
		"crispy_format_type": source.crispy_format_type,
		"doc_type": source.source_doctype,
		"contract": source.source_contract,
		"company": source.company,
		"raw_typst": 1 if source.raw_typst else 0,
		"is_advanced": 1 if source.raw_typst else 0,
		"layout_json": source.layout_json,
		"presentation_settings": source.presentation_settings_json,
		"doc_header": source.doc_header,
		"doc_footer": source.doc_footer,
		"typst_preamble": source.typst_preamble,
		"typst_code": source.typst_code,
		"pdf_standard": source.pdf_standard,
		"compact_item_print": source.compact_item_print,
		"print_uom_after_quantity": source.print_uom_after_quantity,
		"print_taxes_with_zero_amount": source.print_taxes_with_zero_amount,
		"is_default": 0,
	}
	if source.crispy_format_type == "Report":
		format_data.update(_snapshot_report_target_data(source))
	return format_data


def _snapshot_report_target_data(source) -> dict[str, Any]:
	if source.source_crispy_format and frappe.db.exists("Crispy Format", source.source_crispy_format):
		source_format = frappe.get_doc("Crispy Format", source.source_crispy_format)
		return {
			"report": _format_data_from_doc(source_format).get("report"),
			"is_generic": source_format.get("is_generic"),
			"generic_report_type": source_format.get("generic_report_type"),
		}
	if source.source_report:
		return {"report": [{"report": source.source_report, "disabled": 0}], "is_generic": 0}
	frappe.throw(_("Report template duplication requires a source report target."))


def _template_duplicate_payload(
	result: JSONDict,
	*,
	source_template: str,
	cloned_format: str,
	clone_mode: str,
	warnings: list[str],
) -> JSONDict:
	return {
		"success": True,
		"source_template": source_template,
		"cloned_format": cloned_format,
		"clone_mode": clone_mode,
		"template": result,
		"warnings": warnings,
	}


def _template_result_payload(doc) -> JSONDict:
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"company": doc.company,
		"company_abbr": get_company_abbr(doc.company),
		"version": doc.version,
		"status": doc.status,
		"is_active": bool(doc.is_active),
		"source_branding_profile": doc.source_branding_profile,
		"snapshot_hash": doc.snapshot_hash,
		"snapshot_hash_version": doc.snapshot_hash_version,
		"typst_version": doc.typst_version,
		"zebra_version": doc.zebra_version,
		"barcode_symbology": doc.barcode_symbology,
	}


def _require_target_company(company: str | None) -> str:
	company = _clean(company)
	if not company:
		frappe.throw(_("Target company is required."))
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} does not exist.").format(company))
	return company


def _normalize_template_clone_mode(value: str | None) -> str:
	clone_mode = (value or "snapshot").strip().lower()
	if clone_mode not in ALLOWED_TEMPLATE_DUPLICATE_MODES:
		frappe.throw(_("Invalid template duplicate mode: {0}").format(value))
	return clone_mode


def _truthy(value: int | bool | str | None) -> bool:
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return bool(value)


def _clean(value: Any) -> str:
	return str(value or "").strip()


def _parse_version(value: Any) -> tuple[int, int]:
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
