# Crispy Print API Reference (v1)

All endpoints below are whitelisted and callable through `frappe.call`.

Use method path: `crispy_print.api.v1.<endpoint>`

## Compile & Fonts

### `get_typst_local_fonts()`
- Args: none
- Returns: `list[str]`
- Shape: `['Inter', 'Noto Sans', ...]`

### `compile_typst(typst_source, output_format='svg', letterhead_image=None, logo_image=None, chart_svg=None, qr_data=None, qr_filename=None, output_filename=None, return_url=0)`
- Args:
  - `typst_source: str`
  - `output_format: 'svg' | 'pdf'`
  - optional image/qr/output args
- Returns (svg):
  - `{ success, format: 'svg', svg_pages: string[], page_count: number }`
- Returns (pdf):
  - `{ success, format: 'pdf', pdf_data: string }`

## Doc & Formats

### `get_formatted_doc(doctype, name)`
- Args: `doctype: str`, `name: str`
- Returns: formatted document dict

### `get_crispy_formats_for_doctype(doctype)`
- Args: `doctype: str`
- Returns: `[{ name: str, doc_type: str }]`

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
- Args: `payload: dict | str`, `on_conflict: 'copy' | 'replace' | 'skip'`
- Returns: import result dict

## Reports

### `get_reports_without_custom_html(generic_report_type=None)`
- Args: optional `generic_report_type: str`
- Returns: `list[dict]`

### `get_default_report_builder_config(generic_report_type=None)`
- Args: optional `generic_report_type: str`
- Returns: report builder config dict

### `get_available_formats(report)`
- Args: `report: str`
- Returns: available report format metadata

### `get_sample_report_data(report, filters=None, limit=50)`
- Args: `report: str`, optional `filters`, `limit: int`
- Returns: sample report payload (`columns`, `rows`, `filters`, `report_summary`, etc.)

### `get_report_typst_source(report, format_name, ..., limit=50)`
- Args (core):
  - `report: str`
  - `format_name: str`
  - optional toggles: `include_filters`, `include_summary`, `include_total_row`, `include_chart`
  - optional overrides: `typst_preamble_override`, `typst_code_override`, `page_settings`, `preview_data`
  - `limit: int` (preview row cap)
- Returns: Typst source + payload metadata used for preview/printing

### `generate_report_pdf(report, filters=None, format_name=None, orientation='landscape', include_filters=0, column_config=None)`
- Args: report + filter/format options
- Returns: generated PDF response payload

### `run_report_template_parity_check(report, format_name, legacy_template_path=None, filters=None)`
- Args: report + format + optional template path/filters
- Returns: parity result dict

## Notes
- API errors are returned as Frappe exceptions (`ValidationError`, etc.).
- Large report previews are intentionally truncated by `limit`.
