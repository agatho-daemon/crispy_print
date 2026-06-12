from typing import Any

import frappe
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	build_template_id,
	get_company_abbr,
	get_publish_preview,
	publish_crispy_template,
	resolve_active_crispy_template,
)

from .company_context import resolve_effective_company
from .security import ensure_doctype_read_permission

JSONDict = dict[str, Any]


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
