"""Crispy Print - Typst-based print format builder for Frappe"""

import frappe
from frappe.utils.user import is_website_user

__version__ = "0.2.0-rc.1"

# API methods for bench console convenience
from crispy_print.api.v1 import (
	compile_typst,
	get_crispy_formats_for_doctype,
	get_default_doctypes,
	get_formatted_doc,
	get_typst_local_fonts,
)

__all__ = [
	"compile_typst",
	"get_crispy_formats_for_doctype",
	"get_default_doctypes",
	"get_formatted_doc",
	"get_typst_local_fonts",
]


def check_app_permission():
	if frappe.session.user == "Administrator":
		return True

	if is_website_user():
		return False

	return any(
		frappe.has_permission(doctype, "read")
		for doctype in (
			"Crispy Format",
			"Crispy Template",
			"Crispy Typst Block",
			"Crispy Branding Profile",
			"Crispy Issued Document",
		)
	)
