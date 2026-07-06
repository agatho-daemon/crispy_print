from pathlib import Path

import frappe

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


def before_uninstall():
	pass
