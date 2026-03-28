import base64
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import frappe
from frappe import _

APP_PATH = frappe.get_app_path("crispy_print")
TYPST_FONT_DIR = Path(APP_PATH) / "public" / "vendor" / "typst"


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
	if TYPST_FONT_DIR.exists():
		for font_file in TYPST_FONT_DIR.glob("*.[ot]tf"):
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


def compile_typst(
	typst_source,
	output_format="svg",
	letterhead_image=None,
	logo_image=None,
	chart_svg=None,
	qr_data=None,
	qr_filename=None,
	output_filename: str | None = None,
	return_url: int | bool = 0,
):
	"""
	Compile Typst source code using the local Typst CLI.

	Args:
	    typst_source (str): The Typst source code to compile.
	    output_format (str): Desired output format ("pdf" or "svg").
	    letterhead_image (str): Optional path to letterhead image (file path or URL).
	    output_filename (str): Optional output filename for PDF when return_url is enabled.
	    return_url (bool): When true and output_format="pdf", write to public files and return URL.

	Returns:
	    dict: Response with compiled artifact or error.
	"""

	if not typst_source or not typst_source.strip():
		frappe.throw(_("Typst source code is required"))

	# Log document data size for monitoring field filtering
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
				if return_url:
					if not output_filename:
						output_filename = f"crispy_{frappe.generate_hash()}.pdf"
					output_template = Path(frappe.get_site_path("public", "files")) / output_filename
				else:
					output_template = src_path_obj.with_suffix(".pdf")
			else:
				# Include page placeholder so Typst emits page-numbered SVGs (e.g. foo-1.svg, foo-2.svg ...)
				output_template = src_path_obj.with_name(f"{src_path_obj.stem}-{{p}}.svg")

			result = subprocess.run(
				[
					"typst",
					"compile",
					"--font-path",
					str(TYPST_FONT_DIR),
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

				if return_url:
					return {"success": True, "format": "pdf", "pdf_url": f"/files/{output_path.name}"}

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
