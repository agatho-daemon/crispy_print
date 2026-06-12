from typing import Any

import frappe

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	get_branding_profile_presentation_settings as _get_branding_profile_presentation_settings,
)
from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	get_branding_profiles as _get_branding_profiles,
)
from crispy_print.letterhead_lifecycle import (
	get_selectable_letterheads,
	has_letterhead_lifecycle_fields,
)

JSONDict = dict[str, Any]


def get_branding_profiles(company: str | None = None) -> list[JSONDict]:
	return _get_branding_profiles(company=company)


def get_branding_profile_presentation_settings(name: str) -> JSONDict:
	return _get_branding_profile_presentation_settings(name)


def get_letterhead_options(
	company: str | None = None,
	include_current: str | None = None,
) -> list[str]:
	"""Return letterheads allowed by Crispy Print's company policy.

	When Crispy Print's additive lifecycle fields exist, this applies company
	scope, active dates, and retirement policy. Older benches fall back to
	Company.default_letter_head while preserving the current selected value.
	"""
	company = (company or "").strip()
	include_current = (include_current or "").strip()
	if has_letterhead_lifecycle_fields():
		return get_selectable_letterheads(company=company, include_current=include_current)
	if not company:
		return frappe.get_list("Letter Head", pluck="name", order_by="name asc")

	options: list[str] = []
	default_letterhead = _get_company_default_letterhead(company)
	for value in (default_letterhead, include_current):
		if value and value not in options and frappe.db.exists("Letter Head", value):
			options.append(value)
	return options


def _get_company_default_letterhead(company: str) -> str | None:
	if not company or not frappe.db.exists("Company", company):
		return None
	try:
		meta = frappe.get_meta("Company")
	except Exception:
		return None
	if not meta.get_field("default_letter_head"):
		return None
	return frappe.db.get_value("Company", company, "default_letter_head") or None
