import frappe


def execute():
	if not frappe.db.table_exists("Crispy Template"):
		return
	if "snapshot_hash_version" not in frappe.db.get_table_columns("Crispy Template"):
		return
	frappe.db.set_value(
		"Crispy Template",
		{"snapshot_hash_version": ["is", "not set"]},
		"snapshot_hash_version",
		"v1",
		update_modified=False,
	)
