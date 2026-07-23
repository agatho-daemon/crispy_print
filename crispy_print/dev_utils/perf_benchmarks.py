import base64
import io
import json
import resource
import sys
import time
import tracemalloc
from statistics import mean

import frappe

from crispy_print.api.v1.compile import compile_typst
from crispy_print.api.v1.formats import get_available_formats
from crispy_print.api.v1.reports import compile_report_preview


def _measure_stage(fn):
	tracemalloc.start()
	rss_before = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
	child_rss_before = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
	start = time.perf_counter()
	result = fn()
	elapsed_ms = (time.perf_counter() - start) * 1000
	_, peak_bytes = tracemalloc.get_traced_memory()
	tracemalloc.stop()
	rss_after = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
	child_rss_after = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
	rss_divisor = 1024 * 1024 if sys.platform == "darwin" else 1024
	return result, {
		"elapsed_ms": round(elapsed_ms, 3),
		"python_peak_mib": round(peak_bytes / (1024 * 1024), 3),
		"process_max_rss_delta_mib": round(max(0, rss_after - rss_before) / rss_divisor, 3),
		"child_max_rss_delta_mib": round(max(0, child_rss_after - child_rss_before) / rss_divisor, 3),
	}


def _pdf_page_count(pdf_bytes: bytes) -> int | None:
	try:
		from pypdf import PdfReader

		return len(PdfReader(io.BytesIO(pdf_bytes)).pages)
	except (ImportError, ValueError):
		return None


def compile_pagination_acceptance(source_base64: str):
	"""Compile a generated fixture and report page-level accounting markers."""
	from pypdf import PdfReader

	source = base64.b64decode(source_base64).decode("utf-8")
	result = compile_typst(source, output_format="pdf", pdf_standard="PDF/A-2u")
	pdf_bytes = base64.b64decode(result.get("pdf_data") or "")
	pages = PdfReader(io.BytesIO(pdf_bytes)).pages
	page_texts = [(page.extract_text() or "") for page in pages]
	last_content_lines = []
	for text in page_texts:
		lines = [
			line.strip()
			for line in text.splitlines()
			if line.strip() and not line.startswith("Page ") and line != "Wasaq Group General Trading"
		]
		last_content_lines.append(lines[-1] if lines else "")
	metrics = {
		"success": bool(result.get("success")),
		"cache_hit": bool(result.get("cache_hit")),
		"render_ms": result.get("render_ms"),
		"pdf_bytes": len(pdf_bytes),
		"pages": len(pages),
		"pages_with_report_header": sum("CRISPY ACCOUNTING ACCEPTANCE" in text for text in page_texts),
		"pages_with_table_header": sum("Account" in text and "Amount" in text for text in page_texts),
		"pages_with_brand_footer": sum("Wasaq Group General Trading" in text for text in page_texts),
		"pages_with_page_number": sum("Page " in text for text in page_texts),
		"orphan_group_heading_pages": [
			index + 1 for index, line in enumerate(last_content_lines) if line.startswith("GROUP ")
		],
		"grand_total_occurrences": sum("Grand Total" in text for text in page_texts),
		"negative_value_occurrences": sum("KWD -25.125" in text for text in page_texts),
		"zero_value_occurrences": sum("KWD 0.000" in text for text in page_texts),
		"precision_value_occurrences": sum("1,234.567" in text for text in page_texts),
		"subtotal_text_samples": [
			line.strip()
			for text in page_texts
			for line in text.splitlines()
			if "Subtotal" in line or "1,234" in line
		][:12],
	}
	print(json.dumps(metrics, indent=2, sort_keys=True))
	return metrics


def compile_localization_acceptance(source_base64: str):
	"""Compile a bilingual RTL fixture and inspect scripts, values, and embedded fonts."""
	from pypdf import PdfReader

	source = base64.b64decode(source_base64).decode("utf-8")
	result = compile_typst(source, output_format="pdf", pdf_standard="PDF/A-2u")
	pdf_bytes = base64.b64decode(result.get("pdf_data") or "")
	reader = PdfReader(io.BytesIO(pdf_bytes))
	page_texts = [(page.extract_text() or "") for page in reader.pages]
	all_text = "\n".join(page_texts)
	fonts = set()
	for page in reader.pages:
		resources = page.get("/Resources") or {}
		for font in (resources.get("/Font") or {}).values():
			font_object = font.get_object()
			if font_object.get("/BaseFont"):
				fonts.add(str(font_object["/BaseFont"]))
	metrics = {
		"success": bool(result.get("success")),
		"cache_hit": bool(result.get("cache_hit")),
		"render_ms": result.get("render_ms"),
		"pdf_bytes": len(pdf_bytes),
		"pages": len(reader.pages),
		"arabic_codepoints_extracted": sum("\u0600" <= char <= "\u06ff" for char in all_text),
		"pages_with_arabic": sum(any("\u0600" <= char <= "\u06ff" for char in text) for text in page_texts),
		"pages_with_english": sum("English" in text for text in page_texts),
		"pages_with_currency": sum("KWD" in text for text in page_texts),
		"negative_currency_preserved": "-12.375" in all_text,
		"zero_currency_preserved": "0.000" in all_text,
		"latin_date_preserved": "23-07-2026" in all_text or "2026-07-23" in all_text,
		"embedded_fonts": sorted(fonts),
	}
	print(json.dumps(metrics, indent=2, sort_keys=True, ensure_ascii=False))
	return metrics


def run_report_pipeline(
	report: str = "General Ledger",
	format_name: str = "Smoke Test General Ledger",
	filters_json: str | dict | None = None,
	column_config_json: str | list | None = None,
	force_compile_cache_miss: int = 0,
):
	"""Benchmark a real report without creating formats, files, jobs, or database rows."""
	from crispy_print.api.v1.reports import (
		REPORT_DATA_FILENAME,
		_fill_default_report_filters,
		_get_report_data,
		_prepare_typst_report_data,
		_serialize_report_data_file,
		get_report_typst_source,
	)

	frappe.set_user("Administrator")
	filters = json.loads(filters_json) if isinstance(filters_json, str) else dict(filters_json or {})
	column_config = (
		json.loads(column_config_json)
		if isinstance(column_config_json, str)
		else list(column_config_json or [])
	)
	filters = _fill_default_report_filters(report, filters)
	metrics = {
		"report": report,
		"format": format_name,
		"filters": filters,
		"render_timeout_seconds": frappe.db.get_single_value(
			"Crispy Print Settings", "render_timeout_seconds"
		)
		or 60,
	}

	report_data, metrics["erpnext_execution"] = _measure_stage(
		lambda: _get_report_data(report, filters, max_rows=None)
	)
	typst_data, metrics["normalization"] = _measure_stage(
		lambda: _prepare_typst_report_data(
			report,
			report_data,
			filters=filters,
			column_filter=column_config or None,
		)
	)
	json_payload, metrics["temporary_json"] = _measure_stage(lambda: _serialize_report_data_file(typst_data))
	source_payload, metrics["typst_source_generation"] = _measure_stage(
		lambda: get_report_typst_source(
			report=report,
			format_name=format_name,
			filters=filters,
			column_config=column_config or None,
			preview_data=typst_data,
			limit=0,
			_externalize_data=True,
		)
	)
	compile_source = source_payload.get("typst_source") or ""
	if force_compile_cache_miss:
		compile_source = f"{compile_source}\n// benchmark-cache-bust:{time.time_ns()}"
	compile_result, metrics["typst_pdf_compilation"] = _measure_stage(
		lambda: compile_typst(
			compile_source,
			output_format="pdf",
			pdf_standard="PDF/A-2u",
			asset_files=source_payload.get("asset_files") or [],
			chart_svg=source_payload.get("chart_svg"),
			_trusted_data_files=source_payload.get("_generated_data_files")
			or {REPORT_DATA_FILENAME: json_payload.encode("utf-8")},
		)
	)
	pdf_bytes, metrics["base64_decode"] = _measure_stage(
		lambda: base64.b64decode(compile_result.get("pdf_data") or "")
	)
	rpc_payload, metrics["rpc_json_serialization"] = _measure_stage(
		lambda: json.dumps(
			{
				"success": compile_result.get("success"),
				"format": compile_result.get("format"),
				"pdf_data": compile_result.get("pdf_data"),
				"render_ms": compile_result.get("render_ms"),
			},
			separators=(",", ":"),
		)
	)
	_, metrics["pdf_page_metadata"] = _measure_stage(lambda: _pdf_page_count(pdf_bytes))

	row_count = len(typst_data.get("rows") or [])
	column_count = len(typst_data.get("columns") or [])
	pdf_bytes_len = len(pdf_bytes)
	base64_bytes_len = len((compile_result.get("pdf_data") or "").encode("ascii"))
	metrics["sizes"] = {
		"rows": row_count,
		"columns": column_count,
		"temporary_json_bytes": len(json_payload.encode("utf-8")),
		"typst_source_bytes": len((source_payload.get("typst_source") or "").encode("utf-8")),
		"pdf_bytes": pdf_bytes_len,
		"base64_bytes": base64_bytes_len,
		"rpc_json_bytes": len(rpc_payload.encode("utf-8")),
		"base64_expansion_percent": (
			round(((base64_bytes_len / pdf_bytes_len) - 1) * 100, 2) if pdf_bytes_len else 0
		),
		"pdf_pages": _pdf_page_count(pdf_bytes),
	}
	metrics["typst_pdf_compilation"]["reported_render_ms"] = compile_result.get("render_ms")
	metrics["typst_pdf_compilation"]["cache_hit"] = bool(compile_result.get("cache_hit"))
	effective_compile_ms = (
		float(compile_result.get("render_ms") or 0)
		if compile_result.get("cache_hit")
		else metrics["typst_pdf_compilation"]["elapsed_ms"]
	)
	metrics["decision_inputs"] = {
		"server_timeout_headroom_ms": round(
			float(metrics["render_timeout_seconds"]) * 1000 - effective_compile_ms,
			3,
		),
		"compile_succeeded": bool(compile_result.get("success")),
	}
	print(json.dumps(metrics, indent=2, sort_keys=True, default=str))
	return metrics


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
			"report_scope": "All Compatible Reports",
			"report_renderer": "generic_report",
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
