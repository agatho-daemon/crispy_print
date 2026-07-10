from __future__ import annotations

from typing import Any

import frappe
from frappe import _


def clean(value: Any) -> str:
	return str(value or "").strip()


def truthy(value: int | bool | str | None) -> bool:
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return bool(value)


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


def require_target_company(company: str | None) -> str:
	company = clean(company) or None
	if not company:
		frappe.throw(_("Target company is required."))
	if not frappe.db.exists("Company", company):
		frappe.throw(_("Company {0} does not exist.").format(company))
	return company
