import frappe


def execute():
	rename_map = {
		"crispy-print-builder": "crispy-format-builder",
		"typst-print": "crispy-print",
	}

	for old, new in rename_map.items():
		if frappe.db.exists("Page", old) and not frappe.db.exists("Page", new):
			frappe.rename_doc("Page", old, new, force=True)
			try:
				frappe.db.set_value("Page", new, "page_name", new)
			except Exception:
				# Some versions use name as page_name; ignore if field missing.
				pass

