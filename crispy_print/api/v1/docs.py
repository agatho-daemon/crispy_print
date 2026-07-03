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
	data = doc.as_dict()
	data["__crispy_print_context"] = print_policy

	field_map = {df.fieldname: df for df in meta.fields if df.fieldname}

	for df in meta.fields:
		fieldname = df.fieldname
		if not fieldname or fieldname not in data:
			continue

		if df.fieldtype == "Table" and df.options:
			child_meta = frappe.get_meta(df.options)
			child_field_map = {cdf.fieldname: cdf for cdf in child_meta.fields if cdf.fieldname}
			rows = data.get(fieldname) or []
			formatted_rows = []
			for row in rows:
				if not isinstance(row, dict):
					formatted_rows.append(row)
					continue
				formatted_row = dict(row)
				for key, value in row.items():
					cdf = child_field_map.get(key)
					if not cdf:
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

		df_for_field = field_map.get(fieldname)
		if not df_for_field:
			continue
		try:
			formatted_value = frappe.format(data.get(fieldname), df_for_field, doc=doc, translated=False)
			data[fieldname] = normalize_html_text(formatted_value)
		except Exception:
			_log_format_fallback(doctype, name, fieldname)
			data[fieldname] = normalize_html_text(data.get(fieldname))

	document_code = _build_document_code_preview(doc, qr_source_mode=qr_source_mode)
	if document_code:
		data["__crispy_document_code"] = document_code

	return data


def _build_document_code_preview(doc, qr_source_mode: str | None = None) -> dict | None:
	if (qr_source_mode or "").strip() != "document_code_profile":
		return None
	try:
		result = get_preferred_document_code_for_doc(doc)
	except Exception:
		return None
	if not result:
		return None
	return {
		"code_purpose": result.get("code_purpose"),
		"environment": result.get("environment"),
		"profile_name": result.get("profile_name"),
		"code_format": result.get("code_format"),
		"code_symbology": result.get("code_symbology"),
		"payload": result.get("payload"),
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
