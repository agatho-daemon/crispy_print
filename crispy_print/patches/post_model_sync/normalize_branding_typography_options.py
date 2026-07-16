import frappe

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	TYPOGRAPHY_PREFIXES,
)


def execute():
	fields = [
		*(f"{prefix}_font_style" for prefix in TYPOGRAPHY_PREFIXES),
		*(f"{prefix}_font_weight" for prefix in TYPOGRAPHY_PREFIXES),
		"report_title_font_weight",
	]
	for profile in frappe.get_all("Crispy Branding Profile", fields=["name", *fields]):
		values = {
			fieldname: str(profile.get(fieldname) or "").strip().lower()
			for fieldname in fields
			if profile.get(fieldname)
		}
		if values:
			frappe.db.set_value(
				"Crispy Branding Profile",
				profile.name,
				values,
				update_modified=False,
			)
