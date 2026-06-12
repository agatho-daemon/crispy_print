import frappe

from crispy_print.letterhead_lifecycle import LETTER_HEAD_DOCTYPE, letterhead_lifecycle_fields


def execute():
	field_labels = {
		field["fieldname"]: field["label"]
		for field in letterhead_lifecycle_fields()[LETTER_HEAD_DOCTYPE]
		if field.get("label")
	}
	for fieldname, label in field_labels.items():
		frappe.db.set_value(
			"Custom Field",
			{"dt": LETTER_HEAD_DOCTYPE, "fieldname": fieldname},
			"label",
			label,
			update_modified=False,
		)
	frappe.clear_cache(doctype=LETTER_HEAD_DOCTYPE)
