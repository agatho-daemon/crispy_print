import base64
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import frappe
from frappe import _
from frappe.query_builder import DocType


@frappe.whitelist()
def get_typst_local_fonts() -> list[str]:
	"""
	Returns a list of font family names accessible by Typst CLI.

	Must have TYPST_BIN in environment or rely on PATH.

	After installing typst, you can add fonts to typst by setting environment variable TYPST_FONTS_DIR
	in your shell (e.g. in .bashrc or .zshrc):
		export TYPST_FONTS_DIR="/path/to/fonts/directory"
	Or by using the typst CLI:
	    $ typst font add /path/to/font.ttf
	"""
	typst_bin = frappe.conf.get("TYPST_BIN", "typst")

	try:
		result = subprocess.run(
			[typst_bin, "fonts"],
			capture_output=True,
			text=True,
			check=True,
			timeout=5,
		)
	except Exception as e:
		frappe.throw(f"Error running typst fonts: {e}")

	fonts = []
	for line in result.stdout.splitlines():
		line = line.strip()
		if not line:
			continue

		# Typst outputs names like:  "Inter (Regular, Medium, Bold)"
		# So extract the family name (before the parenthesis)
		if "(" in line:
			family = line.split("(", 1)[0].strip()
		else:
			family = line

		fonts.append(family)

	# Add bundled fonts from public/vendor/typst/
	app_path = frappe.get_app_path("crispy_print")
	vendor_font_dir = Path(app_path) / "public" / "vendor" / "typst"

	if vendor_font_dir.exists():
		for font_file in vendor_font_dir.glob("*.[ot]tf"):
			# Extract font family name from filename (basic approach)
			font_name = font_file.stem
			# Remove common suffixes like -Regular, -Bold, etc.
			for suffix in ["-Regular", "-Bold", "-Italic", "-BoldItalic", "-Light", "-Medium", "-Black"]:
				if font_name.endswith(suffix):
					font_name = font_name[: -len(suffix)]
					break
			fonts.append(font_name)

	# Deduplicate and sort
	return sorted(list(set(fonts)))


def _copy_file_to_temp(file_path, temp_dir, label):
	"""
	Copy a file to the temp directory for Typst compilation.

	Args:
	    file_path (str): Path to file (e.g., /files/letterhead.png)
	    temp_dir (str): Temporary directory path

	Returns:
	    str: Filename of copied file (e.g., "letterhead.png")
	"""
	if not file_path:
		return None

	# Handle absolute paths
	path_obj = Path(file_path)
	if path_obj.is_absolute() and path_obj.exists():
		dest_filename = path_obj.name
		dest_path = Path(temp_dir) / dest_filename
		shutil.copy2(path_obj, dest_path)
		return dest_filename

	# Handle Frappe file paths (/files/... or /private/files/...) and relative variants
	if (
		file_path.startswith("/files/")
		or file_path.startswith("/private/files/")
		or file_path.startswith("files/")
		or file_path.startswith("private/files/")
		or file_path.startswith("public/files/")
	):
		# Get site path
		site_path = frappe.get_site_path()

		# Remove leading slash and construct full path
		rel_path = file_path.lstrip("/")
		if rel_path.startswith("files/"):
			rel_path = f"public/{rel_path}"

		if rel_path.startswith("public/files/") or rel_path.startswith("private/files/"):
			source_path = Path(site_path) / rel_path
		else:
			source_path = Path(site_path) / "public" / rel_path

		if not source_path.exists():
			# Try private files
			source_path = Path(site_path) / rel_path.replace("public/", "", 1)

		if not source_path.exists():
			frappe.log_error(f"{label} not found: {file_path}", f"{label} Copy Error")
			return None

		# Copy to temp directory with original filename
		dest_filename = source_path.name
		dest_path = Path(temp_dir) / dest_filename
		shutil.copy2(source_path, dest_path)

		return dest_filename

	# Handle bare filenames stored without /files/ prefix
	site_path = frappe.get_site_path()
	for base in [Path(site_path) / "public" / "files", Path(site_path) / "private" / "files"]:
		source_path = base / file_path.lstrip("/")
		if source_path.exists():
			dest_filename = source_path.name
			dest_path = Path(temp_dir) / dest_filename
			shutil.copy2(source_path, dest_path)
			return dest_filename

	frappe.log_error(f"{label} not found: {file_path}", f"{label} Copy Error")
	return None


def _copy_letterhead_to_temp(letterhead_image, temp_dir):
	return _copy_file_to_temp(letterhead_image, temp_dir, "Letterhead image")


def _copy_logo_to_temp(logo_image, temp_dir):
	return _copy_file_to_temp(logo_image, temp_dir, "Logo image")


def _write_qr_svg(qr_data, qr_filename, temp_dir):
	"""
	Generate a QR code SVG in the temp directory.

	Args:
	    qr_data (str): Payload to encode.
	    qr_filename (str): Target filename (e.g. "DOC-0001-qr.svg").
	    temp_dir (str): Temporary directory path.
	"""
	if not qr_data or not qr_filename:
		return None

	try:
		import pyqrcode
	except Exception as e:
		frappe.log_error(f"PyQRCode not available: {e}", "QR Code Error")
		return None

	filename = Path(qr_filename).name
	if not filename.lower().endswith(".svg"):
		filename = f"{filename}.svg"

	dest_path = Path(temp_dir) / filename

	try:
		qr = pyqrcode.create(str(qr_data))
		qr.svg(str(dest_path), scale=4, quiet_zone=1)
		return filename
	except Exception as e:
		frappe.log_error(f"Failed to generate QR SVG: {e}", "QR Code Error")
		return None


def _write_chart_svg(chart_svg: str, temp_dir: str, filename: str = "report_chart.svg"):
	"""Write report chart SVG to temp directory for Typst image() usage."""
	if not chart_svg:
		return
	# Extract the first <svg>...</svg> block to avoid HTML wrappers.
	import re
	from xml.etree import ElementTree as ET

	match = re.search(r"<svg\\b[^>]*>.*?</svg>", chart_svg, re.DOTALL | re.IGNORECASE)
	svg = (match.group(0) if match else chart_svg).strip()

	# Ensure SVG has the XML namespace (Typst requires a proper root node).
	if "<svg" in svg and "xmlns=" not in svg:
		svg = re.sub(
			r"<svg\\b",
			'<svg xmlns="http://www.w3.org/2000/svg"',
			svg,
			count=1,
			flags=re.IGNORECASE,
		)

	# Add xlink namespace if needed
	if "xlink:" in svg and "xmlns:xlink=" not in svg:
		svg = re.sub(
			r"<svg\\b",
			'<svg xmlns:xlink="http://www.w3.org/1999/xlink"',
			svg,
			count=1,
			flags=re.IGNORECASE,
		)

	# Escape stray & that can break XML parsing.
	svg = re.sub(r"&(?!(?:[a-zA-Z]+|#\\d+|#x[0-9a-fA-F]+);)", "&amp;", svg)

	# Validate XML; if invalid, fall back to minimal SVG to avoid Typst error.
	fallback = '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"></svg>'
	try:
		ET.fromstring(svg)
	except Exception as e:
		frappe.log_error(f"Invalid chart SVG, using fallback: {e}", "Chart SVG Error")
		svg = fallback

	dest_path = Path(temp_dir) / Path(filename).name
	dest_path.write_text(svg, encoding="utf-8")
	return filename


@frappe.whitelist()
def compile_typst(
	typst_source,
	output_format="svg",
	letterhead_image=None,
	logo_image=None,
	chart_svg=None,
	qr_data=None,
	qr_filename=None,
):
	"""
	Compile Typst source code using the local Typst CLI.

	Args:
	    typst_source (str): The Typst source code to compile.
	    output_format (str): Desired output format ("pdf" or "svg").
	    letterhead_image (str): Optional path to letterhead image (file path or URL).

	Returns:
	    dict: Response with compiled artifact or error.
	"""

	if not typst_source or not typst_source.strip():
		frappe.throw(_("Typst source code is required"))

	# Log document data size for monitoring field filtering
	import re

	doc_match = re.search(r"#let doc = \((.*?)\)", typst_source, re.DOTALL)
	if doc_match:
		doc_content = doc_match.group(1)
		# Count top-level fields (rough estimate)
		field_count = len(re.findall(r"^\s+\w+:", doc_content, re.MULTILINE))
		frappe.logger().info(f"[Typst Compile] Document contains ~{field_count} fields")
	else:
		frappe.logger().info("[Typst Compile] No #let doc found in source")

	allowed_formats = {"pdf", "svg"}
	output_format = (output_format or "svg").lower()
	if output_format not in allowed_formats:
		frappe.throw(_("Unsupported Typst output format: {0}").format(output_format))

	try:
		with TemporaryDirectory() as temp_dir:
			# Handle letterhead image if provided
			if letterhead_image:
				_copy_letterhead_to_temp(letterhead_image, temp_dir)
			if logo_image:
				_copy_logo_to_temp(logo_image, temp_dir)
			if chart_svg:
				_write_chart_svg(chart_svg, temp_dir)
			if qr_data and qr_filename:
				_write_qr_svg(qr_data, qr_filename, temp_dir)

			# Write Typst source to temp file
			src_path = Path(temp_dir) / "document.typ"
			src_path.write_text(typst_source, encoding="utf-8")

			src_path_obj = Path(src_path)
			if output_format == "pdf":
				output_template = src_path_obj.with_suffix(".pdf")
			else:
				# Include page placeholder so Typst emits page-numbered SVGs (e.g. foo-1.svg, foo-2.svg ...)
				output_template = src_path_obj.with_name(f"{src_path_obj.stem}-{{p}}.svg")

			app_path = frappe.get_app_path("crispy_print")
			font_dir = Path(app_path) / "public" / "vendor" / "typst"

			result = subprocess.run(
				[
					"typst",
					"compile",
					"--font-path",
					str(font_dir),
					"--format",
					output_format,
					src_path,
					str(output_template),
				],
				capture_output=True,
				text=True,
				timeout=30,
			)

			if result.returncode != 0:
				error_msg = result.stderr or result.stdout or "Unknown compilation error"
				frappe.log_error(
					message=f"Typst CLI error:\n{error_msg}\n\nSource:\n{typst_source[:500]}",
					title="Typst Compilation Error",
				)
				frappe.throw(_("Typst compilation failed: {0}").format(error_msg[:200]))

			if output_format == "pdf":
				output_path = Path(output_template)
				if not output_path.exists():
					frappe.throw(_("Compiled PDF was not produced"))

				with output_path.open("rb") as pdf_file:
					pdf_bytes = pdf_file.read()

				pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
				return {"success": True, "format": "pdf", "pdf_data": pdf_base64}

			# SVG output (may include multiple pages)
			base_name = src_path_obj.stem
			output_dir = Path(output_template).parent

			def svg_sort_key(path: Path):
				name = path.stem
				if name.startswith(f"{base_name}-"):
					suffix = name[len(base_name) + 1 :]
					try:
						return int(suffix)
					except ValueError:
						return 9999
				return 9999

			svg_files = sorted(output_dir.glob(f"{base_name}-*.svg"), key=svg_sort_key)

			if not svg_files:
				frappe.throw(_("Compiled SVG was not produced"))

			svg_pages = []
			for svg_path in svg_files:
				with svg_path.open("r", encoding="utf-8") as svg_file:
					svg_pages.append(svg_file.read())

			return {
				"success": True,
				"format": "svg",
				"svg_pages": svg_pages,
				"page_count": len(svg_pages),
			}

	except FileNotFoundError:
		frappe.throw(_("Typst compiler not found. Please install Typst CLI: brew install typst"))

	except subprocess.TimeoutExpired:
		frappe.throw(_("Compilation timed out. The document may be too complex."))

	except Exception as exc:
		frappe.log_error(message=str(exc), title="Typst Compilation Error")
		frappe.throw(_("Unexpected error during compilation: {0}").format(str(exc)))

	finally:
		# Cleanup temp directory (includes source file, letterhead, and outputs)
		if src_path:
			temp_dir = Path(src_path).parent
			try:
				if temp_dir.exists():
					shutil.rmtree(temp_dir)
			except Exception as e:
				frappe.log_error(f"Failed to cleanup temp directory: {e}", "Typst Cleanup Error")


@frappe.whitelist()
def get_formatted_doc(doctype: str, name: str) -> dict:
	"""
	Return a document with server-side formatted values (currency/date/percent/etc.).

	This keeps Typst preview consistent across pages without relying on client-side meta.
	"""
	if not doctype or not name:
		frappe.throw(_("doctype and name are required"))

	doc = frappe.get_doc(doctype, name)
	meta = frappe.get_meta(doctype)
	data = doc.as_dict()

	field_map = {df.fieldname: df for df in meta.fields if df.fieldname}

	for df in meta.fields:
		fieldname = df.fieldname
		if not fieldname or fieldname not in data:
			continue

		if df.fieldtype == "Table" and df.options:
			child_meta = frappe.get_meta(df.options)
			child_field_map = {cdf.fieldname: cdf for cdf in child_meta.fields if cdf.fieldname}
			rows = data.get(fieldname) or []
			formatted_rows = []
			for row in rows:
				if not isinstance(row, dict):
					formatted_rows.append(row)
					continue
				formatted_row = dict(row)
				for key, value in row.items():
					cdf = child_field_map.get(key)
					if not cdf:
						continue
					try:
						formatted_value = frappe.format(value, cdf, doc=doc, translated=False)
						if cdf.fieldtype in ("Text Editor", "HTML") and isinstance(formatted_value, str):
							formatted_value = frappe.utils.strip_html(formatted_value)
						formatted_row[key] = formatted_value
					except Exception:
						formatted_row[key] = value
				formatted_rows.append(formatted_row)
			data[fieldname] = formatted_rows
			continue

		df_for_field = field_map.get(fieldname)
		if not df_for_field:
			continue
		try:
			formatted_value = frappe.format(data.get(fieldname), df_for_field, doc=doc, translated=False)
			if df_for_field.fieldtype in ("Text Editor", "HTML") and isinstance(formatted_value, str):
				formatted_value = frappe.utils.strip_html(formatted_value)
			data[fieldname] = formatted_value
		except Exception:
			pass

	return data


@frappe.whitelist()
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


@frappe.whitelist()
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


@frappe.whitelist()
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
	import json
	import os
	from tempfile import TemporaryDirectory

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

	# Compile to PDF
	pdf_url = _compile_typst_to_pdf(typst_source)

	return {"pdf_url": pdf_url, "status": "success"}


@frappe.whitelist()
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


@frappe.whitelist()
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


@frappe.whitelist()
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


@frappe.whitelist()
def get_report_typst_source(
	report: str,
	format_name: str,
	filters: dict | str | None = None,
	column_config: list | str | None = None,
	include_filters: int = 0,
	orientation: str | None = None,
	page_settings: dict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
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
	import json

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

	# Get report data
	report_data = _get_report_data(report, filters or {})

	# Get format document
	format_doc = frappe.get_doc("Crispy Format", format_name)

	# Prepare data for Typst
	typst_data = _prepare_typst_report_data(
		report, report_data, filters if include_filters else None, column_filter
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
		code = format_doc.typst_code or ""
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


@frappe.whitelist()
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
	import json

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
	result = frappe.desk.query_report.run(report, filters=filters)

	return {
		"columns": result.get("columns", []),
		"result": result.get("result", []),
		"message": result.get("message"),
		"chart": result.get("chart"),
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

	# Build column width map from filter
	width_map = {}
	if column_filter and len(column_filter) > 0:
		for col_config in column_filter:
			if isinstance(col_config, dict):
				fieldname = col_config.get("fieldname")
				width = col_config.get("width", "auto")
				if fieldname:
					width_map[fieldname] = width

		# Filter to only selected columns (preserve order from column_filter)
		filtered_columns = []
		for col_config in column_filter:
			fieldname = col_config.get("fieldname")
			for col in visible_columns:
				col_fieldname = col.get("fieldname") or col.get("id", "")
				if col_fieldname == fieldname:
					filtered_columns.append(col)
					break
		visible_columns = filtered_columns

	# Prepare column definitions
	typst_columns = []
	for col in visible_columns:
		fieldname = col.get("fieldname") or col.get("id", "")
		custom_width = width_map.get(fieldname, "auto")

		typst_columns.append(
			{
				"label": _(col.get("label", "")),
				"fieldname": fieldname,
				"fieldtype": col.get("fieldtype", "Data"),
				"width": custom_width,  # Use custom width from user or "auto"
				"is_numeric": _is_numeric_fieldtype(col.get("fieldtype", "Data")),
			}
		)

	# Prepare row data
	typst_rows = []
	for idx, row in enumerate(rows):
		formatted_row = _prepare_row_data(row, visible_columns, idx)
		typst_rows.append(formatted_row)

	# Prepare filters if provided
	formatted_filters = []
	if filters:
		for key, value in filters.items():
			if value is not None and value != "":
				# Format filter label (convert from_date to From Date)
				label = key.replace("_", " ").title()
				formatted_filters.append({"label": label, "value": str(value)})

	result = {
		"title": report,
		"subtitle": f"Generated on {frappe.utils.now_datetime().strftime('%d %b %Y at %H:%M')}",
		"total_rows": len(rows),
		"columns": typst_columns,
		"rows": typst_rows,
	}

	if formatted_filters:
		result["filters"] = formatted_filters

	return result


def _prepare_row_data(row, columns: list, index: int) -> dict:
	"""Format a single row for Typst"""
	from frappe.utils import cint

	cells = []
	is_mapping = isinstance(row, dict)
	row_ctx = row if is_mapping else {}

	for col_idx, col in enumerate(columns):
		fieldname = col.get("fieldname") or col.get("id", "")
		if is_mapping:
			value = row.get(fieldname)
		elif isinstance(row, list | tuple):
			value = row[col_idx] if col_idx < len(row) else None
		else:
			value = None

		# Handle total row special case
		if is_mapping and row.get("is_total_row") and col.get("_index") == 0:
			formatted_value = _("Total")
		else:
			formatted_value = _format_cell_value(value, col, row_ctx)

		cells.append(
			{
				"value": formatted_value,
				"raw": value,
				"is_numeric": _is_numeric_fieldtype(col.get("fieldtype", "Data")),
			}
		)

	return {
		"index": index + 1,
		"indent": cint(row.get("indent", 0)) if is_mapping else 0,
		"is_bold": row.get("bold") == 1 if is_mapping else False,
		"is_total_row": row.get("is_total_row", False) if is_mapping else False,
		"cells": cells,
	}


def _format_cell_value(value, col: dict, row: dict) -> str:
	"""Format cell value using Frappe's formatting"""
	from frappe.utils import cint, flt

	if value is None or value == "":
		return ""

	fieldtype = col.get("fieldtype", "Data")

	# Use docfield for formatting if available
	if col.get("docfield"):
		return frappe.format(value, col["docfield"])

	# Default formatting by fieldtype
	if fieldtype == "Currency":
		return frappe.format(value, {"fieldtype": "Currency"})
	elif fieldtype in ["Float", "Percent"]:
		return f"{flt(value, 2)}"
	elif fieldtype == "Int":
		return str(cint(value))
	elif fieldtype == "Date":
		return frappe.format(value, {"fieldtype": "Date"})
	elif fieldtype == "Datetime":
		return frappe.format(value, {"fieldtype": "Datetime"})
	else:
		return str(value)


def _is_numeric_fieldtype(fieldtype: str) -> bool:
	"""Check if fieldtype is numeric"""
	return fieldtype in ["Currency", "Float", "Int", "Percent"]


def _normalize_columns(columns: list) -> list:
	"""Normalize column structure and add indices"""
	normalized = []

	for idx, col in enumerate(columns):
		if isinstance(col, str):
			normalized.append(
				{
					"fieldname": col,
					"label": col.replace("_", " ").title(),
					"fieldtype": "Data",
					"_id": col,
					"_index": idx,
				}
			)
		else:
			col["_id"] = col.get("fieldname", col.get("id", ""))
			col["_index"] = idx
			normalized.append(col)

	return normalized


def _build_typst_document(
	format_doc,
	data_dict: dict,
	variable_name: str = "doc",
	header_block: str | None = None,
	footer_block: str | None = None,
	page_settings_block: str | None = None,
	preamble_override: str | None = None,
) -> str:
	"""
	Build complete Typst document by injecting data into template.

	Unified compilation function for all modes (DocType, Report, Contract).

	Args:
		format_doc: Crispy Format document with fields (typst_preamble, doc_header, doc_footer, typst_code)
		data_dict: Dictionary to inject as Typst variable (doc, data, contract)
		variable_name: Name of Typst variable to create (default: "doc")
		header_block: Optional header block override (for letterhead/branding)
		footer_block: Optional footer block override

	Returns:
		str: Complete Typst document ready for compilation
	"""
	# Convert Python data to Typst syntax
	typst_data = _python_to_typst_dict(data_dict)

	# Build document sections
	sections = []

	# 1. Preamble (set rules, imports, helper functions)
	if preamble_override:
		sections.append(f"// Preamble override\n{preamble_override}")
	if format_doc.typst_preamble:
		sections.append(f"// Preamble\n{format_doc.typst_preamble}")

	# 2. Data variable definition
	sections.append(f"\n// Data injection\n#let {variable_name} = {typst_data}")

	# 3. Default header/footer blocks (safe no-op)
	sections.append("\n#let header_block = []")
	sections.append("#let footer_block = []")

	# 4. Header block (can be overridden for letterhead)
	if header_block:
		sections.append(f"\n// Header (with letterhead)\n{header_block}")
	elif format_doc.doc_header:
		sections.append(f"\n// Header\n{format_doc.doc_header}")

	# 5. Footer block (can be overridden)
	if footer_block:
		sections.append(f"\n// Footer (custom)\n{footer_block}")
	elif format_doc.doc_footer:
		sections.append(f"\n// Footer\n{format_doc.doc_footer}")

	# 6. Page settings block (optional)
	if page_settings_block:
		sections.append(f"\n// Page settings\n{page_settings_block}")

	# 7. Main template code
	sections.append(f"\n// Main template\n{format_doc.typst_code}")

	return "\n".join(sections)


def _compile_typst_to_pdf(typst_source: str, output_filename: str | None = None) -> str:
	"""
	Compile Typst source to PDF and return public URL.

	Args:
		typst_source: Complete Typst document source
		output_filename: Optional output filename (default: auto-generated)

	Returns:
		str: Public URL to generated PDF
	"""
	import os
	from pathlib import Path
	from tempfile import TemporaryDirectory

	with TemporaryDirectory() as temp_dir:
		# Write Typst file
		typst_file = os.path.join(temp_dir, "document.typ")
		with open(typst_file, "w", encoding="utf-8") as f:
			f.write(typst_source)

		# Output PDF path
		if not output_filename:
			output_filename = f"crispy_{frappe.generate_hash()}.pdf"
		output_pdf = os.path.join(frappe.get_site_path("public", "files"), output_filename)

		# Get font directory
		app_path = frappe.get_app_path("crispy_print")
		font_dir = Path(app_path) / "public" / "vendor" / "typst"

		# Compile with Typst CLI
		result = subprocess.run(
			["typst", "compile", "--font-path", str(font_dir), typst_file, output_pdf],
			capture_output=True,
			text=True,
			timeout=30,
		)

		if result.returncode != 0:
			error_msg = result.stderr or result.stdout or "Unknown compilation error"
			frappe.log_error(
				message=f"Typst compilation failed:\n{error_msg}\n\nSource (first 500 chars):\n{typst_source[:500]}",
				title="Typst Compilation Error",
			)
			# Extract the actual error from Typst output
			typst_error = error_msg.split("\n")[0] if error_msg else "Unknown error"
			frappe.throw(_("Typst compilation failed: {0}").format(typst_error))

		# Return public URL
		return f"/files/{output_filename}"


def _python_to_typst_dict(data: dict | list | str | int | float | bool | None) -> str:
	"""
	Convert Python data structures to Typst dictionary/array syntax.

	Example:
		{"title": "Report", "total": 100, "items": ["A", "B"]}
		→ '(title: "Report", total: 100, items: ("A", "B"))'
	"""
	from datetime import date, datetime

	def serialize_value(val):
		if val is None:
			return "none"
		elif isinstance(val, bool):
			return "true" if val else "false"
		elif isinstance(val, int | float):
			return str(val)
		elif isinstance(val, str):
			# Escape backslashes, quotes, and newlines
			escaped = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
			return f'"{escaped}"'
		elif isinstance(val, list | tuple):
			if not val:
				return "()"
			items = ", ".join(serialize_value(v) for v in val)
			# Typst single-item tuples need trailing comma
			return f"({items},)" if len(val) == 1 else f"({items})"
		elif isinstance(val, dict):
			if not val:
				return "()"
			pairs = []
			for k, v in val.items():
				# Sanitize dictionary keys (must be valid Typst identifiers)
				key = str(k).replace("-", "_").replace(" ", "_")
				pairs.append(f"{key}: {serialize_value(v)}")
			return f"({', '.join(pairs)})"
		elif isinstance(val, datetime | date):
			return f'"{val.isoformat()}"'
		else:
			# Fallback: convert to string
			return f'"{val!s}"'

	return serialize_value(data)


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
		return bool(re.search(r"tree\s*:\s*true", js_content, re.IGNORECASE))
	except Exception:
		return None
