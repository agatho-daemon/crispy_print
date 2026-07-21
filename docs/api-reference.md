# Crispy Print API Reference (v1)

All endpoints below are whitelisted and callable through `frappe.call`.

Use method path: `crispy_print.api.v1.<endpoint>`

The `api.v1` module is a stable compatibility facade. Each whitelisted endpoint declares
an explicit facade policy for rate limiting, permission checks, delegated deeper checks,
or a documented low-risk exemption; backend tests audit that new endpoints do not skip
this policy metadata.

## Compile & Fonts

### `get_typst_local_fonts()`

- Args: none
- Returns: `list[str]`
- Shape: `['Inter', 'Noto Sans', ...]`
- Notes: returns canonical Typst family names with bundled/uploaded filename fallbacks merged into matching families

### `get_typst_font_faces()`

- Args: none
- Returns: `list[dict]`
- Shape:

```json
[
  {
    "family": "Rajdhani",
    "styles": ["normal"],
    "weights": ["light", "regular", "medium", "semibold", "bold"],
    "faces": [
      { "label": "Regular", "style": "normal", "weight": "regular" },
      { "label": "Bold", "style": "normal", "weight": "bold" }
    ]
  }
]
```

- Notes: TTC collections are inspected face by face so embedded weights and styles are included even when the Typst family listing reports only Regular

- Notes: used by builder typography controls to restrict style/weight choices to faces Typst can resolve for the selected family

### `compile_typst(typst_source, output_format='svg', pdf_standard=None, asset_files=None, chart_svg=None, qr_data=None, qr_filename=None, barcode_options=None, output_filename=None, return_url=0)`

- Args:
  - `typst_source: str`
  - `output_format: 'svg' | 'pdf'`
  - optional `pdf_standard` (e.g. `PDF/A-2u`, `PDF/A-3u`, `PDF/A-4`, `PDF 1.7`, `PDF 2.0`)
  - optional `asset_files` list for approved site/app assets used by Typst image calls
  - optional chart/qr/barcode/output args
- Returns (svg):
  - `{ success, format: 'svg', svg_pages: string[], page_count: number }`
- Returns (pdf):
  - `{ success, format: 'pdf', pdf_data: string }`
- Notes: Raw Typst `crispy_image("filename.svg", ...)` resolves only supported uploaded private image filenames. Public paths, nested paths, traversal, URLs, unsupported extensions, and missing files are rejected.

### `get_private_image_files(query=None, limit=100)`

- Args: optional search query and result limit
- Returns: private uploaded image metadata usable by Crispy Image fields
- Notes: only supported image files in the site's private files directory are listed; uploads use Frappe's normal private File upload flow

## Doc & Formats

### `get_formatted_doc(doctype, name, qr_source_mode=None, fields=None, allow_document_code_preview=0)`

- Args:
  - `doctype: str`
  - `name: str`
  - optional `qr_source_mode: "basic" | "document_code_profile"`
  - optional `fields: list[str] | JSON string` with top-level fields and child paths such as `items.item_code`
  - optional `allow_document_code_preview: 0 | 1`
- Returns: formatted render payload
- Notes:
  - When `fields` is provided, the payload is limited to requested render fields plus safe essentials: `doctype`, `name`, `docstatus`, `modified`, and `__crispy_print_context`.
  - Child tables return only requested child columns. A top-level child-table field such as `items` keeps the legacy all-child-columns behavior for raw Typst compatibility.
  - When `fields` is provided, hidden, password, internal, and unsupported field paths are ignored instead of being copied from `doc.as_dict()`.
  - Omitting `fields` keeps the legacy broad formatted document payload for backward compatibility; new preview callers should send fields.
  - Document-code QR preview is not executed unless `qr_source_mode="document_code_profile"` and `allow_document_code_preview=1`. Preview output is limited to safe QR metadata and encoded value.

### `get_crispy_formats_for_doctype(doctype, company=None)`

- Args: `doctype: str`, optional `company: str`
- Returns: `[{ name: str, doc_type: str }]`

### `get_crispy_format(name, company=None, source_doctype=None, source_docname=None, report_filters=None)`

- Args: format name plus optional render context
- Returns: Crispy Format payload with transient render hydration

### `get_default_doctypes()`

- Args: none
- Returns: `list[str]`

### `get_builder_mode(format_name)`

- Args: `format_name: str`
- Returns: `{ mode: 'advanced' | 'basic' | 'layout' }`

### `export_crispy_format(name)`

- Args: `name: str`
- Returns: export payload dict

### `check_import_conflicts(payload)`

- Args: `payload: dict | str`
- Returns: conflict report dict

### `import_crispy_format(payload, on_conflict='copy')`

- Args: `payload: dict | str`, `on_conflict: 'copy' | 'overwrite'`
- Returns: import result dict

### `duplicate_crispy_format_for_company(source_name, target_company, set_default=0, name=None, name_strategy='copy')`

- Args: source Crispy Format, target Company, optional default flag/name/name strategy
- Returns: duplicate result payload with `name`, `source_name`, `company`, `is_default`, and `warnings`
- Notes: preserves render fields and retargets company-scoped presentation settings to the target company

### `list_sample_formats()`

- Args: none
- Returns: lightweight sample catalog cards
- Shape: `[{ id, title, description, target_type, doc_type, report_kind, tags, recommended_use, format_name }]`
- Notes: reads app-owned JSON files from `crispy_print/examples/formats/`; does not create site data

### `get_sample_format(sample_id)`

- Args: `sample_id: str`
- Returns: full export-compatible sample payload
- Notes: sample files are validated as company-neutral payloads; company-scoped data and private file paths are rejected

### `create_format_from_sample(sample_id, company, name=None, set_default=0)`

- Args: sample id, target Company, optional format name/default flag
- Returns: creation result payload with `name`, `sample_id`, `company`, `is_default`, and `warnings`
- Notes: always creates a new/copy Crispy Format for the selected company; it never overwrites an existing format and replaces the old automatic `Crispy Format` fixture workflow

## Reports

> **Status: WIP.** These interfaces support renderer development and acceptance testing. Their presence does not mean every supported ERPNext report layout has completed production acceptance testing.

### `get_report_renderer_catalog()`

- Returns: renderer definitions and permission-visible Script/Query Reports classified by renderer

### `get_report_renderer_metadata(format_name)`

- Args: `format_name: str`
- Returns: renderer metadata, curated sections, supported reports, and source fingerprint status for the selected format

### `get_default_report_builder_config(report_renderer=None)`

- Args: optional `report_renderer: str`
- Returns: report builder config dict

### `get_available_formats(report, company=None)`

- Args: `report: str`, optional `company: str`
- Returns: `{ formats, default_format, renderer }`; each format includes company, scope, renderer, layout style, default status, and compatibility status

### `get_sample_report_data(report, filters=None, limit=0, store_snapshot=0)`

- Args: `report: str`, optional `filters`, optional explicit `limit: int`; zero keeps the complete ERPNext result. Set `store_snapshot=1` for the Builder workflow.
- Returns: normalized report payload including `renderer`, `sections`, semantic row roles, `columns`, `rows`, `filters`, `report_summary`, unchanged upstream `chart`, printable `chart_spec`, and compatibility aliases. With `store_snapshot=1`, returns lightweight metadata, columns, and a user-bound `preview_snapshot_id` instead of returning all rows to the browser. The complete prepared result remains available for 15 minutes. Render-time `chart_spec.representation` records the requested, source, applied, and resolved chart kinds when a Basic format requests a compatible representation override.

### `get_report_typst_source(report, format_name=None, format_company=None, ..., preview_snapshot_id=None, limit=0)`

- Args (core):
  - `report: str`
  - optional `format_name: str`; when omitted, the caller must have Crispy Format create permission and supply `typst_code_override` for a transient unsaved preview
  - optional `format_company: str` for a transient format; a saved format always uses its own company as the authoritative report filter/render context
  - optional toggles: `include_filters`, `include_summary`, `include_total_row`, `include_chart`
  - optional overrides: `typst_preamble_override`, `typst_code_override`, `page_settings`, `preview_data`
  - optional `preview_snapshot_id` to project columns and presentation choices from an already-executed report
  - optional explicit `limit: int`; zero keeps the complete ERPNext result
- Returns: Typst source + payload metadata used for preview/printing, including `chart_render` engine/status/reason and pinned helper versions

### `compile_report_preview(report, format_name=None, format_company=None, ..., preview_snapshot_id=None, limit=0, asset_files=None, pdf_standard=None)`

- Args: same core arguments as `get_report_typst_source`, plus optional approved `asset_files`
- Returns: compiled PDF preview payload and report metadata, including native, fallback, empty, or omitted `chart_render` diagnostics. The browser decodes the PDF once and hands it to the shared lazy PDF.js viewer; it no longer receives and injects one SVG string per report page. Internally, complete normalized report data is loaded from a private temporary JSON compile input rather than embedded in the Typst source.

### `generate_report_pdf(report, filters=None, format_name=None, orientation='landscape', include_filters=0, column_config=None)`

- Args: report + filter/format options
- Returns: generated PDF response payload

### `run_report_template_parity_check(report, format_name, legacy_template_path=None, filters=None)`

- Args: report + format + optional template path/filters
- Returns: parity result dict

## Branding, Blocks & Compliance

### `get_branding_profiles(company=None)`

- Args: optional `company: str`
- Returns: available Branding Profile metadata

### `get_branding_profile_presentation_settings(name)`

- Args: `name: str`
- Returns: normalized presentation settings for the profile

### `get_letterhead_options(company=None, include_current=None)`

- Args: optional company and current Letter Head name
- Returns: selectable Letter Head names after Crispy lifecycle filtering

### `get_applicable_typst_blocks(doctype, query=None, category=None, company=None)`

- Args: `doctype: str`, optional search/category/company filters
- Returns: enabled Typst blocks applicable to the document type

### `resolve_document_code(doctype, name, code_purpose='Regulatory', environment='Production', document_role=None, company=None, profile_name=None)`

- Args: document identity plus optional profile selectors
- Returns: resolved document-code payload without necessarily issuing a new code

### `generate_document_code(doctype, name, code_purpose='Regulatory', environment='Production', document_role=None, company=None, profile_name=None)`

- Args: document identity plus optional profile selectors
- Returns: generated document-code payload

### `get_qr_regulatory_profiles(country=None, authority_code=None, enabled_only=1)`

- Args: optional country/authority filters
- Returns: available QR Regulatory Profiles

### `get_qr_regulatory_profile(name)`

- Args: `name: str`
- Returns: QR Regulatory Profile detail

### `get_fiscal_credential_status(company, regulatory_profile, environment='Production', authority_code=None)`

- Args: company, regulatory profile, environment, optional authority code
- Returns: fiscal credential availability/status payload

## Approved Templates

A Crispy Template is a frozen, versioned approved render contract published from a
Crispy Format. Resolution is company-aware, with fallback from company-specific
templates to global templates. Template list and resolution endpoints share the
same backend resolver for target matching, active/approved filtering,
effective-date checks, company fallback, and version ordering.

### `publish_template_from_crispy_format(source_crispy_format, version_bump='minor', make_active=1, effective_from=None, notes=None, company=None)`

- Args: source Crispy Format plus versioning/activation options
- Returns: published Crispy Template payload (with snapshot hash and version)

### `get_crispy_template_publish_preview(source_crispy_format, version_bump='minor', company=None)`

- Args: source Crispy Format, version bump, optional company
- Returns: preview of the template that would be published (no write)

### `duplicate_crispy_template_for_company(source_template, target_company, clone_mode='snapshot', make_active=0, version_bump='minor')`

- Args: source Crispy Template, target Company, clone mode (`snapshot` or `current_format`), activation flag, and version bump
- Returns: duplicate result payload with `source_template`, `cloned_format`, `clone_mode`, `template`, and `warnings`
- Notes: `snapshot` mode preserves the frozen template snapshot by creating a target-company Crispy Format from immutable template fields before publishing; `current_format` mode clones the template's current source format before publishing

### `get_active_crispy_templates_for_document(source_doctype, source_docname=None, company=None)`

- Args: source document identity, optional company
- Returns: `list[dict]` of active templates applicable to the document

### `get_active_crispy_templates_for_render(source_doctype=None, source_docname=None, source_report=None, source_contract=None, company=None)`

- Args: render source identity (doctype/report/contract), optional company
- Returns: `list[dict]` of active templates applicable to the render source

### `get_resolved_crispy_template_for_document(source_doctype, source_docname=None, company=None, template=None, template_name=None)`

- Args: source document identity, optional company and explicit template selector
- Returns: resolved template payload (includes `template_id`)

### `get_resolved_crispy_template_for_render(source_doctype=None, source_docname=None, source_report=None, source_contract=None, company=None, template=None, template_name=None)`

- Args: render source identity, optional company and explicit template selector
- Returns: resolved template payload (includes `template_id`)

## Issued Documents (CID)

The Crispy Issued Document registry records immutable issued snapshots linked to
frozen templates. These are permission-gated user endpoints (not public guest
verification endpoints).

### `get_issued_document(name)`

- Args: `name: str`
- Returns: full Crispy Issued Document payload for users with read permission

### `get_issued_documents(company=None, issuance_status=None, business_status=None, integrity_status=None, limit=50)`

- Args: optional status/company filters and result limit
- Returns: `list[dict]` of issued-document registry rows

### `get_issued_document_audit_events(company=None, issued_document=None, event_type=None, limit=50)`

- Args: optional company, parent issued document, event type, and limit
- Returns: `list[dict]` of trust-event audit rows

### `get_issued_document_by_token(verification_token)`

- Args: `verification_token: str`
- Returns: full Crispy Issued Document payload for users with read permission

### `verify_issued_document_token(verification_token)`

- Args: `verification_token: str`
- Returns: minimal verification summary (`exists`, `verification_status`, status fields)

### `create_issued_document_snapshot(source_doctype, source_docname, crispy_format=None, crispy_template=None)`

- Args: source document identity plus a Crispy Format and/or frozen Crispy Template
- Returns: created Crispy Issued Document payload with immutable render facts

### `cancel_issued_document(name, reason=None)`

- Args: `name: str`, optional `reason: str`
- Returns: updated issued-document payload reflecting cancelled state

### `revoke_issued_document(name, reason=None)`

- Args: `name: str`, optional `reason: str`
- Returns: updated issued-document payload reflecting revoked state

### `supersede_issued_document(name, superseded_by, reason=None)`

- Args: `name: str`, `superseded_by: str` (replacement issued document), optional `reason: str`
- Returns: updated issued-document payload reflecting supersession

### `add_issued_document_trust_event(name, event=None, **values)`

- Args: `name: str`, plus a trust-event dict (or keyword values)
- Returns: updated issued-document payload with the appended trust event

### `record_issued_document_integrity_check(name, integrity_status, message=None)`

- Args: issued document name, integrity status, optional validation message
- Returns: updated issued-document verification summary

## Notes

- API errors are returned as Frappe exceptions (`ValidationError`, etc.).
- Large report previews are intentionally truncated by `limit`.
- Deprecated direct image params such as `letterhead_image` and `logo_image` are rejected by `compile_typst`; use `asset_files`.
