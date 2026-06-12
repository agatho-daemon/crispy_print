import frappe


def execute():
	if not frappe.db.table_exists("Crispy Template"):
		return
	if "snapshot_hash_version" not in frappe.db.get_table_columns("Crispy Template"):
		return
	frappe.db.sql(
		"""
		update `tabCrispy Template`
		set snapshot_hash_version = 'v1'
		where coalesce(snapshot_hash_version, '') = ''
		"""
	)
