import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

from crispy_print.letterhead_lifecycle import (
	LETTER_HEAD_DOCTYPE,
	STATUS_FIELD,
	letterhead_lifecycle_fields,
)


def execute():
	create_custom_fields(letterhead_lifecycle_fields(), ignore_validate=True)
	frappe.clear_cache(doctype=LETTER_HEAD_DOCTYPE)
	if not frappe.db.table_exists(LETTER_HEAD_DOCTYPE):
		return
	if STATUS_FIELD not in frappe.db.get_table_columns(LETTER_HEAD_DOCTYPE):
		return
	frappe.db.sql(
		f"""
		update `tab{LETTER_HEAD_DOCTYPE}`
		set {STATUS_FIELD} = 'Active'
		where coalesce({STATUS_FIELD}, '') = ''
		"""
	)
