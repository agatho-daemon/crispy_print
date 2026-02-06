import re
from pathlib import Path

import frappe
from frappe import _
from frappe.query_builder import DocType


def get_crispy_formats_for_doctype(doctype):
	"""Get all enabled Crispy Formats for a given DocType.

	Returns formats that have both:
	- layout_json (reconstructable layout)
	- page_settings (page configuration)
	"""
	CrispyFormat = DocType("Crispy Format")

	formats = (
		frappe.qb.from_(CrispyFormat)
		.select(CrispyFormat.name, CrispyFormat.doc_type)
		.where(CrispyFormat.doc_type == doctype)
		.where(CrispyFormat.layout_json.isnotnull())  # Must have layout
		.orderby(CrispyFormat.name)
		.run(as_dict=True)
	)

	# Filter formats that have valid layout_json
	valid_formats = []
	for fmt in formats:
		try:
			layout = frappe.get_value(
				"Crispy Format", fmt.name, ["layout_json", "page_settings"], as_dict=True
			)

			# Check if layout_json is parseable
			if layout.get("layout_json"):
				import json

				json.loads(layout["layout_json"])  # Validate JSON
				valid_formats.append(fmt)
		except (json.JSONDecodeError, Exception) as e:
			frappe.log_error(
				f"Invalid layout_json for Crispy Format {fmt.name}: {e!s}",
				"Crispy Print Format Validation",
			)
			continue

	return valid_formats


def get_default_doctypes():
	"""Get all DocTypes that have a default Crispy Format set"""
	CrispyFormat = DocType("Crispy Format")

	results = (
		frappe.qb.from_(CrispyFormat)
		.select(CrispyFormat.doc_type)
		.where(CrispyFormat.is_default == 1)
		.run(as_dict=True)
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
	# Custom formats
	custom_formats = frappe.get_all(
		"Crispy Format",
		filters={"crispy_format_type": "Report", "is_generic": 0, "report": report},
		fields=["name", "modified"],
	)

	# Generic formats
	generic_formats = frappe.get_all(
		"Crispy Format",
		filters={"crispy_format_type": "Report", "is_generic": 1},
		fields=["name", "generic_report_type"],
		order_by="generic_report_type asc",
	)

	is_tree = _get_report_is_tree(report)
	if is_tree is not None:
		expected_type = "Tree" if is_tree else "Grid"
		generic_formats = [fmt for fmt in generic_formats if fmt.get("generic_report_type") == expected_type]

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

	# Determine builder mode
	mode = "visual"  # Default for DocType formats

	# Generic Report formats use code mode
	if format_doc.crispy_format_type == "Report" and format_doc.is_generic:
		mode = "code"
	# Raw Typst mode also uses code editor
	elif format_doc.raw_typst:
		mode = "code"

	return {
		"mode": mode,
		"format_type": format_doc.crispy_format_type,
		"is_generic": format_doc.is_generic or 0,
		"generic_report_type": format_doc.generic_report_type,
		"doc_type": format_doc.doc_type,
		"report": format_doc.report,
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
	reports = frappe.get_all(
		"Report",
		fields=["name", "report_type", "ref_doctype", "module"],
		filters={"disabled": 0, "report_type": ["in", ["Script Report", "Query Report"]]},
		order_by="name asc",
	)

	# Filter out reports with custom HTML and optionally by tree/grid type
	available_reports = []
	for report in reports:
		report_name = report["name"]
		module = report.get("module")

		if not module:
			continue

		report_folder = frappe.scrub(report_name)

		try:
			module_path = frappe.get_module_path(module)
			html_path = Path(module_path) / "report" / report_folder / f"{report_folder}.html"

			# Skip reports with custom HTML
			if html_path.exists():
				continue

			# Detect tree vs grid from JavaScript config
			js_path = Path(module_path) / "report" / report_folder / f"{report_folder}.js"
			is_tree = False
			if js_path.exists():
				js_content = js_path.read_text(encoding="utf-8")
				# Check for tree: true in JavaScript
				if "tree:" in js_content and "true" in js_content:
					is_tree = True

			# Filter by generic_report_type if specified
			if generic_report_type:
				if generic_report_type == "Tree" and not is_tree:
					continue
				if generic_report_type == "Grid" and is_tree:
					continue

			report["is_tree"] = is_tree
			available_reports.append(report)

		except Exception:
			# Module not found or path error - skip
			pass

	return available_reports


def _get_report_is_tree(report: str) -> bool | None:
	"""Return True/False for tree reports, or None when unknown."""
	if not report:
		return None

	try:
		report_doc = frappe.get_doc("Report", report)
		module = report_doc.module
		if not module:
			return None

		report_name = report_doc.report_name or report_doc.name
		report_folder = frappe.scrub(report_name)
		module_path = frappe.get_module_path(module)
		js_path = Path(module_path) / "report" / report_folder / f"{report_folder}.js"

		if not js_path.exists():
			return None

		js_content = js_path.read_text(encoding="utf-8")
		return bool(re.search(r"tree\\s*:\\s*true", js_content, re.IGNORECASE))
	except Exception:
		return None
