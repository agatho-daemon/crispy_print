import json
import time
from statistics import mean

import frappe

from crispy_print.api.v1.compile import compile_typst
from crispy_print.api.v1.formats import get_available_formats
from crispy_print.api.v1.reports import compile_report_preview


def _time_call(fn, iterations: int = 10):
	durations = []
	last_result = None
	for _ in range(iterations):
		start = time.perf_counter()
		last_result = fn()
		durations.append((time.perf_counter() - start) * 1000)
	return {
		"iterations": iterations,
		"min_ms": round(min(durations), 3),
		"mean_ms": round(mean(durations), 3),
		"max_ms": round(max(durations), 3),
		"last_result_type": type(last_result).__name__,
	}


def run(iterations: int = 10):
	frappe.set_user("Administrator")
	report = frappe.db.get_value("Report", {}, "name") or "Style Preview"
	benchmark_format_name = "Crispy Print Benchmark Format"
	if frappe.db.exists("Crispy Format", benchmark_format_name):
		frappe.delete_doc("Crispy Format", benchmark_format_name, force=True)
	format_doc = frappe.get_doc(
		{
			"doctype": "Crispy Format",
			"name": benchmark_format_name,
			"crispy_format_type": "Report",
			"module": "Crispy Print",
			"is_generic": 1,
			"generic_report_type": "Grid",
			"raw_typst": 1,
			"typst_code": "#text(size: 9pt)[Benchmark report preview]",
		}
	)
	format_doc.insert(ignore_permissions=True)

	base_typst = "#set page(width: 30mm, height: 20mm, margin: 2mm)\n#text(size: 9pt)[Crispy benchmark]"
	preview_data = {
		"title": "Benchmark Preview",
		"subtitle": "",
		"filters": [],
		"report_summary": [],
		"columns": [{"fieldname": "name", "label": "Name", "width": "auto"}],
		"rows": [{"name": "Row 1", "cells": [{"fieldname": "name", "value": "Row 1"}]}],
		"total_rows": 1,
	}

	try:
		results = {
			"report": report,
			"format": benchmark_format_name,
			"get_available_formats": _time_call(lambda: get_available_formats(report), iterations),
			"compile_typst_cache_miss": _time_call(
				lambda: compile_typst(
					f"{base_typst}\n// {time.perf_counter_ns()}",
					output_format="svg",
				),
				max(1, min(3, iterations)),
			),
		}
		compile_typst(base_typst, output_format="svg")
		results["compile_typst_cache_hit"] = _time_call(
			lambda: compile_typst(base_typst, output_format="svg"),
			iterations,
		)
		results["compile_report_preview"] = _time_call(
			lambda: compile_report_preview(
				report=report,
				format_name=benchmark_format_name,
				preview_data=preview_data,
				presentation_settings={"page": {"orientation": "landscape"}},
				limit=50,
			),
			max(1, min(5, iterations)),
		)
		print(json.dumps(results, indent=2, sort_keys=True))
		return results
	finally:
		frappe.db.rollback()
		if frappe.db.exists("Crispy Format", benchmark_format_name):
			frappe.delete_doc("Crispy Format", benchmark_format_name, force=True)
			frappe.db.commit()
