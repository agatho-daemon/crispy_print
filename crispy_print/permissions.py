from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.permissions import get_user_permissions

MANAGER_ROLES = {"System Manager", "Crispy Print Manager"}

COMPANY_SCOPED_DOCTYPES_ALLOW_GLOBAL = {
	"Crispy Format": True,
	"Crispy Branding Profile": False,
	"Crispy Template": True,
	"Crispy Issued Document": False,
	"Crispy Typst Block": True,
	"Crispy Document Code Profile": False,
	"Crispy Fiscal Credential": False,
}


def is_crispy_print_manager(user: str | None = None) -> bool:
	user = user or frappe.session.user
	if user == "Administrator":
		return True
	return bool(MANAGER_ROLES.intersection(set(frappe.get_roles(user))))


def get_allowed_company_names(
	user: str | None = None,
	doctype: str | None = None,
) -> list[str] | None:
	"""Return Company User Permission values, or None when unrestricted for this DocType."""
	user = user or frappe.session.user
	if is_crispy_print_manager(user):
		return None

	company_permissions = get_user_permissions(user).get("Company") or []
	if not company_permissions:
		return None

	allowed: list[str] = []
	for permission in company_permissions:
		applicable_for = _get_permission_value(permission, "applicable_for")
		if applicable_for and doctype and applicable_for != doctype:
			continue
		if applicable_for and not doctype:
			continue

		company = _clean_company(_get_permission_value(permission, "doc"))
		if company and company not in allowed:
			allowed.append(company)

	return allowed or None


def has_company_access(
	company: str | None,
	*,
	user: str | None = None,
	doctype: str | None = None,
) -> bool:
	company = _clean_company(company)
	if not company:
		return False

	allowed_companies = get_allowed_company_names(user=user, doctype=doctype)
	if allowed_companies is None:
		return True
	return company in allowed_companies


def ensure_company_access(
	company: str | None,
	*,
	user: str | None = None,
	doctype: str | None = None,
) -> None:
	if has_company_access(company, user=user, doctype=doctype):
		return

	frappe.throw(
		_("Not permitted for Company {0}.").format(frappe.bold(company)),
		frappe.PermissionError,
	)


def company_permission_query_condition(
	user: str | None = None,
	doctype: str | None = None,
) -> str:
	if not doctype or doctype not in COMPANY_SCOPED_DOCTYPES_ALLOW_GLOBAL:
		return ""
	if is_crispy_print_manager(user):
		return ""

	allowed_companies = get_allowed_company_names(user=user, doctype=doctype)
	if allowed_companies is None:
		return ""
	if not allowed_companies:
		return "1=0"

	company_field = f"`tab{doctype}`.`company`"
	escaped_companies = ", ".join(frappe.db.escape(company, percent=False) for company in allowed_companies)
	condition = f"{company_field} in ({escaped_companies})"
	if COMPANY_SCOPED_DOCTYPES_ALLOW_GLOBAL[doctype]:
		return f"(ifnull({company_field}, '')='' or {condition})"
	return condition


def _get_permission_value(permission: Any, key: str) -> Any:
	if isinstance(permission, dict):
		return permission.get(key)
	return getattr(permission, key, None)


def _clean_company(company: Any) -> str | None:
	value = str(company or "").strip()
	return value or None
