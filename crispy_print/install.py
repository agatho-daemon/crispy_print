from pathlib import Path

import frappe
from frappe.model.base_document import get_controller

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	ensure_default_branding_profiles_for_all_companies,
)

SITE_FONT_PATH_PARTS = ("private", "files", "crispy_print", "fonts")


def get_site_font_directory() -> str:
	return str(Path(frappe.get_site_path(*SITE_FONT_PATH_PARTS)).resolve())


def ensure_site_font_directory() -> str:
	path = get_site_font_directory()
	frappe.create_folder(path)
	return path


def after_install():
	ensure_site_font_directory()
	ensure_default_branding_profiles_for_all_companies()
	ensure_print_engine()


def after_sync():
	ensure_print_engine()


def before_uninstall():
	pass


def has_print_engine_doctype() -> bool:
	if not frappe.db.exists("DocType", "Print Engine"):
		return False
	try:
		get_controller("Print Engine")
	except ImportError:
		return False
	return True


def ensure_print_engine():
	if not has_print_engine_doctype():
		return

	engine_values = {
		"engine_name": "crispy_print",
		"label": "Crispy Print",
		"enabled": 1,
		"entry_type": "Client Renderer",
		"standard": 1,
		"app_name": "crispy_print",
		"client_renderer": "crispy_print",
		"client_script": "/assets/crispy_print/js/crispy_print_engine.js",
		"description": "Routes document printing to the Crispy Print Typst preview engine.",
	}

	if frappe.db.exists("Print Engine", "crispy_print"):
		engine = frappe.get_doc("Print Engine", "crispy_print")
		changed = False
		for fieldname, value in engine_values.items():
			if engine.get(fieldname) != value:
				engine.set(fieldname, value)
				changed = True
		if changed:
			engine.save(ignore_permissions=True)
		return

	frappe.get_doc(
		{
			"doctype": "Print Engine",
			**engine_values,
		}
	).insert(ignore_permissions=True)
