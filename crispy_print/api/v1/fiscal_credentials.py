from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime

JSONDict = dict[str, Any]

CREDENTIAL_DOCTYPE = "Crispy Fiscal Credential"
REGULATORY_PROFILE_DOCTYPE = "Crispy QR Regulatory Profile"

SECRET_FIELDS = {
	"private_key_password",
	"api_client_secret",
	"api_token",
}

PUBLIC_CREDENTIAL_FIELDS = [
	"name",
	"credential_name",
	"enabled",
	"company",
	"country",
	"authority_code",
	"regulatory_profile",
	"environment",
	"valid_from",
	"valid_until",
	"modified",
]


def get_fiscal_credential_status(
	company: str,
	regulatory_profile: str,
	environment: str = "Production",
	authority_code: str | None = None,
) -> JSONDict:
	"""Return frontend-safe fiscal credential status.

	This intentionally returns only non-secret metadata. Server-side encoders that need
	credentials should call get_fiscal_credential_doc/get_fiscal_credential_secret.
	"""
	candidates = _get_candidate_rows(
		company=company,
		regulatory_profile=regulatory_profile,
		environment=environment,
		authority_code=authority_code,
		enabled_only=False,
		ignore_permissions=False,
	)
	active = [row for row in candidates if _is_active(row)]
	warnings: list[str] = []

	if len(active) > 1:
		return {
			"exists": True,
			"valid": False,
			"credential": None,
			"warnings": [_("Multiple active fiscal credentials match these filters.")],
		}

	if active:
		row = active[0]
		warnings.extend(_expiry_warnings(row))
		return {
			"exists": True,
			"valid": True,
			"credential": _to_public_credential(row),
			"warnings": warnings,
		}

	if not candidates:
		return {
			"exists": False,
			"valid": False,
			"credential": None,
			"warnings": [_("No fiscal credential found for these filters.")],
		}

	row = candidates[0]
	warnings.extend(_inactive_warnings(row))
	return {
		"exists": True,
		"valid": False,
		"credential": _to_public_credential(row),
		"warnings": warnings,
	}


def get_fiscal_credential_doc(
	company: str,
	regulatory_profile: str,
	environment: str = "Production",
	authority_code: str | None = None,
) -> Any:
	"""Resolve the single active credential document for backend-only use."""
	rows = _get_candidate_rows(
		company=company,
		regulatory_profile=regulatory_profile,
		environment=environment,
		authority_code=authority_code,
		enabled_only=True,
		ignore_permissions=True,
	)
	active = [row for row in rows if _is_active(row)]

	if not active:
		frappe.throw(_("No active fiscal credential found for these filters."))

	if len(active) > 1:
		frappe.throw(_("Multiple active fiscal credentials match these filters."))

	return frappe.get_doc(CREDENTIAL_DOCTYPE, active[0]["name"])


def get_fiscal_credential_secret(credential_name: str, fieldname: str) -> str | None:
	"""Read an encrypted password field for backend-only encoder code."""
	if fieldname not in SECRET_FIELDS:
		frappe.throw(_("Field {0} is not an allowed fiscal credential secret field.").format(fieldname))

	doc = frappe.get_doc(CREDENTIAL_DOCTYPE, credential_name)
	return doc.get_password(fieldname=fieldname, raise_exception=False)


def _get_candidate_rows(
	company: str,
	regulatory_profile: str,
	environment: str = "Production",
	authority_code: str | None = None,
	enabled_only: bool = True,
	ignore_permissions: bool = True,
) -> list[JSONDict]:
	_assert_required(company=company, regulatory_profile=regulatory_profile)
	environment = environment or "Production"
	authority_code = authority_code or _get_profile_authority_code(regulatory_profile)

	filters: JSONDict = {
		"company": company,
		"regulatory_profile": regulatory_profile,
		"environment": environment,
	}
	if enabled_only:
		filters["enabled"] = 1
	if authority_code:
		filters["authority_code"] = authority_code

	query = frappe.get_all if ignore_permissions else frappe.get_list
	return query(
		CREDENTIAL_DOCTYPE,
		filters=filters,
		fields=PUBLIC_CREDENTIAL_FIELDS,
		order_by="modified desc",
	)


def _assert_required(**values: str | None) -> None:
	missing = [key for key, value in values.items() if not value]
	if missing:
		frappe.throw(_("Missing required fiscal credential filters: {0}").format(", ".join(missing)))


def _get_profile_authority_code(regulatory_profile: str) -> str | None:
	if not regulatory_profile:
		return None
	if not frappe.db.exists(REGULATORY_PROFILE_DOCTYPE, regulatory_profile):
		return None
	return frappe.db.get_value(REGULATORY_PROFILE_DOCTYPE, regulatory_profile, "authority_code")


def _is_active(row: JSONDict) -> bool:
	if not row.get("enabled"):
		return False

	now = now_datetime()
	valid_from = row.get("valid_from")
	valid_until = row.get("valid_until")
	if valid_from and get_datetime(valid_from) > now:
		return False
	if valid_until and get_datetime(valid_until) < now:
		return False
	return True


def _is_expired(row: JSONDict) -> bool:
	valid_until = row.get("valid_until")
	return bool(valid_until and get_datetime(valid_until) < now_datetime())


def _is_not_yet_valid(row: JSONDict) -> bool:
	valid_from = row.get("valid_from")
	return bool(valid_from and get_datetime(valid_from) > now_datetime())


def _to_public_credential(row: JSONDict) -> JSONDict:
	credential = {field: row.get(field) for field in PUBLIC_CREDENTIAL_FIELDS if field in row}
	credential["expired"] = _is_expired(row)
	credential["not_yet_valid"] = _is_not_yet_valid(row)
	return credential


def _inactive_warnings(row: JSONDict) -> list[str]:
	warnings: list[str] = []
	if not row.get("enabled"):
		warnings.append(_("The matching fiscal credential is disabled."))
	if _is_expired(row):
		warnings.append(_("The matching fiscal credential is expired."))
	if _is_not_yet_valid(row):
		warnings.append(_("The matching fiscal credential is not valid yet."))
	return warnings or [_("No active fiscal credential found for these filters.")]


def _expiry_warnings(row: JSONDict) -> list[str]:
	valid_until = row.get("valid_until")
	if not valid_until:
		return []

	if get_datetime(valid_until) <= get_datetime(add_days(now_datetime(), 30)):
		return [_("The active fiscal credential expires within 30 days.")]
	return []
