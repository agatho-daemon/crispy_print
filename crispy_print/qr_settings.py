from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _

UNSAFE_CUSTOM_QR_FIELDTYPES = {
	"Password",
	"Attach",
	"Attach Image",
	"Table",
	"Table MultiSelect",
	"Section Break",
	"Column Break",
	"Tab Break",
	"HTML",
	"Code",
	"Text Editor",
	"Markdown Editor",
	"Geolocation",
	"Button",
	"Image",
}


def validate_editable_qr_settings(
	presentation_settings: str | dict | None,
	doctype: str | None,
) -> None:
	settings = _parse_settings(presentation_settings)
	qr = settings.get("qr")
	if not isinstance(qr, dict):
		return
	if not qr.get("enabled"):
		return

	mode = qr.get("sourceMode") or ""
	if mode == "basic":
		frappe.throw(
			_(
				"Legacy Basic QR configuration must be explicitly changed to Custom Document QR before saving or publishing."
			)
		)
	if mode not in {"", "custom", "document_code_profile"}:
		frappe.throw(_("Unsupported QR source mode: {0}").format(mode))
	if mode != "custom":
		return
	if not doctype:
		frappe.throw(_("Custom Document QR requires a DocType-backed format."))

	fields = qr.get("fields")
	if not isinstance(fields, list) or not fields:
		frappe.throw(_("Custom Document QR requires at least one document field."))
	if any(not isinstance(fieldname, str) for fieldname in fields):
		frappe.throw(_("Custom Document QR fields must contain exact fieldname strings."))
	if len(fields) != len(set(fields)):
		frappe.throw(_("Custom Document QR fields cannot contain duplicates."))

	meta = frappe.get_meta(doctype)
	field_map = {df.fieldname: df for df in meta.fields if df.fieldname}
	for fieldname in fields:
		if fieldname == "name":
			continue
		df = field_map.get(fieldname)
		if not df:
			frappe.throw(_("Custom Document QR field is unavailable for {0}: {1}").format(doctype, fieldname))
		if (
			getattr(df, "hidden", 0)
			or fieldname.startswith("_")
			or getattr(df, "fieldtype", "") in UNSAFE_CUSTOM_QR_FIELDTYPES
		):
			frappe.throw(_("Custom Document QR field is unsafe or unsupported: {0}").format(fieldname))


def _parse_settings(value: str | dict | None) -> dict[str, Any]:
	if not value:
		return {}
	if isinstance(value, dict):
		return value
	try:
		parsed = json.loads(value)
	except (TypeError, json.JSONDecodeError):
		return {}
	return parsed if isinstance(parsed, dict) else {}
