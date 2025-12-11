import base64
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import frappe
from frappe.query_builder import DocType
from frappe import _


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


def _copy_letterhead_to_temp(letterhead_image, temp_dir):
	"""
	Copy letterhead image to temp directory for Typst compilation.

	Args:
	    letterhead_image (str): Path to letterhead image (e.g., /files/letterhead.png)
	    temp_dir (str): Temporary directory path

	Returns:
	    str: Filename of copied letterhead (e.g., "letterhead.png")
	"""
	if not letterhead_image:
		return None

	# Handle Frappe file paths (/files/... or /private/files/...)
	if letterhead_image.startswith("/files/") or letterhead_image.startswith("/private/files/"):
		# Get site path
		site_path = frappe.get_site_path()

		# Remove leading slash and construct full path
		rel_path = letterhead_image.lstrip("/")
		source_path = Path(site_path) / "public" / rel_path

		if not source_path.exists():
			# Try private files
			source_path = Path(site_path) / rel_path

		if not source_path.exists():
			frappe.log_error(f"Letterhead image not found: {letterhead_image}", "Letterhead Copy Error")
			return None

		# Copy to temp directory with original filename
		dest_filename = source_path.name
		dest_path = Path(temp_dir) / dest_filename
		shutil.copy2(source_path, dest_path)

		return dest_filename

	return None


@frappe.whitelist()
def compile_typst(typst_source, output_format="svg", letterhead_image=None):
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


import frappe
from frappe.query_builder import DocType


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
				f"Invalid layout_json for Crispy Format {fmt.name}: {str(e)}",
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
