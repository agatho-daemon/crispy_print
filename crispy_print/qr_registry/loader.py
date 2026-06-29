from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import frappe
from frappe import _

JSONDict = dict[str, Any]

REGISTRY_VERSION = 1
REGISTRY_FILENAME = "fields.v1.json"


def get_qr_registry_metadata() -> JSONDict:
	registry = get_qr_field_registry()
	return {
		"version": registry["version"],
		"doctypes": sorted(registry["doctypes"].keys()),
		"authorities": sorted(registry.get("authorities", {}).keys()),
		"business_field_sets": sorted(registry.get("business_field_sets", {}).keys()),
	}


def get_qr_fields(
	doctype: str,
	authority_code: str | None = None,
	include_business_fields: int | bool = 1,
) -> JSONDict:
	registry = get_qr_field_registry()
	doctype = _clean_required_text(doctype, _("DocType"))
	doctype_registry = registry["doctypes"].get(doctype)
	if not doctype_registry:
		return {
			"doctype": doctype,
			"fields": [],
			"authority": None,
			"business_field_sets": [],
		}

	fields = [
		{"key": key, **definition} for key, definition in sorted(doctype_registry.get("fields", {}).items())
	]
	authority = _get_authority_for_doctype(registry, doctype, authority_code)
	if authority:
		allowed = set(authority.get("required_fields", [])) | set(authority.get("optional_fields", []))
		fields = [
			{
				**field,
				"required": field["key"] in authority.get("required_fields", []),
				"optional": field["key"] in authority.get("optional_fields", []),
			}
			for field in fields
			if field["key"] in allowed
		]

	business_sets = []
	if include_business_fields:
		business_sets = [
			{"key": key, **field_set}
			for key, field_set in sorted(registry.get("business_field_sets", {}).items())
			if field_set.get("doctype") == doctype
		]

	return {
		"doctype": doctype,
		"fields": fields,
		"authority": authority,
		"business_field_sets": business_sets,
	}


def get_allowed_qr_field_keys(doctype: str, authority_code: str | None = None) -> set[str]:
	return {field["key"] for field in get_qr_fields(doctype, authority_code=authority_code)["fields"]}


def get_business_field_set(key: str) -> JSONDict:
	registry = get_qr_field_registry()
	key = _clean_required_text(key, _("Business Field Set"))
	field_set = registry.get("business_field_sets", {}).get(key)
	if not field_set:
		frappe.throw(_("Unknown QR business field set: {0}").format(key))
	return {"key": key, **field_set}


def get_qr_field_definition(doctype: str, field_key: str) -> JSONDict:
	registry = get_qr_field_registry()
	doctype = _clean_required_text(doctype, _("DocType"))
	field_key = _clean_required_text(field_key, _("QR Field"))
	field = registry.get("doctypes", {}).get(doctype, {}).get("fields", {}).get(field_key)
	if not field:
		frappe.throw(_("Selected QR fields are not allowed for {0}: {1}").format(doctype, field_key))
	return {"key": field_key, **field}


def validate_qr_field_selection(
	doctype: str,
	selected_fields: list[str] | JSONDict,
	authority_code: str | None = None,
) -> None:
	if not selected_fields:
		return
	allowed = get_allowed_qr_field_keys(doctype, authority_code=authority_code)
	if not allowed:
		frappe.throw(_("No QR field registry is defined for DocType {0}.").format(doctype))

	selected_keys = _selected_field_keys(selected_fields)
	unknown = sorted(key for key in selected_keys if key not in allowed)
	if unknown:
		frappe.throw(
			_("Selected QR fields are not allowed for {0}: {1}").format(
				doctype,
				", ".join(unknown),
			)
		)


@lru_cache(maxsize=1)
def get_qr_field_registry() -> JSONDict:
	path = Path(__file__).with_name(REGISTRY_FILENAME)
	try:
		registry = json.loads(path.read_text(encoding="utf-8"))
	except OSError as exc:
		frappe.throw(_("Unable to read QR field registry: {0}").format(exc))
	except json.JSONDecodeError as exc:
		frappe.throw(_("QR field registry contains invalid JSON: {0}").format(exc))

	_validate_registry(registry)
	return registry


def _validate_registry(registry: Any) -> None:
	if not isinstance(registry, dict):
		frappe.throw(_("QR field registry must be a JSON object."))
	if registry.get("version") != REGISTRY_VERSION:
		frappe.throw(_("Unsupported QR field registry version: {0}").format(registry.get("version")))

	doctypes = registry.get("doctypes")
	if not isinstance(doctypes, dict) or not doctypes:
		frappe.throw(_("QR field registry must define doctypes."))

	for doctype, config in doctypes.items():
		if not isinstance(config, dict):
			frappe.throw(_("QR field registry for {0} must be an object.").format(doctype))
		fields = config.get("fields")
		if not isinstance(fields, dict) or not fields:
			frappe.throw(_("QR field registry for {0} must define fields.").format(doctype))
		for key, definition in fields.items():
			_validate_field_definition(doctype, key, definition)

	for authority_code, authority in (registry.get("authorities") or {}).items():
		_validate_field_set(
			registry,
			authority,
			_("Authority {0}").format(authority_code),
			required_keys=("required_fields", "optional_fields"),
		)

	for key, field_set in (registry.get("business_field_sets") or {}).items():
		_validate_field_set(
			registry,
			field_set,
			_("Business field set {0}").format(key),
			required_keys=("fields",),
		)


def _validate_field_definition(doctype: str, key: str, definition: Any) -> None:
	if not isinstance(definition, dict):
		frappe.throw(_("QR field {0}.{1} must be an object.").format(doctype, key))
	for required_key in ("label", "path", "source", "datatype"):
		if not str(definition.get(required_key) or "").strip():
			frappe.throw(_("QR field {0}.{1} is missing {2}.").format(doctype, key, required_key))
	if ".." in key or key.startswith(".") or key.endswith("."):
		frappe.throw(_("QR field key is invalid: {0}.{1}").format(doctype, key))


def _validate_field_set(
	registry: JSONDict,
	field_set: Any,
	label: str,
	required_keys: tuple[str, ...],
) -> None:
	if not isinstance(field_set, dict):
		frappe.throw(_("{0} must be an object.").format(label))
	doctype = field_set.get("doctype")
	if not doctype or doctype not in registry["doctypes"]:
		frappe.throw(_("{0} references an unknown DocType: {1}").format(label, doctype))

	known_fields = set(registry["doctypes"][doctype]["fields"].keys())
	for field_key in required_keys:
		fields = field_set.get(field_key)
		if not isinstance(fields, list):
			frappe.throw(_("{0}.{1} must be a list.").format(label, field_key))
		unknown = sorted(str(field) for field in fields if str(field) not in known_fields)
		if unknown:
			frappe.throw(
				_("{0}.{1} references unknown fields: {2}").format(
					label,
					field_key,
					", ".join(unknown),
				)
			)


def _get_authority_for_doctype(
	registry: JSONDict,
	doctype: str,
	authority_code: str | None,
) -> JSONDict | None:
	if not authority_code:
		return None
	authority_code = authority_code.strip()
	authority = registry.get("authorities", {}).get(authority_code)
	if not authority or authority.get("doctype") != doctype:
		return None
	return {"key": authority_code, **authority}


def _selected_field_keys(selected_fields: list[str] | JSONDict) -> set[str]:
	if isinstance(selected_fields, dict):
		return {str(value) for value in selected_fields.values()}
	return {str(value) for value in selected_fields}


def _clean_required_text(value: str, label: str) -> str:
	text = str(value or "").strip()
	if not text:
		frappe.throw(_("{0} is required.").format(label))
	return text
