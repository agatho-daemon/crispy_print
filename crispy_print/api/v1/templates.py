from typing import Any

import frappe
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
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
) -> JSONDict:
	return get_publish_preview(source_crispy_format, version_bump=version_bump)


def get_active_crispy_templates_for_document(
	source_doctype: str,
	source_docname: str | None = None,
	company: str | None = None,
) -> list[JSONDict]:
	if not source_doctype:
		frappe.throw("Source DocType is required.")
	ensure_doctype_read_permission(source_doctype)

	effective_company = resolve_effective_company(
		source_doctype=source_doctype,
		source_docname=source_docname,
		explicit_company=company,
		allow_global_fallback=False,
	)
	now = now_datetime()
	filters: dict[str, Any] = {
		"crispy_format_type": "DocType",
		"source_doctype": source_doctype,
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
				"company": row.get("company"),
				"company_abbr": get_company_abbr(row.get("company")),
				"version": row.get("version"),
				"effective_from": row.get("effective_from"),
				"effective_to": row.get("effective_to"),
				"source_branding_profile": row.get("source_branding_profile"),
				"scope": "Company" if row_company else "Global",
			}
		)

	applicable.sort(key=lambda row: str(row.get("template_name") or ""))
	applicable.sort(key=lambda row: _parse_version(row.get("version")), reverse=True)
	applicable.sort(key=lambda row: str(row.get("effective_from") or ""), reverse=True)
	applicable.sort(key=lambda row: 0 if _clean(row.get("company")) == _clean(effective_company) else 1)
	return applicable


def get_resolved_crispy_template_for_document(
	source_doctype: str,
	source_docname: str | None = None,
	company: str | None = None,
	template: str | None = None,
	template_name: str | None = None,
) -> JSONDict:
	if not source_doctype:
		frappe.throw("Source DocType is required.")
	ensure_doctype_read_permission(source_doctype)
	return resolve_active_crispy_template(
		source_doctype=source_doctype,
		source_docname=source_docname,
		company=company,
		template=template,
		template_name=template_name,
	)


def publish_template_from_crispy_format(
	source_crispy_format: str,
	version_bump: str = "minor",
	make_active: int | bool = 1,
	effective_from: str | None = None,
	notes: str | None = None,
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
