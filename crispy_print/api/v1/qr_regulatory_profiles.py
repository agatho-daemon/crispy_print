from __future__ import annotations

from typing import Any

import frappe

JSONDict = dict[str, Any]

DOCTYPE = "Crispy QR Regulatory Profile"

PUBLIC_FIELDS = [
	"name",
	"profile_name",
	"enabled",
	"country",
	"authority_code",
	"standard",
	"version",
	"payload_format",
	"output_encoding",
	"error_correction",
	"include_signature",
	"include_hash",
	"requires_online_verification",
	"verification_url_template",
	"encoder_key",
	"encoder_settings_json",
]


def get_qr_regulatory_profiles(
	country: str | None = None,
	authority_code: str | None = None,
	enabled_only: int | bool = 1,
) -> list[JSONDict]:
	filters: JSONDict = {}
	if enabled_only:
		filters["enabled"] = 1
	if country:
		filters["country"] = country
	if authority_code:
		filters["authority_code"] = authority_code

	return frappe.get_list(
		DOCTYPE,
		filters=filters,
		fields=PUBLIC_FIELDS,
		order_by="country asc, standard asc, profile_name asc",
	)


def get_qr_regulatory_profile(name: str) -> JSONDict:
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	return {field: doc.get(field) for field in PUBLIC_FIELDS}
