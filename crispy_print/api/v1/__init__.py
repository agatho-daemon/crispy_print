import json
from typing import Any

import frappe
from frappe import _

from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	get_applicable_typst_blocks as _get_applicable_typst_blocks,
)

from .branding_profiles import (
	get_branding_profile_presentation_settings as _get_branding_profile_presentation_settings,
)
from .branding_profiles import get_branding_profiles as _get_branding_profiles
from .compile import compile_typst as _compile_typst
from .compile import get_typst_local_fonts as _get_typst_local_fonts
from .docs import get_formatted_doc as _get_formatted_doc
from .document_codes import generate_document_code as _generate_document_code
from .document_codes import resolve_document_code as _resolve_document_code
from .fiscal_credentials import get_fiscal_credential_status as _get_fiscal_credential_status
from .formats import check_import_conflicts as _check_import_conflicts
from .formats import export_crispy_format as _export_crispy_format
from .formats import get_available_formats as _get_available_formats
from .formats import get_builder_mode as _get_builder_mode
from .formats import get_crispy_format as _get_crispy_format
from .formats import get_crispy_formats_for_doctype as _get_crispy_formats_for_doctype
from .formats import get_default_doctypes as _get_default_doctypes
from .formats import get_default_report_builder_config as _get_default_report_builder_config
from .formats import get_reports_without_custom_html as _get_reports_without_custom_html
from .formats import import_crispy_format as _import_crispy_format
from .issued_documents import create_issued_document_snapshot as _create_issued_document_snapshot
from .issued_documents import get_issued_document as _get_issued_document
from .issued_documents import get_issued_document_by_token as _get_issued_document_by_token
from .issued_documents import verify_issued_document_token as _verify_issued_document_token
from .parity import run_report_template_parity_check as _run_report_template_parity_check
from .qr_regulatory_profiles import get_qr_regulatory_profile as _get_qr_regulatory_profile
from .qr_regulatory_profiles import get_qr_regulatory_profiles as _get_qr_regulatory_profiles
from .reports import compile_report_preview as _compile_report_preview
from .reports import generate_report_pdf as _generate_report_pdf
from .reports import get_report_typst_source as _get_report_typst_source
from .reports import get_sample_report_data as _get_sample_report_data
from .security import enforce_rate_limit, ensure_doctype_read_permission

JSONDict = dict[str, Any]


def _normalize_rpc_list(value: Any) -> Any:
	if not isinstance(value, str):
		return value
	clean = value.strip()
	if not clean.startswith("["):
		return value
	try:
		return json.loads(clean)
	except json.JSONDecodeError:
		return value


@frappe.whitelist()
def get_typst_local_fonts() -> list[str]:
	return _get_typst_local_fonts()


@frappe.whitelist()
def get_applicable_typst_blocks(
	doctype: str,
	query: str | None = None,
	category: str | None = None,
) -> list[JSONDict]:
	if not frappe.has_permission("Crispy Typst Block", "read"):
		frappe.throw(_("Not permitted to read Crispy Typst Blocks."), frappe.PermissionError)

	rows = _get_applicable_typst_blocks(doctype, enabled_only=True, category=category)
	search = (query or "").strip().lower()
	if not search:
		return rows

	def matches(row: JSONDict) -> bool:
		values = [
			row.get("name"),
			row.get("block_name"),
			row.get("block_key"),
			row.get("category"),
			row.get("description"),
		]
		return any(search in str(value or "").lower() for value in values)

	return [row for row in rows if matches(row)]


@frappe.whitelist()
def compile_typst(
	typst_source: str,
	output_format: str = "svg",
	pdf_standard: str | None = None,
	asset_files: Any = None,
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
		frappe.throw(_("Deprecated params are not supported. Use asset_files only."))
	if filtered_kwargs:
		frappe.throw(
			_("Unsupported compile_typst params: {0}").format(", ".join(sorted(filtered_kwargs.keys())))
		)
	return _compile_typst(
		typst_source,
		output_format=output_format,
		pdf_standard=pdf_standard,
		asset_files=_normalize_rpc_list(asset_files),
		chart_svg=chart_svg,
		qr_data=qr_data,
		qr_filename=qr_filename,
		output_filename=output_filename,
		return_url=return_url,
	)


@frappe.whitelist()
def get_formatted_doc(doctype: str, name: str, qr_source_mode: str | None = None) -> JSONDict:
	return _get_formatted_doc(doctype, name, qr_source_mode=qr_source_mode)


@frappe.whitelist()
def get_crispy_formats_for_doctype(doctype: str) -> list[dict[str, str]]:
	ensure_doctype_read_permission("Crispy Format")
	enforce_rate_limit("get_crispy_formats_for_doctype", limit=120, window_seconds=60)
	return _get_crispy_formats_for_doctype(doctype)


@frappe.whitelist()
def get_crispy_format(name: str) -> JSONDict:
	return _get_crispy_format(name)


@frappe.whitelist()
def get_default_doctypes() -> list[str]:
	ensure_doctype_read_permission("Crispy Format")
	enforce_rate_limit("get_default_doctypes", limit=120, window_seconds=60)
	return _get_default_doctypes()


@frappe.whitelist()
def get_default_report_builder_config(generic_report_type: str | None = None) -> JSONDict:
	return _get_default_report_builder_config(generic_report_type)


@frappe.whitelist()
def get_branding_profiles(company: str | None = None) -> list[JSONDict]:
	enforce_rate_limit("get_branding_profiles", limit=120, window_seconds=60)
	return _get_branding_profiles(company=company)


@frappe.whitelist()
def get_branding_profile_presentation_settings(name: str) -> JSONDict:
	return _get_branding_profile_presentation_settings(name)


@frappe.whitelist()
def generate_report_pdf(
	report: str,
	filters: JSONDict | str | None = None,
	format_name: str | None = None,
	orientation: str = "landscape",
	include_filters: int = 0,
	column_config: list[JSONDict] | str | None = None,
) -> JSONDict:
	report_key = frappe.scrub(str(report or "unknown"))
	enforce_rate_limit("generate_report_pdf", limit=8, window_seconds=60)
	enforce_rate_limit(f"generate_report_pdf:{report_key}", limit=4, window_seconds=60)
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
	presentation_settings: JSONDict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	typst_code_override: str | None = None,
	preview_data: JSONDict | str | None = None,
	limit: int = 50,
) -> JSONDict:
	enforce_rate_limit("get_report_typst_source", limit=60, window_seconds=60)
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
		presentation_settings=presentation_settings,
		chart_svg=chart_svg,
		typst_preamble_override=typst_preamble_override,
		typst_code_override=typst_code_override,
		preview_data=preview_data,
		limit=limit,
	)


@frappe.whitelist()
def compile_report_preview(
	report: str,
	format_name: str,
	filters: JSONDict | str | None = None,
	column_config: list[JSONDict] | str | None = None,
	include_filters: int = 0,
	include_summary: int = 1,
	include_total_row: int = 1,
	include_chart: int = 1,
	orientation: str | None = None,
	presentation_settings: JSONDict | str | None = None,
	chart_svg: str | None = None,
	typst_preamble_override: str | None = None,
	typst_code_override: str | None = None,
	preview_data: JSONDict | str | None = None,
	limit: int = 50,
	asset_files: list[str] | str | None = None,
) -> JSONDict:
	enforce_rate_limit("compile_report_preview", limit=60, window_seconds=60)
	return _compile_report_preview(
		report=report,
		format_name=format_name,
		filters=filters,
		column_config=column_config,
		include_filters=include_filters,
		include_summary=include_summary,
		include_total_row=include_total_row,
		include_chart=include_chart,
		orientation=orientation,
		presentation_settings=presentation_settings,
		chart_svg=chart_svg,
		typst_preamble_override=typst_preamble_override,
		typst_code_override=typst_code_override,
		preview_data=preview_data,
		limit=limit,
		asset_files=_normalize_rpc_list(asset_files),
	)


@frappe.whitelist()
def get_sample_report_data(report: str, filters: JSONDict | str | None = None, limit: int = 50) -> JSONDict:
	enforce_rate_limit("get_sample_report_data", limit=60, window_seconds=60)
	return _get_sample_report_data(report, filters=filters, limit=limit)


@frappe.whitelist()
def resolve_document_code(
	doctype: str,
	name: str,
	code_purpose: str = "Regulatory",
	environment: str = "Production",
	document_role: str | None = None,
	company: str | None = None,
	profile_name: str | None = None,
) -> JSONDict:
	enforce_rate_limit("resolve_document_code", limit=60, window_seconds=60)
	return _resolve_document_code(
		doctype=doctype,
		name=name,
		code_purpose=code_purpose,
		environment=environment,
		document_role=document_role,
		company=company,
		profile_name=profile_name,
	)


@frappe.whitelist()
def generate_document_code(
	doctype: str,
	name: str,
	code_purpose: str = "Regulatory",
	environment: str = "Production",
	document_role: str | None = None,
	company: str | None = None,
	profile_name: str | None = None,
) -> JSONDict:
	enforce_rate_limit("generate_document_code", limit=30, window_seconds=60)
	return _generate_document_code(
		doctype=doctype,
		name=name,
		code_purpose=code_purpose,
		environment=environment,
		document_role=document_role,
		company=company,
		profile_name=profile_name,
	)


@frappe.whitelist()
def get_fiscal_credential_status(
	company: str,
	regulatory_profile: str,
	environment: str = "Production",
	authority_code: str | None = None,
) -> JSONDict:
	return _get_fiscal_credential_status(
		company=company,
		regulatory_profile=regulatory_profile,
		environment=environment,
		authority_code=authority_code,
	)


@frappe.whitelist()
def get_qr_regulatory_profiles(
	country: str | None = None,
	authority_code: str | None = None,
	enabled_only: int | bool = 1,
) -> list[JSONDict]:
	enforce_rate_limit("get_qr_regulatory_profiles", limit=120, window_seconds=60)
	return _get_qr_regulatory_profiles(
		country=country,
		authority_code=authority_code,
		enabled_only=enabled_only,
	)


@frappe.whitelist()
def get_qr_regulatory_profile(name: str) -> JSONDict:
	return _get_qr_regulatory_profile(name)


@frappe.whitelist()
def get_issued_document(name: str) -> JSONDict:
	enforce_rate_limit("get_issued_document", limit=120, window_seconds=60)
	return _get_issued_document(name)


@frappe.whitelist()
def get_issued_document_by_token(verification_token: str) -> JSONDict:
	enforce_rate_limit("get_issued_document_by_token", limit=120, window_seconds=60)
	return _get_issued_document_by_token(verification_token)


@frappe.whitelist()
def verify_issued_document_token(verification_token: str) -> JSONDict:
	enforce_rate_limit("verify_issued_document_token", limit=120, window_seconds=60)
	return _verify_issued_document_token(verification_token)


@frappe.whitelist()
def create_issued_document_snapshot(
	source_doctype: str,
	source_docname: str,
	crispy_format: str,
) -> JSONDict:
	enforce_rate_limit("create_issued_document_snapshot", limit=20, window_seconds=60)
	return _create_issued_document_snapshot(
		source_doctype=source_doctype,
		source_docname=source_docname,
		crispy_format=crispy_format,
	)


@frappe.whitelist()
def run_report_template_parity_check(
	report: str,
	format_name: str,
	legacy_template_path: str | None = None,
	filters: JSONDict | str | None = None,
) -> JSONDict:
	enforce_rate_limit("run_report_template_parity_check", limit=20, window_seconds=60)
	return _run_report_template_parity_check(
		report=report,
		format_name=format_name,
		legacy_template_path=legacy_template_path,
		filters=filters,
	)


__all__ = [
	"check_import_conflicts",
	"compile_report_preview",
	"compile_typst",
	"create_issued_document_snapshot",
	"export_crispy_format",
	"generate_document_code",
	"generate_report_pdf",
	"get_applicable_typst_blocks",
	"get_available_formats",
	"get_branding_profile_presentation_settings",
	"get_branding_profiles",
	"get_builder_mode",
	"get_crispy_format",
	"get_crispy_formats_for_doctype",
	"get_default_doctypes",
	"get_default_report_builder_config",
	"get_fiscal_credential_status",
	"get_formatted_doc",
	"get_issued_document",
	"get_issued_document_by_token",
	"get_qr_regulatory_profile",
	"get_qr_regulatory_profiles",
	"get_report_typst_source",
	"get_reports_without_custom_html",
	"get_sample_report_data",
	"get_typst_local_fonts",
	"import_crispy_format",
	"resolve_document_code",
	"run_report_template_parity_check",
	"verify_issued_document_token",
]
