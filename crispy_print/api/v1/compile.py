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
IMAGE_EXTENSIONS = {
	".png",
	".jpg",
	".jpeg",
	".svg",
	".gif",
	".webp",
	".bmp",
	".tif",
	".tiff",
	".avif",
}
_IMAGE_SUFFIX_RE = re.compile(r"\.([A-Za-z0-9]+)(?:[#?].*)?$")
_TYPST_IMAGE_LITERAL_RE = re.compile(r'image\(\s*"([^"\n]+)"')
_TYPST_FILE_NOT_FOUND_RE = re.compile(r"file not found \(searched at ([^)]+)\)")


def _strip_url_suffix(value: str) -> str:
	return re.split(r"[?#]", value, maxsplit=1)[0]


def _is_image_asset_value(value: str) -> bool:
	match = _IMAGE_SUFFIX_RE.search(str(value or "").strip())
	if not match:
		return False
	return f".{match.group(1).lower()}" in IMAGE_EXTENSIONS


def _is_external_asset_path(path: str) -> bool:
	raw = str(path or "").strip().lower()
	return raw.startswith("http://") or raw.startswith("https://") or raw.startswith("data:")


def _normalize_typst_image_literals(typst_source: str) -> tuple[str, list[str]]:
	"""Normalize literal image paths in Typst source to local basenames.

	Returns:
	    tuple[str, list[str]]: (updated_typst_source, collected_original_paths)
	"""
	collected: list[str] = []
	seen: set[str] = set()

	def repl(match: re.Match[str]) -> str:
		raw_path = match.group(1)
		clean_path = _strip_url_suffix(raw_path)
		basename = Path(clean_path).name

		if (
			not _is_image_asset_value(clean_path)
			or _is_external_asset_path(clean_path)
			or not basename
			or clean_path == "report_chart.svg"
		):
			return match.group(0)

		has_dirs = "/" in clean_path or "\\" in clean_path
		if has_dirs:
			if raw_path not in seen:
				seen.add(raw_path)
				collected.append(raw_path)
			return match.group(0).replace(raw_path, basename, 1)

		return match.group(0)

	return _TYPST_IMAGE_LITERAL_RE.sub(repl, typst_source), collected


def _extract_missing_image_basenames(error_msg: str) -> list[str]:
	"""Extract missing image basenames from Typst file-not-found errors."""
	if not error_msg:
		return []
	names: list[str] = []
	seen: set[str] = set()
	for match in _TYPST_FILE_NOT_FOUND_RE.findall(error_msg):
		candidate = Path(_strip_url_suffix(match.strip())).name
		if not candidate:
			continue
		if not _is_image_asset_value(candidate):
			continue
		if candidate in seen:
			continue
		seen.add(candidate)
		names.append(candidate)
	return names


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


def _find_filename_in_site_files(filename: str) -> Path | None:
	"""Find bare filename in standard Frappe file directories.

	Search order: private first, then public.
	Within each tier, multiple matches are treated as ambiguous and raise.
	"""
	site_path = Path(frappe.get_site_path())
	search_roots = [
		("private", site_path / "private" / "files"),
		("public", site_path / "public" / "files"),
	]

	for tier, root in search_roots:
		if not root.exists():
			continue
		matches = [p for p in root.rglob(filename) if p.is_file()]
		if not matches:
			continue
		if len(matches) > 1:
			rel_matches = [str(path.relative_to(site_path)) for path in sorted(matches)]
			frappe.throw(
				_("{0} is ambiguous in {1} files: {2}").format(
					filename,
					tier,
					", ".join(rel_matches),
				)
			)
		return matches[0]

	return None


def _resolve_source_path(file_path: str, label: str) -> Path:
	"""Resolve a source file path for Typst asset copying."""
	clean_path = _strip_url_suffix(file_path)
	basename = Path(clean_path).name

	# Handle absolute paths
	path_obj = Path(clean_path)
	if path_obj.is_absolute():
		if path_obj.exists() and path_obj.is_file():
			return path_obj
		# Fallback to filename-only search in standard Frappe file trees.
		if basename:
			source_path = _find_filename_in_site_files(basename)
			if source_path:
				return source_path
		frappe.throw(_("{0} not found: {1}").format(label, file_path))

	site_path = Path(frappe.get_site_path())

	# Handle Frappe file paths (/files/... or /private/files/...) and relative variants
	if (
		clean_path.startswith("/files/")
		or clean_path.startswith("/private/files/")
		or clean_path.startswith("files/")
		or clean_path.startswith("private/files/")
		or clean_path.startswith("public/files/")
	):
		rel_path = clean_path.lstrip("/")
		if rel_path.startswith("files/"):
			rel_path = f"public/{rel_path}"

		if rel_path.startswith("public/files/") or rel_path.startswith("private/files/"):
			source_path = site_path / rel_path
		else:
			source_path = site_path / "public" / rel_path

		if not source_path.exists():
			source_path = site_path / rel_path.replace("public/", "", 1)

		if source_path.exists() and source_path.is_file():
			return source_path
		if basename:
			fallback = _find_filename_in_site_files(basename)
			if fallback:
				return fallback
		frappe.throw(_("{0} not found: {1}").format(label, file_path))

	# Treat slashless values as filename-only lookup in standard file dirs.
	if "/" not in clean_path and "\\" not in clean_path:
		source_path = _find_filename_in_site_files(clean_path)
		if source_path:
			return source_path
		frappe.throw(_("{0} not found in private/files or public/files: {1}").format(label, file_path))

	# Fallback for relative paths with directories
	source_path = site_path / clean_path.lstrip("/")
	if source_path.exists() and source_path.is_file():
		return source_path
	if basename:
		fallback = _find_filename_in_site_files(basename)
		if fallback:
			return fallback

	frappe.throw(_("{0} not found: {1}").format(label, file_path))


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

	source_path = _resolve_source_path(str(file_path), label)
	dest_filename = source_path.name
	dest_path = Path(temp_dir) / dest_filename
	shutil.copy2(source_path, dest_path)
	return dest_filename


def _normalize_asset_files(asset_files) -> list[str]:
	if asset_files is None:
		return []
	if not isinstance(asset_files, list):
		frappe.throw(_("asset_files must be a list of image file paths"))

	normalized: list[str] = []
	seen: set[str] = set()
	invalid_entries: list[str] = []
	for value in asset_files:
		if not isinstance(value, str):
			invalid_entries.append(f"{value!r}: must be a string path")
			continue
		raw = value.strip()
		if not raw:
			invalid_entries.append(f"{value!r}: path cannot be empty")
			continue
		if not _is_image_asset_value(raw):
			invalid_entries.append(f"{value!r}: unsupported image extension")
			continue
		if _is_external_asset_path(raw):
			invalid_entries.append(f"{value!r}: external/data URLs are not allowed")
			continue
		if raw in seen:
			continue
		seen.add(raw)
		normalized.append(raw)

	if invalid_entries:
		frappe.throw(_("Invalid asset_files entries:\n{0}").format("\n".join(invalid_entries)))
	return normalized


def _copy_asset_files_to_temp(asset_files, temp_dir):
	normalized_assets = _normalize_asset_files(asset_files)
	if not normalized_assets:
		return

	errors: list[str] = []
	for asset in normalized_assets:
		try:
			_copy_file_to_temp(asset, temp_dir, "Asset file")
		except Exception as exc:
			errors.append(f"{asset}: {exc}")

	if errors:
		frappe.throw(_("Asset file resolution failed:\n{0}").format("\n".join(errors)))


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
	asset_files=None,
	chart_svg=None,
	qr_data=None,
	qr_filename=None,
	output_filename: str | None = None,
	return_url: int | bool = 0,
	**kwargs,
):
	"""
	Compile Typst source code using the local Typst CLI.

	Args:
	    typst_source (str): The Typst source code to compile.
	    output_format (str): Desired output format ("pdf" or "svg").
	    asset_files (list[str]): Optional image asset paths/filenames to resolve.
	    output_filename (str): Optional output filename for PDF when return_url is enabled.
	    return_url (bool): When true and output_format="pdf", write to public files and return URL.

	Returns:
	    dict: Response with compiled artifact or error.
	"""

	if not typst_source or not typst_source.strip():
		frappe.throw(_("Typst source code is required"))
	if "letterhead_image" in kwargs or "logo_image" in kwargs:
		frappe.throw(_("Deprecated params are not supported. Use asset_files only."))
	if kwargs:
		frappe.throw(_("Unsupported compile_typst params: {0}").format(", ".join(sorted(kwargs.keys()))))

	typst_source, literal_asset_files = _normalize_typst_image_literals(typst_source)
	normalized_assets = _normalize_asset_files(asset_files)
	combined_assets = _normalize_asset_files([*normalized_assets, *literal_asset_files])

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
			if combined_assets:
				_copy_asset_files_to_temp(combined_assets, temp_dir)
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
				error_msg = result.stderr or result.stdout or ""
				recovered_any = False
				for missing_name in _extract_missing_image_basenames(error_msg):
					try:
						_copy_file_to_temp(missing_name, temp_dir, "Asset file")
						recovered_any = True
					except Exception:
						# Keep original Typst error context if fallback resolution fails.
						pass

				if recovered_any:
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

	except frappe.ValidationError:
		raise

	except Exception as exc:
		frappe.log_error(message=str(exc), title="Typst Compilation Error")
		frappe.throw(_("Unexpected error during compilation: {0}").format(str(exc)))
