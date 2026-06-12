import base64
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import frappe
from frappe import _

from .security import enforce_rate_limit, ensure_compile_typst_permission

APP_PATH = frappe.get_app_path("crispy_print")
TYPST_FONT_DIR = Path(APP_PATH) / "public" / "vendor" / "typst"
TYPST_PACKAGE_DIR = TYPST_FONT_DIR / "packages"
ZEBRA_VERSION = "0.1.0"
MAX_TYPST_SOURCE_BYTES = 512 * 1024
MAX_CHART_SVG_BYTES = 512 * 1024
MAX_QR_DATA_BYTES = 16 * 1024
MAX_INLINE_DATA_URI_BYTES = 256 * 1024
COMPILE_CACHE_TTL_SECONDS = 5 * 60
PDF_STANDARD_LABELS = {
	"PDF 1.7": "1.7",
	"PDF 2.0": "2.0",
	"PDF/A-2u": "a-2u",
	"PDF/A-3u": "a-3u",
	"PDF/A-4": "a-4",
}
TYPST_PDF_STANDARDS = {
	"1.4",
	"1.5",
	"1.6",
	"1.7",
	"2.0",
	"a-1b",
	"a-1a",
	"a-2b",
	"a-2u",
	"a-2a",
	"a-3b",
	"a-3u",
	"a-3a",
	"a-4",
	"a-4f",
	"a-4e",
	"ua-1",
}
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
QR_ERROR_CORRECTION_MAP = {
	"l": "l",
	"low": "l",
	"m": "m",
	"medium": "m",
	"q": "q",
	"quartile": "q",
	"h": "h",
	"high": "h",
}
BARCODE_SYMBOLOGY_ALIASES = {
	"qr": "QR Code",
	"qrcode": "QR Code",
	"qr code": "QR Code",
	"datamatrix": "DataMatrix",
	"data matrix": "DataMatrix",
	"data_matrix": "DataMatrix",
}


def _utf8_size(value: str | None) -> int:
	return len(str(value or "").encode("utf-8"))


def _throw_if_too_large(value: str | None, label: str, max_bytes: int) -> None:
	if _utf8_size(value) > max_bytes:
		frappe.throw(_("{0} exceeds the maximum size of {1} KB.").format(label, max_bytes // 1024))


def _normalize_barcode_options(value) -> dict:
	if not value:
		return {}
	if isinstance(value, str):
		try:
			value = json.loads(value)
		except json.JSONDecodeError:
			frappe.throw(_("Barcode options must be a JSON object."))
	if not isinstance(value, dict):
		frappe.throw(_("Barcode options must be a JSON object."))

	normalized = {}
	for key, option_value in value.items():
		if option_value in (None, ""):
			continue
		key = str(key).strip()
		if not key:
			continue
		normalized[key] = option_value

	symbology_raw = (
		normalized.get("symbology")
		or normalized.get("code_symbology")
		or normalized.get("code_format")
		or "QR Code"
	)
	symbology = BARCODE_SYMBOLOGY_ALIASES.get(str(symbology_raw).strip().lower(), str(symbology_raw).strip())
	if symbology not in {"QR Code", "DataMatrix"}:
		frappe.throw(_("Unsupported barcode symbology for Typst compile fallback: {0}").format(symbology))
	normalized["symbology"] = symbology

	error_correction = (
		normalized.get("error_correction") or normalized.get("ec_level") or normalized.get("ec-level")
	)
	if error_correction:
		ec = QR_ERROR_CORRECTION_MAP.get(str(error_correction).strip().lower())
		if not ec:
			frappe.throw(_("Unsupported QR error correction level: {0}").format(error_correction))
		normalized["error_correction"] = ec

	for numeric_key in ("quiet_zone", "module_size", "scale", "width", "height"):
		if numeric_key in normalized:
			normalized[numeric_key] = _coerce_barcode_number(normalized[numeric_key], numeric_key)

	return dict(sorted(normalized.items()))


def _coerce_barcode_number(value, key: str) -> float | int:
	try:
		number = float(value)
	except (TypeError, ValueError):
		frappe.throw(_("Barcode option {0} must be numeric.").format(key))
	if number < 0:
		frappe.throw(_("Barcode option {0} cannot be negative.").format(key))
	return int(number) if number.is_integer() else number


def _minimal_subprocess_env(home: str | None = None) -> dict[str, str]:
	env = {
		"PATH": os.environ.get("PATH", ""),
		"LANG": os.environ.get("LANG", "C.UTF-8"),
		"LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
	}
	# HOME is required for Typst to discover OS-level user fonts
	# (e.g. ~/Library/Fonts on macOS, ~/.fonts and ~/.local/share/fonts on Linux).
	# Callers that need an isolated working directory may override HOME by
	# passing it explicitly.
	env["HOME"] = home or os.environ.get("HOME", "")
	# TYPST_FONT_PATHS is the official Typst CLI env var for additional font
	# directories (colon/semicolon-separated). Forward it when present so users
	# can point Typst at extra font locations without modifying app code.
	typst_font_paths = os.environ.get("TYPST_FONT_PATHS")
	if typst_font_paths:
		env["TYPST_FONT_PATHS"] = typst_font_paths
	return env


def _typst_compile_command(
	typst_bin: str,
	output_format: str,
	pdf_standard_cli: str,
	src_path,
	output_template,
) -> list[str]:
	command = [
		typst_bin,
		"compile",
		"--font-path",
		str(TYPST_FONT_DIR),
	]
	if TYPST_PACKAGE_DIR.exists():
		command.extend(["--package-path", str(TYPST_PACKAGE_DIR)])
	command.extend(
		[
			"--format",
			output_format,
			*(["--pdf-standard", pdf_standard_cli] if output_format == "pdf" and pdf_standard_cli else []),
			str(src_path),
			str(output_template),
		]
	)
	return command


def _is_relative_to(path: Path, root: Path) -> bool:
	try:
		path.relative_to(root)
		return True
	except ValueError:
		return False


def _allowed_asset_roots() -> list[Path]:
	site_path = Path(frappe.get_site_path()).resolve()
	return [
		(site_path / "private" / "files").resolve(),
		(site_path / "public" / "files").resolve(),
		TYPST_FONT_DIR.resolve(),
		(Path(APP_PATH) / "public").resolve(),
	]


def _is_allowed_asset_path(path: Path) -> bool:
	resolved = path.resolve()
	return any(_is_relative_to(resolved, root) for root in _allowed_asset_roots())


def _reject_path_traversal(clean_path: str, label: str) -> None:
	parts = Path(clean_path.replace("\\", "/")).parts
	if ".." in parts:
		frappe.throw(_("{0} path traversal is not allowed: {1}").format(label, clean_path))


def _safe_output_filename(output_filename: str | None) -> str:
	if not output_filename:
		return f"crispy_{frappe.generate_hash()}.pdf"
	filename = Path(str(output_filename)).name
	if not filename.lower().endswith(".pdf"):
		filename = f"{filename}.pdf"
	if not filename or filename in {".pdf", "..pdf"}:
		filename = f"crispy_{frappe.generate_hash()}.pdf"
	return filename


def _resolve_pdf_standard_cli(pdf_standard: str | None) -> str:
	standard = str(pdf_standard or "PDF/A-2u").strip() or "PDF/A-2u"
	if standard in PDF_STANDARD_LABELS:
		return PDF_STANDARD_LABELS[standard]

	parts = [part.strip().lower() for part in standard.split(",") if part.strip()]
	if parts and all(part in TYPST_PDF_STANDARDS for part in parts):
		return ",".join(parts)

	allowed = [*PDF_STANDARD_LABELS, *sorted(TYPST_PDF_STANDARDS)]
	if standard not in allowed:
		frappe.throw(
			_("Unsupported PDF standard: {0}. Allowed values: {1}").format(standard, ", ".join(allowed))
		)
	return standard


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

	After installing typst, you can add fonts to typst by setting environment variable TYPST_FONT_PATHS
	in your shell (e.g. in .bashrc or .zshrc):
		export TYPST_FONT_PATHS="/path/to/fonts/directory"
	Or by using the typst CLI:
	    $ typst font add /path/to/font.ttf
	"""
	ensure_compile_typst_permission()
	enforce_rate_limit("typst_fonts", limit=20, window_seconds=60)

	cache_key = "crispy_print:typst_local_fonts:v1"
	cached_fonts = frappe.cache().get_value(cache_key, expires=True)
	if isinstance(cached_fonts, list):
		return cached_fonts

	typst_bin = frappe.conf.get("TYPST_BIN", "typst")

	try:
		result = subprocess.run(
			[typst_bin, "fonts"],
			capture_output=True,
			text=True,
			check=True,
			timeout=5,
			env=_minimal_subprocess_env(),
			start_new_session=True,
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
	fonts = sorted(list(set(fonts)))
	frappe.cache().set_value(cache_key, fonts, expires_in_sec=5 * 60)
	return fonts


def _resolve_source_path(file_path: str, label: str) -> Path:
	"""Resolve a source file path for Typst asset copying."""
	clean_path = _strip_url_suffix(file_path)
	_reject_path_traversal(clean_path, label)

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

		if source_path.is_symlink():
			frappe.throw(_("{0} cannot be a symlink: {1}").format(label, file_path))
		resolved = source_path.resolve()
		if resolved.exists() and resolved.is_file() and _is_allowed_asset_path(resolved):
			return resolved
		frappe.throw(_("{0} not found: {1}").format(label, file_path))

	# Handle explicit filesystem paths only after Frappe URL-style file paths.
	path_obj = Path(clean_path)
	if path_obj.is_absolute():
		if path_obj.is_symlink():
			frappe.throw(_("{0} cannot be a symlink: {1}").format(label, file_path))
		resolved = path_obj.resolve()
		if resolved.exists() and resolved.is_file() and _is_allowed_asset_path(resolved):
			return resolved
		frappe.throw(_("{0} not found: {1}").format(label, file_path))

	if "/" not in clean_path and "\\" not in clean_path:
		frappe.throw(
			_("{0} must use an explicit /files/ or /private/files/ path: {1}").format(label, file_path)
		)

	# Fallback for relative paths with directories
	source_path = site_path / clean_path.lstrip("/")
	if source_path.is_symlink():
		frappe.throw(_("{0} cannot be a symlink: {1}").format(label, file_path))
	resolved = source_path.resolve()
	if resolved.exists() and resolved.is_file() and _is_allowed_asset_path(resolved):
		return resolved

	frappe.throw(_("{0} not found: {1}").format(label, file_path))


def _copy_resolved_source_to_temp(source_path: Path, temp_dir: str, label: str) -> str:
	try:
		fd = os.open(source_path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
	except OSError as exc:
		frappe.throw(_("{0} could not be opened safely: {1}").format(label, exc))

	try:
		file_stat = os.fstat(fd)
		if not stat.S_ISREG(file_stat.st_mode):
			frappe.throw(_("{0} must be a regular file: {1}").format(label, source_path))
		dest_filename = source_path.name
		dest_path = Path(temp_dir) / dest_filename
		dest_path.parent.mkdir(parents=True, exist_ok=True)
		with os.fdopen(fd, "rb", closefd=False) as src_handle, dest_path.open("wb") as dest_handle:
			while True:
				chunk = src_handle.read(64 * 1024)
				if not chunk:
					break
				dest_handle.write(chunk)
		return dest_filename
	finally:
		os.close(fd)


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
	return _copy_resolved_source_to_temp(source_path, temp_dir, label)


def _build_asset_source_index(asset_files: list[str]) -> dict[str, str]:
	index: dict[str, str] = {}
	duplicates: dict[str, list[str]] = {}
	for raw in asset_files:
		basename = Path(_strip_url_suffix(raw)).name
		if not basename:
			continue
		if basename in index and index[basename] != raw:
			duplicates.setdefault(basename, [index[basename]])
			duplicates[basename].append(raw)
			continue
		index[basename] = raw
	if duplicates:
		lines = [f"{basename}: {', '.join(paths)}" for basename, paths in sorted(duplicates.items())]
		frappe.throw(
			_("Asset filenames must be unique within a compile request:\n{0}").format("\n".join(lines))
		)
	return index


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
		return {}
	asset_index = _build_asset_source_index(normalized_assets)

	errors: list[str] = []
	for asset in normalized_assets:
		try:
			_copy_file_to_temp(asset, temp_dir, "Asset file")
		except Exception as exc:
			errors.append(f"{asset}: {exc}")

	if errors:
		frappe.throw(_("Asset file resolution failed:\n{0}").format("\n".join(errors)))
	return asset_index


def _asset_signature(asset_files: list[str]) -> list[dict[str, str | int]]:
	signature: list[dict[str, str | int]] = []
	errors: list[str] = []
	for asset in asset_files:
		try:
			source_path = _resolve_source_path(asset, "Asset file")
			file_stat = source_path.stat()
			signature.append(
				{
					"asset": asset,
					"path": str(source_path),
					"size": int(file_stat.st_size),
					"mtime_ns": int(file_stat.st_mtime_ns),
				}
			)
		except Exception as exc:
			errors.append(f"{asset}: {exc}")
	if errors:
		frappe.throw(_("Asset file resolution failed:\n{0}").format("\n".join(errors)))
	return signature


def _compile_cache_key(
	*,
	typst_source: str,
	output_format: str,
	pdf_standard: str,
	asset_files: list[str],
	chart_svg: str | None,
	qr_data: str | None,
	qr_filename: str | None,
	barcode_options: dict | None,
	typst_bin: str,
) -> str:
	payload = {
		"typst_source": typst_source,
		"output_format": output_format,
		"pdf_standard": pdf_standard,
		"assets": _asset_signature(asset_files),
		"chart_svg": chart_svg or "",
		"qr_data": qr_data or "",
		"qr_filename": qr_filename or "",
		"barcode_options": barcode_options or {},
		"typst_bin": typst_bin,
		"font_dir": str(TYPST_FONT_DIR),
		"package_dir": str(TYPST_PACKAGE_DIR) if TYPST_PACKAGE_DIR.exists() else "",
	}
	raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
	return f"crispy_print:compile_typst:v2:{hashlib.sha256(raw).hexdigest()}"


def _write_qr_svg(qr_data, qr_filename, temp_dir, barcode_options: dict | None = None):
	"""
	Generate a QR code SVG in the temp directory.

	Args:
	    qr_data (str): Payload to encode.
	    qr_filename (str): Target filename (e.g. "DOC-0001-qr.svg").
	    temp_dir (str): Temporary directory path.
	"""
	if not qr_data or not qr_filename:
		return None

	barcode_options = _normalize_barcode_options(barcode_options)
	if barcode_options.get("symbology") == "DataMatrix":
		frappe.throw(_("Python barcode fallback only supports QR Code. DataMatrix requires Zebra."))

	try:
		import segno
	except Exception as e:
		frappe.log_error(f"Segno not available: {e}", "QR Code Error")
		frappe.throw(_("QR SVG generation requires the segno Python package."))

	filename = Path(qr_filename).name
	if not filename.lower().endswith(".svg"):
		filename = f"{filename}.svg"

	dest_path = Path(temp_dir) / filename

	try:
		error_correction = barcode_options.get("error_correction") or "m"
		scale = barcode_options.get("module_size") or barcode_options.get("scale") or 4
		quiet_zone = barcode_options.get("quiet_zone")
		if quiet_zone is None:
			quiet_zone = 1
		qr = segno.make(str(qr_data), error=str(error_correction))
		qr.save(str(dest_path), kind="svg", scale=scale, border=int(quiet_zone))
		return filename
	except Exception as e:
		frappe.log_error(f"Failed to generate QR SVG: {e}", "QR Code Error")
		frappe.throw(_("Failed to generate QR SVG: {0}").format(e))


def _write_chart_svg(chart_svg: str, temp_dir: str, filename: str = "report_chart.svg"):
	"""Write report chart SVG to temp directory for Typst image() usage."""
	if not chart_svg:
		return
	# Extract the first <svg>...</svg> block to avoid HTML wrappers.
	from xml.etree import ElementTree as ET

	match = re.search(r"<svg\b[^>]*>.*?</svg>", chart_svg, re.DOTALL | re.IGNORECASE)
	svg = (match.group(0) if match else chart_svg).strip()

	# Ensure SVG has the XML namespace (Typst requires a proper root node).
	if "<svg" in svg and "xmlns=" not in svg:
		svg = re.sub(
			r"<svg\b",
			'<svg xmlns="http://www.w3.org/2000/svg"',
			svg,
			count=1,
			flags=re.IGNORECASE,
		)

	# Add xlink namespace if needed
	if "xlink:" in svg and "xmlns:xlink=" not in svg:
		svg = re.sub(
			r"<svg\b",
			'<svg xmlns:xlink="http://www.w3.org/1999/xlink"',
			svg,
			count=1,
			flags=re.IGNORECASE,
		)

	# Escape stray & that can break XML parsing.
	svg = re.sub(r"&(?!(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);)", "&amp;", svg)

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
	pdf_standard: str | None = None,
	asset_files=None,
	chart_svg=None,
	qr_data=None,
	qr_filename=None,
	barcode_options=None,
	output_filename: str | None = None,
	return_url: int | bool = 0,
	**kwargs,
):
	"""
	Compile Typst source code using the local Typst CLI.

	Args:
	    typst_source (str): The Typst source code to compile.
	    output_format (str): Desired output format ("pdf" or "svg").
	    pdf_standard (str): PDF output standard label or Typst standard value.
	    asset_files (list[str]): Optional image asset paths/filenames to resolve.
	    output_filename (str): Optional output filename for PDF when return_url is enabled.
	    return_url (bool): When true and output_format="pdf", write to public files and return URL.

	Returns:
	    dict: Response with compiled artifact or error.
	"""
	ensure_compile_typst_permission()
	enforce_rate_limit(
		"compile_typst",
		limit=60,
		window_seconds=60,
		error_message=_("Too many Typst compile requests. Please wait a moment and try again."),
	)

	if not typst_source or not typst_source.strip():
		frappe.throw(_("Typst source code is required"))
	_throw_if_too_large(typst_source, _("Typst source"), MAX_TYPST_SOURCE_BYTES)
	_throw_if_too_large(chart_svg, _("Chart SVG"), MAX_CHART_SVG_BYTES)
	_throw_if_too_large(qr_data, _("QR data"), MAX_QR_DATA_BYTES)
	if "letterhead_image" in kwargs or "logo_image" in kwargs:
		frappe.throw(_("Deprecated params are not supported. Use asset_files only."))
	if kwargs:
		frappe.throw(_("Unsupported compile_typst params: {0}").format(", ".join(sorted(kwargs.keys()))))

	typst_source, literal_asset_files = _normalize_typst_image_literals(typst_source)
	normalized_assets = _normalize_asset_files(asset_files)
	combined_assets = _normalize_asset_files([*normalized_assets, *literal_asset_files])
	normalized_barcode_options = _normalize_barcode_options(barcode_options)
	uses_zebra_barcode = (
		"@local/crispy-print" in typst_source
		or "crispy-qrcode" in typst_source
		or "crispy-datamatrix" in typst_source
	)

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
	pdf_standard_cli = _resolve_pdf_standard_cli(pdf_standard) if output_format == "pdf" else ""

	typst_bin = frappe.conf.get("TYPST_BIN", "typst")
	cache_ttl = int(frappe.conf.get("CRISPY_PRINT_COMPILE_CACHE_TTL_SECONDS", COMPILE_CACHE_TTL_SECONDS) or 0)
	cache_key = None
	if cache_ttl > 0 and not return_url:
		try:
			cache_key = _compile_cache_key(
				typst_source=typst_source,
				output_format=output_format,
				pdf_standard=pdf_standard_cli,
				asset_files=combined_assets,
				chart_svg=chart_svg,
				qr_data=qr_data,
				qr_filename=qr_filename,
				barcode_options=normalized_barcode_options,
				typst_bin=typst_bin,
			)
		except Exception:
			cache_key = None
		if cache_key:
			cached_result = frappe.cache().get_value(cache_key, expires=True)
			if isinstance(cached_result, dict):
				return cached_result

	try:
		with TemporaryDirectory() as temp_dir:
			asset_index: dict[str, str] = {}
			if combined_assets:
				asset_index = _copy_asset_files_to_temp(combined_assets, temp_dir)
			if chart_svg:
				_write_chart_svg(chart_svg, temp_dir)
			if (
				qr_data
				and qr_filename
				and not uses_zebra_barcode
				and normalized_barcode_options.get("symbology", "QR Code") != "DataMatrix"
			):
				_write_qr_svg(qr_data, qr_filename, temp_dir, normalized_barcode_options)

			# Write Typst source to temp file
			src_path = Path(temp_dir) / "document.typ"
			src_path.write_text(typst_source, encoding="utf-8")

			src_path_obj = Path(src_path)
			if output_format == "pdf":
				if return_url:
					output_filename = _safe_output_filename(output_filename)
					output_template = Path(frappe.get_site_path("public", "files")) / output_filename
				else:
					output_template = src_path_obj.with_suffix(".pdf")
			else:
				# Include page placeholder so Typst emits page-numbered SVGs (e.g. foo-1.svg, foo-2.svg ...)
				output_template = src_path_obj.with_name(f"{src_path_obj.stem}-{{p}}.svg")

			result = subprocess.run(
				_typst_compile_command(
					typst_bin,
					output_format,
					pdf_standard_cli,
					src_path,
					output_template,
				),
				capture_output=True,
				text=True,
				timeout=30,
				env=_minimal_subprocess_env(),
				cwd=temp_dir,
				start_new_session=True,
			)

			if result.returncode != 0:
				error_msg = result.stderr or result.stdout or ""
				recovered_any = False
				for missing_name in _extract_missing_image_basenames(error_msg):
					approved_source = asset_index.get(missing_name)
					if not approved_source:
						continue
					try:
						_copy_file_to_temp(approved_source, temp_dir, "Asset file")
						recovered_any = True
					except Exception:
						# Keep original Typst error context if fallback resolution fails.
						pass

				if recovered_any:
					result = subprocess.run(
						_typst_compile_command(
							typst_bin,
							output_format,
							pdf_standard_cli,
							src_path,
							output_template,
						),
						capture_output=True,
						text=True,
						timeout=30,
						env=_minimal_subprocess_env(),
						cwd=temp_dir,
						start_new_session=True,
					)

			if result.returncode != 0:
				error_msg = result.stderr or result.stdout or "Unknown compilation error"
				frappe.log_error(
					message=f"Typst CLI error:\n{error_msg}\n\nSource:\n{typst_source[:500]}",
					title="Typst Compilation Error",
				)
				frappe.throw(_("Typst compilation failed. Check the server error log for details."))

			if output_format == "pdf":
				output_path = Path(output_template)
				if not output_path.exists():
					frappe.throw(_("Compiled PDF was not produced"))

				if return_url:
					return {"success": True, "format": "pdf", "pdf_url": f"/files/{output_path.name}"}

				with output_path.open("rb") as pdf_file:
					pdf_bytes = pdf_file.read()

				pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
				result_payload = {"success": True, "format": "pdf", "pdf_data": pdf_base64}
				if cache_key:
					frappe.cache().set_value(cache_key, result_payload, expires_in_sec=cache_ttl)
				return result_payload

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

			result_payload = {
				"success": True,
				"format": "svg",
				"svg_pages": svg_pages,
				"page_count": len(svg_pages),
			}
			if cache_key:
				frappe.cache().set_value(cache_key, result_payload, expires_in_sec=cache_ttl)
			return result_payload

	except FileNotFoundError:
		frappe.throw(_("Typst compiler not found. Please install Typst CLI: brew install typst"))

	except subprocess.TimeoutExpired:
		frappe.throw(_("Compilation timed out. The document may be too complex."))

	except frappe.ValidationError:
		raise

	except Exception:
		frappe.log_error(message=frappe.get_traceback(), title="Typst Compilation Error")
		frappe.throw(_("Unexpected error during compilation. Check the server error log for details."))
