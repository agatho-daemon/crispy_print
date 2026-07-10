from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

JSONDict = dict[str, Any]


def resolve_effective_company(
	*,
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_doc: Any | None = None,
	report_filters: JSONDict | str | None = None,
	explicit_company: str | None = None,
	allow_global_fallback: bool = False,
	required: bool = False,
) -> str | None:
	"""Resolve the single company context for a render operation.

	Precedence is intentionally narrow:
	1. Source document company.
	2. Report/company filter value.
	3. Explicit preview/editor company.
	4. Controlled user/global default fallback, when enabled.
	"""
	company = (
		_resolve_source_document_company(source_doc=source_doc, doctype=source_doctype, name=source_docname)
		or _resolve_report_filter_company(report_filters)
		or clean_company(explicit_company)
	)

	if not company and allow_global_fallback:
		company = _resolve_default_company()

	if required and not company:
		frappe.throw(_("Unable to resolve company for this render context."))

	return company


def apply_effective_company_to_presentation_settings(
	presentation_settings: JSONDict | None,
	company: str | None,
) -> JSONDict:
	"""Return a copy with branding company/logo company aligned to render company."""
	settings = dict(presentation_settings or {})
	if not company:
		return settings

	branding = dict(settings.get("branding") or {})
	branding["company"] = company
	logo = dict(branding.get("logo") or {})
	logo["company"] = company
	branding["logo"] = logo
	settings["branding"] = branding
	return settings


def clean_company(company: Any) -> str | None:
	value = str(company or "").strip()
	return value or None


def extract_presentation_settings_company(settings: JSONDict | str | None) -> str | None:
	if isinstance(settings, str):
		try:
			settings = json.loads(settings)
		except json.JSONDecodeError:
			return None

	if not isinstance(settings, dict):
		return None

	branding = settings.get("branding") or {}
	if not isinstance(branding, dict):
		return None

	logo = branding.get("logo") or {}
	company = branding.get("company")
	if not company and isinstance(logo, dict):
		company = logo.get("company")
	return clean_company(company)


def extract_source_company(source: Any) -> str | None:
	if hasattr(source, "as_dict"):
		values = source.as_dict()
	elif isinstance(source, dict):
		values = source
	else:
		values = {}

	company = clean_company(values.get("company") or values.get("company_name"))
	if company:
		return company
	return extract_presentation_settings_company(values.get("presentation_settings"))


def _resolve_source_document_company(
	*,
	source_doc: Any | None = None,
	doctype: str | None = None,
	name: str | None = None,
) -> str | None:
	if source_doc is not None:
		return _infer_company_from_doc(source_doc)

	if not doctype or not name:
		return None

	if not frappe.db.exists(doctype, name):
		return None

	meta = frappe.get_meta(doctype)
	for fieldname in ("company", "company_name"):
		df = meta.get_field(fieldname)
		if not df or df.fieldtype != "Link" or df.options != "Company":
			continue
		return clean_company(frappe.db.get_value(doctype, name, fieldname))

	return None


def _infer_company_from_doc(doc: Any) -> str | None:
	if hasattr(doc, "as_dict"):
		values = doc.as_dict()
	elif isinstance(doc, dict):
		values = doc
	else:
		values = {}

	return clean_company(values.get("company") or values.get("company_name"))


def _resolve_report_filter_company(filters: JSONDict | str | None) -> str | None:
	if not filters:
		return None

	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except json.JSONDecodeError:
			return None

	if not isinstance(filters, dict):
		return None

	for key in ("company", "company_name"):
		company = clean_company(filters.get(key))
		if company:
			return company
	return None


def _resolve_default_company() -> str | None:
	return (
		clean_company(frappe.defaults.get_user_default("Company"))
		or clean_company(frappe.defaults.get_user_default("company"))
		or clean_company(frappe.defaults.get_global_default("company"))
		or clean_company(frappe.db.get_single_value("Global Defaults", "default_company"))
	)


def _clean_company(company: Any) -> str | None:
	return clean_company(company)
