import frappe
from frappe import _


def get_formatted_doc(doctype: str, name: str) -> dict:
	"""
	Return a document with server-side formatted values (currency/date/percent/etc.).

	This keeps Typst preview consistent across pages without relying on client-side meta.
	"""
	if not doctype or not name:
		frappe.throw(_("doctype and name are required"))

	doc = frappe.get_doc(doctype, name)
	meta = frappe.get_meta(doctype)
	data = doc.as_dict()

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
						if cdf.fieldtype in ("Text Editor", "HTML") and isinstance(formatted_value, str):
							formatted_value = frappe.utils.strip_html(formatted_value)
						formatted_row[key] = formatted_value
					except Exception:
						formatted_row[key] = value
				formatted_rows.append(formatted_row)
			data[fieldname] = formatted_rows
			continue

		df_for_field = field_map.get(fieldname)
		if not df_for_field:
			continue
		try:
			formatted_value = frappe.format(data.get(fieldname), df_for_field, doc=doc, translated=False)
			if df_for_field.fieldtype in ("Text Editor", "HTML") and isinstance(formatted_value, str):
				formatted_value = frappe.utils.strip_html(formatted_value)
			data[fieldname] = formatted_value
		except Exception:
			pass

	return data
