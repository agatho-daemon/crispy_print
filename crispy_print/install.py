import frappe

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	ensure_default_branding_profiles_for_all_companies,
)

SITE_FONT_PATH_PARTS = ("private", "files", "crispy_print", "fonts")
APP_DESKTOP_ICON_NAME = "Crispy Print"
STUDIO_DESKTOP_ICON_NAME = "Crispy Studio"
STUDIO_WORKSPACE_SIDEBAR_NAME = "Crispy Studio"
AUTO_WORKSPACE_SIDEBAR_NAME = "Crispy Print"


def get_site_font_directory() -> str:
	return frappe.get_site_path(*SITE_FONT_PATH_PARTS)


def ensure_site_font_directory() -> str:
	path = get_site_font_directory()
	frappe.create_folder(path)
	return path


def after_install():
	ensure_site_font_directory()
	ensure_default_branding_profiles_for_all_companies()


def after_sync():
	cleanup_auto_generated_navigation_records()


def before_uninstall():
	cleanup_crispy_print_navigation_records()


def cleanup_auto_generated_navigation_records() -> None:
	"""Remove Frappe-generated navigation records that collide with app exports.

	Crispy Print keeps the public workspace named "Crispy Print" but ships the
	curated Frappe v16 sidebar as "Crispy Studio" to avoid colliding with the app
	Desktop Icon. Frappe still auto-generates a non-standard sidebar named after
	the public workspace during install; remove that local generated record so the
	curated sidebar remains the single navigation surface.
	"""
	_delete_workspace_sidebar_if_local(AUTO_WORKSPACE_SIDEBAR_NAME)
	_delete_desktop_icon_if_not_app(APP_DESKTOP_ICON_NAME)


def cleanup_crispy_print_navigation_records() -> None:
	"""Delete app navigation records without deleting exported JSON source files."""
	for name in (APP_DESKTOP_ICON_NAME, STUDIO_DESKTOP_ICON_NAME):
		_delete_doc_if_exists("Desktop Icon", name)
	for name in (STUDIO_WORKSPACE_SIDEBAR_NAME, AUTO_WORKSPACE_SIDEBAR_NAME):
		_delete_doc_if_exists("Workspace Sidebar", name)


def _delete_workspace_sidebar_if_local(name: str) -> None:
	if not frappe.db.exists("Workspace Sidebar", name):
		return
	app = frappe.db.get_value("Workspace Sidebar", name, "app")
	standard = frappe.db.get_value("Workspace Sidebar", name, "standard")
	if not app and not standard:
		_delete_doc_if_exists("Workspace Sidebar", name)


def _delete_desktop_icon_if_not_app(name: str) -> None:
	if not frappe.db.exists("Desktop Icon", name):
		return
	icon_type = frappe.db.get_value("Desktop Icon", name, "icon_type")
	if icon_type != "App":
		_delete_doc_if_exists("Desktop Icon", name)


def _delete_doc_if_exists(doctype: str, name: str) -> None:
	if not frappe.db.exists(doctype, name):
		return
	frappe.delete_doc(
		doctype,
		name,
		force=True,
		ignore_permissions=True,
		ignore_on_trash=True,
		ignore_missing=True,
	)
