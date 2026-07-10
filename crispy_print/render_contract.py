from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class RenderContractField:
	format_field: str | None = None
	template_field: str | None = None
	exported: bool = False
	import_max_bytes: int | None = None
	snapshotted: bool = False
	immutable: bool = False
	hashed_v1: bool = False
	hashed_v2: bool = False


RENDER_CONTRACT_FIELDS: tuple[RenderContractField, ...] = (
	RenderContractField("name", exported=True, import_max_bytes=140),
	RenderContractField("crispy_format_type", "crispy_format_type", True, 40, True, True, True, True),
	RenderContractField("doc_type", "source_doctype", True, 140, True, True, True, True),
	RenderContractField("report", "source_report", True, 140, True, True, True, True),
	RenderContractField("contract", "source_contract", True, 140, True, True, True, True),
	RenderContractField("company", "company", True, 140, True, True, True, True),
	RenderContractField("is_generic", exported=True),
	RenderContractField("is_advanced", exported=True),
	RenderContractField("generic_report_type", exported=True, import_max_bytes=140),
	RenderContractField("raw_typst", "raw_typst", True, 256 * 1024, True, True, True, True),
	RenderContractField("layout_json", "layout_json", True, 512 * 1024, True, True, True, True),
	RenderContractField(
		"presentation_settings",
		"presentation_settings_json",
		True,
		128 * 1024,
		True,
		True,
		True,
		True,
	),
	RenderContractField("doc_header", "doc_header", True, 128 * 1024, True, True, True, True),
	RenderContractField("doc_footer", "doc_footer", True, 128 * 1024, True, True, True, True),
	RenderContractField("typst_preamble", "typst_preamble", True, 256 * 1024, True, True, True, True),
	RenderContractField("typst_code", "typst_code", True, 512 * 1024, True, True, True, True),
	RenderContractField("default_print_language", exported=True, import_max_bytes=140),
	RenderContractField("pdf_standard", "pdf_standard", True, 40, True, True, True, True),
	RenderContractField("compact_item_print", "compact_item_print", True, 8, True, True, True, True),
	RenderContractField(
		"print_uom_after_quantity",
		"print_uom_after_quantity",
		True,
		8,
		True,
		True,
		True,
		True,
	),
	RenderContractField(
		"print_taxes_with_zero_amount",
		"print_taxes_with_zero_amount",
		True,
		8,
		True,
		True,
		True,
		True,
	),
	RenderContractField(template_field="template_name", immutable=True, hashed_v1=True, hashed_v2=True),
	RenderContractField(template_field="version", immutable=True, hashed_v1=True, hashed_v2=True),
	RenderContractField(
		template_field="source_crispy_format", immutable=True, hashed_v1=True, hashed_v2=True
	),
	RenderContractField(
		template_field="source_branding_profile", immutable=True, hashed_v1=True, hashed_v2=True
	),
	RenderContractField(template_field="typst_version", immutable=True, hashed_v1=True, hashed_v2=True),
	RenderContractField(template_field="zebra_version", immutable=True, hashed_v2=True),
	RenderContractField(template_field="barcode_symbology", immutable=True, hashed_v2=True),
	RenderContractField(template_field="snapshot_hash", immutable=True),
	RenderContractField(template_field="snapshot_hash_version", immutable=True, hashed_v2=True),
	RenderContractField(template_field="approved_by", immutable=True),
	RenderContractField(template_field="approved_at", immutable=True),
	RenderContractField(template_field="retired_by", immutable=True),
	RenderContractField(template_field="retired_at", immutable=True),
)


FORMAT_EXPORT_FIELDS = tuple(
	field.format_field for field in RENDER_CONTRACT_FIELDS if field.exported and field.format_field
)

FORMAT_IMPORT_FIELD_MAX_BYTES = {
	field.format_field: field.import_max_bytes
	for field in RENDER_CONTRACT_FIELDS
	if field.format_field and field.import_max_bytes is not None
}

TEMPLATE_SNAPSHOT_FIELD_MAP = tuple(
	(field.format_field, field.template_field)
	for field in RENDER_CONTRACT_FIELDS
	if field.snapshotted and field.format_field and field.template_field
)

TEMPLATE_IMMUTABLE_AFTER_INSERT_FIELDS = tuple(
	field.template_field for field in RENDER_CONTRACT_FIELDS if field.immutable and field.template_field
)

TEMPLATE_SNAPSHOT_HASH_FIELDS_V1 = tuple(
	field.template_field for field in RENDER_CONTRACT_FIELDS if field.hashed_v1 and field.template_field
)

TEMPLATE_SNAPSHOT_HASH_FIELDS_V2 = tuple(
	field.template_field for field in RENDER_CONTRACT_FIELDS if field.hashed_v2 and field.template_field
)


def format_data_from_doc(doc: Any) -> dict[str, Any]:
	return {field: doc.get(field) for field in FORMAT_EXPORT_FIELDS}
