from typing import Any

import frappe

from .compile import compile_typst as _compile_typst
from .compile import get_typst_local_fonts as _get_typst_local_fonts
from .docs import get_formatted_doc as _get_formatted_doc
from .formats import check_import_conflicts as _check_import_conflicts
from .formats import export_crispy_format as _export_crispy_format
from .formats import get_available_formats as _get_available_formats
from .formats import get_builder_mode as _get_builder_mode
from .formats import get_crispy_formats_for_doctype as _get_crispy_formats_for_doctype
from .formats import get_default_doctypes as _get_default_doctypes
from .formats import get_default_report_builder_config as _get_default_report_builder_config
from .formats import get_reports_without_custom_html as _get_reports_without_custom_html
from .formats import import_crispy_format as _import_crispy_format
from .parity import run_report_template_parity_check as _run_report_template_parity_check
from .reports import generate_report_pdf as _generate_report_pdf
from .reports import get_report_typst_source as _get_report_typst_source
from .reports import get_sample_report_data as _get_sample_report_data

JSONDict = dict[str, Any]


@frappe.whitelist()
def get_typst_local_fonts() -> list[str]:
	return _get_typst_local_fonts()


@frappe.whitelist()
def compile_typst(
	typst_source: str,
	output_format: str = "svg",
	asset_files: list[str] | None = None,
	chart_svg: str | None = None,
	qr_data: str | None = None,
	qr_filename: str | None = None,
	output_filename: str | None = None,
	return_url: int | bool = 0,
	**kwargs: Any,
) -> JSONDict | None:
	filtered_kwargs = {
		key: value for key, value in kwargs.items() if key not in {"cmd"} and not key.startswith("_")
	}
	deprecated = [key for key in ("letterhead_image", "logo_image") if key in filtered_kwargs]
	if deprecated:
		frappe.throw("Deprecated params are not supported. Use asset_files only.")
	if filtered_kwargs:
		frappe.throw(f"Unsupported compile_typst params: {', '.join(sorted(filtered_kwargs.keys()))}")
	return _compile_typst(
		typst_source,
		output_format=output_format,
		asset_files=asset_files,
		chart_svg=chart_svg,
		qr_data=qr_data,
		qr_filename=qr_filename,
		output_filename=output_filename,
		return_url=return_url,
	)


@frappe.whitelist()
def get_formatted_doc(doctype: str, name: str) -> JSONDict:
	return _get_formatted_doc(doctype, name)


@frappe.whitelist()
def get_crispy_formats_for_doctype(doctype: str) -> list[dict[str, str]]:
	return _get_crispy_formats_for_doctype(doctype)


@frappe.whitelist()
def get_default_doctypes() -> list[str]:
	return _get_default_doctypes()


@frappe.whitelist()
def get_default_report_builder_config(generic_report_type: str | None = None) -> JSONDict:
	return _get_default_report_builder_config(generic_report_type)


@frappe.whitelist()
def generate_report_pdf(
	report: str,
	filters: JSONDict | str | None = None,
	format_name: str | None = None,
	orientation: str = "landscape",
	include_filters: int = 0,
	column_config: list[JSONDict] | str | None = None,
) -> JSONDict:
	return _generate_report_pdf(
		report,
		filters=filters,
		format_name=format_name,
		orientation=orientation,
		include_filters=include_filters,
		column_config=column_config,
	)


@frappe.whitelist()
def get_available_formats(report: str) -> JSONDict:
	return _get_available_formats(report)


@frappe.whitelist()
def get_builder_mode(format_name: str) -> JSONDict:
	return _get_builder_mode(format_name)


@frappe.whitelist()
def export_crispy_format(name: str) -> JSONDict:
	return _export_crispy_format(name)


@frappe.whitelist()
def check_import_conflicts(payload: JSONDict | str) -> JSONDict:
	return _check_import_conflicts(payload)


@frappe.whitelist()
def import_crispy_format(payload: JSONDict | str, on_conflict: str = "copy") -> JSONDict:
	return _import_crispy_format(payload, on_conflict=on_conflict)


@frappe.whitelist()
def get_reports_without_custom_html(generic_report_type: str | None = None) -> list[JSONDict]:
	return _get_reports_without_custom_html(generic_report_type)


@frappe.whitelist()
def get_report_typst_source(
	report: str,
	format_name: str,
	filters: JSONDict | str | None = None,
	column_config: list[JSONDict] | str | None = None,
	include_filters: int = 0,
	include_summary: int = 1,
	include_total_row: int = 1,
	include_chart: int = 1,
	orientation: str | None = None,
	page_settings: JSONDict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	typst_code_override: str | None = None,
	preview_data: JSONDict | str | None = None,
	limit: int = 50,
) -> JSONDict:
	return _get_report_typst_source(
		report=report,
		format_name=format_name,
		filters=filters,
		column_config=column_config,
		include_filters=include_filters,
		include_summary=include_summary,
		include_total_row=include_total_row,
		include_chart=include_chart,
		orientation=orientation,
		page_settings=page_settings,
		chart_svg=chart_svg,
		typst_preamble_override=typst_preamble_override,
		typst_code_override=typst_code_override,
		preview_data=preview_data,
		limit=limit,
	)


@frappe.whitelist()
def get_sample_report_data(report: str, filters: JSONDict | str | None = None, limit: int = 50) -> JSONDict:
	return _get_sample_report_data(report, filters=filters, limit=limit)


@frappe.whitelist()
def run_report_template_parity_check(
	report: str,
	format_name: str,
	legacy_template_path: str | None = None,
	filters: JSONDict | str | None = None,
) -> JSONDict:
	return _run_report_template_parity_check(
		report=report,
		format_name=format_name,
		legacy_template_path=legacy_template_path,
		filters=filters,
	)


__all__ = [
	"check_import_conflicts",
	"compile_typst",
	"export_crispy_format",
	"generate_report_pdf",
	"get_available_formats",
	"get_builder_mode",
	"get_crispy_formats_for_doctype",
	"get_default_doctypes",
	"get_default_report_builder_config",
	"get_formatted_doc",
	"get_report_typst_source",
	"get_reports_without_custom_html",
	"get_sample_report_data",
	"get_typst_local_fonts",
	"import_crispy_format",
	"run_report_template_parity_check",
]
