# Known Limitations

_Part of the [Crispy Print documentation](README.md)._

As a **beta release**, Crispy Print has several known limitations:

### System & Dependencies

- **Typst CLI Required**: Must be installed separately; document rendering will not work without it.
- **Frappe v15/v16/current dev-17 Only**: Older Frappe versions are not supported. dev-17 compatibility reflects the development branch tested for this beta and should be retested before production use.
- **Server-Side Rendering**: PDF and SVG compilation happen on the server through Typst CLI.
- **Font Discovery**: Depends on bundled fonts, uploaded site fonts, system font configuration, and `TYPST_FONT_PATHS`.
- **Font Face Metadata**: Typography weight/style choices are constrained by Typst-discovered faces. If a font has unusual internal naming, verify the rendered output during beta testing.

### Layout Builder

- **Field Coverage**: Standard document fields and child tables are the main target; complex custom fields may require Raw Typst.
- **Grid Model**: The visual builder uses a constrained column layout to keep output predictable.
- **Conditional Logic**: Visual conditional visibility is not implemented yet.
- **Report Scope (WIP)**: The renderer architecture currently covers generic reports, receivables/payables, financial statements, General Ledger, and Bank Reconciliation. It has not completed comprehensive acceptance testing, so every generated report PDF must be reviewed before operational or accounting use.
- **Report Family Coverage**: Known renderer mappings are curated. New or renamed ERPNext reports fall back to the generic renderer until deliberately classified and tested.
- **Upstream Report Changes**: Source fingerprints warn when referenced Frappe/ERPNext HTML changes, but native Typst renderers are not automatically regenerated. A designer must review and approve corresponding renderer changes.
- **Report Edge Cases**: Dynamic columns, unusual filters, empty datasets, very wide reports, long values, multiple pages, charts, totals, RTL content, and custom ERPNext modifications require report-specific testing. Advanced Raw Typst may still be necessary.
- **Native Chart Coverage (WIP)**: Lilaq rendering is limited to accounting-core bar, grouped bar, line, mixed, horizontal bar, percentage aging, and waterfall specs. Unsupported browser charts may use sanitized Frappe SVG; unsupported background charts are omitted with diagnostics.
- **Contract Scope**: Contract format type exists as a foundation, but contract authoring workflows are WIP.

### Typst Integration

- **Raw Typst Mode Limitations**:
  - Requires knowledge of Typst syntax
  - Preview requires explicit recompilation
  - Syntax errors not caught until compilation
- **Raw Private Images**: Raw image helpers intentionally resolve only uploaded private files by filename; public paths, nested paths, URLs, and traversal are rejected.
- **Raw Typst Ownership**: Raw Typst mode intentionally hides builder-owned print behavior, page, typography, and table controls. Authors must define those concerns directly in Typst source.
- **QR Code Format**: QR output is SVG-based.
- **Table Styling**: Visual controls expose common table options; full Typst table control is available through Raw Typst.

### PDF Generation

- **Browser Preview**: The preview surface renders sanitized SVG; downloaded PDFs are native Typst output.
- **Image Formats**: Letterhead, logo, and asset files must use formats supported by Typst.
- **No Real-Time Collaboration**: Multiple users cannot safely edit the same format simultaneously.
- **Text Editor / HTML Fields**: HTML content is reduced to text-oriented output before rendering.
- **PDF/A Font Embedding**: PDF/A output embeds fonts, so fonts that disallow embedding/subsetting may fail or be substituted.

### Letterhead & Branding

- **Letterhead Source**: Frappe Letter Head documents and uploaded assets are supported, but full letterhead authoring remains outside Crispy Print.
- **Absolute Branding Placement**: Logo and QR offsets are explicit numeric positioning controls.

### Data & Compatibility

- **LTR Languages Only**: Builder UI and text direction currently support left-to-right languages only (English, Spanish, French, etc.). RTL support (Arabic, Hebrew) not yet implemented. Multi-language content is possible via Raw Typst Mode if document fields contain the target language data.
- **No Jinja Support**: Crispy Print uses structured layouts and Typst, not Frappe Print Format Jinja templates.
- **No Python Scripts**: Formats do not execute custom Python code.
- **Import/Export Scope**: Format import/export exists, but cross-site migration should still be tested carefully in beta.
- **Draft Format Versioning**: The builder does not keep a history of draft format edits, but published **Crispy Templates** are versioned, frozen render snapshots.

### Performance

- **First Compile Cost**: Initial Typst compilation can take longer than cached repeat previews.
- **SVG Preview Size**: Multi-page SVG previews can be memory-intensive in the browser.
- **Font Loading**: Large custom font collections may slow down font discovery.
- **Report Preview Cost**: Report previews may execute report data loading plus Typst compilation.
- **Render Timeout**: Each Typst render and font-discovery command is bounded by the configurable render timeout in Crispy Print Settings (default 60s).
