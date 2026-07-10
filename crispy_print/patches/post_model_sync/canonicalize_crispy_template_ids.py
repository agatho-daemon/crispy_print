import frappe
from frappe.model.rename_doc import rename_doc

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import build_template_id


def execute():
	if not frappe.db.table_exists("Crispy Template"):
		return

	for row in frappe.get_all(
		"Crispy Template",
		fields=["name", "template_name", "company", "version", "source_crispy_format"],
	):
		base_key = _get_base_key(row)
		canonical_id = build_template_id(base_key, row.get("company"), row.get("version"))
		current_name = row.get("name")

		if current_name != canonical_id:
			if frappe.db.exists("Crispy Template", canonical_id):
				frappe.throw(
					f"Cannot canonicalize Crispy Template {current_name}: target {canonical_id} already exists. "
					"Resolve the duplicate template records manually and take a database backup before "
					"rerunning migration."
				)
			rename_doc(
				"Crispy Template",
				current_name,
				canonical_id,
				force=True,
				ignore_permissions=True,
			)

		if frappe.db.get_value("Crispy Template", canonical_id, "template_name") != canonical_id:
			frappe.db.set_value(
				"Crispy Template",
				canonical_id,
				"template_name",
				canonical_id,
				update_modified=False,
			)

	frappe.clear_cache(doctype="Crispy Template")


def _get_base_key(row) -> str:
	source_format = row.get("source_crispy_format")
	if source_format and frappe.db.exists("Crispy Format", source_format):
		return source_format
	return row.get("template_name") or row.get("name")
