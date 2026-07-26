# Known Limitations

_Part of the [Crispy Print documentation](README.md)._

As a **beta release**, Crispy Print has several known limitations:

### Beta Installation and Compatibility

- **Fresh Install Only**: Beta 2 has no supported in-place upgrade path from Beta 1 or any alpha release. Install it where Crispy Print has not previously been installed.
- **No Persisted-Data Guarantee**: Database records, formats, templates, issued-document data, exports, and other persisted state may change incompatibly between beta releases. Keep earlier sites or backups when historical test data matters.

### System & Dependencies

- **Typst CLI Required**: Must be installed separately; document rendering will not work without it.
- **Node/Yarn Build Toolchain**: Development and asset builds are pinned to Node.js `24.18.0` LTS and Yarn Classic `1.22.22`.
- **Frappe v15/v16/current dev-17 Only**: Older Frappe versions are not supported. dev-17 compatibility reflects the development branch tested for this beta and should be retested before production use.
- **Server-Side Rendering**: PDF and SVG compilation happen on the server through Typst CLI.
- **Font Discovery**: Depends on bundled fonts, uploaded site fonts, system font configuration, and `TYPST_FONT_PATHS`.
- **Font Face Metadata**: Typography weight/style choices are constrained by Typst-discovered faces. If a font has unusual internal naming, verify the rendered output during beta testing.

### Layout Builder

- **Field Coverage**: Standard document fields and child tables are the main target; complex custom fields may require Raw Typst.
- **Grid Model**: The visual builder uses a constrained column layout to keep output predictable.
- **Conditional Logic**: Visual conditional visibility is not implemented yet.
- **Report Acceptance Scope**: The Beta 2 renderer architecture covers generic reports, receivables/payables, financial statements, General Ledger, and Bank Reconciliation. Comprehensive family/site acceptance is still ongoing, so every generated report PDF must be reviewed before operational or accounting use.
- **Report Family Coverage**: Known renderer mappings are curated. New or renamed ERPNext reports fall back to the generic renderer until deliberately classified and tested.
- **Upstream Report Changes**: Composite HTML/JavaScript/JSON/Python fingerprints and Report registry checks warn when reviewed Frappe/ERPNext sources change, but native Typst renderers are not automatically regenerated. A designer must review structural snapshots and representative PDFs, acknowledge the current fingerprint, and publish a new template version where required.
- **Report Edge Cases**: Dynamic columns, unusual filters, empty datasets, very wide reports, long values, multiple pages, charts, totals, RTL content, and custom ERPNext modifications require report-specific testing. Advanced Raw Typst may still be necessary.
- **Native Chart Coverage (WIP)**: Lilaq rendering is limited to accounting-core bar, grouped bar, line, mixed, horizontal bar, percentage aging, and waterfall specs. Basic formats may request compatible bar, line, or single-series horizontal-bar representations, but percentage-aging and waterfall semantics cannot be overridden. Unsupported browser charts may use sanitized Frappe SVG; unsupported background charts are omitted with diagnostics.
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

- **Browser Preview**: Complete DocType and Report previews render native Typst PDF output through PDF.js with a bounded five-page canvas and selectable-text window. Full-document search and enhanced semantic screen-reader navigation are not implemented. Focused Branding Profile and Typst Block authoring specimens render sanitized SVG.
- **Image Formats**: Letterhead, logo, and asset files must use formats supported by Typst.
- **No Real-Time Collaboration**: Multiple users cannot safely edit the same format simultaneously.
- **Text Editor / HTML Fields**: HTML content is reduced to text-oriented output before rendering.
- **PDF/A Font Embedding**: PDF/A output embeds fonts, so fonts that disallow embedding/subsetting may fail or be substituted.

### Letterhead & Branding

- **Letterhead Source**: Frappe Letter Head documents and uploaded assets are supported, but full letterhead authoring remains outside Crispy Print.
- **Branding Placement**: Existing left/right logo and QR anchors remain
  physical. New start/end anchors are semantic; numeric offsets remain physical.

### Data & Compatibility

- **RTL Acceptance Scope**: DocType and managed Report builders/output share
  end-to-end direction handling for Arabic and Persian. Hebrew and Urdu are
  recognized by the generic engine but have no shipped catalogs or native
  acceptance gate. Raw Typst authors remain responsible for direction in their
  custom source.
- **Native Review Required**: Automated browser/PDF tests verify layout,
  extracted order, and font availability, but native Arabic/Persian linguistic
  and regulatory approval is still required before production release.
- **No Jinja Support**: Crispy Print uses structured layouts and Typst, not Frappe Print Format Jinja templates.
- **No Python Scripts**: Formats do not execute custom Python code.
- **Import/Export Scope**: Format import/export exists, but cross-site migration should still be tested carefully in beta.
- **Draft Format Versioning**: The builder does not keep a history of draft format edits, but published **Crispy Templates** are versioned, frozen render snapshots.

### Performance

- **First Compile Cost**: Initial Typst compilation can take longer than cached repeat previews.
- **PDF Preview Size**: Complete DocType and Report previews retain only five PDF.js canvas and text layers, with zero-sized offscreen canvas placeholders, but exceptionally large PDFs still consume browser memory while their document structure, text/font data, and visible pages are loaded.
- **Font Loading**: Large custom font collections may slow down font discovery.
- **Report Preview Cost**: **Run Preview** executes and snapshots the complete ERPNext result once; Builder-only changes reuse the snapshot but still require Typst compilation. Very large results can therefore remain expensive to compile even though the report is not rerun.
- **Large Report Preview Rendering**: PDF.js removes the former all-pages inline-SVG insertion cost and lazily paints only the first and near-visible report pages. It materially reduces live DOM size and main-thread SVG sanitization/insertion work, but it does not make ERPNext report execution or server-side Typst compilation faster. Very large report PDFs still carry response-transfer, PDF parsing, page-metadata, and visible-canvas costs.
- **Render Timeout**: Each Typst render and font-discovery command is bounded by the configurable render timeout in Crispy Print Settings (default 60s).
