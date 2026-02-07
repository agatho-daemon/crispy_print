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
from .formats import get_reports_without_custom_html as _get_reports_without_custom_html
from .formats import import_crispy_format as _import_crispy_format
from .reports import generate_report_pdf as _generate_report_pdf
from .reports import get_report_typst_source as _get_report_typst_source
from .reports import get_sample_report_data as _get_sample_report_data


@frappe.whitelist()
def get_typst_local_fonts() -> list[str]:
	return _get_typst_local_fonts()


@frappe.whitelist()
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
	return _compile_typst(
		typst_source,
		output_format=output_format,
		letterhead_image=letterhead_image,
		logo_image=logo_image,
		chart_svg=chart_svg,
		qr_data=qr_data,
		qr_filename=qr_filename,
		output_filename=output_filename,
		return_url=return_url,
	)


@frappe.whitelist()
def get_formatted_doc(doctype: str, name: str) -> dict:
	return _get_formatted_doc(doctype, name)


@frappe.whitelist()
def get_crispy_formats_for_doctype(doctype):
	return _get_crispy_formats_for_doctype(doctype)


@frappe.whitelist()
def get_default_doctypes():
	return _get_default_doctypes()


@frappe.whitelist()
def generate_report_pdf(
	report: str,
	filters: dict | str | None = None,
	format_name: str | None = None,
	orientation: str = "landscape",
	include_filters: int = 0,
	column_config=None,
):
	return _generate_report_pdf(
		report,
		filters=filters,
		format_name=format_name,
		orientation=orientation,
		include_filters=include_filters,
		column_config=column_config,
	)


@frappe.whitelist()
def get_available_formats(report: str) -> dict:
	return _get_available_formats(report)


@frappe.whitelist()
def get_builder_mode(format_name: str) -> dict:
	return _get_builder_mode(format_name)


@frappe.whitelist()
def export_crispy_format(name: str) -> dict:
	return _export_crispy_format(name)


@frappe.whitelist()
def check_import_conflicts(payload: dict | str) -> dict:
	return _check_import_conflicts(payload)


@frappe.whitelist()
def import_crispy_format(payload: dict | str, on_conflict: str = "copy") -> dict:
	return _import_crispy_format(payload, on_conflict=on_conflict)


@frappe.whitelist()
def get_reports_without_custom_html(generic_report_type: str | None = None) -> list[dict]:
	return _get_reports_without_custom_html(generic_report_type)


@frappe.whitelist()
def get_report_typst_source(
	report: str,
	format_name: str,
	filters: dict | str | None = None,
	column_config: list | str | None = None,
	include_filters: int = 0,
	orientation: str | None = None,
	page_settings: dict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	letterhead_image: str | None = None,
	limit: int = 50,
) -> str:
	return _get_report_typst_source(
		report=report,
		format_name=format_name,
		filters=filters,
		column_config=column_config,
		include_filters=include_filters,
		orientation=orientation,
		page_settings=page_settings,
		chart_svg=chart_svg,
		typst_preamble_override=typst_preamble_override,
		letterhead_image=letterhead_image,
		limit=limit,
	)


@frappe.whitelist()
def get_sample_report_data(report: str, filters=None, limit: int = 50) -> dict:
	return _get_sample_report_data(report, filters=filters, limit=limit)


__all__ = [
	"check_import_conflicts",
	"compile_typst",
	"export_crispy_format",
	"generate_report_pdf",
	"get_available_formats",
	"get_builder_mode",
	"get_crispy_formats_for_doctype",
	"get_default_doctypes",
	"get_formatted_doc",
	"get_report_typst_source",
	"get_reports_without_custom_html",
	"get_sample_report_data",
	"get_typst_local_fonts",
	"import_crispy_format",
]
