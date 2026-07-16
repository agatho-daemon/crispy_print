import json
from typing import Any

import frappe
from frappe import _

from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	get_applicable_typst_blocks as _get_applicable_typst_blocks,
)
from crispy_print.report_renderers import get_renderer_metadata as _get_renderer_metadata
from crispy_print.report_renderers import infer_report_renderer

from .branding_profiles import (
	get_branding_profile_presentation_settings as _get_branding_profile_presentation_settings,
)
from .branding_profiles import get_branding_profiles as _get_branding_profiles
from .branding_profiles import get_letterhead_options as _get_letterhead_options
from .compile import compile_typst as _compile_typst
from .compile import get_typst_font_faces as _get_typst_font_faces
from .compile import get_typst_local_fonts as _get_typst_local_fonts
from .docs import get_formatted_doc as _get_formatted_doc
from .document_codes import generate_document_code as _generate_document_code
from .document_codes import resolve_document_code as _resolve_document_code
from .fiscal_credentials import get_fiscal_credential_status as _get_fiscal_credential_status
from .formats import check_import_conflicts as _check_import_conflicts
from .formats import duplicate_crispy_format_for_company as _duplicate_crispy_format_for_company
from .formats import export_crispy_format as _export_crispy_format
from .formats import get_available_formats as _get_available_formats
from .formats import get_builder_mode as _get_builder_mode
from .formats import get_crispy_format as _get_crispy_format
from .formats import get_crispy_formats_for_doctype as _get_crispy_formats_for_doctype
from .formats import get_default_doctypes as _get_default_doctypes
from .formats import get_default_report_builder_config as _get_default_report_builder_config
from .formats import get_report_renderer_catalog as _get_report_renderer_catalog
from .formats import import_crispy_format as _import_crispy_format
from .images import get_private_image_files as _get_private_image_files
from .issued_documents import add_issued_document_trust_event as _add_issued_document_trust_event
from .issued_documents import cancel_issued_document as _cancel_issued_document
from .issued_documents import create_issued_document_snapshot as _create_issued_document_snapshot
from .issued_documents import get_issued_document as _get_issued_document
from .issued_documents import get_issued_document_audit_events as _get_issued_document_audit_events
from .issued_documents import get_issued_document_by_token as _get_issued_document_by_token
from .issued_documents import get_issued_documents as _get_issued_documents
from .issued_documents import (
	record_issued_document_integrity_check as _record_issued_document_integrity_check,
)
from .issued_documents import render_issued_document_pdf as _render_issued_document_pdf
from .issued_documents import revoke_issued_document as _revoke_issued_document
from .issued_documents import supersede_issued_document as _supersede_issued_document
from .issued_documents import verify_issued_document_token as _verify_issued_document_token
from .parity import run_report_template_parity_check as _run_report_template_parity_check
from .qr_field_registry import get_qr_business_field_set as _get_qr_business_field_set
from .qr_field_registry import get_qr_field_registry_metadata as _get_qr_field_registry_metadata
from .qr_field_registry import get_qr_registry_fields as _get_qr_registry_fields
from .qr_regulatory_profiles import get_qr_regulatory_profile as _get_qr_regulatory_profile
from .qr_regulatory_profiles import get_qr_regulatory_profiles as _get_qr_regulatory_profiles
from .reports import compile_report_preview as _compile_report_preview
from .reports import generate_report_pdf as _generate_report_pdf
from .reports import get_report_typst_source as _get_report_typst_source
from .reports import get_sample_report_data as _get_sample_report_data
from .sample_formats import create_format_from_sample as _create_format_from_sample
from .sample_formats import get_sample_format as _get_sample_format
from .sample_formats import list_sample_formats as _list_sample_formats
from .security import endpoint_policy, enforce_rate_limit, ensure_doctype_read_permission
from .templates import duplicate_crispy_template_for_company as _duplicate_crispy_template_for_company
from .templates import (
	get_active_crispy_templates_for_document as _get_active_crispy_templates_for_document,
)
from .templates import get_active_crispy_templates_for_render as _get_active_crispy_templates_for_render
from .templates import get_crispy_template_publish_preview as _get_crispy_template_publish_preview
from .templates import get_resolved_crispy_template_for_document as _get_resolved_crispy_template_for_document
from .templates import get_resolved_crispy_template_for_render as _get_resolved_crispy_template_for_render
from .templates import publish_template_from_crispy_format as _publish_template_from_crispy_format

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
@endpoint_policy(delegated=True, exempt_reason="Compile module enforces Typst permission and rate limit.")
def get_typst_local_fonts() -> list[str]:
	return _get_typst_local_fonts()


@frappe.whitelist()
@endpoint_policy(delegated=True, exempt_reason="Compile module enforces Typst permission and rate limit.")
def get_typst_font_faces() -> list[JSONDict]:
	return _get_typst_font_faces()


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_applicable_typst_blocks",
	limit=120,
	window_seconds=60,
	permissions=(("Crispy Typst Block", "read"),),
)
def get_applicable_typst_blocks(
	doctype: str,
	query: str | None = None,
	category: str | None = None,
	company: str | None = None,
) -> list[JSONDict]:
	if not frappe.has_permission("Crispy Typst Block", "read"):
		frappe.throw(_("Not permitted to read Crispy Typst Blocks."), frappe.PermissionError)

	rows = _get_applicable_typst_blocks(
		doctype,
		enabled_only=True,
		category=category,
		company=company,
	)
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
@endpoint_policy(
	rate_key="get_private_image_files",
	limit=120,
	window_seconds=60,
	permissions=(("File", "read"),),
)
def get_private_image_files(query: str | None = None, limit: int | None = 100) -> list[JSONDict]:
	return _get_private_image_files(query=query, limit=limit)


@frappe.whitelist()
@endpoint_policy(delegated=True, exempt_reason="Compile module enforces Typst permission and rate limit.")
def compile_typst(
	typst_source: str,
	output_format: str = "svg",
	pdf_standard: str | None = None,
	asset_files: Any = None,
	chart_svg: str | None = None,
	qr_data: str | None = None,
	qr_filename: str | None = None,
	barcode_options: JSONDict | str | None = None,
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
		barcode_options=barcode_options,
		output_filename=output_filename,
		return_url=return_url,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_formatted_doc",
	limit=60,
	window_seconds=60,
	delegated=True,
	exempt_reason="Document module checks source document read permission.",
)
def get_formatted_doc(
	doctype: str,
	name: str,
	qr_source_mode: str | None = None,
	fields: list[str] | str | None = None,
	allow_document_code_preview: int | bool = 0,
) -> JSONDict:
	return _get_formatted_doc(
		doctype,
		name,
		qr_source_mode=qr_source_mode,
		fields=fields,
		allow_document_code_preview=allow_document_code_preview,
	)


@frappe.whitelist()
@endpoint_policy(delegated=True, exempt_reason="Facade body enforces Crispy Format read and rate limit.")
def get_crispy_formats_for_doctype(
	doctype: str,
	company: str | None = None,
) -> list[dict[str, str]]:
	ensure_doctype_read_permission("Crispy Format")
	enforce_rate_limit("get_crispy_formats_for_doctype", limit=120, window_seconds=60)
	return _get_crispy_formats_for_doctype(doctype, company=company)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_crispy_format",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Format module checks selected format and source document read permissions.",
)
def get_crispy_format(
	name: str,
	company: str | None = None,
	source_doctype: str | None = None,
	source_docname: str | None = None,
	report_filters: JSONDict | str | None = None,
) -> JSONDict:
	return _get_crispy_format(
		name,
		company=company,
		source_doctype=source_doctype,
		source_docname=source_docname,
		report_filters=report_filters,
	)


@frappe.whitelist()
@endpoint_policy(delegated=True, exempt_reason="Facade body enforces Crispy Format read and rate limit.")
def get_default_doctypes() -> list[str]:
	ensure_doctype_read_permission("Crispy Format")
	enforce_rate_limit("get_default_doctypes", limit=120, window_seconds=60)
	return _get_default_doctypes()


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_default_report_builder_config",
	limit=120,
	window_seconds=60,
	exempt_reason="Static builder defaults with no site data access.",
)
def get_default_report_builder_config(report_renderer: str | None = None) -> JSONDict:
	return _get_default_report_builder_config(report_renderer)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_report_renderer_metadata",
	limit=120,
	window_seconds=60,
	permissions=(("Crispy Format", "read"),),
)
def get_report_renderer_metadata(format_name: str) -> JSONDict:
	doc = frappe.get_doc("Crispy Format", format_name)
	doc.check_permission("read")
	metadata = _get_renderer_metadata(doc.report_renderer, doc.report_source_fingerprint)
	if doc.report_scope == "Selected Reports":
		metadata["preview_candidates"] = [
			row.report for row in (doc.report or []) if row.report and not row.disabled
		]
	else:
		reports = frappe.get_list(
			"Report",
			filters={"disabled": 0, "report_type": ["in", ["Script Report", "Query Report"]]},
			pluck="name",
			order_by="name asc",
		)
		metadata["preview_candidates"] = [
			report for report in reports if infer_report_renderer(report) == doc.report_renderer
		]
	return metadata


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; Branding module uses permission-aware list."
)
def get_branding_profiles(company: str | None = None) -> list[JSONDict]:
	enforce_rate_limit("get_branding_profiles", limit=120, window_seconds=60)
	return _get_branding_profiles(company=company)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_branding_profile_presentation_settings",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Branding module checks profile read permission.",
)
def get_branding_profile_presentation_settings(name: str) -> JSONDict:
	return _get_branding_profile_presentation_settings(name)


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; Letter Head list uses permission-aware access."
)
def get_letterhead_options(
	company: str | None = None,
	include_current: str | None = None,
) -> list[str]:
	enforce_rate_limit("get_letterhead_options", limit=120, window_seconds=60)
	return _get_letterhead_options(company=company, include_current=include_current)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces report PDF rate limits; report module checks report/format permissions.",
)
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
@endpoint_policy(
	rate_key="get_available_formats",
	limit=120,
	window_seconds=60,
	permissions=(("Crispy Format", "read"),),
)
def get_available_formats(report: str, company: str | None = None) -> JSONDict:
	return _get_available_formats(report, company=company)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_builder_mode",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Format module checks selected format read permission.",
)
def get_builder_mode(format_name: str) -> JSONDict:
	return _get_builder_mode(format_name)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_crispy_template_publish_preview",
	limit=60,
	window_seconds=60,
	delegated=True,
	exempt_reason="Template module checks source format read/write semantics for publish preview.",
)
def get_crispy_template_publish_preview(
	source_crispy_format: str,
	version_bump: str = "minor",
	company: str | None = None,
) -> JSONDict:
	return _get_crispy_template_publish_preview(
		source_crispy_format=source_crispy_format,
		version_bump=version_bump,
		company=company,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="publish_template_from_crispy_format",
	limit=20,
	window_seconds=60,
	delegated=True,
	exempt_reason="Template controller checks source format read/write permissions.",
)
def publish_template_from_crispy_format(
	source_crispy_format: str,
	version_bump: str = "minor",
	make_active: int | bool = 1,
	effective_from: str | None = None,
	notes: str | None = None,
	company: str | None = None,
) -> JSONDict:
	return _publish_template_from_crispy_format(
		source_crispy_format=source_crispy_format,
		version_bump=version_bump,
		make_active=make_active,
		effective_from=effective_from,
		notes=notes,
		company=company,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; format module checks source read/create/target company.",
)
def duplicate_crispy_format_for_company(
	source_name: str,
	target_company: str,
	set_default: int | bool = 0,
	name: str | None = None,
	name_strategy: str = "copy",
) -> JSONDict:
	enforce_rate_limit("duplicate_crispy_format_for_company", limit=20, window_seconds=60)
	return _duplicate_crispy_format_for_company(
		source_name=source_name,
		target_company=target_company,
		set_default=set_default,
		name=name,
		name_strategy=name_strategy,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; template module checks source permissions and target company.",
)
def duplicate_crispy_template_for_company(
	source_template: str,
	target_company: str,
	clone_mode: str = "snapshot",
	make_active: int | bool = 0,
	version_bump: str = "minor",
) -> JSONDict:
	enforce_rate_limit("duplicate_crispy_template_for_company", limit=12, window_seconds=60)
	return _duplicate_crispy_template_for_company(
		source_template=source_template,
		target_company=target_company,
		clone_mode=clone_mode,
		make_active=make_active,
		version_bump=version_bump,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_active_crispy_templates_for_document",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Template module checks source document and Crispy Template read permissions.",
)
def get_active_crispy_templates_for_document(
	source_doctype: str,
	source_docname: str | None = None,
	company: str | None = None,
) -> list[JSONDict]:
	return _get_active_crispy_templates_for_document(
		source_doctype=source_doctype,
		source_docname=source_docname,
		company=company,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_active_crispy_templates_for_render",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Template module checks render source and Crispy Template read permissions.",
)
def get_active_crispy_templates_for_render(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
) -> list[JSONDict]:
	return _get_active_crispy_templates_for_render(
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_report=source_report,
		source_contract=source_contract,
		company=company,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_resolved_crispy_template_for_document",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Template module checks source document and Crispy Template read permissions.",
)
def get_resolved_crispy_template_for_document(
	source_doctype: str,
	source_docname: str | None = None,
	company: str | None = None,
	template: str | None = None,
	template_name: str | None = None,
) -> JSONDict:
	return _get_resolved_crispy_template_for_document(
		source_doctype=source_doctype,
		source_docname=source_docname,
		company=company,
		template=template,
		template_name=template_name,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_resolved_crispy_template_for_render",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="Template module checks render source and Crispy Template read permissions.",
)
def get_resolved_crispy_template_for_render(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
	template: str | None = None,
	template_name: str | None = None,
) -> JSONDict:
	return _get_resolved_crispy_template_for_render(
		source_doctype=source_doctype,
		source_docname=source_docname,
		source_report=source_report,
		source_contract=source_contract,
		company=company,
		template=template,
		template_name=template_name,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="export_crispy_format",
	limit=60,
	window_seconds=60,
	delegated=True,
	exempt_reason="Format module checks selected format read permission.",
)
def export_crispy_format(name: str) -> JSONDict:
	return _export_crispy_format(name)


@frappe.whitelist()
@endpoint_policy(
	rate_key="check_import_conflicts",
	limit=60,
	window_seconds=60,
	permissions=(("Crispy Format", "create"),),
)
def check_import_conflicts(payload: JSONDict | str) -> JSONDict:
	return _check_import_conflicts(payload)


@frappe.whitelist()
@endpoint_policy(
	rate_key="import_crispy_format",
	limit=20,
	window_seconds=60,
	delegated=True,
	exempt_reason="Format module checks create/write permissions according to conflict action.",
)
def import_crispy_format(payload: JSONDict | str, on_conflict: str = "copy") -> JSONDict:
	return _import_crispy_format(payload, on_conflict=on_conflict)


@frappe.whitelist()
@endpoint_policy(rate_key="list_sample_formats", limit=120, window_seconds=60)
def list_sample_formats() -> list[JSONDict]:
	return _list_sample_formats()


@frappe.whitelist()
@endpoint_policy(rate_key="get_sample_format", limit=120, window_seconds=60)
def get_sample_format(sample_id: str) -> JSONDict:
	return _get_sample_format(sample_id)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; sample module checks create permission and target company.",
)
def create_format_from_sample(
	sample_id: str,
	company: str,
	name: str | None = None,
	set_default: int | bool = 0,
) -> JSONDict:
	enforce_rate_limit("create_format_from_sample", limit=20, window_seconds=60)
	return _create_format_from_sample(
		sample_id=sample_id,
		company=company,
		name=name,
		set_default=set_default,
	)


@frappe.whitelist()
@endpoint_policy(
	rate_key="get_report_renderer_catalog",
	limit=120,
	window_seconds=60,
	permissions=(("Report", "read"),),
)
def get_report_renderer_catalog() -> JSONDict:
	return _get_report_renderer_catalog()


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; report module checks report/format permissions."
)
def get_report_typst_source(
	report: str,
	format_name: str | None = None,
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
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; report module checks report/format permissions."
)
def compile_report_preview(
	report: str,
	format_name: str | None = None,
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
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; report module checks report permission and internal report rate.",
)
def get_sample_report_data(report: str, filters: JSONDict | str | None = None, limit: int = 50) -> JSONDict:
	enforce_rate_limit("get_sample_report_data", limit=60, window_seconds=60)
	return _get_sample_report_data(report, filters=filters, limit=limit)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; document-code module checks source document read permission.",
)
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
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; document-code module checks source document read permission.",
)
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
@endpoint_policy(
	rate_key="get_fiscal_credential_status",
	limit=120,
	window_seconds=60,
	permissions=(("Crispy Fiscal Credential", "read"),),
)
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
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; QR profile module uses permission-aware list."
)
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
@endpoint_policy(
	rate_key="get_qr_regulatory_profile",
	limit=120,
	window_seconds=60,
	delegated=True,
	exempt_reason="QR profile module checks selected profile read permission.",
)
def get_qr_regulatory_profile(name: str) -> JSONDict:
	return _get_qr_regulatory_profile(name)


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; registry metadata is app-owned static data."
)
def get_qr_field_registry_metadata() -> JSONDict:
	enforce_rate_limit("get_qr_field_registry_metadata", limit=120, window_seconds=60)
	return _get_qr_field_registry_metadata()


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; registry fields are app-owned static data."
)
def get_qr_registry_fields(
	doctype: str,
	authority_code: str | None = None,
	include_business_fields: int | bool = 1,
) -> JSONDict:
	enforce_rate_limit("get_qr_registry_fields", limit=120, window_seconds=60)
	return _get_qr_registry_fields(
		doctype=doctype,
		authority_code=authority_code,
		include_business_fields=include_business_fields,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; business field sets are app-owned static data."
)
def get_qr_business_field_set(key: str) -> JSONDict:
	enforce_rate_limit("get_qr_business_field_set", limit=120, window_seconds=60)
	return _get_qr_business_field_set(key)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module checks document read permission.",
)
def get_issued_document(name: str) -> JSONDict:
	enforce_rate_limit("get_issued_document", limit=120, window_seconds=60)
	return _get_issued_document(name)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module checks DocType read permission.",
)
def get_issued_documents(
	company: str | None = None,
	issuance_status: str | None = None,
	business_status: str | None = None,
	integrity_status: str | None = None,
	limit: int = 50,
) -> list[JSONDict]:
	enforce_rate_limit("get_issued_documents", limit=120, window_seconds=60)
	return _get_issued_documents(
		company=company,
		issuance_status=issuance_status,
		business_status=business_status,
		integrity_status=integrity_status,
		limit=limit,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module checks DocType read permission.",
)
def get_issued_document_audit_events(
	company: str | None = None,
	issued_document: str | None = None,
	event_type: str | None = None,
	limit: int = 50,
) -> list[JSONDict]:
	enforce_rate_limit("get_issued_document_audit_events", limit=120, window_seconds=60)
	return _get_issued_document_audit_events(
		company=company,
		issued_document=issued_document,
		event_type=event_type,
		limit=limit,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; token lookup module returns verification-safe payload.",
)
def get_issued_document_by_token(verification_token: str) -> JSONDict:
	enforce_rate_limit("get_issued_document_by_token", limit=120, window_seconds=60)
	return _get_issued_document_by_token(verification_token)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; token verification module returns verification-safe payload.",
)
def verify_issued_document_token(verification_token: str) -> JSONDict:
	enforce_rate_limit("verify_issued_document_token", limit=120, window_seconds=60)
	return _verify_issued_document_token(verification_token)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module checks source document and format/template permissions.",
)
def create_issued_document_snapshot(
	source_doctype: str,
	source_docname: str,
	crispy_format: str | None = None,
	crispy_template: str | None = None,
	typst_source: str | None = None,
) -> JSONDict:
	enforce_rate_limit("create_issued_document_snapshot", limit=20, window_seconds=60)
	return _create_issued_document_snapshot(
		source_doctype=source_doctype,
		source_docname=source_docname,
		crispy_format=crispy_format,
		crispy_template=crispy_template,
		typst_source=typst_source,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; issued-document module checks read permission."
)
def render_issued_document_pdf(name: str) -> JSONDict:
	enforce_rate_limit("render_issued_document_pdf", limit=30, window_seconds=60)
	return _render_issued_document_pdf(name)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module requires manager permission.",
)
def revoke_issued_document(name: str, reason: str | None = None) -> JSONDict:
	enforce_rate_limit("revoke_issued_document", limit=20, window_seconds=60)
	return _revoke_issued_document(name, reason=reason)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module requires manager permission.",
)
def cancel_issued_document(name: str, reason: str | None = None) -> JSONDict:
	enforce_rate_limit("cancel_issued_document", limit=20, window_seconds=60)
	return _cancel_issued_document(name, reason=reason)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module requires manager permission.",
)
def supersede_issued_document(
	name: str,
	superseded_by: str,
	reason: str | None = None,
) -> JSONDict:
	enforce_rate_limit("supersede_issued_document", limit=20, window_seconds=60)
	return _supersede_issued_document(name, superseded_by=superseded_by, reason=reason)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module requires manager permission.",
)
def record_issued_document_integrity_check(
	name: str,
	integrity_status: str,
	message: str | None = None,
) -> JSONDict:
	enforce_rate_limit("record_issued_document_integrity_check", limit=30, window_seconds=60)
	return _record_issued_document_integrity_check(
		name,
		integrity_status=integrity_status,
		message=message,
	)


@frappe.whitelist()
@endpoint_policy(
	delegated=True,
	exempt_reason="Facade body enforces rate; issued-document module requires manager permission.",
)
def add_issued_document_trust_event(name: str, event: JSONDict | None = None, **values: Any) -> JSONDict:
	enforce_rate_limit("add_issued_document_trust_event", limit=60, window_seconds=60)
	return _add_issued_document_trust_event(name, event=event, **values)


@frappe.whitelist()
@endpoint_policy(
	delegated=True, exempt_reason="Facade body enforces rate; parity module requires manager permission."
)
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
	"add_issued_document_trust_event",
	"cancel_issued_document",
	"check_import_conflicts",
	"compile_report_preview",
	"compile_typst",
	"create_format_from_sample",
	"create_issued_document_snapshot",
	"export_crispy_format",
	"generate_document_code",
	"generate_report_pdf",
	"get_active_crispy_templates_for_document",
	"get_active_crispy_templates_for_render",
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
	"get_issued_document_audit_events",
	"get_issued_document_by_token",
	"get_issued_documents",
	"get_letterhead_options",
	"get_qr_business_field_set",
	"get_qr_field_registry_metadata",
	"get_qr_registry_fields",
	"get_qr_regulatory_profile",
	"get_qr_regulatory_profiles",
	"get_report_renderer_catalog",
	"get_report_renderer_metadata",
	"get_report_typst_source",
	"get_resolved_crispy_template_for_document",
	"get_resolved_crispy_template_for_render",
	"get_sample_format",
	"get_sample_report_data",
	"get_typst_font_faces",
	"get_typst_local_fonts",
	"import_crispy_format",
	"list_sample_formats",
	"record_issued_document_integrity_check",
	"render_issued_document_pdf",
	"resolve_document_code",
	"revoke_issued_document",
	"run_report_template_parity_check",
	"supersede_issued_document",
	"verify_issued_document_token",
]
