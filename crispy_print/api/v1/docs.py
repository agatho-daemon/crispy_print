import json
from typing import Any

import frappe
from frappe import _

from crispy_print.crispy_print.doctype.crispy_print_settings.crispy_print_settings import (
	validate_document_print_policy,
)

from .document_codes import get_preferred_document_code_for_doc
from .text import normalize_html_text


def get_formatted_doc(
	doctype: str,
	name: str,
	qr_source_mode: str | None = None,
	fields: list[str] | str | None = None,
	allow_document_code_preview: int | bool = 0,
) -> dict:
	"""
	Return a document with server-side formatted values (currency/date/percent/etc.).

	This keeps Typst preview consistent across pages without relying on client-side meta.
	"""
	if not doctype or not name:
		frappe.throw(_("doctype and name are required"))

	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	print_policy = validate_document_print_policy(doc)
	meta = frappe.get_meta(doctype)
	raw_data = doc.as_dict()
	requested = _parse_requested_fields(fields)
	field_map = {df.fieldname: df for df in meta.fields if df.fieldname}
	data = _build_initial_payload(doc, raw_data, doctype, print_policy, requested, field_map)
	requested_children = _requested_child_fields(requested)
	fieldnames = _fieldnames_to_format(raw_data, field_map, requested)

	for fieldname in fieldnames:
		df = field_map.get(fieldname)
		if not df:
			continue
		if requested is not None and not _is_supported_render_field(df):
			continue
		fieldname = df.fieldname
		if not fieldname or fieldname not in data:
			continue

		if df.fieldtype == "Table" and df.options:
			child_meta = frappe.get_meta(df.options)
			child_field_map = {cdf.fieldname: cdf for cdf in child_meta.fields if cdf.fieldname}
			rows = data.get(fieldname) or []
			child_fieldnames = requested_children.get(fieldname)
			formatted_rows = []
			for row in rows:
				if not isinstance(row, dict):
					formatted_rows.append(row)
					continue
				row_values = dict(row)
				if child_fieldnames is None:
					keys = list(row_values)
				else:
					keys = [key for key in child_fieldnames if key in row_values]
				formatted_row = {}
				for key in keys:
					value = row_values.get(key)
					cdf = child_field_map.get(key)
					if not cdf:
						continue
					if requested is not None and not _is_supported_render_field(cdf):
						continue
					try:
						formatted_value = frappe.format(value, cdf, doc=doc, translated=False)
						formatted_row[key] = normalize_html_text(formatted_value)
					except Exception:
						_log_format_fallback(doctype, name, f"{fieldname}.{key}")
						formatted_row[key] = normalize_html_text(value)
				formatted_rows.append(formatted_row)
			data[fieldname] = formatted_rows
			continue

		try:
			formatted_value = frappe.format(data.get(fieldname), df, doc=doc, translated=False)
			data[fieldname] = normalize_html_text(formatted_value)
		except Exception:
			_log_format_fallback(doctype, name, fieldname)
			data[fieldname] = normalize_html_text(data.get(fieldname))

	document_code = _build_document_code_preview(
		doc,
		qr_source_mode=qr_source_mode,
		allow_document_code_preview=allow_document_code_preview,
	)
	if document_code:
		data["__crispy_document_code"] = document_code

	return data


def _parse_requested_fields(fields: list[str] | str | None) -> set[str] | None:
	if fields is None:
		return None
	if isinstance(fields, str):
		raw = fields.strip()
		if not raw:
			return set()
		try:
			parsed = json.loads(raw)
		except json.JSONDecodeError:
			parsed = [part.strip() for part in raw.split(",")]
	else:
		parsed = fields
	if not isinstance(parsed, list | tuple | set):
		frappe.throw(_("fields must be a list of field paths"))

	clean: set[str] = set()
	for value in parsed:
		field_path = _clean_field_path(value)
		if field_path:
			clean.add(field_path)
	return clean


def _clean_field_path(value: Any) -> str | None:
	text = str(value or "").strip()
	if not text:
		return None
	parts = text.split(".")
	if len(parts) > 2:
		return None
	if not all(part and part.replace("_", "").isalnum() for part in parts):
		return None
	return ".".join(parts)


def _build_initial_payload(
	doc,
	raw_data: dict,
	doctype: str,
	print_policy: dict,
	requested: set[str] | None,
	field_map: dict,
) -> dict:
	if requested is None:
		data = dict(raw_data)
	else:
		data = {}
		for fieldname in _requested_top_fields(requested):
			if fieldname in raw_data and _is_supported_requested_field(fieldname, field_map):
				data[fieldname] = raw_data.get(fieldname)

	data["doctype"] = raw_data.get("doctype") or getattr(doc, "doctype", None) or doctype
	data["name"] = raw_data.get("name") or getattr(doc, "name", None)
	for essential in ("docstatus", "modified"):
		if essential in raw_data:
			data[essential] = raw_data.get(essential)
	data["__crispy_print_context"] = print_policy
	return data


def _requested_top_fields(requested: set[str] | None) -> set[str]:
	if requested is None:
		return set()
	return {field_path.split(".", 1)[0] for field_path in requested}


def _requested_child_fields(requested: set[str] | None) -> dict[str, set[str] | None]:
	if requested is None:
		return {}
	children: dict[str, set[str] | None] = {}
	for field_path in requested:
		if "." not in field_path:
			children.setdefault(field_path, None)
			continue
		parent, child = field_path.split(".", 1)
		if children.get(parent) is None and parent in children:
			continue
		children.setdefault(parent, set())
		if isinstance(children[parent], set):
			children[parent].add(child)
	return children


def _fieldnames_to_format(
	raw_data: dict,
	field_map: dict,
	requested: set[str] | None,
) -> list[str]:
	if requested is None:
		return [fieldname for fieldname in field_map if fieldname in raw_data]
	return [
		fieldname
		for fieldname in _requested_top_fields(requested)
		if fieldname in raw_data and _is_supported_requested_field(fieldname, field_map)
	]


def _is_supported_requested_field(fieldname: str, field_map: dict) -> bool:
	df = field_map.get(fieldname)
	return bool(df and _is_supported_render_field(df))


def _is_supported_render_field(df) -> bool:
	if getattr(df, "hidden", 0):
		return False
	return getattr(df, "fieldtype", None) not in {"Password"}


def _truthy(value: int | bool | str | None) -> bool:
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return bool(value)


def _build_document_code_preview(
	doc,
	qr_source_mode: str | None = None,
	allow_document_code_preview: int | bool = 0,
) -> dict | None:
	if (qr_source_mode or "").strip() != "document_code_profile":
		return None
	if not _truthy(allow_document_code_preview):
		return None
	try:
		result = get_preferred_document_code_for_doc(doc, allow_custom_methods=False)
	except Exception:
		return None
	if not result:
		return None
	profile_name = result.get("profile_name")
	if profile_name:
		frappe.get_doc("Crispy Document Code Profile", profile_name).check_permission("read")
	return {
		"code_purpose": result.get("code_purpose"),
		"environment": result.get("environment"),
		"profile_name": result.get("profile_name"),
		"code_format": result.get("code_format"),
		"code_symbology": result.get("code_symbology"),
		"encoded_value": result.get("encoded_value"),
	}


def _log_format_fallback(doctype: str, name: str, fieldname: str) -> None:
	frappe.logger("crispy_print").debug(
		"Falling back to raw value while formatting %s %s field %s",
		doctype,
		name,
		fieldname,
		exc_info=True,
	)
