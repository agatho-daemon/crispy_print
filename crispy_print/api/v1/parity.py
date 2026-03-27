import re
from pathlib import Path

import frappe


def _normalize_condition(value: str) -> str:
	text = (value or "").strip()
	if not text:
		return ""
	text = text.replace("\n", " ")
	text = re.sub(r"\s+", " ", text)
	return text


def extract_legacy_template_signals(source: str) -> dict:
	"""Extract conditional and filter-key signals from legacy report HTML/JS templates."""
	if not source:
		return {"conditions": [], "filter_keys": []}

	conditions: list[str] = []
	filter_keys: set[str] = set()

	for match in re.findall(r"{%\s*(?:if|else if)\s*\((.*?)\)\s*\{\s*%}", source, flags=re.DOTALL):
		normalized = _normalize_condition(match)
		if normalized:
			conditions.append(normalized)

	for match in re.findall(r"filters\.([a-zA-Z_]\w*)", source):
		filter_keys.add(match)
	for match in re.findall(r"['\"]([a-zA-Z_]\w*)['\"]\s+in\s+filters", source):
		filter_keys.add(match)
	for match in re.findall(r"filters\[['\"]([a-zA-Z_]\w*)['\"]\]", source):
		filter_keys.add(match)

	return {"conditions": sorted(set(conditions)), "filter_keys": sorted(filter_keys)}


def extract_typst_template_signals(source: str) -> dict:
	"""Extract conditional and filter-key signals from Typst templates."""
	if not source:
		return {"conditions": [], "filter_keys": []}

	conditions: list[str] = []
	filter_keys: set[str] = set()

	for match in re.findall(r"#if\s+([^\[\n]+)", source):
		normalized = _normalize_condition(match)
		if normalized:
			conditions.append(normalized)

	for match in re.findall(r"(?:data|filters)\.([a-zA-Z_]\w*)", source):
		filter_keys.add(match)
	for match in re.findall(r'get-filter-value\("([^"]+)"\)', source):
		key = frappe.scrub(str(match))
		if key:
			filter_keys.add(key)
	for match in re.findall(r'getFilterValue\("([^"]+)"\)', source):
		key = frappe.scrub(str(match))
		if key:
			filter_keys.add(key)
	for match in re.findall(r"data\.filters_map\.([a-zA-Z_]\w*)", source):
		filter_keys.add(match)

	return {"conditions": sorted(set(conditions)), "filter_keys": sorted(filter_keys)}


def compare_template_signals(legacy_source: str, typst_source: str) -> dict:
	"""Compare legacy template signals against Typst template signals."""
	legacy = extract_legacy_template_signals(legacy_source)
	typst = extract_typst_template_signals(typst_source)

	legacy_filter_keys = set(legacy["filter_keys"])
	typst_filter_keys = set(typst["filter_keys"])
	missing_filter_keys = sorted(legacy_filter_keys - typst_filter_keys)

	return {
		"legacy": legacy,
		"typst": typst,
		"summary": {
			"legacy_condition_count": len(legacy["conditions"]),
			"typst_condition_count": len(typst["conditions"]),
			"legacy_filter_count": len(legacy_filter_keys),
			"typst_filter_count": len(typst_filter_keys),
			"missing_filter_keys": missing_filter_keys,
			"filter_coverage_percent": round(
				(100.0 * (len(legacy_filter_keys) - len(missing_filter_keys)) / len(legacy_filter_keys)),
				2,
			)
			if legacy_filter_keys
			else 100.0,
		},
	}


def _resolve_report_html_path(report: str, explicit_path: str | None = None) -> Path:
	if explicit_path:
		path = Path(explicit_path)
		if not path.exists():
			frappe.throw(f"Legacy template file not found: {path}")
		return path

	report_doc = frappe.get_doc("Report", report)
	module = report_doc.get("module")
	if not module:
		frappe.throw(f"Report '{report}' has no module configured")

	try:
		module_path = Path(frappe.get_module_path(module))
	except Exception:
		frappe.throw(f"Unable to resolve module path for report '{report}'")

	report_folder = frappe.scrub(report)
	path = module_path / "report" / report_folder / f"{report_folder}.html"
	if not path.exists():
		frappe.throw(f"Legacy report template not found: {path}")
	return path


def _read_legacy_template_source(path: Path, depth: int = 0) -> str:
	"""Read legacy template and inline top-level {% include %} directives."""
	if depth > 5:
		return path.read_text(encoding="utf-8")

	source = path.read_text(encoding="utf-8")
	include_pattern = r'{%\s*include\s+"([^"]+)"\s*%}'
	matches = re.findall(include_pattern, source)
	if not matches:
		return source

	inlined = source
	for include_ref in matches:
		include_path = None

		# ERPNext/Frappe include references are commonly app-relative.
		if not include_path:
			try:
				erpnext_root = Path(frappe.get_app_path("erpnext"))
				candidate = erpnext_root / include_ref
				if candidate.exists():
					include_path = candidate
			except Exception:
				include_path = None

		# Fallback to relative include from current template directory.
		if not include_path:
			candidate = (path.parent / include_ref).resolve()
			if candidate.exists():
				include_path = candidate

		if not include_path:
			continue

		include_tag = '{% include "' + include_ref + '" %}'
		inlined = inlined.replace(include_tag, _read_legacy_template_source(include_path, depth + 1))

	return inlined


def run_report_template_parity_check(
	report: str,
	format_name: str,
	legacy_template_path: str | None = None,
	filters: dict | str | None = None,
) -> dict:
	"""Build Typst source and compare it with a legacy report HTML template."""
	legacy_path = _resolve_report_html_path(report, legacy_template_path)
	legacy_source = _read_legacy_template_source(legacy_path)

	from .reports import get_report_typst_source

	typst_source = get_report_typst_source(
		report=report,
		format_name=format_name,
		filters=filters or {},
		include_filters=1,
		preview_data={
			"title": report,
			"subtitle": "",
			"filters": [],
			"columns": [],
			"rows": [],
			"report_summary": [],
			"chart": {},
		},
	)
	if isinstance(typst_source, dict):
		typst_source = typst_source.get("typst_source", "")

	comparison = compare_template_signals(legacy_source, typst_source)
	comparison["report"] = report
	comparison["format_name"] = format_name
	comparison["legacy_template_path"] = str(legacy_path)
	return comparison
