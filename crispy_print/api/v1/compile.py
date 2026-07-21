import base64
import hashlib
import json
import os
import re
import stat
import subprocess
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import frappe
from frappe import _

from crispy_print.crispy_print.doctype.crispy_print_settings.crispy_print_settings import (
	get_render_timeout_seconds,
	get_typst_font_dirs,
	should_ignore_system_fonts,
)

from .security import enforce_rate_limit, ensure_compile_typst_permission

APP_PATH = frappe.get_app_path("crispy_print")
TYPST_VENDOR_DIR = Path(APP_PATH) / "public" / "vendor"
TYPST_FONT_DIR = TYPST_VENDOR_DIR / "fonts"
TYPST_PACKAGE_DIR = TYPST_VENDOR_DIR / "typst" / "packages"
ZEBRA_VERSION = "0.1.0"
MIN_TYPST_VERSION = (0, 15, 0)
MIN_TYPST_VERSION_LABEL = ".".join(str(part) for part in MIN_TYPST_VERSION)
MAX_TYPST_SOURCE_BYTES = 512 * 1024
MAX_CHART_SVG_BYTES = 512 * 1024
MAX_CHART_SVG_ELEMENTS = 5_000
MAX_CHART_SVG_PATH_BYTES = 256 * 1024
MAX_QR_DATA_BYTES = 16 * 1024
MAX_INLINE_DATA_URI_BYTES = 256 * 1024
COMPILE_CACHE_TTL_SECONDS = 5 * 60
TYPST_VERSION_CACHE_TTL_SECONDS = 5 * 60
FONT_WEIGHT_ORDER = {
	"thin": 100,
	"extralight": 200,
	"light": 300,
	"regular": 400,
	"medium": 500,
	"semibold": 600,
	"bold": 700,
	"extrabold": 800,
	"black": 900,
}
FONT_STYLE_ORDER = {"normal": 0, "italic": 1, "oblique": 2}
FONT_WEIGHT_ALIASES = {
	"hairline": "thin",
	"thin": "thin",
	"extralight": "extralight",
	"extra light": "extralight",
	"ultralight": "extralight",
	"ultra light": "extralight",
	"light": "light",
	"book": "regular",
	"normal": "regular",
	"regular": "regular",
	"roman": "regular",
	"medium": "medium",
	"semibold": "semibold",
	"semi bold": "semibold",
	"demibold": "semibold",
	"demi bold": "semibold",
	"bold": "bold",
	"extrabold": "extrabold",
	"extra bold": "extrabold",
	"ultrabold": "extrabold",
	"ultra bold": "extrabold",
	"black": "black",
	"heavy": "black",
}
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
_CRISPY_IMAGE_LITERAL_RE = re.compile(r'crispy_image\(\s*"([^"\n]+)"')
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

_SVG_NAMESPACE = "http://www.w3.org/2000/svg"
_XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
_ALLOWED_SVG_ELEMENTS = {
	"svg",
	"g",
	"defs",
	"clipPath",
	"mask",
	"linearGradient",
	"radialGradient",
	"stop",
	"path",
	"line",
	"rect",
	"circle",
	"ellipse",
	"polyline",
	"polygon",
	"text",
	"tspan",
}
_ALLOWED_SVG_ATTRIBUTES = {
	"xmlns",
	"viewBox",
	"width",
	"height",
	"preserveAspectRatio",
	"fill",
	"fill-opacity",
	"stroke",
	"stroke-width",
	"stroke-opacity",
	"stroke-dasharray",
	"stroke-linecap",
	"stroke-linejoin",
	"opacity",
	"transform",
	"d",
	"x",
	"y",
	"x1",
	"y1",
	"x2",
	"y2",
	"cx",
	"cy",
	"r",
	"rx",
	"ry",
	"points",
	"dx",
	"dy",
	"text-anchor",
	"font-family",
	"font-size",
	"font-style",
	"font-weight",
	"dominant-baseline",
	"alignment-baseline",
	"class",
	"id",
	"clip-path",
	"mask",
	"offset",
	"stop-color",
	"stop-opacity",
	"gradientUnits",
	"gradientTransform",
	"spreadMethod",
	"href",
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


def _minimal_subprocess_env(
	home: str | None = None, include_system_fonts: bool | None = None
) -> dict[str, str]:
	env = {
		"PATH": os.environ.get("PATH", ""),
		"LANG": os.environ.get("LANG", "C.UTF-8"),
		"LC_ALL": os.environ.get("LC_ALL", "C.UTF-8"),
	}
	# HOME is required for Typst to discover OS-level user fonts
	# (e.g. ~/Library/Fonts on macOS, ~/.fonts and ~/.local/share/fonts on Linux).
	# Callers that need an isolated working directory may override HOME by
	# passing it explicitly.
	if include_system_fonts is None:
		include_system_fonts = not should_ignore_system_fonts()
	env["HOME"] = home or (os.environ.get("HOME", "") if include_system_fonts else "")
	# TYPST_FONT_PATHS is the official Typst CLI env var for additional font
	# directories (colon/semicolon-separated). Forward it when present so users
	# can point Typst at extra font locations without modifying app code.
	typst_font_paths = os.environ.get("TYPST_FONT_PATHS")
	if typst_font_paths:
		env["TYPST_FONT_PATHS"] = typst_font_paths
	return env


def _typst_font_dirs() -> list[Path]:
	return get_typst_font_dirs(existing_only=True)


def _site_font_dir() -> Path:
	for font_dir in get_typst_font_dirs(existing_only=False):
		if font_dir.name == "fonts" and "private" in font_dir.parts:
			return font_dir
	return Path(frappe.get_site_path("private", "files", "crispy_print", "fonts"))


def _typst_font_path_arg() -> str:
	return os.pathsep.join(str(font_dir) for font_dir in _typst_font_dirs())


def _parse_typst_version(output: str) -> tuple[int, int, int] | None:
	match = re.search(r"\btypst\s+(\d+)\.(\d+)\.(\d+)", output or "", re.IGNORECASE)
	if not match:
		return None
	return tuple(int(part) for part in match.groups())


def _typst_version_cache_key(typst_bin: str) -> str:
	digest = hashlib.sha256(str(typst_bin or "typst").encode("utf-8")).hexdigest()
	return f"crispy_print:typst_version:{digest}"


def _ensure_typst_minimum_version(typst_bin: str) -> str:
	cache_key = _typst_version_cache_key(typst_bin)
	cached_output = frappe.cache().get_value(cache_key, expires=True)
	if isinstance(cached_output, str) and cached_output:
		return cached_output

	result = subprocess.run(
		[typst_bin, "--version"],
		capture_output=True,
		text=True,
		timeout=5,
		env=_minimal_subprocess_env(),
	)
	output = (result.stdout or result.stderr or "").strip()
	version = _parse_typst_version(output)
	if result.returncode != 0 or version is None:
		frappe.throw(
			_("Unable to determine Typst CLI version. Crispy Print requires Typst {0} or newer.").format(
				MIN_TYPST_VERSION_LABEL
			)
		)
	if version < MIN_TYPST_VERSION:
		frappe.throw(
			_("Typst CLI {0} or newer is required. Found: {1}").format(MIN_TYPST_VERSION_LABEL, output)
		)
	output = str(output)
	cache_ttl = int(
		frappe.conf.get("CRISPY_PRINT_TYPST_VERSION_CACHE_TTL_SECONDS", TYPST_VERSION_CACHE_TTL_SECONDS) or 0
	)
	if cache_ttl > 0:
		frappe.cache().set_value(cache_key, output, expires_in_sec=cache_ttl)
	return output


def get_cached_typst_version(typst_bin: str | None = None) -> str:
	return _ensure_typst_minimum_version(typst_bin or frappe.conf.get("TYPST_BIN", "typst"))


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
	]
	font_path = _typst_font_path_arg()
	if font_path:
		command.extend(["--font-path", font_path])
	if should_ignore_system_fonts():
		command.append("--ignore-system-fonts")
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


def _current_site_name() -> str:
	return str(getattr(frappe.local, "site", "") or "").strip()


def _private_asset_url(filename: str) -> str:
	return f"/assets/{_current_site_name()}/private/files/{filename}"


def _validate_crispy_private_image_filename(filename: str, label: str = "Crispy image") -> str:
	raw = str(filename or "").strip()
	if not raw:
		frappe.throw(_("{0} filename is required.").format(label))
	if "/" in raw or "\\" in raw or raw != Path(raw).name:
		frappe.throw(_("{0} must be a filename only: {1}").format(label, raw))
	if ".." in Path(raw).parts or ".." in raw:
		frappe.throw(_("{0} path traversal is not allowed: {1}").format(label, raw))
	if _is_external_asset_path(raw) or Path(raw).is_absolute():
		frappe.throw(_("{0} must be a private file filename only: {1}").format(label, raw))
	if not _is_image_asset_value(raw):
		frappe.throw(_("{0} has an unsupported image extension: {1}").format(label, raw))
	return raw


def _resolve_private_asset_filename(filename: str, label: str) -> Path:
	clean_filename = _validate_crispy_private_image_filename(filename, label)
	source_path = Path(frappe.get_site_path("private", "files", clean_filename))
	if source_path.is_symlink():
		frappe.throw(_("{0} cannot be a symlink: {1}").format(label, clean_filename))
	resolved = source_path.resolve()
	allowed_root = Path(frappe.get_site_path("private", "files")).resolve()
	if not _is_relative_to(resolved, allowed_root) or not resolved.exists() or not resolved.is_file():
		frappe.throw(_("{0} not found: {1}").format(label, clean_filename))
	return resolved


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


def _extract_crispy_image_assets(typst_source: str) -> list[str]:
	assets: list[str] = []
	seen: set[str] = set()
	for match in _CRISPY_IMAGE_LITERAL_RE.finditer(typst_source or ""):
		filename = _validate_crispy_private_image_filename(match.group(1), "Crispy image")
		asset = _private_asset_url(filename)
		if asset in seen:
			continue
		seen.add(asset)
		assets.append(asset)
	return assets


def _ensure_crispy_image_helper(typst_source: str) -> str:
	if "crispy_image(" not in (typst_source or ""):
		return typst_source
	if "#let crispy_image" in typst_source:
		return typst_source
	return "#let crispy_image(filename, ..args) = image(filename, ..args)\n\n" + typst_source


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


def _normalize_font_style(value: str) -> str:
	normalized = value.strip().lower()
	if "oblique" in normalized:
		return "oblique"
	if "italic" in normalized:
		return "italic"
	return "normal"


def _normalize_font_weight(value: str) -> str:
	normalized = re.sub(r"[_-]+", " ", value.strip().lower())
	normalized = re.sub(r"\s+", " ", normalized)
	candidates = [
		normalized.replace(" italic", "").replace(" oblique", "").strip(),
		normalized,
	]
	for candidate in candidates:
		if candidate in FONT_WEIGHT_ALIASES:
			return FONT_WEIGHT_ALIASES[candidate]
	for name in sorted(FONT_WEIGHT_ALIASES, key=len, reverse=True):
		if re.search(rf"\b{re.escape(name)}\b", normalized):
			return FONT_WEIGHT_ALIASES[name]
	return "regular"


def _font_face_from_label(label: str) -> dict[str, str]:
	clean_label = label.strip() or "Regular"
	return {
		"label": clean_label,
		"style": _normalize_font_style(clean_label),
		"weight": _normalize_font_weight(clean_label),
	}


def _font_family_key(family: str) -> str:
	return re.sub(r"[^a-z0-9]+", "", family.strip().lower())


def _resolve_font_family_name(existing_families: list[str], family: str) -> str:
	clean_family = family.strip()
	if not clean_family:
		return ""
	key = _font_family_key(clean_family)
	for existing in existing_families:
		if _font_family_key(existing) == key:
			return existing
	return clean_family


def _add_font_family_name(families: dict[str, str], family: str) -> None:
	clean_family = family.strip()
	if not clean_family:
		return
	key = _font_family_key(clean_family)
	if key not in families:
		families[key] = clean_family


def _font_family_from_filename(font_path: Path) -> str:
	font_name = font_path.stem
	for suffix in [
		"-ExtraBoldItalic",
		"ExtraBoldItalic",
		"-SemiBoldItalic",
		"SemiBoldItalic",
		"-BoldItalic",
		"BoldItalic",
		"-ExtraLightItalic",
		"ExtraLightItalic",
		"-LightItalic",
		"LightItalic",
		"-MediumItalic",
		"MediumItalic",
		"-BlackItalic",
		"BlackItalic",
		"-RegularItalic",
		"RegularItalic",
		"-Italic",
		"Italic",
		"-ExtraBold",
		"ExtraBold",
		"-SemiBold",
		"SemiBold",
		"-ExtraLight",
		"ExtraLight",
		"-Regular",
		"Regular",
		"-Medium",
		"Medium",
		"-Light",
		"Light",
		"-Black",
		"Black",
		"-Bold",
		"Bold",
	]:
		if font_name.endswith(suffix) and len(font_name) > len(suffix):
			return font_name[: -len(suffix)]
	return font_name


def _font_face_label_from_filename(font_path: Path) -> str:
	family = _font_family_from_filename(font_path)
	label = font_path.stem[len(family) :].lstrip("-_ ")
	return label or "Regular"


def _variable_font_faces(font_path: Path) -> list[dict[str, str]]:
	try:
		from fontTools.ttLib import TTFont

		font = TTFont(font_path, lazy=True)
		try:
			if "fvar" not in font:
				return []
			weight_axis = next(
				(axis for axis in font["fvar"].axes if axis.axisTag == "wght"),
				None,
			)
			if not weight_axis:
				return []
			minimum = float(weight_axis.minValue)
			maximum = float(weight_axis.maxValue)
		finally:
			font.close()
	except Exception:
		return []

	style = _normalize_font_style(_font_face_label_from_filename(font_path))
	faces = []
	for weight, numeric_weight in FONT_WEIGHT_ORDER.items():
		if minimum <= numeric_weight <= maximum:
			label = weight.capitalize()
			if style != "normal":
				label = f"{label} {style.capitalize()}"
			faces.append({"label": label, "style": style, "weight": weight})
	return faces


def _ttc_font_faces(font_path: Path) -> list[tuple[str, dict[str, str]]]:
	if font_path.suffix.lower() != ".ttc":
		return []

	try:
		from fontTools.ttLib import TTCollection

		collection = TTCollection(font_path, lazy=True)
	except Exception:
		return []

	faces = []
	try:
		for font in collection.fonts:
			name_table = font.get("name")
			family = ""
			subfamily = ""
			if name_table:
				family = name_table.getDebugName(16) or name_table.getDebugName(1) or ""
				subfamily = name_table.getDebugName(17) or name_table.getDebugName(2) or ""
			if not family:
				continue

			weight_number = int(getattr(font.get("OS/2"), "usWeightClass", 400))
			weight = min(FONT_WEIGHT_ORDER, key=lambda name: abs(FONT_WEIGHT_ORDER[name] - weight_number))
			style = _normalize_font_style(subfamily)
			if style == "normal" and int(getattr(font.get("head"), "macStyle", 0)) & 0b10:
				style = "italic"
			label = subfamily.strip() or weight.capitalize()
			faces.append((family, {"label": label, "style": style, "weight": weight}))
	finally:
		collection.close()

	return faces


def _empty_font_family_faces(family: str) -> dict[str, object]:
	return {"family": family, "faces": [], "styles": [], "weights": []}


def _add_font_face(families: dict[str, dict[str, object]], family: str, face: dict[str, str]) -> None:
	clean_family = _resolve_font_family_name(list(families), family)
	if not clean_family:
		return
	record = families.setdefault(clean_family, _empty_font_family_faces(clean_family))
	faces = record["faces"]
	if not isinstance(faces, list):
		return
	key = (face["style"], face["weight"])
	if any((existing.get("style"), existing.get("weight")) == key for existing in faces):
		return
	faces.append(face)


def _parse_typst_font_faces(stdout: str) -> list[dict[str, object]]:
	families: dict[str, dict[str, object]] = {}
	for raw_line in stdout.splitlines():
		line = raw_line.strip()
		if not line:
			continue
		if "(" in line and line.endswith(")"):
			family, face_list = line.split("(", 1)
			for face_label in face_list[:-1].split(","):
				_add_font_face(families, family, _font_face_from_label(face_label))
		else:
			_add_font_face(families, line, _font_face_from_label("Regular"))
	return _finalize_font_faces(families)


def _finalize_font_faces(families: dict[str, dict[str, object]]) -> list[dict[str, object]]:
	result = []
	for family in sorted(families):
		record = families[family]
		faces = record["faces"]
		if not isinstance(faces, list):
			continue
		faces.sort(
			key=lambda face: (
				FONT_WEIGHT_ORDER.get(str(face.get("weight", "")), 400),
				str(face.get("style", "")),
				str(face.get("label", "")),
			)
		)
		styles = sorted(
			{str(face.get("style")) for face in faces if face.get("style")},
			key=lambda style: FONT_STYLE_ORDER.get(style, 99),
		)
		weights = sorted(
			{str(face.get("weight")) for face in faces if face.get("weight")},
			key=lambda weight: FONT_WEIGHT_ORDER.get(weight, 400),
		)
		result.append({"family": family, "faces": faces, "styles": styles, "weights": weights})
	return result


def _add_font_file_faces(families: dict[str, dict[str, object]]) -> None:
	for font_dir in _typst_font_dirs():
		for font_file in [
			*font_dir.rglob("*.ttf"),
			*font_dir.rglob("*.otf"),
			*font_dir.rglob("*.ttc"),
			*font_dir.rglob("*.woff"),
			*font_dir.rglob("*.woff2"),
		]:
			collection_faces = _ttc_font_faces(font_file)
			if collection_faces:
				for family, face in collection_faces:
					_add_font_face(families, family, face)
				continue
			family = _font_family_from_filename(font_file)
			variable_faces = _variable_font_faces(font_file)
			if variable_faces:
				for face in variable_faces:
					_add_font_face(families, family, face)
			else:
				_add_font_face(
					families,
					family,
					_font_face_from_label(_font_face_label_from_filename(font_file)),
				)


def get_typst_font_faces() -> list[dict[str, object]]:
	"""Returns Typst font families with the styles and weights Typst can resolve."""
	ensure_compile_typst_permission()
	enforce_rate_limit("typst_font_faces", limit=20, window_seconds=60)

	cache_key = "crispy_print:typst_font_faces:v4"
	cached_faces = frappe.cache().get_value(cache_key, expires=True)
	if isinstance(cached_faces, list):
		return cached_faces

	typst_bin = frappe.conf.get("TYPST_BIN", "typst")
	try:
		font_path = _typst_font_path_arg()
		command = [typst_bin, "fonts"]
		if font_path:
			command.extend(["--font-path", font_path])
		if should_ignore_system_fonts():
			command.append("--ignore-system-fonts")
		result = subprocess.run(
			command,
			capture_output=True,
			text=True,
			check=True,
			timeout=get_render_timeout_seconds(),
			env=_minimal_subprocess_env(),
			start_new_session=True,
		)
	except Exception as e:
		frappe.throw(f"Error running typst fonts: {e}")

	families: dict[str, dict[str, object]] = {}
	for record in _parse_typst_font_faces(result.stdout):
		family = str(record.get("family") or "")
		for face in record.get("faces") or []:
			if isinstance(face, dict):
				_add_font_face(families, family, face)
	_add_font_file_faces(families)
	font_faces = _finalize_font_faces(families)
	frappe.cache().set_value(cache_key, font_faces, expires_in_sec=5 * 60)
	return font_faces


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

	cache_key = "crispy_print:typst_local_fonts:v4"
	cached_fonts = frappe.cache().get_value(cache_key, expires=True)
	if isinstance(cached_fonts, list):
		return cached_fonts

	typst_bin = frappe.conf.get("TYPST_BIN", "typst")

	try:
		font_path = _typst_font_path_arg()
		command = [typst_bin, "fonts"]
		if font_path:
			command.extend(["--font-path", font_path])
		if should_ignore_system_fonts():
			command.append("--ignore-system-fonts")
		result = subprocess.run(
			command,
			capture_output=True,
			text=True,
			check=True,
			timeout=get_render_timeout_seconds(),
			env=_minimal_subprocess_env(),
			start_new_session=True,
		)
	except Exception as e:
		frappe.throw(f"Error running typst fonts: {e}")

	fonts: dict[str, str] = {}
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

		_add_font_family_name(fonts, family)

	# Add app-bundled and site-private fonts by filename as a fallback.
	for font_dir in _typst_font_dirs():
		for font_file in [
			*font_dir.rglob("*.ttf"),
			*font_dir.rglob("*.otf"),
			*font_dir.rglob("*.ttc"),
			*font_dir.rglob("*.woff"),
			*font_dir.rglob("*.woff2"),
		]:
			fallback_family = _font_family_from_filename(font_file)
			canonical_family = _resolve_font_family_name(list(fonts.values()), fallback_family)
			_add_font_family_name(fonts, canonical_family)

	# Deduplicate and sort
	font_list = sorted(fonts.values())
	frappe.cache().set_value(cache_key, font_list, expires_in_sec=5 * 60)
	return font_list


def _resolve_source_path(file_path: str, label: str) -> Path:
	"""Resolve a source file path for Typst asset copying."""
	clean_path = _strip_url_suffix(file_path)
	_reject_path_traversal(clean_path, label)

	site_path = Path(frappe.get_site_path())
	site_name = _current_site_name()
	private_asset_prefix = f"/assets/{site_name}/private/files/"
	if site_name and clean_path.startswith(private_asset_prefix):
		filename = clean_path[len(private_asset_prefix) :]
		return _resolve_private_asset_filename(filename, label)

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


def _normalize_trusted_data_files(data_files) -> dict[str, str]:
	"""Validate server-generated compile inputs that are never exposed by the RPC facade."""
	if data_files is None:
		return {}
	if not isinstance(data_files, dict):
		frappe.throw(_("Generated data files must be a dictionary."))

	normalized: dict[str, str] = {}
	for raw_name, content in data_files.items():
		name = str(raw_name or "").strip()
		if not name or Path(name).name != name or Path(name).suffix.lower() not in {".json", ".csv"}:
			frappe.throw(_("Invalid generated data filename: {0}").format(name or "(empty)"))
		if not isinstance(content, str):
			frappe.throw(_("Generated data file {0} must contain text.").format(name))
		normalized[name] = content
	return normalized


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
	generated_data_files: dict[str, str] | None = None,
) -> str:
	payload = {
		"typst_source": typst_source,
		"output_format": output_format,
		"pdf_standard": pdf_standard,
		"assets": _asset_signature(asset_files),
		"generated_data_files": {
			name: hashlib.sha256(content.encode("utf-8")).hexdigest()
			for name, content in sorted((generated_data_files or {}).items())
		},
		"chart_svg": chart_svg or "",
		"qr_data": qr_data or "",
		"qr_filename": qr_filename or "",
		"barcode_options": barcode_options or {},
		"typst_bin": typst_bin,
		"font_dirs": [str(font_dir) for font_dir in _typst_font_dirs()],
		"ignore_system_fonts": should_ignore_system_fonts(),
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


def sanitize_chart_svg(chart_svg: str | None) -> str | None:
	"""Return a constrained Frappe chart SVG or ``None`` when it is unsafe/invalid."""
	if not isinstance(chart_svg, str) or not chart_svg.strip():
		return None
	from xml.etree import ElementTree as ET

	match = re.search(r"<svg\b[^>]*>.*?</svg>", chart_svg, re.DOTALL | re.IGNORECASE)
	svg = (match.group(0) if match else chart_svg).strip()
	if "<svg" not in svg.lower():
		return None
	if "xmlns=" not in svg:
		svg = re.sub(
			r"<svg\b",
			f'<svg xmlns="{_SVG_NAMESPACE}"',
			svg,
			count=1,
			flags=re.IGNORECASE,
		)
	if "xlink:" in svg and "xmlns:xlink=" not in svg:
		svg = re.sub(
			r"<svg\b",
			f'<svg xmlns:xlink="{_XLINK_NAMESPACE}"',
			svg,
			count=1,
			flags=re.IGNORECASE,
		)
	svg = re.sub(r"&(?!(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);)", "&amp;", svg)

	try:
		root = ET.fromstring(svg)
	except Exception:
		return None
	if _svg_local_name(root.tag) != "svg" or _svg_namespace(root.tag) not in {"", _SVG_NAMESPACE}:
		return None

	element_count = 0
	path_bytes = 0
	for parent in list(root.iter()):
		for child in list(parent):
			name = _svg_local_name(child.tag)
			namespace = _svg_namespace(child.tag)
			if namespace not in {"", _SVG_NAMESPACE} or name not in _ALLOWED_SVG_ELEMENTS:
				parent.remove(child)
	for element in root.iter():
		element_count += 1
		if element_count > MAX_CHART_SVG_ELEMENTS:
			return None
		if _svg_local_name(element.tag) == "path":
			path_bytes += len(str(element.attrib.get("d") or "").encode("utf-8"))
			if path_bytes > MAX_CHART_SVG_PATH_BYTES:
				return None
		for raw_name, raw_value in list(element.attrib.items()):
			name = _svg_local_name(raw_name)
			namespace = _svg_namespace(raw_name)
			value = str(raw_value or "").strip()
			if name.lower().startswith("on"):
				del element.attrib[raw_name]
				continue
			if namespace not in {"", _XLINK_NAMESPACE} or name not in _ALLOWED_SVG_ATTRIBUTES:
				del element.attrib[raw_name]
				continue
			if name == "href" and value and not value.startswith("#"):
				del element.attrib[raw_name]
				continue
			if "url(" in value.lower() and not re.fullmatch(r"url\(\s*#[A-Za-z0-9_.:-]+\s*\)", value):
				del element.attrib[raw_name]

	visible = any(
		_svg_local_name(element.tag)
		in {"path", "line", "rect", "circle", "ellipse", "polyline", "polygon", "text"}
		for element in root.iter()
	)
	if not visible:
		return None
	ET.register_namespace("", _SVG_NAMESPACE)
	ET.register_namespace("xlink", _XLINK_NAMESPACE)
	return ET.tostring(root, encoding="unicode")


def _svg_local_name(value: str) -> str:
	return value.rsplit("}", 1)[-1] if "}" in value else value


def _svg_namespace(value: str) -> str:
	return value[1:].split("}", 1)[0] if value.startswith("{") and "}" in value else ""


def _write_chart_svg(chart_svg: str, temp_dir: str, filename: str = "report_chart.svg"):
	"""Write a sanitized report chart SVG to the Typst working directory."""
	svg = sanitize_chart_svg(chart_svg)
	if not svg:
		frappe.log_error("Invalid or unsafe chart SVG omitted.", "Chart SVG Error")
		return None
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
	_trusted_data_files: dict[str, str] | None = None,
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

	typst_source = _ensure_crispy_image_helper(typst_source)
	crispy_image_asset_files = _extract_crispy_image_assets(typst_source)
	typst_source, literal_asset_files = _normalize_typst_image_literals(typst_source)
	normalized_assets = _normalize_asset_files(asset_files)
	combined_assets = _normalize_asset_files(
		[*normalized_assets, *literal_asset_files, *crispy_image_asset_files]
	)
	normalized_barcode_options = _normalize_barcode_options(barcode_options)
	generated_data_files = _normalize_trusted_data_files(_trusted_data_files)
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
	try:
		typst_version = str(_ensure_typst_minimum_version(typst_bin) or "")
	except FileNotFoundError:
		frappe.throw(_("Typst compiler not found. Please install Typst CLI: brew install typst"))
	except subprocess.TimeoutExpired:
		frappe.throw(_("Unable to determine Typst CLI version before timeout."))

	render_timeout = get_render_timeout_seconds()
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
				generated_data_files=generated_data_files,
				typst_bin=typst_bin,
			)
		except Exception:
			cache_key = None
		if cache_key:
			cached_result = frappe.cache().get_value(cache_key, expires=True)
			if isinstance(cached_result, dict):
				return {
					**cached_result,
					"cache_hit": True,
					"cache_ttl_seconds": cache_ttl,
					"typst_version": cached_result.get("typst_version") or typst_version,
				}

	try:
		start_time = time.perf_counter()
		with TemporaryDirectory() as temp_dir:
			for filename, content in generated_data_files.items():
				(Path(temp_dir) / filename).write_text(content, encoding="utf-8")
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
				timeout=render_timeout,
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
						timeout=render_timeout,
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
					return {
						"success": True,
						"format": "pdf",
						"pdf_url": f"/files/{output_path.name}",
						"cache_hit": False,
						"render_ms": round((time.perf_counter() - start_time) * 1000),
						"typst_version": typst_version,
						"pdf_standard": pdf_standard_cli or None,
					}

				with output_path.open("rb") as pdf_file:
					pdf_bytes = pdf_file.read()

				pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")
				result_payload = {
					"success": True,
					"format": "pdf",
					"pdf_data": pdf_base64,
					"cache_hit": False,
					"render_ms": round((time.perf_counter() - start_time) * 1000),
					"typst_version": typst_version,
					"pdf_standard": pdf_standard_cli or None,
				}
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
				"cache_hit": False,
				"render_ms": round((time.perf_counter() - start_time) * 1000),
				"typst_version": typst_version,
				"pdf_standard": None,
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
