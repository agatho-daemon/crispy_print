import base64
import hashlib
import json
import re
from copy import copy, deepcopy
from pathlib import Path

import frappe
from frappe import _

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	resolve_effective_presentation_settings,
)
from crispy_print.permissions import ensure_company_access
from crispy_print.report_charts import (
	apply_chart_representation,
	normalize_chart_theme,
	normalize_report_chart,
	resolve_chart_render,
)
from crispy_print.report_renderers import get_renderer_metadata, infer_report_renderer

from .company_context import (
	apply_effective_company_to_presentation_settings,
	clean_company,
	extract_presentation_settings_company,
	resolve_effective_company,
)
from .compile import compile_typst, sanitize_chart_svg
from .formats import get_custom_report_formats
from .security import enforce_rate_limit
from .typst_doc import _build_typst_document

REPORT_PREVIEW_SNAPSHOT_TTL_SECONDS = 15 * 60
REPORT_DATA_FILENAME = "crispy-report-data.json"
RTL_LANGUAGE_PREFIXES = {"ar", "fa", "he", "ur"}
IMAGE_EXTENSIONS = {
	"png",
	"jpg",
	"jpeg",
	"svg",
	"gif",
	"webp",
	"bmp",
	"tif",
	"tiff",
	"avif",
}
_IMAGE_SUFFIX_RE = re.compile(r"\.([A-Za-z0-9]+)(?:[#?].*)?$")


class ReportTruncationTracker:
	def __init__(self):
		self.columns_truncated = False
		self.original_column_count = 0
		self.returned_column_count = 0
		self.cells_truncated_count = 0
		self.truncated_fieldnames: set[str] = set()

	def mark_columns(self, original_count: int, returned_count: int) -> None:
		self.original_column_count = original_count
		self.returned_column_count = returned_count
		self.columns_truncated = returned_count < original_count

	def mark_cell(self, fieldname: str | None = None) -> None:
		self.cells_truncated_count += 1
		if fieldname:
			self.truncated_fieldnames.add(str(fieldname))

	def as_dict(self) -> dict:
		return {
			"columns_truncated": self.columns_truncated,
			"original_column_count": self.original_column_count,
			"returned_column_count": self.returned_column_count,
			"cells_truncated_count": self.cells_truncated_count,
			"cells_truncated": self.cells_truncated_count > 0,
			"truncated_fieldnames": sorted(self.truncated_fieldnames),
		}


def _ensure_report_read_permission(report: str) -> None:
	report_doc = frappe.get_doc("Report", report)
	report_doc.check_permission("read")


def _build_truncation_payload(
	*,
	original_rows: int,
	returned_rows: int,
	max_rows: int | None,
	result_truncated: bool,
	columns_truncated: bool,
	original_column_count: int,
	returned_column_count: int,
	cells_truncated_count: int,
	truncated_fieldnames: list[str] | None = None,
) -> dict:
	return {
		"is_truncated": bool(result_truncated or columns_truncated or cells_truncated_count),
		"rows": {
			"truncated": bool(result_truncated),
			"original": int(original_rows),
			"returned": int(returned_rows),
			"max": max_rows,
		},
		"columns": {
			"truncated": bool(columns_truncated),
			"original": int(original_column_count),
			"returned": int(returned_column_count),
			"max": None,
		},
		"cells_truncated_count": int(cells_truncated_count),
		"truncated_fieldnames": list(truncated_fieldnames or []),
	}


def _snapshot_company(typst_data: dict) -> str | None:
	filters_map = typst_data.get("filters_map")
	if isinstance(filters_map, dict):
		company = filters_map.get("company")
		if isinstance(company, str) and company.strip():
			return company.strip()
	return None


def _require_preview_tab_id(preview_tab_id: str | None) -> str:
	value = str(preview_tab_id or "").strip()
	if not value or len(value) > 128:
		frappe.throw(_("Report preview tab context is invalid. Run Preview again."))
	return value


def _store_report_preview_snapshot(
	report: str,
	typst_data: dict,
	preview_tab_id: str | None = None,
) -> str:
	preview_tab_id = _require_preview_tab_id(preview_tab_id)
	snapshot_id = frappe.generate_hash(length=32)
	frappe.cache.set_value(
		f"crispy_report_preview:{snapshot_id}",
		{
			"report": report,
			"data": typst_data,
			"owner": frappe.session.user,
			"preview_tab_id": preview_tab_id,
			"company": _snapshot_company(typst_data),
		},
		user=True,
		expires_in_sec=REPORT_PREVIEW_SNAPSHOT_TTL_SECONDS,
	)
	return snapshot_id


def _load_report_preview_snapshot(
	report: str,
	snapshot_id: str | None,
	preview_tab_id: str | None = None,
) -> dict | None:
	if not snapshot_id:
		return None
	preview_tab_id = _require_preview_tab_id(preview_tab_id)
	payload = frappe.cache.get_value(
		f"crispy_report_preview:{snapshot_id}",
		user=True,
		expires=True,
	)
	if (
		not isinstance(payload, dict)
		or payload.get("report") != report
		or payload.get("owner") not in (None, frappe.session.user)
		or payload.get("preview_tab_id") != preview_tab_id
	):
		frappe.throw(_("Report preview data has expired. Run Preview again."))
	try:
		_ensure_report_read_permission(report)
		if payload.get("company"):
			ensure_company_access(payload["company"], doctype="Report")
	except frappe.PermissionError:
		frappe.throw(
			_("Report preview access has changed. Run Preview again."),
			frappe.PermissionError,
		)
	data = payload.get("data")
	if not isinstance(data, dict):
		frappe.throw(_("Report preview data has expired. Run Preview again."))
	return data


def _serialize_report_data_file(data: dict) -> str:
	return json.dumps(data, ensure_ascii=False, separators=(",", ":"), default=str)


def _normalize_report_language(language: str | None) -> str:
	value = str(language or "en").strip().replace("_", "-")
	return value or "en"


def _localize_report_typst_data(typst_data: dict, language: str | None) -> dict:
	"""Localize labels/dates while retaining raw accounting values for re-rendering."""
	language = _normalize_report_language(language)
	language_prefix = language.split("-", 1)[0].lower()
	columns = [column for column in typst_data.get("columns") or [] if isinstance(column, dict)]
	columns_by_fieldname = {
		str(column.get("fieldname") or ""): column for column in columns if column.get("fieldname")
	}

	for column in columns:
		label = str(column.get("label") or "")
		if label:
			column["label"] = _(label, lang=language)

	previous_language = getattr(frappe.local, "lang", None)
	frappe.local.lang = language
	try:
		for row in typst_data.get("rows") or []:
			if not isinstance(row, dict):
				continue
			for cell in row.get("cells") or []:
				if not isinstance(cell, dict):
					continue
				fieldname = str(cell.get("fieldname") or "")
				column = columns_by_fieldname.get(fieldname) or {}
				fieldtype = str(column.get("fieldtype") or "")
				label = str(cell.get("label") or "")
				if label:
					cell["label"] = _(label, lang=language)
				if fieldtype in {"Date", "Datetime", "Time"} and cell.get("raw_value") not in (None, ""):
					cell["value"] = str(
						frappe.format(
							cell.get("raw_value"),
							{"fieldtype": fieldtype},
							translated=True,
						)
					)
	finally:
		if previous_language is None:
			frappe.local.lang = "en"
		else:
			frappe.local.lang = previous_language

	typst_data["locale"] = {
		"language": language,
		"direction": "rtl" if language_prefix in RTL_LANGUAGE_PREFIXES else "ltr",
		# Accounting reports retain Latin digits unless a future explicit
		# numbering-system setting requests conversion.
		"numbering_system": "latn",
	}
	return typst_data


def _is_image_asset_value(value: str) -> bool:
	if not isinstance(value, str):
		return False
	raw = value.strip()
	if not raw:
		return False
	match = _IMAGE_SUFFIX_RE.search(raw)
	if not match:
		return False
	return match.group(1).lower() in IMAGE_EXTENSIONS


def _normalize_image_assets(data: dict | list | str | int | float | bool | None) -> tuple[object, list[str]]:
	"""Normalize image-like string values to basename and collect original asset paths."""
	collected: list[str] = []
	seen: set[str] = set()

	def collect_asset(value: str):
		if value not in seen:
			seen.add(value)
			collected.append(value)

	def normalize(value):
		if isinstance(value, dict):
			return {key: normalize(item) for key, item in value.items()}
		if isinstance(value, list):
			return [normalize(item) for item in value]
		if isinstance(value, str):
			raw = value.strip()
			if not _is_image_asset_value(raw):
				return value
			if raw == "report_chart.svg":
				return raw
			collect_asset(raw)
			return Path(raw).name
		return value

	return normalize(data), collected


def _is_basic_report_format(format_doc) -> bool:
	return not bool(getattr(format_doc, "raw_typst", 0))


def _prepare_basic_chart_source(
	code: str,
	typst_data: dict,
	presentation_settings: dict,
) -> str:
	"""Add a deterministic chart section to Basic sources only once."""
	report_settings = presentation_settings.get("report") or {}
	if not bool(report_settings.get("chart_enabled", True)):
		return code

	chart_spec = typst_data.get("chart_spec") or {}
	engine = chart_spec.get("engine") or "none"
	if engine == "none":
		return code
	if engine == "lilaq" and (
		"crispy-chart(" in code or "data.chart_spec" in code or "CRISPY-CHART-SECTION" in code
	):
		return code
	if engine == "frappe_svg" and "data.chart_svg" in code:
		return code

	width = max(10, min(100, int(report_settings.get("chart_width_percent", 100) or 100)))
	height = max(60, min(600, int(report_settings.get("chart_max_height_pt", 220) or 220)))
	spacing_top = max(0, min(120, int(report_settings.get("chart_spacing_top_pt", 0) or 0)))
	spacing_bottom = max(0, min(120, int(report_settings.get("chart_spacing_bottom_pt", 12) or 12)))
	top = f"#v({spacing_top}pt)\n" if spacing_top else ""
	bottom = f"#v({spacing_bottom}pt)\n" if spacing_bottom else ""
	if engine == "lilaq":
		chart_body = (
			'#import "@local/crispy-charts:0.1.1": crispy-chart\n'
			'#if "chart_spec" in data and data.chart_spec.engine == "lilaq" [\n'
			f"{top}"
			"#align(center)[\n"
			f"  #crispy-chart(data.chart_spec, theme: data.chart_theme, width: {width}%, height: {height}pt)\n"
			"]\n"
			f"{bottom}"
			"]\n"
		)
	else:
		chart_body = (
			'#if "chart_svg" in data and data.chart_svg != "" [\n'
			f"{top}"
			"#align(center)[\n"
			f'  #image(data.chart_svg, width: {width}%, height: {height}pt, fit: "contain")\n'
			"]\n"
			f"{bottom}"
			"]\n"
		)
	chart_block = f"\n// CRISPY-CHART-SECTION v2\n{chart_body}// /CRISPY-CHART-SECTION\n"
	for marker in ("// TABLE SETUP", "#table("):
		position = code.find(marker)
		if position != -1:
			return code[:position] + chart_block + code[position:]
	return code + chart_block


def generate_report_pdf(
	report: str,
	filters: dict | str | None = None,
	format_name: str | None = None,
	orientation: str = "landscape",
	include_filters: int = 0,
	column_config=None,
):
	"""
	Generate PDF for a report using Typst.

	Args:
		report: Report name
		filters: Report filters (dict or JSON string, optional)
		format_name: Crispy Format name (optional, auto-selects if not provided)
		orientation: Page orientation ("portrait" or "landscape", default: "landscape")
		include_filters: Whether to include filters in PDF (0 or 1, default: 0)
		column_config: List of column configurations with widths (JSON string or list, optional)
		              Format: [{"fieldname": "item_code", "width": "1fr"}, ...]

	Returns:
		dict: {"pdf_url": str, "status": str}
	"""
	from frappe.utils import cint

	# Parse filters if it's a string
	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except json.JSONDecodeError:
			frappe.throw(_("Invalid filters format"))
	if not isinstance(filters, dict):
		filters = {}
	_ensure_report_read_permission(report)

	# Parse column_config if it's a string
	column_filter = None
	if column_config:
		if isinstance(column_config, str):
			try:
				column_filter = json.loads(column_config)
			except json.JSONDecodeError:
				frappe.throw(_("Invalid column_config format"))
		elif isinstance(column_config, list):
			column_filter = column_config

	# Get or auto-select format
	if not format_name:
		format_name = _get_format_for_report(report)

	format_doc = frappe.get_doc("Crispy Format", format_name)
	format_doc.check_permission("read")

	# Get report data only after the selected format is readable.
	report_data = _get_report_data(report, filters or {})

	# Prepare data for Typst
	typst_data = _prepare_typst_report_data(
		report, report_data, filters if cint(include_filters) else None, column_filter
	)

	# Add canonical presentation settings.
	format_presentation_settings = {}
	if format_doc.get("presentation_settings"):
		try:
			format_presentation_settings = json.loads(format_doc.get("presentation_settings") or "{}")
		except json.JSONDecodeError:
			format_presentation_settings = {}
	effective_company = resolve_effective_company(
		report_filters=filters,
		explicit_company=extract_presentation_settings_company(format_presentation_settings)
		or format_doc.get("company"),
	)
	format_presentation_settings = resolve_effective_presentation_settings(
		format_presentation_settings,
		company=effective_company,
	)
	format_presentation_settings = apply_effective_company_to_presentation_settings(
		format_presentation_settings,
		effective_company,
	)
	format_presentation_settings.setdefault("page", {})
	format_presentation_settings["page"]["orientation"] = orientation.lower() if orientation else "landscape"
	report_presentation_settings = _normalize_report_presentation_settings(format_presentation_settings)
	typst_data["presentation_settings"] = report_presentation_settings
	typst_data["chart_theme"] = normalize_chart_theme(report_presentation_settings)
	typst_data["chart_spec"] = apply_chart_representation(
		typst_data.get("chart_spec"),
		(report_presentation_settings.get("report") or {}).get("chart_representation"),
	)
	typst_data["chart_spec"], chart_render = resolve_chart_render(typst_data.get("chart_spec"), None)
	format_doc_for_render = copy(format_doc)
	if _is_basic_report_format(format_doc_for_render):
		format_doc_for_render.typst_code = _prepare_basic_chart_source(
			format_doc_for_render.typst_code or "",
			typst_data,
			report_presentation_settings,
		)
	normalized_typst_data, asset_files = _normalize_image_assets(typst_data)

	# Build Typst document using unified compilation
	typst_source = _build_typst_document(
		format_doc=format_doc_for_render,
		data_dict=None,
		variable_name="data",  # Reports use #data.* namespace
		data_file=REPORT_DATA_FILENAME,
	)

	# Compile to PDF (write to public files and return URL)
	result = compile_typst(
		typst_source,
		output_format="pdf",
		pdf_standard=format_doc.get("pdf_standard") or "PDF/A-2u",
		asset_files=asset_files,
		return_url=1,
		_trusted_data_files={REPORT_DATA_FILENAME: _serialize_report_data_file(normalized_typst_data)},
	)

	report_truncation = normalized_typst_data.get("truncation") or {}
	return {
		"pdf_url": result.get("pdf_url"),
		"status": "success",
		"chart_render": chart_render,
		"truncation": _build_truncation_payload(
			original_rows=normalized_typst_data.get(
				"original_row_count", len(normalized_typst_data.get("rows") or [])
			),
			returned_rows=len(normalized_typst_data.get("rows") or []),
			max_rows=normalized_typst_data.get("max_rows"),
			result_truncated=bool(normalized_typst_data.get("result_truncated")),
			columns_truncated=bool(report_truncation.get("columns_truncated")),
			original_column_count=int(
				report_truncation.get("original_column_count")
				or len(normalized_typst_data.get("columns") or [])
			),
			returned_column_count=int(
				report_truncation.get("returned_column_count")
				or len(normalized_typst_data.get("columns") or [])
			),
			cells_truncated_count=int(report_truncation.get("cells_truncated_count") or 0),
			truncated_fieldnames=report_truncation.get("truncated_fieldnames") or [],
		),
	}


def get_report_typst_source(
	report: str,
	format_name: str | None = None,
	format_company: str | None = None,
	filters: dict | str | None = None,
	column_config: list | str | None = None,
	include_filters: int = 0,
	include_summary: int = 1,
	include_total_row: int = 1,
	include_chart: int = 1,
	orientation: str | None = None,
	presentation_settings: dict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	typst_code_override: str | None = None,
	preview_data: dict | str | None = None,
	preview_snapshot_id: str | None = None,
	preview_tab_id: str | None = None,
	limit: int = 0,
	_externalize_data: bool = False,
) -> dict:
	"""
	Build Typst source for report preview.

	Frontend calls this to get source, then passes to compile_typst().
	Same pattern as DocType mode - no duplication.

	Args:
		report: Report name
		format_name: Crispy Format name
		filters: Report filters (dict or JSON string, optional)
		column_config: Column configuration with widths (optional)
		limit: Optional caller-requested row limit. Zero returns the complete ERPNext result.

	Returns:
		dict: {"typst_source": str, "truncation": dict}
	"""
	from frappe.utils import cint

	# Parse preview_data if string (used by style-only builder preview mode)
	preview_data_dict = None
	if preview_data:
		if isinstance(preview_data, str):
			try:
				preview_data_dict = json.loads(preview_data)
			except json.JSONDecodeError:
				preview_data_dict = None
		elif isinstance(preview_data, dict):
			preview_data_dict = preview_data
	if preview_snapshot_id:
		preview_data_dict = _load_report_preview_snapshot(report, preview_snapshot_id, preview_tab_id)

	# Parse filters if string
	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except json.JSONDecodeError:
			filters = {}
	if not isinstance(filters, dict):
		filters = {}
	if not preview_data_dict:
		_ensure_report_read_permission(report)

	# Fill missing required filters with defaults only for live report previews.
	if not preview_data_dict:
		filters = _fill_default_report_filters(report, filters)

	# Parse column_config if string
	column_filter = None
	if column_config:
		if isinstance(column_config, str):
			try:
				column_filter = json.loads(column_config)
			except json.JSONDecodeError:
				column_filter = None
		elif isinstance(column_config, list):
			column_filter = column_config

	# Parse canonical presentation settings.
	presentation_settings_dict = None
	if presentation_settings:
		if isinstance(presentation_settings, str):
			try:
				presentation_settings_dict = json.loads(presentation_settings)
			except json.JSONDecodeError:
				presentation_settings_dict = None
		elif isinstance(presentation_settings, dict):
			presentation_settings_dict = presentation_settings
	requested_language = str((presentation_settings_dict or {}).get("language") or "").strip() or None

	# Saved formats are optional in the Builder. A transient preview requires
	# create permission and explicit Typst supplied by the current editor state.
	if format_name:
		format_doc = frappe.get_doc("Crispy Format", format_name)
		format_doc.check_permission("read")
		canonical_format_company = clean_company(getattr(format_doc, "company", None))
	else:
		if not frappe.has_permission("Crispy Format", "create"):
			frappe.throw(
				_("You need permission to create Crispy Format before previewing an unsaved report.")
			)
		if not isinstance(typst_code_override, str) or not typst_code_override.strip():
			frappe.throw(_("Typst code is required for an unsaved report preview."))
		format_doc = frappe._dict(
			name="",
			company=clean_company(format_company) or "",
			typst_code=typst_code_override,
			typst_preamble="",
			doc_header="",
			doc_footer="",
			raw_typst=0,
		)
		canonical_format_company = clean_company(format_company)
	if canonical_format_company:
		filters = {**filters, "company": canonical_format_company}
	effective_company = resolve_effective_company(
		source_doc={"company": canonical_format_company} if canonical_format_company else None,
		report_filters=filters,
		explicit_company=extract_presentation_settings_company(presentation_settings_dict)
		or getattr(format_doc, "company", None),
		allow_global_fallback=bool(preview_data_dict),
	)
	presentation_settings_dict = _normalize_report_presentation_settings(
		resolve_effective_presentation_settings(presentation_settings_dict, company=effective_company),
		(orientation or "landscape").lower(),
	)
	presentation_settings_dict["language"] = _normalize_report_language(
		requested_language
		or getattr(format_doc, "default_print_language", None)
		or getattr(frappe.local, "lang", None)
	)
	presentation_settings_dict = apply_effective_company_to_presentation_settings(
		presentation_settings_dict,
		effective_company,
	)
	format_doc_for_render = copy(format_doc)
	if isinstance(typst_code_override, str) and typst_code_override.strip():
		# Raw Typst overrides are trusted editor input. They are concatenated
		# directly into the generated Typst, but only writable callers can supply
		# them and Typst execution remains sandboxed.
		if format_name:
			format_doc.check_permission("write")
		format_doc_for_render.typst_code = typst_code_override
	if (
		_is_basic_report_format(format_doc_for_render)
		and not str(getattr(format_doc_for_render, "typst_code", "") or "").strip()
	):
		frappe.throw(
			_(
				"This Basic report format has no generated Typst code. Open it in the Report Format Builder, save it, and try again."
			)
		)

	# Prepare data for Typst
	if preview_data_dict:
		typst_data = _project_report_preview_data(
			preview_data_dict,
			column_filter,
			include_filters=bool(cint(include_filters)),
			include_summary=bool(cint(include_summary)),
			include_total_row=bool(cint(include_total_row)),
		)
		typst_data.setdefault("title", report or "Style Preview")
		typst_data.setdefault("subtitle", "")
		typst_data.setdefault("filters", [])
		typst_data.setdefault("report_summary", [])
		typst_data.setdefault("columns", [])
		typst_data.setdefault("rows", [])
		typst_data.setdefault("total_rows", len(typst_data.get("rows") or []))
		typst_data.setdefault("result_truncated", False)
		typst_data.setdefault("original_row_count", len(typst_data.get("rows") or []))
		typst_data.setdefault("returned_row_count", len(typst_data.get("rows") or []))
		typst_data.setdefault("max_rows", None)
		typst_data.setdefault("chart", {})
		typst_data.setdefault("chart_spec", normalize_report_chart(typst_data.get("chart"), report or None))
		typst_data.setdefault("skip_total_row", False)
	else:
		report_data = _get_report_data(report, filters or {}, max_rows=limit or None)
		typst_data = _prepare_typst_report_data(
			report,
			report_data,
			filters if cint(include_filters) else None,
			column_filter,
			include_summary=bool(cint(include_summary)),
			include_total_row=bool(cint(include_total_row)),
		)

	# Limit rows for preview
	preview_truncated = False
	preview_original_rows = len(typst_data.get("rows") or [])
	if limit and len(typst_data["rows"]) > limit:
		preview_truncated = True
		typst_data["rows"] = typst_data["rows"][:limit]
		typst_data["total_rows"] = limit

	# Add presentation settings (default to landscape for reports)
	orientation_value = (orientation or "landscape").lower()
	presentation_settings_dict["page"]["orientation"] = (
		presentation_settings_dict.get("page", {}).get("orientation") or orientation_value
	)
	typst_data["presentation_settings"] = presentation_settings_dict
	_localize_report_typst_data(typst_data, presentation_settings_dict.get("language"))

	# Resolve the chart independently of report execution. Native Lilaq wins;
	# sanitized Frappe SVG is retained only as a compatibility fallback.
	typst_data["chart_theme"] = normalize_chart_theme(presentation_settings_dict)
	typst_data["chart_spec"] = apply_chart_representation(
		typst_data.get("chart_spec"),
		(presentation_settings_dict.get("report") or {}).get("chart_representation"),
	)
	sanitized_chart_svg = None
	if bool(cint(include_chart)) and isinstance(chart_svg, str) and chart_svg.strip():
		sanitized_chart_svg = sanitize_chart_svg(chart_svg)
	typst_data["chart_spec"], chart_render = resolve_chart_render(
		typst_data.get("chart_spec"),
		sanitized_chart_svg if bool(cint(include_chart)) else None,
	)
	if not bool(cint(include_chart)):
		typst_data["chart_spec"]["engine"] = "none"
		chart_render.update({"engine": "none", "status": "omitted", "reason": "chart_section_disabled"})
	is_basic_format = _is_basic_report_format(format_doc_for_render)
	if sanitized_chart_svg and chart_render.get("engine") == "frappe_svg":
		typst_data["chart_svg"] = "report_chart.svg"
	else:
		typst_data.pop("chart_svg", None)
	if is_basic_format:
		format_doc_for_render.typst_code = _prepare_basic_chart_source(
			format_doc_for_render.typst_code or "",
			typst_data,
			presentation_settings_dict,
		)

	# Build Typst document using unified compilation
	preamble_override = (
		typst_preamble_override.strip()
		if isinstance(typst_preamble_override, str) and typst_preamble_override.strip()
		else None
	)
	normalized_typst_data, asset_files = _normalize_image_assets(typst_data)
	branding_settings = presentation_settings_dict.get("branding") or {}
	letterhead_image_path = branding_settings.get("letterhead_image") or ""
	logo_image_path = (branding_settings.get("logo") or {}).get("image") or ""
	letterhead_filename = Path(letterhead_image_path).name if letterhead_image_path else None
	logo_filename = Path(logo_image_path).name if logo_image_path else None
	for branding_asset in (letterhead_image_path, logo_image_path):
		if branding_asset:
			asset_files.append(branding_asset)
	asset_files = list(dict.fromkeys(asset_files))
	presentation_settings_block = _build_report_presentation_settings_block(
		presentation_settings_dict,
		letterhead_filename,
		logo_filename,
	)
	typst_source = _build_typst_document(
		format_doc=format_doc_for_render,
		data_dict=None if _externalize_data else normalized_typst_data,
		variable_name="data",  # Reports use #data.* namespace
		presentation_settings_block=presentation_settings_block,
		preamble_override=preamble_override,
		data_file=REPORT_DATA_FILENAME if _externalize_data else None,
	)

	report_truncation = normalized_typst_data.get("truncation") or {}
	result_truncated = bool(preview_truncated or normalized_typst_data.get("result_truncated"))

	payload = {
		"typst_source": typst_source,
		"truncation": _build_truncation_payload(
			original_rows=normalized_typst_data.get("original_row_count", preview_original_rows),
			returned_rows=len(normalized_typst_data.get("rows") or []),
			max_rows=limit
			if preview_truncated
			else (normalized_typst_data.get("max_rows") or (limit if limit else None)),
			result_truncated=result_truncated,
			columns_truncated=bool(report_truncation.get("columns_truncated")),
			original_column_count=int(
				report_truncation.get("original_column_count")
				or len(normalized_typst_data.get("columns") or [])
			),
			returned_column_count=int(
				report_truncation.get("returned_column_count")
				or len(normalized_typst_data.get("columns") or [])
			),
			cells_truncated_count=int(report_truncation.get("cells_truncated_count") or 0),
			truncated_fieldnames=report_truncation.get("truncated_fieldnames") or [],
		),
		"asset_files": asset_files,
		"chart_spec": normalized_typst_data.get("chart_spec") or {},
		"chart_render": chart_render,
		"chart_svg": sanitized_chart_svg if typst_data.get("chart_svg") else None,
	}
	if _externalize_data:
		payload["_generated_data_files"] = {
			REPORT_DATA_FILENAME: _serialize_report_data_file(normalized_typst_data)
		}
	return payload


def compile_report_preview(
	report: str,
	format_name: str | None = None,
	format_company: str | None = None,
	filters: dict | str | None = None,
	column_config: list | str | None = None,
	include_filters: int = 0,
	include_summary: int = 1,
	include_total_row: int = 1,
	include_chart: int = 1,
	orientation: str | None = None,
	presentation_settings: dict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	typst_code_override: str | None = None,
	preview_data: dict | str | None = None,
	preview_snapshot_id: str | None = None,
	preview_tab_id: str | None = None,
	limit: int = 0,
	asset_files: list | str | None = None,
	pdf_standard: str | None = None,
	output_action: str | None = None,
) -> dict:
	"""Build and compile a report preview PDF in one request."""
	source_payload = get_report_typst_source(
		report=report,
		format_name=format_name,
		format_company=format_company,
		filters=filters,
		column_config=column_config,
		include_filters=include_filters,
		include_summary=include_summary,
		include_total_row=include_total_row,
		include_chart=include_chart,
		orientation=orientation,
		presentation_settings=presentation_settings,
		chart_svg=chart_svg,
		typst_preamble_override=typst_preamble_override,
		typst_code_override=typst_code_override,
		preview_data=preview_data,
		preview_snapshot_id=preview_snapshot_id,
		preview_tab_id=preview_tab_id,
		limit=limit,
		_externalize_data=True,
	)
	compile_asset_files = list(source_payload.get("asset_files") or [])
	if asset_files:
		if isinstance(asset_files, str):
			try:
				asset_files = json.loads(asset_files)
			except json.JSONDecodeError:
				asset_files = []
		if isinstance(asset_files, list):
			compile_asset_files.extend(str(item) for item in asset_files if item)
	compile_asset_files = list(dict.fromkeys(compile_asset_files))
	result = compile_typst(
		source_payload.get("typst_source") or "",
		output_format="pdf",
		pdf_standard=pdf_standard,
		asset_files=compile_asset_files,
		chart_svg=source_payload.get("chart_svg"),
		_trusted_data_files=source_payload.get("_generated_data_files"),
	)
	audit_event = None
	if str(output_action or "").strip().lower() in {"download", "print"}:
		audit_event = _record_report_output_audit(
			report=report,
			format_name=format_name,
			filters=filters,
			output_action=str(output_action).strip().lower(),
			result=result,
			source_payload=source_payload,
			pdf_standard=pdf_standard,
		)
	return {
		**result,
		"typst_source": source_payload.get("typst_source") or "",
		"truncation": source_payload.get("truncation") or {},
		"asset_files": compile_asset_files,
		"chart_spec": source_payload.get("chart_spec") or {},
		"chart_render": source_payload.get("chart_render") or {},
		"report_output_audit": audit_event,
	}


def _record_report_output_audit(
	*,
	report: str,
	format_name: str | None,
	filters: dict | str | None,
	output_action: str,
	result: dict,
	source_payload: dict,
	pdf_standard: str | None,
) -> dict:
	"""Record a metadata-only report output event; reports never enter CID."""
	if not format_name:
		frappe.throw(_("A saved Report format is required for audited output."))
	format_doc = frappe.get_doc("Crispy Format", format_name)
	format_doc.check_permission("read")
	if format_doc.crispy_format_type != "Report":
		frappe.throw(_("Report output audit requires a Report format."))
	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except json.JSONDecodeError:
			filters = {}
	filters = filters if isinstance(filters, dict) else {}
	try:
		pdf_bytes = base64.b64decode(str(result.get("pdf_data") or ""), validate=True)
	except (ValueError, TypeError):
		pdf_bytes = b""
	filters_hash = hashlib.sha256(
		json.dumps(filters, sort_keys=True, separators=(",", ":"), default=str).encode()
	).hexdigest()
	pdf_hash = hashlib.sha256(pdf_bytes).hexdigest() if pdf_bytes else ""
	template = _latest_report_template_for_audit(report, format_doc)
	details = {
		"schema_version": 1,
		"report": report,
		"action": output_action,
		"format": format_doc.name,
		"renderer": format_doc.report_renderer,
		"format_source_fingerprint": format_doc.report_source_fingerprint,
		"template": template.get("name") if template else None,
		"template_version": template.get("version") if template else None,
		"template_snapshot_hash": template.get("snapshot_hash") if template else None,
		"filters_hash": filters_hash,
		"pdf_sha256": pdf_hash,
		"pdf_standard": pdf_standard or format_doc.pdf_standard,
		"page_count": result.get("page_count"),
		"row_count": (source_payload.get("truncation") or {}).get("rows", {}).get("returned"),
	}
	log = frappe.get_doc(
		{
			"doctype": "Crispy Report Output Audit",
			"report": report,
			"action": output_action.title(),
			"crispy_format": format_doc.name,
			"company": format_doc.company,
			"crispy_template": details["template"],
			"template_version": details["template_version"],
			"template_snapshot_hash": details["template_snapshot_hash"],
			"renderer": details["renderer"],
			"format_source_fingerprint": details["format_source_fingerprint"],
			"filters_hash": filters_hash,
			"pdf_sha256": pdf_hash,
			"pdf_standard": details["pdf_standard"],
			"page_count": details["page_count"],
			"row_count": details["row_count"],
		}
	)
	log.insert(ignore_permissions=True)
	return {"name": log.name, **details}


def _latest_report_template_for_audit(report: str, format_doc) -> dict | None:
	rows = frappe.get_all(
		"Crispy Template",
		filters={
			"crispy_format_type": "Report",
			"source_report": report,
			"source_crispy_format": format_doc.name,
			"status": "Approved",
			"is_active": 1,
		},
		fields=["name", "version", "snapshot_hash", "company", "effective_from"],
		order_by="effective_from desc, version desc",
		limit=20,
	)
	company = str(format_doc.company or "").strip()
	for row in rows:
		if str(row.get("company") or "").strip() == company:
			return dict(row)
	return None


def get_sample_report_data(
	report: str,
	filters=None,
	limit: int = 0,
	store_snapshot: int = 0,
	preview_tab_id: str | None = None,
) -> dict:
	"""
	Get sample data from a report for preview purposes.

	Args:
		report: Report name
		filters: Report filters (dict or JSON string, optional)
		limit: Optional caller-requested row limit. Zero returns the complete ERPNext result.
		store_snapshot: Store prepared report data server-side and return a lightweight handle.

	Returns:
		dict: {
			"columns": [...],
			"rows": [...],
			"title": str,
			"subtitle": str
		}
	"""

	# Parse filters if string
	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except json.JSONDecodeError:
			filters = {}
	if not isinstance(filters, dict):
		filters = {}

	# Fill missing required filters with defaults for preview
	filters = _fill_default_report_filters(report, filters)

	# Get report data
	report_data = _get_report_data(report, filters, max_rows=limit or None)

	# Prepare for Typst
	typst_data = _prepare_typst_report_data(report, report_data, filters=filters, column_filter=None)

	# Limit rows
	if limit and len(typst_data["rows"]) > limit:
		typst_data["rows"] = typst_data["rows"][:limit]
		typst_data["total_rows"] = limit

	if store_snapshot:
		snapshot_id = _store_report_preview_snapshot(report, typst_data, preview_tab_id)
		row_count = len(typst_data.get("rows") or [])
		return {
			"preview_snapshot_id": snapshot_id,
			"columns": typst_data.get("columns") or [],
			"title": typst_data.get("title") or report,
			"subtitle": typst_data.get("subtitle") or "",
			"total_rows": typst_data.get("total_rows", row_count),
			"original_row_count": typst_data.get("original_row_count", row_count),
			"returned_row_count": typst_data.get("returned_row_count", row_count),
			"result_truncated": bool(typst_data.get("result_truncated")),
			"max_rows": typst_data.get("max_rows"),
		}

	return typst_data


def _project_report_preview_data(
	preview_data: dict,
	column_filter: list | None,
	*,
	include_filters: bool,
	include_summary: bool,
	include_total_row: bool,
) -> dict:
	"""Apply Builder presentation choices to an already-executed report snapshot."""
	typst_data = deepcopy(preview_data)
	all_columns = [column for column in typst_data.get("columns") or [] if isinstance(column, dict)]
	visible_columns = all_columns

	if column_filter:
		columns_by_fieldname = {
			str(column.get("fieldname") or ""): column for column in all_columns if column.get("fieldname")
		}
		visible_columns = []
		for config in column_filter:
			if not isinstance(config, dict):
				continue
			fieldname = str(config.get("fieldname") or "")
			column = columns_by_fieldname.get(fieldname)
			if not column:
				continue
			projected = deepcopy(column)
			projected["width"] = _normalize_typst_column_width(config.get("width", "auto"))
			visible_columns.append(projected)

	for column in visible_columns:
		column.update(_normalize_typst_column_width_parts(column.get("width", "auto")))
	typst_data["columns"] = visible_columns

	visible_fieldnames = [str(column.get("fieldname") or "") for column in visible_columns]
	for row in typst_data.get("rows") or []:
		if not isinstance(row, dict):
			continue
		cells_by_fieldname = {
			str(cell.get("fieldname") or ""): cell
			for cell in row.get("cells") or []
			if isinstance(cell, dict) and cell.get("fieldname")
		}
		row["cells"] = [
			deepcopy(cells_by_fieldname[fieldname])
			for fieldname in visible_fieldnames
			if fieldname in cells_by_fieldname
		]

	if not include_filters:
		typst_data["filters"] = []
	if not include_summary:
		typst_data["report_summary"] = []
	if not include_total_row:
		typst_data["rows"] = [
			row
			for row in typst_data.get("rows") or []
			if not isinstance(row, dict)
			or (
				not row.get("is_total_row")
				and not row.get("is_total_like_row")
				and not row.get("is_auxiliary_row")
			)
		]
		typst_data["show_totals"] = False

	return typst_data


def _get_report_data(report: str, filters: dict, max_rows: int | None = None) -> dict:
	"""Execute report and return raw data"""
	_ensure_report_read_permission(report)
	enforce_rate_limit("report_data", limit=20, window_seconds=60)
	enforce_rate_limit(f"report_data:{frappe.scrub(report)}", limit=10, window_seconds=60)
	# Always run live for Crispy preview/PDF so prepared-report queue state
	# does not return empty placeholder payloads.
	result = frappe.desk.query_report.run(
		report,
		filters=filters,
		ignore_prepared_report=True,
		are_default_filters=False,
	)

	raw_result = result.get("result", []) or []
	original_row_count = len(raw_result) if isinstance(raw_result, list) else 0
	rows = raw_result
	result_truncated = False

	if isinstance(raw_result, list) and max_rows and max_rows > 0 and len(raw_result) > max_rows:
		rows = raw_result[:max_rows]
		result_truncated = True

	return {
		"columns": result.get("columns", []),
		"result": rows,
		"result_truncated": result_truncated,
		"original_row_count": original_row_count,
		"returned_row_count": len(rows) if isinstance(rows, list) else original_row_count,
		"max_rows": max_rows,
		"message": result.get("message"),
		"chart": result.get("chart"),
		"report_summary": result.get("report_summary"),
		"skip_total_row": result.get("skip_total_row"),
	}


def _fill_default_report_filters(report: str, filters: dict) -> dict:
	"""
	Fill missing required report filters with safe defaults for preview use.

	Uses Report filter defaults when defined; falls back to common defaults for
	date and company/fiscal year fields.
	"""
	from frappe.utils import add_days, nowdate

	if not report:
		return filters

	report_doc = frappe.get_doc("Report", report)
	report_doc.check_permission("read")
	report_filters = report_doc.filters or []
	filled = dict(filters or {})

	for flt in report_filters:
		fieldname = getattr(flt, "fieldname", None) or flt.get("fieldname")
		if not fieldname:
			continue

		current = filled.get(fieldname)
		if current not in (None, "", []):
			continue

		default = getattr(flt, "default", None) or flt.get("default")
		if default not in (None, "", []):
			filled[fieldname] = default
			continue

		reqd = getattr(flt, "reqd", None)
		if reqd is None:
			reqd = flt.get("reqd")
		if not reqd:
			continue

		fieldtype = getattr(flt, "fieldtype", None) or flt.get("fieldtype")
		options = getattr(flt, "options", None) or flt.get("options")

		if fieldtype in ("Date", "Datetime"):
			fieldname_lower = fieldname.lower()
			if "from" in fieldname_lower or fieldname_lower.endswith("_from"):
				filled[fieldname] = add_days(nowdate(), -30)
			elif "to" in fieldname_lower or fieldname_lower.endswith("_to"):
				filled[fieldname] = nowdate()
			else:
				filled[fieldname] = nowdate()
			continue

		if fieldname == "company":
			default_company = frappe.defaults.get_user_default("Company")
			if not default_company:
				default_company = frappe.defaults.get_user_default("company")
			if not default_company:
				default_company = frappe.defaults.get_global_default("company")
			if default_company:
				filled[fieldname] = default_company
			continue

		if fieldname in ("fiscal_year", "year") or options == "Fiscal Year":
			default_fy = frappe.defaults.get_user_default("fiscal_year")
			if not default_fy:
				default_fy = frappe.defaults.get_global_default("fiscal_year")
			if default_fy:
				filled[fieldname] = default_fy

	return filled


def _prepare_typst_report_data(
	report: str,
	report_data: dict,
	filters: dict | None = None,
	column_filter: list | None = None,
	include_summary: bool = True,
	include_total_row: bool = True,
) -> dict:
	"""Transform report data into Typst-friendly structure

	Args:
		column_filter: List of dicts with 'fieldname' and 'width' keys
		              Example: [{"fieldname": "item", "width": "2fr"}, {"fieldname": "qty", "width": "1fr"}]
	"""
	from frappe.utils import cint, flt

	truncation_tracker = ReportTruncationTracker()
	columns = _normalize_columns(report_data["columns"])
	rows = report_data["result"]

	# Filter visible columns
	visible_columns = [col for col in columns if col.get("label") and col.get("_id") != "_check"]
	original_column_count = len(visible_columns)
	truncation_tracker.mark_columns(original_column_count, len(visible_columns))
	# Default width semantics are backend-owned: report metadata widths are ignored unless
	# caller provides explicit column_config widths.
	for col in visible_columns:
		col["width"] = "auto"

	# Build column width map from filter
	width_map = {}
	if column_filter and len(column_filter) > 0:
		for col_config in column_filter:
			if isinstance(col_config, dict):
				fieldname = col_config.get("fieldname")
				width = _normalize_typst_column_width(col_config.get("width", "auto"))
				if fieldname:
					width_map[fieldname] = width

		# Filter to only selected columns (preserve order from column_filter)
		filtered_columns = []
		for col_config in column_filter:
			if isinstance(col_config, dict):
				fieldname = col_config.get("fieldname")
				if fieldname:
					col = next((c for c in visible_columns if c.get("fieldname") == fieldname), None)
					if col:
						col["width"] = width_map.get(fieldname, "auto")
						filtered_columns.append(col)
		visible_columns = filtered_columns

	# Apply widths if not already applied
	for col in visible_columns:
		if col.get("fieldname") in width_map:
			col["width"] = _normalize_typst_column_width(width_map[col.get("fieldname")])
		col.update(_normalize_typst_column_width_parts(col.get("width")))

	# Convert rows to dictionary for Typst
	processed_rows = []
	for index, row in enumerate(rows):
		processed_rows.append(_prepare_row_data(row, visible_columns, index, truncation_tracker))
	renderer = infer_report_renderer(report)
	processed_rows = _adapt_report_rows(renderer, processed_rows)
	base_rows = [row for row in processed_rows if not row.get("is_total_row")]
	final_rows = (
		processed_rows
		if include_total_row
		else [
			row for row in base_rows if not row.get("is_total_like_row") and not row.get("is_auxiliary_row")
		]
	)

	# Generate report title
	report_title = report_data.get("message") or report
	report_key = frappe.scrub(report or "")
	filters_map = _normalize_filters_map(filters)
	show_future_payments = _coerce_filter_bool(filters_map.get("show_future_payments"))
	show_sales_person = _coerce_filter_bool(filters_map.get("show_sales_person"))

	# Get report chart if any
	report_chart = report_data.get("chart") or {}
	chart_spec = normalize_report_chart(report_chart, report)
	report_summary = _normalize_report_summary_for_typst(report_data.get("report_summary") or [])
	if not include_summary:
		report_summary = []
	skip_total_row = bool(report_data.get("skip_total_row"))

	return {
		"renderer": renderer,
		"sections": get_renderer_metadata(renderer)["sections"],
		"columns": visible_columns,
		"rows": final_rows,
		"total_rows": len(base_rows),
		"show_totals": bool(include_total_row),
		"result_truncated": bool(report_data.get("result_truncated")),
		"original_row_count": report_data.get(
			"original_row_count", len(rows) if isinstance(rows, list) else 0
		),
		"returned_row_count": report_data.get(
			"returned_row_count", len(rows) if isinstance(rows, list) else 0
		),
		"max_rows": report_data.get("max_rows"),
		"filters": _normalize_filters_for_typst(filters),
		"filters_map": filters_map,
		"title": report_title,
		"subtitle": "",
		"chart": report_chart,
		"chart_spec": chart_spec,
		"report_summary": report_summary,
		"skip_total_row": skip_total_row,
		"report_name": report,
		"report_key": report_key,
		"report_context": {
			"is_accounts_receivable": report in ("Accounts Receivable", "Accounts Receivable Summary"),
			"is_accounts_payable": report in ("Accounts Payable", "Accounts Payable Summary"),
			"is_summary_report": report.endswith("Summary") if isinstance(report, str) else False,
			"is_detail_report": not (report.endswith("Summary") if isinstance(report, str) else False),
			"show_future_payments": show_future_payments,
			"show_sales_person": show_sales_person,
			"has_party_filter": bool(filters_map.get("party")),
		},
		"truncation": truncation_tracker.as_dict(),
	}


def _adapt_report_rows(renderer: str, rows: list[dict]) -> list[dict]:
	"""Attach stable presentation roles without discarding upstream row metadata."""
	if renderer == "bank_reconciliation":
		rows = _enrich_report_rows_for_typst("Bank Reconciliation Statement", rows)
		rows = _mark_report_total_like_rows("Bank Reconciliation Statement", rows)
	for row in rows:
		if row.get("is_total_row"):
			role = "grand_total"
		elif row.get("is_total_like_row"):
			role = "calculation"
		elif row.get("is_auxiliary_row"):
			role = "auxiliary"
		elif not any(cell.get("value") for cell in row.get("cells") or []):
			role = "spacer"
		elif (
			renderer == "financial_statement"
			and not row.get("parent_account")
			and not row.get("parent_section")
		):
			role = "section"
		elif row.get("indent"):
			role = "detail"
		else:
			role = "detail"
		row["role"] = role
	return rows


def _coerce_filter_bool(value) -> bool:
	if isinstance(value, bool):
		return value
	if value is None:
		return False
	text = str(value).strip().lower()
	return text in {"1", "true", "yes", "y", "on"}


def _normalize_report_summary_for_typst(report_summary: list) -> list[dict]:
	"""Attach report-view-like formatted values and color class hints for Typst templates."""
	normalized: list[dict] = []

	for item in report_summary:
		if not isinstance(item, dict):
			continue

		normalized_item = dict(item)
		normalized_item.setdefault("type", "")
		normalized_item.setdefault("label", "")
		normalized_item.setdefault("value", "")
		datatype = item.get("datatype") or "Data"
		df = {"fieldtype": datatype}
		currency = None

		if datatype == "Currency":
			df["options"] = "currency"
			currency = item.get("currency")

		try:
			formatted = frappe.format(item.get("value"), df, currency=currency, translated=False)
		except Exception:
			formatted = "" if item.get("value") is None else str(item.get("value"))

		normalized_item["formatted_value"] = "" if formatted is None else str(formatted)
		normalized_item["color_class"] = str(item.get("indicator") or item.get("color") or "").strip().lower()
		normalized.append(normalized_item)

	return normalized


def _normalize_filters_for_typst(filters: dict | list | None) -> list[dict]:
	"""Return report filters as Typst-friendly array of (label, value) objects."""
	if not filters:
		return []

	if isinstance(filters, list):
		out = []
		for entry in filters:
			if not isinstance(entry, dict):
				continue
			label = str(entry.get("label") or entry.get("fieldname") or "").strip()
			value = entry.get("value")
			if not label:
				continue
			out.append({"label": label, "value": "" if value is None else str(value)})
		return out

	if isinstance(filters, dict):
		out = []
		for key, value in filters.items():
			if key in (None, ""):
				continue
			out.append({"label": str(key), "value": "" if value is None else str(value)})
		return out

	return []


def _normalize_filters_map(filters: dict | list | None) -> dict[str, str]:
	"""Return filters as key->value map with normalized keys for Typst branching."""
	if not filters:
		return {}

	out: dict[str, str] = {}
	if isinstance(filters, list):
		for entry in filters:
			if not isinstance(entry, dict):
				continue
			raw_key = entry.get("fieldname") or entry.get("label")
			key = _normalize_filter_key(raw_key)
			if not key:
				continue
			value = entry.get("value")
			out[key] = "" if value is None else str(value)
		return out

	if isinstance(filters, dict):
		for raw_key, value in filters.items():
			key = _normalize_filter_key(raw_key)
			if not key:
				continue
			out[key] = "" if value is None else str(value)
		return out

	return {}


def _normalize_filter_key(raw_key) -> str:
	if raw_key in (None, ""):
		return ""
	return frappe.scrub(str(raw_key))


def _enrich_report_rows_for_typst(report: str, rows: list[dict]) -> list[dict]:
	"""Apply report-specific presentation enrichments without patching source reports."""
	if report != "Bank Reconciliation Statement" or not rows:
		return rows

	payment_entry_names = [
		row.get("payment_entry_raw") or row.get("payment_entry")
		for row in rows
		if row.get("payment_document_raw") == "Payment Entry"
		and (row.get("payment_entry_raw") or row.get("payment_entry"))
	]
	if not payment_entry_names:
		return rows

	unique_payment_entries = tuple(dict.fromkeys(payment_entry_names))
	request_cache = getattr(frappe.local, "cache", None)
	cache_key = ("crispy_print:payment_entry_party_names", unique_payment_entries)
	party_name_by_entry = None
	if isinstance(request_cache, dict):
		party_name_by_entry = request_cache.get(cache_key)
	if party_name_by_entry is None:
		payment_entries = frappe.get_list(
			"Payment Entry",
			filters={"name": ["in", list(unique_payment_entries)]},
			fields=["name", "party", "party_name"],
		)
		party_name_by_entry = {
			entry["name"]: (entry.get("party_name") or entry.get("party") or "")
			for entry in payment_entries
			if entry.get("name")
		}
		if isinstance(request_cache, dict):
			request_cache[cache_key] = party_name_by_entry

	if not party_name_by_entry:
		return rows

	for row in rows:
		if row.get("payment_document_raw") != "Payment Entry":
			continue
		entry_name = row.get("payment_entry_raw") or row.get("payment_entry")
		party_name = party_name_by_entry.get(entry_name)
		if not party_name:
			continue
		row["against_account_display"] = str(party_name)
		row["against_account"] = str(party_name)
		for cell in row.get("cells", []):
			if cell.get("fieldname") == "against_account":
				cell["value"] = str(party_name)
				break

	return rows


def _mark_report_total_like_rows(report: str, rows: list[dict]) -> list[dict]:
	"""Mark report-specific summary/spacer rows so UI toggles can hide them."""
	if report != "Bank Reconciliation Statement" or not rows:
		return rows

	for row in rows:
		payment_entry_raw = str(row.get("payment_entry_raw") or row.get("payment_entry") or "").strip()
		has_posting_date = bool(row.get("posting_date_raw") or row.get("posting_date"))
		has_amount = bool(
			(row.get("debit_raw") not in (None, "", 0, 0.0))
			or (row.get("credit_raw") not in (None, "", 0, 0.0))
		)
		is_blank_spacer = not has_posting_date and not payment_entry_raw and not has_amount
		is_total_like = not has_posting_date and payment_entry_raw in {
			"Bank Statement balance as per General Ledger",
			"Outstanding Cheques and Deposits to clear",
			"Cheques and Deposits incorrectly cleared",
			"Calculated Bank Statement balance",
		}
		row["is_total_like_row"] = bool(is_total_like)
		row["is_auxiliary_row"] = bool(is_blank_spacer)

	return rows


def _prepare_row_data(
	row,
	columns: list,
	index: int,
	truncation_tracker: ReportTruncationTracker | None = None,
) -> dict:
	"""Transform a row into a Typst row dict"""
	out = {
		"_idx": index,
		"cells": [],
		"is_bold": False,
		"is_total_row": False,
		"indent": 0,
		"warn_if_negative": False,
	}

	# Row can be list or dict
	if isinstance(row, dict):
		out["is_bold"] = bool(row.get("bold") or row.get("is_bold"))
		out["is_total_row"] = bool(row.get("is_total_row"))
		out["warn_if_negative"] = bool(row.get("warn_if_negative"))
		# Preserve hierarchy metadata even when not present in visible columns.
		out["parent_account"] = row.get("parent_account")
		out["parent_section"] = row.get("parent_section")
		try:
			out["indent"] = int(row.get("indent") or 0)
		except Exception:
			out["indent"] = 0
		for col in columns:
			fieldname = col.get("fieldname")
			if fieldname:
				raw_value = row.get(fieldname)
				value = _format_cell_value(raw_value, col, row)
				value = _truncate_report_cell_value(value, fieldname, truncation_tracker)
				value = _apply_tree_indent_to_value(
					value,
					indent=out.get("indent", 0),
					is_first_cell=len(out["cells"]) == 0,
				)
				out[fieldname] = value
				out[f"{fieldname}_raw"] = _truncate_report_cell_value(
					raw_value, fieldname, truncation_tracker
				)
				if col.get("fieldtype") == "Currency":
					currency_display, amount_display = _split_currency_display(
						value, row.get(col.get("options")) if isinstance(row, dict) else None
					)
					out[f"{fieldname}_currency_display"] = currency_display
					out[f"{fieldname}_amount_display"] = amount_display
				out["cells"].append(
					{
						"value": value,
						"raw_value": _truncate_report_cell_value(raw_value, fieldname, truncation_tracker),
						"fieldname": fieldname,
						"label": col.get("label") or fieldname,
						"is_numeric": bool(col.get("is_numeric")),
					}
				)
				if fieldname == "indent":
					try:
						out["indent"] = int(raw_value or 0)
					except Exception:
						out["indent"] = 0
		return out

	# Handle list rows
	if isinstance(row, list | tuple):
		for col in columns:
			fieldname = col.get("fieldname")
			col_index = col.get("col_index")
			if fieldname and col_index is not None and col_index < len(row):
				raw_value = row[col_index]
				value = _format_cell_value(raw_value, col, row)
				value = _truncate_report_cell_value(value, fieldname, truncation_tracker)
				value = _apply_tree_indent_to_value(
					value,
					indent=out.get("indent", 0),
					is_first_cell=len(out["cells"]) == 0,
				)
				out[fieldname] = value
				out[f"{fieldname}_raw"] = _truncate_report_cell_value(
					raw_value, fieldname, truncation_tracker
				)
				if col.get("fieldtype") == "Currency":
					currency_display, amount_display = _split_currency_display(value, None)
					out[f"{fieldname}_currency_display"] = currency_display
					out[f"{fieldname}_amount_display"] = amount_display
				out["cells"].append(
					{
						"value": value,
						"raw_value": _truncate_report_cell_value(raw_value, fieldname, truncation_tracker),
						"fieldname": fieldname,
						"label": col.get("label") or fieldname,
						"is_numeric": bool(col.get("is_numeric")),
					}
				)
				if fieldname == "indent":
					try:
						out["indent"] = int(raw_value or 0)
					except Exception:
						out["indent"] = 0
		return out

	return out


def _truncate_report_cell_value(
	value,
	fieldname: str | None = None,
	truncation_tracker: ReportTruncationTracker | None = None,
):
	return value


def _apply_tree_indent_to_value(value: str, indent: int, is_first_cell: bool) -> str:
	"""Apply visible indentation prefix for tree-style report rows on first column."""
	if not is_first_cell:
		return value
	if not value:
		return value
	try:
		indent_level = int(indent or 0)
	except Exception:
		indent_level = 0
	if indent_level <= 0:
		return value
	# Use non-breaking spaces so indentation is preserved in Typst text output.
	return ("\u00a0" * (indent_level * 4)) + value


def _format_cell_value(value, col: dict, row: dict) -> str:
	"""Format a cell value for Typst output"""
	fieldtype = col.get("fieldtype")

	if value is None:
		return ""

	if isinstance(value, str):
		return value.strip()

	if _is_numeric_fieldtype(fieldtype):
		try:
			if fieldtype == "Currency":
				currency = None
				options = col.get("options")
				if isinstance(row, dict) and options:
					currency = row.get(options)
				df = {"fieldtype": "Currency", "options": options}
				return str(frappe.format(value, df, currency=currency, translated=False))
			if fieldtype == "Percent":
				return f"{float(value):,.2f}%"
			return f"{float(value):,.2f}"
		except Exception:
			return str(value)

	return str(value)


def _is_numeric_fieldtype(fieldtype: str) -> bool:
	return fieldtype in ("Int", "Float", "Currency", "Percent")


def _split_currency_display(formatted_value: str, currency: str | None) -> tuple[str, str]:
	"""Split a formatted currency value into currency label and numeric portion."""
	text = "" if formatted_value is None else str(formatted_value).strip()
	currency_text = "" if currency is None else str(currency).strip()

	if not text:
		return "", ""
	if currency_text:
		prefix = f"{currency_text} "
		if text.startswith(prefix):
			return currency_text, text[len(prefix) :]
	return currency_text, text


def _normalize_typst_column_width(width) -> str:
	"""Normalize to Typst table width tokens (auto, fraction, relative length)."""
	if width in (None, ""):
		return "auto"

	if isinstance(width, int | float):
		return f"{round(float(width))}pt" if float(width) > 0 else "auto"

	width_str = str(width).strip().lower()
	if not width_str:
		return "auto"
	if width_str == "auto":
		return "auto"

	import re

	if re.fullmatch(r"\d+(\.\d+)?(fr|pt|em|rem|%|cm|mm|in)", width_str):
		return width_str

	if re.fullmatch(r"\d+(\.\d+)?", width_str):
		return f"{round(float(width_str))}pt"

	return "auto"


def _normalize_typst_column_width_parts(width) -> dict:
	"""Return a Typst-safe column width descriptor without requiring Typst eval()."""
	import re

	width_token = _normalize_typst_column_width(width)
	if width_token == "auto":
		return {"width": "auto", "width_kind": "auto", "width_value": None}

	match = re.fullmatch(r"(\d+(?:\.\d+)?)(fr|pt|em|rem|%|cm|mm|in)", width_token)
	if not match:
		return {"width": "auto", "width_kind": "auto", "width_value": None}

	value = float(match.group(1))
	if value.is_integer():
		value = int(value)

	return {"width": width_token, "width_kind": match.group(2), "width_value": value}


def _normalize_columns(columns: list) -> list:
	"""Normalize report columns to a consistent format"""
	normalized = []
	for i, col in enumerate(columns):
		if isinstance(col, str):
			# String format: "label:fieldtype:width"
			parts = col.split(":")
			label = parts[0].strip()
			fieldtype = parts[1].strip() if len(parts) > 1 else "Data"
			width = parts[2].strip() if len(parts) > 2 else None
			normalized.append(
				{
					"label": label,
					"fieldname": frappe.scrub(label),
					"fieldtype": fieldtype,
					"is_numeric": _is_numeric_fieldtype(fieldtype),
					"width": width,
					"col_index": i,
				}
			)
			continue

		if isinstance(col, dict):
			col.setdefault("fieldname", col.get("fieldname") or frappe.scrub(col.get("label") or ""))
			col.setdefault("fieldtype", col.get("fieldtype") or "Data")
			col["is_numeric"] = _is_numeric_fieldtype(col.get("fieldtype"))
			normalized.append(col)
			continue

	return normalized


def _get_format_for_report(report: str) -> str:
	"""Auto-select the highest-ranked compatible live format."""
	from crispy_print.api.v1.formats import get_available_formats

	available = get_available_formats(report)
	if available.get("default_format"):
		return available["default_format"]

	frappe.throw(_("No print format found for report '{0}'").format(report))


def _build_report_presentation_settings_block(
	presentation_settings: dict | None,
	letterhead_filename: str | None,
	logo_filename: str | None,
) -> str:
	"""Build a #set page() block for report previews using presentation settings."""
	presentation_settings = _normalize_report_presentation_settings(presentation_settings) or {}
	page = presentation_settings.get("page") or {}
	branding = presentation_settings.get("branding") or {}
	page_size = str(page.get("size") or "A4").lower()
	# Reports default to landscape unless explicitly overridden
	orientation = str(page.get("orientation") or "landscape").lower()
	margins = page.get("margins") or {}
	margin_top = margins.get("top", 25)
	margin_bottom = margins.get("bottom", 20)
	margin_left = margins.get("left", 20)
	margin_right = margins.get("right", 20)
	branding_mode = str(branding.get("mode") or "none")
	language = _normalize_report_language(presentation_settings.get("language"))
	language_parts = language.split("-", 1)
	language_code = language_parts[0].lower()
	region = language_parts[1].upper() if len(language_parts) > 1 else ""
	is_rtl = language_code in RTL_LANGUAGE_PREFIXES
	page_label = _("Page", lang=language)
	logo = branding.get("logo") or {}
	logo_image = logo_filename or logo.get("image") or ""
	logo_size = logo.get("size", 25)
	logo_dx = logo.get("dx", 0)
	logo_dy = logo.get("dy", 0)

	lines = []
	lines.append("#set page(")
	lines.append(f'  paper: "{page_size}",')
	if orientation == "landscape":
		lines.append("  flipped: true,")
	lines.append(
		f"  margin: (top: {margin_top}mm, bottom: {margin_bottom}mm, left: {margin_left}mm, right: {margin_right}mm),"
	)
	lines.append("  header: header_block,")
	lines.append("  footer: context {")
	lines.append("    grid(")
	lines.append("      columns: (1fr, auto),")
	lines.append("      column-gutter: 8pt,")
	lines.append("      footer_block,")
	lines.append(
		f'      text(size: 8pt, fill: rgb("#64748b"), lang: "{language_code}"'
		+ (f', region: "{region}"' if region else "")
		+ f', dir: {"rtl" if is_rtl else "ltr"})['
	)
	lines.append(f'        {page_label} #text(dir: ltr)[#counter(page).display("1 / 1", both: true)]')
	lines.append("      ],")
	lines.append("    )")
	lines.append("  },")

	if branding_mode in {"letterhead", "logo_letterhead"} and letterhead_filename:
		lines.append(f'  background: image("{letterhead_filename}", width: 100%)')

	if branding_mode in {"logo", "logo_letterhead"} and logo_image:
		lines.append("  foreground: [")
		lines.append(
			f'    #place(top + left, dx: {logo_dx}mm, dy: {logo_dy}mm, image("{logo_image}", width: {logo_size}mm))'
		)
		lines.append("  ]")

	lines.append(")")
	return "\n".join(lines)


def _normalize_report_presentation_settings(
	settings: dict | None,
	orientation: str = "landscape",
) -> dict:
	settings = settings or {}
	page = dict(settings.get("page") or {})
	page.setdefault("size", "A4")
	page.setdefault("orientation", orientation)
	page.setdefault("margins", {})
	branding = dict(settings.get("branding") or {})
	branding.setdefault("mode", "none")
	branding.setdefault("letterhead", "")
	branding.setdefault("letterhead_image", "")
	branding.setdefault("logo", {})
	return {
		**settings,
		"page": page,
		"branding": branding,
		"typography": settings.get("typography") or {},
		"table": settings.get("table") or {},
		"qr": settings.get("qr") or {},
		"report": settings.get("report") or {},
	}
