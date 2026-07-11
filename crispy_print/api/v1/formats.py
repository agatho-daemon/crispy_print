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
from crispy_print.permissions import ensure_company_access
from crispy_print.render_contract import (
	FORMAT_EXPORT_FIELDS,
	FORMAT_IMPORT_FIELD_MAX_BYTES,
	format_data_from_doc,
)
from crispy_print.report_renderers import get_renderer_metadata, infer_report_renderer, list_renderer_metadata

from ._common import require_target_company, truthy
from .company_context import apply_effective_company_to_presentation_settings, resolve_effective_company
from .security import ensure_doctype_read_permission

EXPORT_SCHEMA_VERSION = 2
ALLOWED_IMPORT_CONFLICT_ACTIONS = {"copy", "overwrite"}
ALLOWED_DUPLICATE_NAME_STRATEGIES = {"copy", "replace"}
MAX_IMPORT_FIELD_BYTES = {
	**FORMAT_IMPORT_FIELD_MAX_BYTES,
}
EXPORT_FIELDS = list(FORMAT_EXPORT_FIELDS)
FORMAT_LIST_CACHE_TTL_SECONDS = 5 * 60


def _clean_company(company: str | None) -> str | None:
	clean = (company or "").strip()
	return clean or None


def _get_crispy_formats_cache_key(doctype: str, company: str | None = None) -> str:
	if not company:
		return f"crispy_print:formats_for_doctype:{doctype}"
	return f"crispy_print:formats_for_doctype:{doctype}:company:{company}"


def _get_crispy_formats_cache_index_key(doctype: str) -> str:
	return f"crispy_print:formats_for_doctype:{doctype}:cache_keys"


def _remember_crispy_formats_cache_key(doctype: str, cache_key: str) -> None:
	index_key = _get_crispy_formats_cache_index_key(doctype)
	cache = frappe.cache()
	keys = cache.get_value(index_key, expires=True)
	if not isinstance(keys, list):
		keys = []
	if cache_key not in keys:
		keys.append(cache_key)
	cache.set_value(index_key, keys, expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS)


def invalidate_crispy_formats_cache_for_doctype(doctype: str | None) -> None:
	"""Clear cached format list for a specific DocType."""
	if not doctype:
		return

	cache = frappe.cache()
	index_key = _get_crispy_formats_cache_index_key(doctype)
	cache_keys = cache.get_value(index_key, expires=True)
	if not isinstance(cache_keys, list):
		cache_keys = []
	cache_keys.append(_get_crispy_formats_cache_key(doctype))
	for cache_key in set(cache_keys):
		cache.delete_value(cache_key)
	cache.delete_value(index_key)


def get_crispy_formats_for_doctype(doctype, company: str | None = None):
	"""Get all enabled Crispy Formats for a given DocType.

	Returns formats that have both:
	- layout_json (reconstructable layout)
	- presentation_settings (rendering presentation configuration)
	"""
	if not doctype:
		return []
	ensure_doctype_read_permission("Crispy Format")

	company = _clean_company(company)
	cache_key = _get_crispy_formats_cache_key(doctype, company=company)
	cached_formats = frappe.cache().get_value(cache_key, expires=True)
	if isinstance(cached_formats, list):
		return cached_formats

	formats = _compute_crispy_formats_for_doctype(doctype, company=company)
	frappe.cache().set_value(cache_key, formats, expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS)
	_remember_crispy_formats_cache_key(doctype, cache_key)
	return formats


def get_crispy_format(
	name: str,
	company: str | None = None,
	source_doctype: str | None = None,
	source_docname: str | None = None,
	report_filters: dict | str | None = None,
) -> dict:
	"""Return a Crispy Format payload with server-side transient render hydration."""
	if not name:
		frappe.throw(_("Format name is required"))

	doc = frappe.get_doc("Crispy Format", name)
	doc.check_permission("read")
	data = {field: doc.get(field) for field in EXPORT_FIELDS}
	data["is_default"] = doc.get("is_default")
	source_doc = None
	if source_doctype and source_docname:
		source_doc = frappe.get_doc(source_doctype, source_docname)
		source_doc.check_permission("read")
	effective_company = resolve_effective_company(
		source_doc=source_doc,
		report_filters=report_filters,
		explicit_company=company or data.get("company"),
	)
	data["effective_company"] = effective_company

	if data.get("layout_json"):
		try:
			data["layout_json"] = resolve_layout_json_typst_blocks(
				data.get("layout_json"),
				data.get("doc_type") or "",
				company=effective_company,
			)
		except json.JSONDecodeError:
			# Let the existing frontend parser surface invalid layout_json consistently.
			pass

	return data


def _compute_crispy_formats_for_doctype(doctype: str, company: str | None = None) -> list[dict]:
	formats = frappe.get_list(
		"Crispy Format",
		fields=["name", "doc_type", "company", "is_default", "layout_json"],
		filters={"doc_type": doctype},
		order_by="name asc",
	)

	# Filter formats that have valid layout_json
	valid_formats = []
	for fmt in formats:
		row_company = _clean_company(fmt.get("company"))
		if company and row_company not in (company, None):
			continue
		try:
			# Check if layout_json is parseable
			if fmt.get("layout_json"):
				json.loads(fmt["layout_json"])  # Validate JSON
				valid_formats.append(
					{
						"name": fmt.get("name"),
						"doc_type": fmt.get("doc_type"),
						"company": fmt.get("company"),
						"is_default": fmt.get("is_default"),
					}
				)
		except (json.JSONDecodeError, Exception) as e:
			frappe.log_error(
				title="Crispy Print Format Validation",
				message=f"Invalid layout_json for Crispy Format {fmt.name}: {e!s}",
			)
			continue

	if company:
		valid_formats.sort(key=lambda row: 0 if _clean_company(row.get("company")) == company else 1)

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


def get_available_formats(report: str, company: str | None = None) -> dict:
	"""Return all compatible formats in report/company resolution order."""
	ensure_doctype_read_permission("Crispy Format")
	company = _clean_company(company) or _clean_company(frappe.defaults.get_user_default("Company"))
	renderer = infer_report_renderer(report)
	exact = get_custom_report_formats(report, company=company)
	fallbacks = frappe.get_list(
		"Crispy Format",
		filters={
			"crispy_format_type": "Report",
			"report_scope": "All Compatible Reports",
			"report_renderer": ["in", [renderer, "generic_report"]],
		},
		fields=["name", "company", "is_default", "report_scope", "report_renderer", "presentation_settings"],
		order_by="name asc",
	)
	fallbacks = [
		row for row in fallbacks if not company or _clean_company(row.get("company")) in (company, None)
	]
	seen = {row.get("name") for row in exact}
	rows = exact + [row for row in fallbacks if row.get("name") not in seen]

	def rank(row):
		exact_target = row.get("report_scope") == "Selected Reports"
		exact_company = bool(company and _clean_company(row.get("company")) == company)
		global_company = not _clean_company(row.get("company"))
		exact_renderer = row.get("report_renderer") == renderer
		if exact_target and exact_company and row.get("is_default"):
			bucket = 0
		elif exact_target and exact_company:
			bucket = 1
		elif exact_target and global_company:
			bucket = 2
		elif exact_renderer and exact_company:
			bucket = 3
		elif exact_renderer and global_company:
			bucket = 4
		elif exact_company:
			bucket = 5
		else:
			bucket = 6
		return bucket, 0 if row.get("is_default") else 1, str(row.get("name"))

	rows.sort(key=rank)
	formats = []
	for row in rows:
		try:
			settings = json.loads(row.get("presentation_settings") or "{}")
		except (TypeError, json.JSONDecodeError):
			settings = {}
		formats.append(
			{
				"name": row.get("name"),
				"company": row.get("company"),
				"report_scope": row.get("report_scope"),
				"report_renderer": row.get("report_renderer"),
				"layout_style": (settings.get("report") or {}).get("layout_style") or "Standard",
				"is_default": row.get("is_default"),
				"compatibility_status": "compatible",
			}
		)
	return {
		"formats": formats,
		"default_format": formats[0]["name"] if formats else None,
		"renderer": renderer,
	}


def get_custom_report_formats(report: str, company: str | None = None) -> list[dict]:
	"""Return custom report formats linked to a report through child table rows."""
	ensure_doctype_read_permission("Crispy Format")
	company = _clean_company(company)
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

	rows = frappe.get_list(
		"Crispy Format",
		filters={
			"name": ["in", parent_names],
			"crispy_format_type": "Report",
			"report_scope": "Selected Reports",
		},
		fields=[
			"name",
			"modified",
			"company",
			"is_default",
			"report_scope",
			"report_renderer",
			"presentation_settings",
		],
		order_by="modified desc",
	)
	if not company:
		return rows

	rows = [row for row in rows if _clean_company(row.get("company")) in (company, None)]
	rows.sort(
		key=lambda row: (
			0 if _clean_company(row.get("company")) == company else 1,
			0 if row.get("is_default") else 1,
		),
	)
	return rows


def get_builder_mode(format_name: str) -> dict:
	"""
	Determine which builder mode to use for a Crispy Format.

	Returns:
		dict: Builder mode, target type, report scope/renderer, and linked targets.
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
		"report_scope": format_doc.report_scope,
		"is_advanced": getattr(format_doc, "is_advanced", 0) or 0,
		"report_renderer": format_doc.report_renderer,
		"doc_type": format_doc.doc_type,
		"report": format_doc.report,
	}


def get_default_report_builder_config(report_renderer: str | None = None) -> dict:
	"""Return canonical server-side defaults for report builder basic mode."""
	return {
		"mode": "basic",
		"renderer": report_renderer or "generic_report",
		"preset": "grid",
		"layout_style": "Standard",
		"sections": get_renderer_metadata(report_renderer or "generic_report")["sections"],
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
		"font_family": "Inter",
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


def get_report_renderer_catalog() -> dict:
	"""Return product-owned renderer definitions and classified reports."""
	reports = frappe.get_list(
		"Report",
		fields=["name", "report_type", "ref_doctype", "module"],
		filters={"disabled": 0, "report_type": ["in", ["Script Report", "Query Report"]]},
		order_by="name asc",
	)
	for report in reports:
		report["report_renderer"] = infer_report_renderer(report["name"])
	return {"renderers": list_renderer_metadata(), "reports": reports}


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
	"""Export a Crispy Format in portable schema v2 JSON payload."""
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
		"metadata": _build_export_metadata(doc),
	}


def check_import_conflicts(payload: dict | str) -> dict:
	"""Preflight payload validation and collision check."""
	_ensure_create_permission()
	parsed = _convert_v1_import_payload(_parse_import_payload(payload))
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
	"""Import a Crispy Format, converting portable schema v1 when necessary."""
	parsed = _parse_import_payload(payload)
	parsed = _convert_v1_import_payload(parsed)
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
	warnings.extend(_collect_metadata_reference_warnings(parsed))

	return {
		"success": True,
		"name": imported_doc.name,
		"warnings": warnings,
		"conflict_action": on_conflict_value,
	}


def _convert_v1_import_payload(payload: dict) -> dict:
	if payload.get("schema_version") != 1:
		return payload
	converted = dict(payload)
	data = dict(converted.get("format") or {})
	legacy_generic = bool(data.pop("is_generic", 0))
	legacy_type = data.pop("generic_report_type", None)
	reports = [
		row.get("report") for row in (data.get("report") or []) if isinstance(row, dict) and row.get("report")
	]
	data["report_scope"] = "All Compatible Reports" if legacy_generic else "Selected Reports"
	data["report_renderer"] = (
		"generic_report" if legacy_generic else infer_report_renderer(reports[0] if reports else None)
	)
	try:
		settings = json.loads(data.get("presentation_settings") or "{}")
	except (TypeError, json.JSONDecodeError):
		settings = {}
	style = {"Summary": "Summary Focus", "Minimal": "Minimal"}.get(legacy_type, "Standard")
	settings.setdefault("report", {})["layout_style"] = style
	data["presentation_settings"] = json.dumps(settings, separators=(",", ":"))
	converted["format"] = data
	converted["schema_version"] = EXPORT_SCHEMA_VERSION
	return converted


def duplicate_crispy_format_for_company(
	source_name: str,
	target_company: str,
	set_default: int | bool = 0,
	name: str | None = None,
	name_strategy: str = "copy",
) -> dict:
	"""Clone a Crispy Format to another company, preserving render fields."""
	if not source_name:
		frappe.throw(_("Source Crispy Format is required."))

	target_company = _require_target_company(target_company)
	name_strategy = _normalize_duplicate_name_strategy(name_strategy)
	source = frappe.get_doc("Crispy Format", source_name)
	source.check_permission("read")
	if _clean_company(source.get("company")) == target_company:
		frappe.throw(_("Target company must be different from the source company."))

	format_data = _format_data_from_doc(source)
	doc, warnings = _insert_format_duplicate_for_company(
		format_data,
		target_company=target_company,
		source_name=source.name,
		set_default=set_default,
		name=name,
		name_strategy=name_strategy,
	)
	return _format_duplicate_payload(doc, source.name, warnings)


def _format_data_from_doc(doc) -> dict:
	data = format_data_from_doc(doc)
	if isinstance(data.get("report"), list):
		data["report"] = [
			{"report": row.get("report"), "disabled": row.get("disabled") or 0}
			for row in data["report"]
			if row.get("report")
		]
	return data


def _insert_format_duplicate_for_company(
	format_data: dict,
	*,
	target_company: str,
	source_name: str,
	set_default: int | bool = 0,
	name: str | None = None,
	name_strategy: str = "copy",
) -> tuple["frappe.model.document.Document", list[str]]:
	_ensure_create_permission()
	target_company = _require_target_company(target_company)
	ensure_company_access(target_company, doctype="Crispy Format")
	name_strategy = _normalize_duplicate_name_strategy(name_strategy)
	doc_data = {field: format_data.get(field) for field in EXPORT_FIELDS}
	warnings: list[str] = []

	base_name = (name or _get_company_duplicate_base_name(source_name, target_company)).strip()
	doc_data["name"] = _resolve_duplicate_format_name(base_name, name_strategy=name_strategy)
	doc_data["doctype"] = "Crispy Format"
	doc_data["company"] = target_company
	doc_data["is_default"] = 1 if _truthy(set_default) else 0
	doc_data["presentation_settings"], settings_warnings = _retarget_presentation_settings(
		doc_data.get("presentation_settings"),
		target_company,
	)
	warnings.extend(settings_warnings)

	doc = frappe.get_doc(doc_data)
	doc.flags.from_copy = True
	doc.insert(ignore_permissions=True)
	if _truthy(set_default):
		doc.is_default = 1
		doc.save(ignore_permissions=True)
	return doc, warnings


def _format_duplicate_payload(doc, source_name: str, warnings: list[str]) -> dict:
	return {
		"success": True,
		"name": doc.name,
		"source_name": source_name,
		"company": doc.get("company"),
		"is_default": 1 if doc.get("is_default") else 0,
		"warnings": warnings,
	}


def _require_target_company(company: str | None) -> str:
	return require_target_company(company)


def _normalize_duplicate_name_strategy(value: str | None) -> str:
	strategy = (value or "copy").strip().lower()
	if strategy not in ALLOWED_DUPLICATE_NAME_STRATEGIES:
		frappe.throw(_("Invalid duplicate name strategy: {0}").format(value))
	return strategy


def _get_company_duplicate_base_name(source_name: str, target_company: str) -> str:
	abbr = frappe.db.get_value("Company", target_company, "abbr") or target_company
	return f"{source_name} - {abbr}"


def _resolve_duplicate_format_name(base_name: str, *, name_strategy: str = "copy") -> str:
	base_name = (base_name or "Duplicated Crispy Format").strip()[:120]
	if name_strategy == "replace":
		return base_name
	if not frappe.db.exists("Crispy Format", base_name):
		return base_name
	index = 2
	while True:
		candidate = f"{base_name} {index}"
		if not frappe.db.exists("Crispy Format", candidate):
			return candidate
		index += 1


def _retarget_presentation_settings(
	raw_settings: str | None, target_company: str
) -> tuple[str | None, list[str]]:
	if not raw_settings:
		return raw_settings, []
	try:
		settings = json.loads(raw_settings)
	except json.JSONDecodeError:
		return raw_settings, [_("presentation_settings could not be parsed while retargeting company")]
	if not isinstance(settings, dict):
		return raw_settings, []

	warnings: list[str] = []
	settings = apply_effective_company_to_presentation_settings(settings, target_company)
	branding = settings.get("branding") if isinstance(settings.get("branding"), dict) else {}
	profile = (branding.get("profile") or "").strip()
	if profile:
		profile_company = _clean_company(frappe.db.get_value("Crispy Branding Profile", profile, "company"))
		if profile_company and profile_company != target_company:
			branding["profile"] = ""
			settings["source"] = "custom"
			warnings.append(
				_("Cleared source Branding Profile {0} because it belongs to another company.").format(
					profile
				)
			)

	return json.dumps(settings, sort_keys=True, separators=(",", ":"), default=str), warnings


def _truthy(value: int | bool | str | None) -> bool:
	return truthy(value)


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


def _build_export_metadata(doc) -> dict:
	company = doc.get("company")
	return {
		"company": {
			"name": company,
			"abbr": frappe.db.get_value("Company", company, "abbr") if company else None,
		}
		if company
		else None,
		"templates": frappe.get_all(
			"Crispy Template",
			filters={"source_crispy_format": doc.name},
			fields=["name", "template_name", "version", "company", "status", "is_active"],
			order_by="template_name asc, version desc",
		),
	}


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
		("company", "Company"),
		("report", "Report"),
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


def _collect_metadata_reference_warnings(payload: dict) -> list[str]:
	warnings: list[str] = []
	metadata = payload.get("metadata")
	if not isinstance(metadata, dict):
		return warnings

	company = metadata.get("company")
	if isinstance(company, dict):
		company_name = company.get("name")
		if company_name and not frappe.db.exists("Company", company_name):
			warnings.append(_("Missing reference: Company '{0}' (metadata)").format(company_name))

	templates = metadata.get("templates")
	if isinstance(templates, list):
		for template in templates:
			if not isinstance(template, dict):
				continue
			template_name = template.get("name")
			if template_name and not frappe.db.exists("Crispy Template", template_name):
				warnings.append(
					_("Missing reference: Crispy Template '{0}' (metadata)").format(template_name)
				)

	return warnings
