# Known Limitations

_Part of the [Crispy Print documentation](README.md)._

As an **alpha release**, Crispy Print has several known limitations:

### System & Dependencies

- **Typst CLI Required**: Must be installed separately; document rendering will not work without it.
- **Frappe v15+ Only**: Older Frappe versions are not supported.
- **Server-Side Rendering**: PDF and SVG compilation happen on the server through Typst CLI.
- **Font Discovery**: Depends on system font configuration, bundled fonts, and `TYPST_FONT_PATHS`.

### Layout Builder

- **Field Coverage**: Standard document fields and child tables are the main target; complex custom fields may require Raw Typst.
- **Grid Model**: The visual builder uses a constrained column layout to keep output predictable.
- **Conditional Logic**: Visual conditional visibility is not implemented yet.
- **Report Scope**: Report support is WIP; Basic mode covers common report patterns while complex report logic still requires Advanced Raw Typst.
- **Contract Scope**: Contract format type exists as a foundation, but contract authoring workflows are WIP.

### Typst Integration

- **Raw Typst Mode Limitations**:
  - Requires knowledge of Typst syntax
  - Preview requires explicit recompilation
  - Syntax errors not caught until compilation
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
- **Import/Export Scope**: Format import/export exists, but cross-site migration should still be tested carefully in alpha.
- **Draft Format Versioning**: The builder does not keep a history of draft format edits, but published **Crispy Templates** are versioned, frozen render snapshots.

### Performance

- **First Compile Cost**: Initial Typst compilation can take longer than cached repeat previews.
- **SVG Preview Size**: Multi-page SVG previews can be memory-intensive in the browser.
- **Font Loading**: Large custom font collections may slow down font discovery.
- **Report Preview Cost**: Report previews may execute report data loading plus Typst compilation.
- **Render Timeout**: Each Typst render and font-discovery command is bounded by the configurable render timeout in Crispy Print Settings (default 60s).
