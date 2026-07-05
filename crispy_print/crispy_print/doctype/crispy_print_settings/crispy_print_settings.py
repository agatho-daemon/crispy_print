# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

import shutil
import stat
from pathlib import Path

import frappe
from frappe import _
from frappe.model.document import Document

from crispy_print.install import ensure_site_font_directory, get_site_font_directory

FONT_CACHE_KEY = "crispy_print:typst_local_fonts:v3"
MAX_UPLOADED_FONT_BYTES = 25 * 1024 * 1024
ALLOWED_FONT_EXTENSIONS = {".ttf", ".otf", ".ttc", ".woff", ".woff2"}


class CrispyPrintSettings(Document):
	def validate(self):
		self.render_timeout_seconds = get_render_timeout_seconds(self)
		self.font_search_paths = get_font_search_paths_display(self)

	def on_update(self):
		frappe.cache().delete_value(FONT_CACHE_KEY)


def get_settings_doc() -> Document:
	settings = frappe.get_single("Crispy Print Settings")
	apply_settings_defaults(settings)
	return settings


def apply_settings_defaults(settings: Document) -> Document:
	if settings.get("enable_uploaded_fonts") in (None, ""):
		settings.enable_uploaded_fonts = 1
	if settings.get("enable_system_fonts") in (None, ""):
		settings.enable_system_fonts = 0
	if settings.get("render_timeout_seconds") in (None, "", 0):
		settings.render_timeout_seconds = 60
	if settings.get("allow_print_for_draft") in (None, ""):
		settings.allow_print_for_draft = 1
	if settings.get("always_add_draft_heading") in (None, ""):
		settings.always_add_draft_heading = 1
	if settings.get("allow_print_for_cancelled") in (None, ""):
		settings.allow_print_for_cancelled = 0
	return settings


def get_render_timeout_seconds(settings: Document | None = None) -> int:
	settings = settings or get_settings_doc()
	try:
		timeout = int(settings.get("render_timeout_seconds") or 60)
	except (TypeError, ValueError):
		timeout = 60
	return max(1, min(timeout, 600))


def get_bundled_font_directory() -> Path:
	return Path(frappe.get_app_path("crispy_print")) / "public" / "vendor" / "fonts"


def get_uploaded_font_directory() -> Path:
	return Path(get_site_font_directory())


def get_typst_font_dirs(settings: Document | None = None, existing_only: bool = True) -> list[Path]:
	settings = settings or get_settings_doc()
	dirs = [get_bundled_font_directory()]
	if int(settings.get("enable_uploaded_fonts") or 0):
		dirs.append(get_uploaded_font_directory())
	if existing_only:
		return [font_dir for font_dir in dirs if font_dir.exists()]
	return dirs


def get_font_search_paths_display(settings: Document | None = None) -> str:
	settings = settings or get_settings_doc()
	lines = ["Bundled fonts:\ncrispy_print/public/vendor/fonts"]
	if int(settings.get("enable_uploaded_fonts") or 0):
		lines.append("Uploaded fonts:\nprivate/files/crispy_print/fonts")
	else:
		lines.append("Uploaded fonts:\nDisabled")
	if int(settings.get("enable_system_fonts") or 0):
		lines.append("System fonts:\nEnabled (discovered by Typst)")
	else:
		lines.append("System fonts:\nDisabled")
	return "\n\n".join(lines)


def should_ignore_system_fonts(settings: Document | None = None) -> bool:
	settings = settings or get_settings_doc()
	return not bool(int(settings.get("enable_system_fonts") or 0))


def refresh_font_search_paths() -> str:
	ensure_site_font_directory()
	settings = get_settings_doc()
	settings.font_search_paths = get_font_search_paths_display(settings)
	settings.db_set("font_search_paths", settings.font_search_paths, update_modified=False)
	frappe.cache().delete_value(FONT_CACHE_KEY)
	return settings.font_search_paths


@frappe.whitelist()
def refresh_font_list() -> dict:
	if not frappe.has_permission("Crispy Print Settings", "write"):
		frappe.throw(_("Not permitted to update Crispy Print Settings."), frappe.PermissionError)
	return {"font_search_paths": refresh_font_search_paths()}


@frappe.whitelist()
def import_uploaded_font(file_name: str | None = None, file_url: str | None = None) -> dict:
	if not frappe.has_permission("Crispy Print Settings", "write"):
		frappe.throw(_("Not permitted to update Crispy Print Settings."), frappe.PermissionError)

	file_doc = _resolve_file_doc(file_name=file_name, file_url=file_url)
	source_path = Path(file_doc.get_full_path()).resolve()
	_validate_font_source(source_path)

	target_dir = Path(ensure_site_font_directory()).resolve()
	target_dir.mkdir(parents=True, exist_ok=True)
	target_path = _unique_target_path(target_dir, source_path.name)

	shutil.copy2(source_path, target_path)
	refresh_font_search_paths()
	return {
		"file_name": target_path.name,
		"path": str(target_path),
		"font_search_paths": get_font_search_paths_display(),
	}


def _resolve_file_doc(file_name: str | None = None, file_url: str | None = None) -> Document:
	if file_name:
		return frappe.get_doc("File", file_name)
	if file_url:
		name = frappe.db.get_value("File", {"file_url": file_url}, "name")
		if name:
			return frappe.get_doc("File", name)
	frappe.throw(_("Uploaded file was not found."))


def _validate_font_source(source_path: Path) -> None:
	if source_path.is_symlink():
		frappe.throw(_("Font file cannot be a symlink."))
	if not source_path.exists() or not source_path.is_file():
		frappe.throw(_("Font file was not found."))
	file_stat = source_path.stat()
	if not stat.S_ISREG(file_stat.st_mode):
		frappe.throw(_("Font upload must be a regular file."))
	if source_path.suffix.lower() not in ALLOWED_FONT_EXTENSIONS:
		frappe.throw(
			_("Unsupported font file type. Allowed extensions: {0}").format(
				", ".join(sorted(ALLOWED_FONT_EXTENSIONS))
			)
		)
	if file_stat.st_size > MAX_UPLOADED_FONT_BYTES:
		frappe.throw(_("Font file exceeds the maximum size of 25 MB."))


def _unique_target_path(target_dir: Path, filename: str) -> Path:
	clean_name = Path(filename).name
	if not clean_name:
		clean_name = frappe.generate_hash(length=10)
	target = target_dir / clean_name
	if not target.exists():
		return target
	stem = target.stem
	suffix = target.suffix
	for index in range(1, 1000):
		candidate = target_dir / f"{stem}-{index}{suffix}"
		if not candidate.exists():
			return candidate
	frappe.throw(_("Unable to allocate a unique font filename."))


def validate_document_print_policy(doc) -> dict:
	settings = get_settings_doc()
	docstatus = int(getattr(doc, "docstatus", doc.get("docstatus", 0)) or 0)
	if docstatus == 0 and not int(settings.get("allow_print_for_draft") or 0):
		frappe.throw(_("Printing draft documents is disabled in Crispy Print Settings."))
	if docstatus == 2 and not int(settings.get("allow_print_for_cancelled") or 0):
		frappe.throw(_("Printing cancelled documents is disabled in Crispy Print Settings."))
	return {
		"is_draft": docstatus == 0,
		"is_cancelled": docstatus == 2,
		"show_draft_heading": bool(
			docstatus == 0
			and int(settings.get("allow_print_for_draft") or 0)
			and int(settings.get("always_add_draft_heading") or 0)
		),
	}
