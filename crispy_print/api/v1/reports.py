import json
from pathlib import Path

import frappe
from frappe import _

from .compile import compile_typst
from .typst_doc import _build_typst_document


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

	# Get report data
	report_data = _get_report_data(report, filters or {})

	# Get or auto-select format
	if not format_name:
		format_name = _get_format_for_report(report)

	format_doc = frappe.get_doc("Crispy Format", format_name)

	# Prepare data for Typst
	typst_data = _prepare_typst_report_data(
		report, report_data, filters if cint(include_filters) else None, column_filter
	)

	# Add page settings
	typst_data["page_settings"] = {"orientation": orientation.lower() if orientation else "landscape"}

	# Build Typst document using unified compilation
	typst_source = _build_typst_document(
		format_doc=format_doc,
		data_dict=typst_data,
		variable_name="data",  # Reports use #data.* namespace
	)

	# Compile to PDF (write to public files and return URL)
	result = compile_typst(typst_source, output_format="pdf", return_url=1)

	return {"pdf_url": result.get("pdf_url"), "status": "success"}


def get_report_typst_source(
	report: str,
	format_name: str,
	filters: dict | str | None = None,
	column_config: list | str | None = None,
	include_filters: int = 0,
	include_summary: int = 1,
	include_total_row: int = 1,
	orientation: str | None = None,
	page_settings: dict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	typst_code_override: str | None = None,
	preview_data: dict | str | None = None,
	letterhead_image: str | None = None,
	limit: int = 50,
) -> str:
	"""
	Build Typst source for report preview.

	Frontend calls this to get source, then passes to compile_typst().
	Same pattern as DocType mode - no duplication.

	Args:
		report: Report name
		format_name: Crispy Format name
		filters: Report filters (dict or JSON string, optional)
		column_config: Column configuration with widths (optional)
		limit: Maximum rows for preview (default: 50)

	Returns:
		str: Complete Typst source code
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

	# Parse filters if string
	if isinstance(filters, str):
		try:
			filters = json.loads(filters)
		except json.JSONDecodeError:
			filters = {}
	if not isinstance(filters, dict):
		filters = {}

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

	# Parse page settings if string
	page_settings_dict = None
	if page_settings:
		if isinstance(page_settings, str):
			try:
				page_settings_dict = json.loads(page_settings)
			except json.JSONDecodeError:
				page_settings_dict = None
		elif isinstance(page_settings, dict):
			page_settings_dict = page_settings

	# Get format document
	format_doc = frappe.get_doc("Crispy Format", format_name)
	if isinstance(typst_code_override, str) and typst_code_override.strip():
		format_doc.typst_code = typst_code_override

	# Prepare data for Typst
	if preview_data_dict:
		typst_data = dict(preview_data_dict)
		typst_data.setdefault("title", report or "Style Preview")
		typst_data.setdefault("subtitle", "")
		typst_data.setdefault("filters", [])
		typst_data.setdefault("report_summary", [])
		typst_data.setdefault("columns", [])
		typst_data.setdefault("rows", [])
		typst_data.setdefault("total_rows", len(typst_data.get("rows") or []))
		typst_data.setdefault("chart", {})
		typst_data.setdefault("skip_total_row", False)
	else:
		report_data = _get_report_data(report, filters or {})
		typst_data = _prepare_typst_report_data(
			report,
			report_data,
			filters if cint(include_filters) else None,
			column_filter,
			include_summary=bool(cint(include_summary)),
			include_total_row=bool(cint(include_total_row)),
		)

	# Limit rows for preview
	if limit and len(typst_data["rows"]) > limit:
		typst_data["rows"] = typst_data["rows"][:limit]
		typst_data["total_rows"] = limit

	# Add page settings (default to landscape for reports)
	orientation_value = (orientation or "landscape").lower()
	if page_settings_dict:
		logo = page_settings_dict.get("logo") or {}
		logo_image = logo.get("image") or ""
		if logo_image:
			logo["image"] = Path(logo_image).name
			page_settings_dict["logo"] = logo

		typst_data["page_settings"] = {
			**page_settings_dict,
			"orientation": page_settings_dict.get("orientation", orientation_value),
		}
	else:
		typst_data["page_settings"] = {"orientation": orientation_value}

	# Attach chart placeholder for Typst if SVG is provided
	if isinstance(chart_svg, str) and chart_svg.strip():
		typst_data["chart_svg"] = "report_chart.svg"
		code = format_doc.typst_code or ""
		if "data.chart_svg" not in code:
			chart_block = (
				"\n// Report chart\n"
				'#if "chart_svg" in data and data.chart_svg != "" [\n'
				"  #block(\n"
				'    stroke: (paint: rgb("#E5E7EB"), thickness: 0.5pt),\n'
				"    inset: (x: 8pt, y: 8pt),\n"
				"    radius: 2pt,\n"
				"  )[\n"
				"    #image(data.chart_svg, width: 100%)\n"
				"  ]\n"
				"  #v(1em)\n"
				"]\n"
			)
			inserted = False
			for marker in ("// TABLE SETUP", "#table("):
				pos = code.find(marker)
				if pos != -1:
					format_doc.typst_code = code[:pos] + chart_block + code[pos:]
					inserted = True
					break
			if not inserted:
				format_doc.typst_code = code + chart_block

	# Build Typst document using unified compilation
	preamble_override = (
		typst_preamble_override.strip()
		if isinstance(typst_preamble_override, str) and typst_preamble_override.strip()
		else None
	)
	letterhead_filename = Path(letterhead_image).name if letterhead_image else None
	page_settings_block = _build_report_page_settings_block(
		page_settings_dict,
		letterhead_filename,
		page_settings_dict.get("logo", {}).get("image") if page_settings_dict else None,
	)
	typst_source = _build_typst_document(
		format_doc=format_doc,
		data_dict=typst_data,
		variable_name="data",  # Reports use #data.* namespace
		page_settings_block=page_settings_block,
		preamble_override=preamble_override,
	)

	return typst_source


def get_sample_report_data(report: str, filters=None, limit: int = 50) -> dict:
	"""
	Get sample data from a report for preview purposes.

	Args:
		report: Report name
		filters: Report filters (dict or JSON string, optional)
		limit: Maximum rows to return (default: 50)

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
	report_data = _get_report_data(report, filters)

	# Prepare for Typst
	typst_data = _prepare_typst_report_data(report, report_data, filters=None, column_filter=None)

	# Limit rows
	if limit and len(typst_data["rows"]) > limit:
		typst_data["rows"] = typst_data["rows"][:limit]
		typst_data["total_rows"] = limit

	return typst_data


def _get_report_data(report: str, filters: dict) -> dict:
	"""Execute report and return raw data"""
	# Always run live for Crispy preview/PDF so prepared-report queue state
	# does not return empty placeholder payloads.
	result = frappe.desk.query_report.run(
		report,
		filters=filters,
		ignore_prepared_report=True,
		are_default_filters=False,
	)

	return {
		"columns": result.get("columns", []),
		"result": result.get("result", []),
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

	columns = _normalize_columns(report_data["columns"])
	rows = report_data["result"]

	# Filter visible columns
	visible_columns = [col for col in columns if col.get("label") and col.get("_id") != "_check"]
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

	# Convert rows to dictionary for Typst
	processed_rows = []
	for index, row in enumerate(rows):
		processed_rows.append(_prepare_row_data(row, visible_columns, index))
	base_rows = [row for row in processed_rows if not row.get("is_total_row")]
	final_rows = processed_rows if include_total_row else base_rows

	# Generate report title
	report_title = report_data.get("message") or report

	# Get report chart if any
	report_chart = report_data.get("chart") or {}
	report_summary = report_data.get("report_summary") or []
	if not include_summary:
		report_summary = []
	skip_total_row = bool(report_data.get("skip_total_row"))

	return {
		"columns": visible_columns,
		"rows": final_rows,
		"total_rows": len(base_rows),
		"filters": _normalize_filters_for_typst(filters),
		"title": report_title,
		"subtitle": "",
		"chart": report_chart,
		"report_summary": report_summary,
		"skip_total_row": skip_total_row,
	}


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


def _prepare_row_data(row, columns: list, index: int) -> dict:
	"""Transform a row into a Typst row dict"""
	out = {"_idx": index, "cells": [], "is_bold": False, "is_total_row": False}

	# Row can be list or dict
	if isinstance(row, dict):
		out["is_bold"] = bool(row.get("bold") or row.get("is_bold"))
		out["is_total_row"] = bool(row.get("is_total_row"))
		for col in columns:
			fieldname = col.get("fieldname")
			if fieldname:
				value = _format_cell_value(row.get(fieldname), col, row)
				out[fieldname] = value
				out["cells"].append(
					{
						"value": value,
						"fieldname": fieldname,
						"label": col.get("label") or fieldname,
						"is_numeric": bool(col.get("is_numeric")),
					}
				)
		return out

	# Handle list rows
	if isinstance(row, list | tuple):
		for col in columns:
			fieldname = col.get("fieldname")
			col_index = col.get("col_index")
			if fieldname and col_index is not None and col_index < len(row):
				value = _format_cell_value(row[col_index], col, row)
				out[fieldname] = value
				out["cells"].append(
					{
						"value": value,
						"fieldname": fieldname,
						"label": col.get("label") or fieldname,
						"is_numeric": bool(col.get("is_numeric")),
					}
				)
		return out

	return out


def _format_cell_value(value, col: dict, row: dict) -> str:
	"""Format a cell value for Typst output"""
	fieldtype = col.get("fieldtype")

	if value is None:
		return ""

	if isinstance(value, str):
		return value.strip()

	if _is_numeric_fieldtype(fieldtype):
		try:
			if fieldtype == "Percent":
				return f"{float(value):,.2f}%"
			return f"{float(value):,.2f}"
		except Exception:
			return str(value)

	return str(value)


def _is_numeric_fieldtype(fieldtype: str) -> bool:
	return fieldtype in ("Int", "Float", "Currency", "Percent")


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
	"""Auto-select format for report (custom or generic)"""
	# Check for custom format
	custom = frappe.db.get_value(
		"Crispy Format", {"crispy_format_type": "Report", "is_generic": 0, "report": report}, "name"
	)

	if custom:
		return custom

	# Fallback to first available generic Grid template
	generic = frappe.db.get_value(
		"Crispy Format",
		{"crispy_format_type": "Report", "is_generic": 1, "generic_report_type": "Grid"},
		"name",
	)

	if generic:
		return generic

	frappe.throw(_("No print format found for report '{0}'").format(report))


def _build_report_page_settings_block(
	page_settings: dict | None,
	letterhead_filename: str | None,
	logo_filename: str | None,
) -> str:
	"""Build a #set page() block for report previews using page settings."""
	page_settings = page_settings or {}
	page_size = str(page_settings.get("pageSize") or "A4").lower()
	# Reports default to landscape unless explicitly overridden
	orientation = str(page_settings.get("orientation") or "landscape").lower()
	margins = page_settings.get("margins") or {}
	margin_top = margins.get("top", 25)
	margin_bottom = margins.get("bottom", 20)
	margin_left = margins.get("left", 20)
	margin_right = margins.get("right", 20)
	branding_mode = str(page_settings.get("brandingMode") or "none")
	logo = page_settings.get("logo") or {}
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
	lines.append("  footer: footer_block,")

	if branding_mode == "letterhead" and letterhead_filename:
		lines.append(f'  background: image("{letterhead_filename}", width: 100%)')

	if branding_mode == "logo" and logo_image:
		lines.append("  foreground: [")
		lines.append(
			f'    #place(top + left, dx: {logo_dx}mm, dy: {logo_dy}mm, image("{logo_image}", width: {logo_size}mm))'
		)
		lines.append("  ]")

	lines.append(")")
	return "\n".join(lines)
