"""Normalize ERPNext/Frappe chart payloads for deterministic Typst rendering."""

from __future__ import annotations

import math
from copy import deepcopy
from typing import Any

import frappe

LILAQ_VERSION = "0.6.0"
CRISPY_CHARTS_VERSION = "0.1.1"
CHART_SPEC_VERSION = 1
MAX_NATIVE_CHART_SERIES = 24
MAX_NATIVE_CHART_POINTS = 2_000
SUPPORTED_KINDS = {
	"bar",
	"grouped_bar",
	"line",
	"mixed",
	"horizontal_bar",
	"percentage_stacked",
	"waterfall",
}

DEFAULT_CHART_THEME = {
	"horizontal_grid": True,
	"vertical_grid": True,
	"minor_grid": False,
	"grid_color": "#CBD5E1",
	"grid_stroke_pt": 0.4,
	"axis_color": "#64748B",
	"axis_stroke_pt": 0.6,
	"zero_line_color": "#475569",
	"zero_line_stroke_pt": 1.0,
	"legend_position": "auto",
	"label_size_pt": 8.0,
	"data_labels": "auto",
	"line_stroke_pt": 1.2,
	"marker_size_pt": 4.0,
	"accessibility_mode": True,
}


def get_report_chart_engine() -> str:
	"""Return the site-wide chart engine, defaulting safely to Lilaq."""
	value = str(frappe.conf.get("CRISPY_PRINT_REPORT_CHART_ENGINE", "lilaq") or "lilaq")
	value = value.strip().lower()
	return value if value in {"lilaq", "frappe_svg"} else "lilaq"


def normalize_report_chart(raw_chart: Any, report_name: str | None = None) -> dict[str, Any]:
	"""Convert an upstream Frappe chart dictionary to the stable chart-spec contract."""
	base = _base_spec(raw_chart)
	if not isinstance(raw_chart, dict) or not raw_chart:
		return _with_status(base, "empty", "none", "empty_chart", "No chart data was returned.")

	source_type = str(raw_chart.get("type") or raw_chart.get("kind") or "").strip().lower()
	base["source_type"] = source_type
	data = raw_chart.get("data") if isinstance(raw_chart.get("data"), dict) else raw_chart
	labels = _normalize_labels(data.get("labels") if isinstance(data, dict) else None)
	datasets = data.get("datasets") if isinstance(data, dict) else None

	if source_type == "percentage":
		return _normalize_percentage(base, labels, datasets, raw_chart, report_name)
	if source_type in {"horizontal_bar", "waterfall"}:
		return _normalize_direct_kind(base, source_type, labels, datasets, raw_chart, report_name)
	if source_type not in {"bar", "line", "axis-mixed"}:
		if not labels and not datasets:
			return _with_status(base, "empty", "none", "empty_chart", "No chart data was returned.")
		return _with_status(
			base,
			"unsupported",
			"none",
			"unsupported_chart_type",
			f"Chart type {source_type or 'unknown'} is not supported by the native renderer.",
		)

	if source_type == "bar" and _is_stacked(raw_chart):
		return _with_status(
			base,
			"unsupported",
			"none",
			"unsupported_stacked_chart",
			"Generic stacked Frappe charts require the SVG fallback.",
		)

	series, error = _normalize_datasets(datasets, labels, default_kind=source_type)
	if error:
		return _with_status(base, "invalid", "none", error[0], error[1])
	if not series or not any(_has_numeric_values(item.get("values")) for item in series):
		return _with_status(base, "empty", "none", "empty_chart", "The chart contains no plottable values.")

	kind = source_type
	if source_type == "axis-mixed":
		kind = "mixed"
		for item in series:
			item["kind"] = "bar" if item["kind"] == "bar" else "line"
	elif source_type == "bar" and len(series) > 1:
		kind = "grouped_bar"

	base.update(
		{
			"kind": kind,
			"labels": labels,
			"series": series,
			"value_format": _value_format(raw_chart),
			"options": _options(raw_chart),
		}
	)
	return _finalize_ready(base, report_name)


def resolve_chart_render(
	spec: dict[str, Any] | None,
	chart_svg: str | None,
	engine_preference: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
	"""Resolve native/fallback/omitted rendering without altering the raw chart."""
	resolved = deepcopy(spec or _base_spec({}))
	preference = (engine_preference or get_report_chart_engine()).strip().lower()
	if preference not in {"lilaq", "frappe_svg"}:
		preference = "lilaq"
	has_svg = bool(isinstance(chart_svg, str) and chart_svg.strip())
	status = resolved.get("status") or "empty"

	if preference == "lilaq" and status == "ready" and resolved.get("kind") in SUPPORTED_KINDS:
		resolved["engine"] = "lilaq"
		render_status = "ready"
		reason = "native_lilaq"
	elif has_svg and status != "empty":
		resolved["engine"] = "frappe_svg"
		render_status = "fallback"
		reason = (
			"engine_disabled"
			if preference == "frappe_svg"
			else resolved.get("diagnostic", {}).get("code", "unsupported")
		)
	else:
		resolved["engine"] = "none"
		render_status = "empty" if status == "empty" else "omitted"
		reason = (
			"engine_disabled_no_svg"
			if preference == "frappe_svg" and status == "ready"
			else resolved.get("diagnostic", {}).get("code") or "chart_unavailable"
		)

	metadata = {
		"engine": resolved["engine"],
		"status": render_status,
		"reason": reason,
		"lilaq_version": LILAQ_VERSION,
		"native_package_version": LILAQ_VERSION,
		"helper_version": CRISPY_CHARTS_VERSION,
		"message": (resolved.get("diagnostic") or {}).get("message", ""),
	}
	return resolved, metadata


def normalize_chart_theme(presentation_settings: dict[str, Any] | None) -> dict[str, Any]:
	settings = presentation_settings if isinstance(presentation_settings, dict) else {}
	report_theme = settings.get("reportTheme") or settings.get("report_theme") or {}
	chart = report_theme.get("chart") if isinstance(report_theme, dict) else {}
	chart = chart if isinstance(chart, dict) else {}
	palette = report_theme.get("chartPalette") or report_theme.get("chart_palette") or []
	if not isinstance(palette, list):
		palette = []
	result = {**DEFAULT_CHART_THEME}
	result.update(
		{
			"horizontal_grid": _bool(chart, "horizontalGrid", "horizontal_grid", default=True),
			"vertical_grid": _bool(chart, "verticalGrid", "vertical_grid", default=True),
			"minor_grid": _bool(chart, "minorGrid", "minor_grid", default=False),
			"grid_color": _color(chart, "gridColor", "grid_color", default="#CBD5E1"),
			"grid_stroke_pt": _number(chart, "gridStrokePt", "grid_stroke_pt", 0.4, 0, 5),
			"axis_color": _color(chart, "axisColor", "axis_color", default="#64748B"),
			"axis_stroke_pt": _number(chart, "axisStrokePt", "axis_stroke_pt", 0.6, 0, 5),
			"zero_line_color": _color(chart, "zeroLineColor", "zero_line_color", default="#475569"),
			"zero_line_stroke_pt": _number(chart, "zeroLineStrokePt", "zero_line_stroke_pt", 1.0, 0, 5),
			"legend_position": _choice(
				chart, "legendPosition", "legend_position", {"auto", "top", "bottom", "hidden"}, "auto"
			),
			"label_size_pt": _number(chart, "labelSizePt", "label_size_pt", 8, 6, 18),
			"data_labels": _choice(chart, "dataLabels", "data_labels", {"auto", "always", "never"}, "auto"),
			"line_stroke_pt": _number(chart, "lineStrokePt", "line_stroke_pt", 1.2, 0.25, 8),
			"marker_size_pt": _number(chart, "markerSizePt", "marker_size_pt", 4, 0, 20),
			"accessibility_mode": _bool(chart, "accessibilityMode", "accessibility_mode", default=True),
			"negative_color": str(report_theme.get("negativeColor") or "#B91C1C"),
			"muted_color": str(report_theme.get("mutedColor") or "#64748B"),
			"palette": [str(value) for value in palette[:12] if str(value).strip()],
		}
	)
	return result


def _base_spec(raw_chart: Any) -> dict[str, Any]:
	return {
		"schema_version": CHART_SPEC_VERSION,
		"status": "empty",
		"engine": "none",
		"source_type": "",
		"kind": "",
		"labels": [],
		"series": [],
		"value_format": {"fieldtype": "", "currency": "", "precision": 2, "suffix": ""},
		"options": {"stacked": False, "orientation": "vertical", "show_legend": True},
		"accessibility": {"summary": ""},
		"diagnostic": {"code": "", "message": ""},
	}


def _normalize_percentage(base, labels, datasets, raw_chart, report_name):
	if not labels or not isinstance(datasets, list) or not datasets:
		return _with_status(base, "empty", "none", "empty_chart", "The percentage chart is empty.")
	aggregates = [0.0] * len(labels)
	for dataset in datasets:
		if not isinstance(dataset, dict):
			return _with_status(base, "invalid", "none", "invalid_dataset", "A chart dataset is invalid.")
		values = dataset.get("values")
		if not isinstance(values, list | tuple) or len(values) != len(labels):
			return _with_status(
				base, "invalid", "none", "dataset_length_mismatch", "Chart labels and values do not match."
			)
		for index, value in enumerate(values):
			number, valid = _number_or_none(value)
			if not valid:
				return _with_status(
					base, "invalid", "none", "non_finite_value", "The chart contains a non-finite value."
				)
			if number is not None:
				if number < 0:
					return _with_status(
						base,
						"invalid",
						"none",
						"negative_percentage_value",
						"Percentage aging charts cannot contain negative values.",
					)
				aggregates[index] += number
	if not any(aggregates):
		return _with_status(base, "empty", "none", "empty_chart", "The percentage chart is empty.")
	base.update(
		{
			"kind": "percentage_stacked",
			"labels": labels,
			"series": [
				{"name": label, "kind": "bar", "values": [aggregates[index]]}
				for index, label in enumerate(labels)
			],
			"value_format": _value_format(raw_chart),
			"options": {**_options(raw_chart), "stacked": True, "orientation": "horizontal"},
		}
	)
	return _finalize_ready(base, report_name)


def _normalize_direct_kind(base, kind, labels, datasets, raw_chart, report_name):
	series, error = _normalize_datasets(datasets, labels, default_kind="bar")
	if error:
		return _with_status(base, "invalid", "none", error[0], error[1])
	if not series or not any(_has_numeric_values(item.get("values")) for item in series):
		return _with_status(base, "empty", "none", "empty_chart", "The chart contains no plottable values.")
	base.update(
		{
			"kind": kind,
			"labels": labels,
			"series": series,
			"value_format": _value_format(raw_chart),
			"options": _options(raw_chart),
		}
	)
	return _finalize_ready(base, report_name)


def _normalize_datasets(datasets, labels, default_kind):
	if not isinstance(datasets, list):
		return [], ("invalid_datasets", "Chart datasets must be a list.")
	series = []
	point_count = 0
	for index, dataset in enumerate(datasets):
		if not isinstance(dataset, dict):
			return [], ("invalid_dataset", "A chart dataset is invalid.")
		values = dataset.get("values")
		if not isinstance(values, list | tuple) or len(values) != len(labels):
			return [], ("dataset_length_mismatch", "Chart labels and values do not match.")
		normalized_values = []
		for value in values:
			number, valid = _number_or_none(value)
			if not valid:
				return [], ("non_finite_value", "The chart contains a non-finite value.")
			normalized_values.append(number)
		name = str(dataset.get("name") or dataset.get("label") or f"Series {index + 1}")
		kind = str(dataset.get("chartType") or dataset.get("kind") or default_kind).strip().lower()
		series.append({"name": name, "kind": kind, "values": normalized_values})
		point_count += len(normalized_values)
	if len(series) > MAX_NATIVE_CHART_SERIES:
		return [], ("too_many_series", f"Native charts support at most {MAX_NATIVE_CHART_SERIES} series.")
	if point_count > MAX_NATIVE_CHART_POINTS:
		return [], ("too_many_points", f"Native charts support at most {MAX_NATIVE_CHART_POINTS} points.")
	return series, None


def _finalize_ready(spec, report_name):
	if spec.get("kind") not in SUPPORTED_KINDS:
		return _with_status(
			spec, "unsupported", "none", "unsupported_chart_kind", "The normalized chart kind is unsupported."
		)
	spec["status"] = "ready"
	spec["engine"] = "lilaq"
	spec["diagnostic"] = {"code": "", "message": ""}
	spec["accessibility"] = {"summary": _accessibility_summary(spec, report_name)}
	return spec


def _accessibility_summary(spec, report_name):
	title = str(report_name or "Report")
	series = spec.get("series") or []
	parts = [f"{title} chart."]
	for item in series[:6]:
		values = [value for value in item.get("values", []) if isinstance(value, int | float)]
		if not values:
			continue
		name = str(item.get("name") or "Series")
		if len(values) == 1:
			parts.append(f"{name}: {values[0]:g}.")
		else:
			parts.append(
				f"{name} starts at {values[0]:g}, ends at {values[-1]:g}, "
				f"with a minimum of {min(values):g} and maximum of {max(values):g}."
			)
	negative_count = sum(
		1
		for item in series
		for value in item.get("values", [])
		if isinstance(value, int | float) and value < 0
	)
	if negative_count:
		parts.append(f"The chart contains {negative_count} negative value(s).")
	currency = str((spec.get("value_format") or {}).get("currency") or "")
	if currency:
		parts.append(f"Values are in {currency}.")
	return " ".join(parts)


def _with_status(spec, status, engine, code, message):
	spec["status"] = status
	spec["engine"] = engine
	spec["diagnostic"] = {"code": code, "message": message}
	return spec


def _normalize_labels(value):
	if not isinstance(value, list | tuple):
		return []
	return [str(label or "") for label in value]


def _number_or_none(value):
	if value is None or value == "":
		return None, True
	if isinstance(value, bool):
		return None, False
	try:
		number = float(value)
	except (TypeError, ValueError):
		return None, False
	if not math.isfinite(number):
		return None, False
	return (int(number) if number.is_integer() else number), True


def _has_numeric_values(values):
	return isinstance(values, list) and any(isinstance(value, int | float) for value in values)


def _value_format(raw_chart):
	precision = raw_chart.get("precision", 2)
	try:
		precision = max(0, min(9, int(precision)))
	except (TypeError, ValueError):
		precision = 2
	return {
		"fieldtype": str(raw_chart.get("fieldtype") or ""),
		"currency": str(raw_chart.get("currency") or ""),
		"precision": precision,
		"suffix": str(raw_chart.get("suffix") or ""),
	}


def _options(raw_chart):
	return {
		"stacked": _is_stacked(raw_chart),
		"orientation": str(raw_chart.get("orientation") or "vertical"),
		"show_legend": True,
		"invert_categories": bool(raw_chart.get("invert_categories")),
	}


def _is_stacked(raw_chart):
	bar_options = raw_chart.get("barOptions") if isinstance(raw_chart.get("barOptions"), dict) else {}
	return bool(bar_options.get("stacked") or raw_chart.get("stacked"))


def _pick(mapping, *keys, default=None):
	for key in keys:
		if key in mapping and mapping.get(key) not in (None, ""):
			return mapping.get(key)
	return default


def _bool(mapping, *keys, default=False):
	value = _pick(mapping, *keys, default=default)
	if isinstance(value, str):
		return value.strip().lower() in {"1", "true", "yes", "on"}
	return bool(value)


def _number(mapping, key, alias, default, minimum, maximum):
	value = _pick(mapping, key, alias, default=default)
	try:
		return max(minimum, min(maximum, float(value)))
	except (TypeError, ValueError):
		return default


def _choice(mapping, key, alias, allowed, default):
	value = str(_pick(mapping, key, alias, default=default)).strip().lower()
	return value if value in allowed else default


def _color(mapping, key, alias, default):
	value = str(_pick(mapping, key, alias, default=default)).strip()
	if len(value) == 7 and value.startswith("#"):
		try:
			int(value[1:], 16)
			return value.upper()
		except ValueError:
			pass
	return default
