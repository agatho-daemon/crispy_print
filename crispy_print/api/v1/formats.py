import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	resolve_effective_presentation_settings,
)
from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	resolve_layout_json_typst_blocks,
)

from .security import ensure_doctype_read_permission

EXPORT_SCHEMA_VERSION = 1
ALLOWED_IMPORT_CONFLICT_ACTIONS = {"copy", "overwrite"}
MAX_IMPORT_FIELD_BYTES = {
	"name": 140,
	"crispy_format_type": 40,
	"doc_type": 140,
	"report": 140,
	"contract": 140,
	"generic_report_type": 140,
	"raw_typst": 256 * 1024,
	"layout_json": 512 * 1024,
	"presentation_settings": 128 * 1024,
	"doc_header": 128 * 1024,
	"doc_footer": 128 * 1024,
	"typst_preamble": 256 * 1024,
	"typst_code": 512 * 1024,
	"default_print_language": 140,
}
EXPORT_FIELDS = [
	"name",
	"crispy_format_type",
	"doc_type",
	"report",
	"contract",
	"is_generic",
	"is_advanced",
	"generic_report_type",
	"raw_typst",
	"layout_json",
	"presentation_settings",
	"doc_header",
	"doc_footer",
	"typst_preamble",
	"typst_code",
	"default_print_language",
]
FORMAT_LIST_CACHE_TTL_SECONDS = 5 * 60


def _get_crispy_formats_cache_key(doctype: str) -> str:
	return f"crispy_print:formats_for_doctype:{doctype}"


def invalidate_crispy_formats_cache_for_doctype(doctype: str | None) -> None:
	"""Clear cached format list for a specific DocType."""
	if not doctype:
		return

	cache_key = _get_crispy_formats_cache_key(doctype)
	frappe.cache().delete_value(cache_key)


def get_crispy_formats_for_doctype(doctype):
	"""Get all enabled Crispy Formats for a given DocType.

	Returns formats that have both:
	- layout_json (reconstructable layout)
	- presentation_settings (rendering presentation configuration)
	"""
	if not doctype:
		return []
	ensure_doctype_read_permission("Crispy Format")

	cache_key = _get_crispy_formats_cache_key(doctype)
	cached_formats = frappe.cache().get_value(cache_key, expires=True)
	if isinstance(cached_formats, list):
		return cached_formats

	formats = _compute_crispy_formats_for_doctype(doctype)
	frappe.cache().set_value(cache_key, formats, expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS)
	return formats


def get_crispy_format(name: str) -> dict:
	"""Return a Crispy Format payload with server-side transient render hydration."""
	if not name:
		frappe.throw(_("Format name is required"))

	doc = frappe.get_doc("Crispy Format", name)
	doc.check_permission("read")
	data = {field: doc.get(field) for field in EXPORT_FIELDS}
	data["is_default"] = doc.get("is_default")

	if data.get("layout_json"):
		try:
			data["layout_json"] = resolve_layout_json_typst_blocks(
				data.get("layout_json"),
				data.get("doc_type") or "",
			)
		except json.JSONDecodeError:
			# Let the existing frontend parser surface invalid layout_json consistently.
			pass

	return data


def _compute_crispy_formats_for_doctype(doctype: str) -> list[dict]:
	formats = frappe.get_list(
		"Crispy Format",
		fields=["name", "doc_type", "layout_json"],
		filters={"doc_type": doctype},
		order_by="name asc",
	)

	# Filter formats that have valid layout_json
	valid_formats = []
	for fmt in formats:
		try:
			# Check if layout_json is parseable
			if fmt.get("layout_json"):
				json.loads(fmt["layout_json"])  # Validate JSON
				valid_formats.append({"name": fmt.get("name"), "doc_type": fmt.get("doc_type")})
		except (json.JSONDecodeError, Exception) as e:
			frappe.log_error(
				f"Invalid layout_json for Crispy Format {fmt.name}: {e!s}",
				"Crispy Print Format Validation",
			)
			continue

	return valid_formats


def get_default_doctypes():
	"""Get all DocTypes that have a default Crispy Format set"""
	ensure_doctype_read_permission("Crispy Format")
	results = frappe.get_list(
		"Crispy Format",
		fields=["doc_type"],
		filters={"crispy_format_type": "DocType", "is_default": 1},
	)

	return [res.doc_type for res in results]


def get_available_formats(report: str) -> dict:
	"""
	Get all available formats for a report (custom + generic).

	Returns:
		dict: {
			"custom_formats": [...],
			"generic_formats": [...],
			"default_format": str
		}
	"""
	ensure_doctype_read_permission("Crispy Format")
	# Custom formats linked to this report via child table rows.
	custom_formats = get_custom_report_formats(report)

	# Generic formats are fallback-only.
	generic_formats = []
	if not custom_formats:
		generic_formats = frappe.get_list(
			"Crispy Format",
			filters={"crispy_format_type": "Report", "is_generic": 1},
			fields=["name", "generic_report_type"],
			order_by="generic_report_type asc",
		)

		is_tree = _get_report_is_tree(report)
		if is_tree is not None:
			expected_type = "Tree" if is_tree else "Grid"
			generic_formats = [
				fmt for fmt in generic_formats if fmt.get("generic_report_type") == expected_type
			]

	# Determine default
	default = (
		custom_formats[0]["name"]
		if custom_formats
		else (generic_formats[0]["name"] if generic_formats else None)
	)

	return {
		"custom_formats": custom_formats,
		"generic_formats": generic_formats,
		"default_format": default,
	}


def get_custom_report_formats(report: str) -> list[dict]:
	"""Return custom report formats linked to a report through child table rows."""
	ensure_doctype_read_permission("Crispy Format")
	report_rows = frappe.get_all(
		"Crispy Format Reports",
		fields=["parent"],
		filters={
			"parenttype": "Crispy Format",
			"report": report,
			"disabled": 0,
		},
	)
	parent_names = list(dict.fromkeys(row.get("parent") for row in report_rows if row.get("parent")))
	if not parent_names:
		return []

	return frappe.get_list(
		"Crispy Format",
		fields=["name", "modified"],
		filters={
			"name": ["in", parent_names],
			"crispy_format_type": "Report",
			"is_generic": 0,
		},
		order_by="modified desc",
	)


def get_builder_mode(format_name: str) -> dict:
	"""
	Determine which builder mode to use for a Crispy Format.

	Returns:
		dict: {
			"mode": "visual" | "code",
			"format_type": "DocType" | "Report" | "Contract",
			"is_generic": bool,
			"generic_report_type": str | None,
			"doc_type": str | None,
			"report": str | None
		}
	"""
	format_doc = frappe.get_doc("Crispy Format", format_name)
	format_doc.check_permission("read")

	# Determine builder mode
	mode = "visual"  # Default for DocType formats

	# Report formats now use is_advanced as mode source of truth.
	if format_doc.crispy_format_type == "Report":
		if getattr(format_doc, "is_advanced", 0) or format_doc.raw_typst:
			mode = "code"
	# Raw Typst mode also uses code editor for non-report formats.
	elif format_doc.raw_typst:
		mode = "code"

	return {
		"mode": mode,
		"format_type": format_doc.crispy_format_type,
		"is_generic": format_doc.is_generic or 0,
		"is_advanced": getattr(format_doc, "is_advanced", 0) or 0,
		"generic_report_type": format_doc.generic_report_type,
		"doc_type": format_doc.doc_type,
		"report": format_doc.report,
	}


def get_default_report_builder_config(generic_report_type: str | None = None) -> dict:
	"""Return canonical server-side defaults for report builder basic mode."""
	report_type = (generic_report_type or "").strip().lower()
	preset = "grid"
	if report_type in ("tree", "summary", "minimal", "grid"):
		preset = report_type

	return {
		"mode": "basic",
		"preset": preset,
		"show_filters": True,
		"show_summary": True,
		"include_total_row": True,
		"show_footer_total": True,
		"chart_enabled": True,
		"chart_width_percent": 100,
		"chart_max_height_pt": 220,
		"chart_card_border": True,
		"chart_spacing_top_pt": 0,
		"chart_spacing_bottom_pt": 12,
		"header_fill": "#B3D7FF",
		"header_text_weight": "bold",
		"font_family": "Inter 18pt",
		"font_size_pt": 9,
		"row_striping": False,
		"row_stripe_fill": "#F8FBFF",
		"column_align_strategy": "auto",
		"table_inset_x_pt": 8,
		"table_inset_y_pt": 6,
		"table_stroke_top_pt": 1,
		"table_stroke_body_pt": 0.5,
		"raw_signature": None,
		"report_table_sync_signature": None,
	}


def get_reports_without_custom_html(generic_report_type: str | None = None) -> list[dict]:
	"""
	Get list of reports that don't have custom HTML templates.

	These reports are suitable for generic Typst templates and preview testing.

	Args:
		generic_report_type: Optional filter by "Grid" or "Tree" (checks JS config)

	Returns:
		list: [{"name": "Sales Register", "report_type": "Script Report", "is_tree": false}, ...]
	"""
	reports = frappe.get_list(
		"Report",
		fields=["name", "report_type", "ref_doctype", "module"],
		filters={"disabled": 0, "report_type": ["in", ["Script Report", "Query Report"]]},
		order_by="name asc",
	)

	normalized_report_type = (generic_report_type or "").strip().lower()

	# Filter out reports with custom HTML and optionally by tree/grid type.
	# Grid/Tree are strict; all other generic types fall back to full no-HTML list.
	available_reports = []
	for report in reports:
		report_name = report["name"]
		module = report.get("module")

		if not module:
			continue

		report_folder = frappe.scrub(report_name)

		try:
			module_path = frappe.get_module_path(module)
		except Exception:
			# Module not found or path error - skip
			continue

		html_path = Path(module_path) / "report" / report_folder / f"{report_folder}.html"

		# Skip reports with custom HTML
		try:
			if Path.exists(html_path):
				continue
		except Exception:
			continue

		# Detect tree vs grid from JavaScript config.
		# Metadata-based detection (no JS parsing).
		# Unknown reports are treated as non-tree for grid fallback behavior.
		is_tree_flag = _get_report_is_tree(report_name)
		is_tree = bool(is_tree_flag)

		if normalized_report_type == "tree" and not is_tree:
			continue
		if normalized_report_type == "grid" and is_tree:
			continue

		report["is_tree"] = is_tree
		available_reports.append(report)

	return available_reports


def _get_report_is_tree(report: str) -> bool | None:
	"""Return True/False for tree reports, or None when unknown."""
	if not report:
		return None

	try:
		report_doc = frappe.get_doc("Report", report)
		return _get_report_is_tree_from_doc(report_doc)
	except Exception:
		return None


def _get_report_is_tree_from_doc(report_doc, _depth: int = 0) -> bool | None:
	"""Infer tree/grid from Report metadata only (no JS parsing)."""
	if not report_doc or _depth > 1:
		return None

	# Report Builder / Custom Report usually persist settings in JSON field.
	tree_from_json = _extract_tree_flag_from_json(report_doc.get("json"))
	if tree_from_json is not None:
		return tree_from_json

	# Custom reports may point to a reference report that has metadata.
	reference_report = report_doc.get("reference_report")
	if reference_report:
		try:
			return _get_report_is_tree_from_doc(frappe.get_doc("Report", reference_report), _depth + 1)
		except Exception:
			return None

	return None


def _extract_tree_flag_from_json(raw_json: str | None) -> bool | None:
	if not raw_json:
		return None

	try:
		payload = json.loads(raw_json)
	except Exception:
		return None

	return _find_tree_flag(payload)


def _find_tree_flag(node) -> bool | None:
	if isinstance(node, dict):
		for key in ("tree", "is_tree"):
			if key in node:
				coerced = _coerce_tree_bool(node.get(key))
				if coerced is not None:
					return coerced
		for value in node.values():
			found = _find_tree_flag(value)
			if found is not None:
				return found
	elif isinstance(node, list):
		for value in node:
			found = _find_tree_flag(value)
			if found is not None:
				return found
	return None


def _coerce_tree_bool(value) -> bool | None:
	if isinstance(value, bool):
		return value
	if isinstance(value, int):
		return bool(value)
	if isinstance(value, str):
		normalized = value.strip().lower()
		if normalized in {"1", "true", "yes", "on"}:
			return True
		if normalized in {"0", "false", "no", "off"}:
			return False
	return None


def export_crispy_format(name: str) -> dict:
	"""Export a Crispy Format in portable schema v1 JSON payload."""
	if not name:
		frappe.throw(_("Format name is required"))

	doc = frappe.get_doc("Crispy Format", name)
	doc.check_permission("read")

	format_data = {field: doc.get(field) for field in EXPORT_FIELDS}

	return {
		"schema_version": EXPORT_SCHEMA_VERSION,
		"exported_at": now_datetime().isoformat(),
		"app": "crispy_print",
		"format": format_data,
	}


def check_import_conflicts(payload: dict | str) -> dict:
	"""Preflight payload validation and collision check."""
	_ensure_create_permission()
	parsed = _parse_import_payload(payload)
	format_data = _validate_import_payload(parsed)
	name = format_data.get("name")
	exists = bool(name and frappe.db.exists("Crispy Format", name))

	return {
		"schema_version": EXPORT_SCHEMA_VERSION,
		"name": name,
		"exists": exists,
		"conflict": exists,
	}


def import_crispy_format(payload: dict | str, on_conflict: str = "copy") -> dict:
	"""Import a Crispy Format exported via schema v1."""
	parsed = _parse_import_payload(payload)
	format_data = _validate_import_payload(parsed)
	on_conflict_value = (on_conflict or "copy").strip().lower()

	if on_conflict_value not in ALLOWED_IMPORT_CONFLICT_ACTIONS:
		frappe.throw(_("Invalid conflict action: {0}").format(on_conflict))

	target_name = format_data.get("name")
	if not target_name:
		frappe.throw(_("Format name is required in payload"))

	existing_name = frappe.db.exists("Crispy Format", target_name)
	imported_doc = None

	if existing_name:
		if on_conflict_value == "overwrite":
			imported_doc = _overwrite_format(target_name, format_data)
		else:
			imported_doc = _insert_new_format(format_data, copy_name=True)
	else:
		imported_doc = _insert_new_format(format_data, copy_name=False)

	warnings = _collect_reference_warnings(imported_doc)

	return {
		"success": True,
		"name": imported_doc.name,
		"warnings": warnings,
		"conflict_action": on_conflict_value,
	}


def _parse_import_payload(payload: dict | str) -> dict:
	if isinstance(payload, str):
		raw = payload.strip()
		if not raw:
			frappe.throw(_("Import payload cannot be empty"))
		try:
			parsed = json.loads(raw)
		except json.JSONDecodeError:
			frappe.throw(_("Invalid JSON payload"))
	elif isinstance(payload, dict):
		parsed = payload
	else:
		frappe.throw(_("Payload must be a JSON object or JSON string"))

	if not isinstance(parsed, dict):
		frappe.throw(_("Payload must be a JSON object"))

	return parsed


def _validate_import_payload(parsed: dict) -> dict:
	if parsed.get("schema_version") != EXPORT_SCHEMA_VERSION:
		frappe.throw(_("Unsupported schema_version. Expected {0}").format(EXPORT_SCHEMA_VERSION))

	format_data = parsed.get("format")
	if not isinstance(format_data, dict):
		frappe.throw(_("Payload must include a 'format' object"))

	unknown_fields = sorted(set(format_data) - set(EXPORT_FIELDS))
	if unknown_fields:
		frappe.throw(_("Unsupported import fields: {0}").format(", ".join(unknown_fields)))

	for key in ("layout_json", "presentation_settings"):
		value = format_data.get(key)
		if value:
			try:
				json.loads(value)
			except json.JSONDecodeError:
				frappe.throw(_("{0} must contain valid JSON").format(key))

	for field, max_bytes in MAX_IMPORT_FIELD_BYTES.items():
		value = format_data.get(field)
		if value is None:
			continue
		if len(str(value).encode("utf-8")) > max_bytes:
			frappe.throw(_("{0} exceeds the maximum size of {1} KB").format(field, max_bytes // 1024))

	return {field: format_data.get(field) for field in EXPORT_FIELDS}


def _insert_new_format(format_data: dict, copy_name: bool) -> "frappe.model.document.Document":
	_ensure_create_permission()
	doc_data = dict(format_data)
	original_name = str(doc_data.get("name") or "").strip()

	if copy_name or frappe.db.exists("Crispy Format", original_name):
		doc_data["name"] = _get_imported_copy_name(original_name)
	else:
		doc_data["name"] = original_name

	doc_data["doctype"] = "Crispy Format"
	doc_data["is_default"] = 0
	doc = frappe.get_doc(doc_data)
	doc.insert(ignore_links=True)
	return doc


def _overwrite_format(target_name: str, format_data: dict) -> "frappe.model.document.Document":
	doc = frappe.get_doc("Crispy Format", target_name)
	doc.check_permission("write")

	preserved_is_default = doc.is_default

	for field in EXPORT_FIELDS:
		if field in ("name",):
			continue
		doc.set(field, format_data.get(field))

	doc.is_default = preserved_is_default
	doc.flags.ignore_links = True
	doc.save()
	return doc


def _get_imported_copy_name(base_name: str) -> str:
	base = (base_name or "Imported Format").strip()
	candidate = f"{base} (Imported)"
	if not frappe.db.exists("Crispy Format", candidate):
		return candidate

	index = 2
	while True:
		next_candidate = f"{base} (Imported {index})"
		if not frappe.db.exists("Crispy Format", next_candidate):
			return next_candidate
		index += 1


def _ensure_create_permission():
	if not frappe.has_permission("Crispy Format", "create"):
		frappe.throw(_("You don't have permission to create Crispy Format"))


def _collect_reference_warnings(doc) -> list[str]:
	warnings: list[str] = []

	link_checks = [
		("doc_type", "DocType"),
		("report", "Report"),
		("generic_report_type", "Crispy Generic Report"),
		("default_print_language", "Language"),
	]
	for fieldname, doctype in link_checks:
		value = doc.get(fieldname)
		if value and not frappe.db.exists(doctype, value):
			warnings.append(_("Missing reference: {0} '{1}' (field: {2})").format(doctype, value, fieldname))

	presentation_settings_raw = doc.get("presentation_settings")
	presentation_settings = {}
	if presentation_settings_raw:
		try:
			presentation_settings = json.loads(presentation_settings_raw)
		except json.JSONDecodeError:
			# Should already be validated, keep as safety net.
			warnings.append(_("presentation_settings could not be parsed for reference checks"))
			presentation_settings = {}

	branding = presentation_settings.get("branding") or {}
	try:
		presentation_settings = resolve_effective_presentation_settings(presentation_settings)
		branding = presentation_settings.get("branding") or {}
	except Exception:
		warnings.append(_("Could not resolve selected Crispy Branding Profile for reference checks"))

	letterhead = branding.get("letterhead")
	if letterhead and not frappe.db.exists("Letter Head", letterhead):
		warnings.append(_("Missing reference: Letter Head '{0}'").format(letterhead))

	logo = branding.get("logo") or {}
	company = logo.get("company")
	if company and not frappe.db.exists("Company", company):
		warnings.append(_("Missing reference: Company '{0}'").format(company))

	logo_image = logo.get("image")
	if logo_image and logo_image.startswith("/"):
		file_exists = frappe.db.exists("File", {"file_url": logo_image})
		if not file_exists:
			warnings.append(_("File not found for logo image path: {0}").format(logo_image))

	return warnings
