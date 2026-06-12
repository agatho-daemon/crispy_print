# Crispy Print

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-alpha-orange)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Frappe](https://img.shields.io/badge/frappe-v15+-orange.svg)](https://frappeframework.com/)

> [!CAUTION]
> # MAJOR UPDATE
> ## This commit will break existing formats.
>
> This is due to changes in fields representation in the backend and exchange of that data between Python and TS/JS parts along with Typst translation logic. Please backup your formats before pulling this update.
>
> A migration patch is provided to convert existing formats to the new structure, but complex custom layouts may require manual adjustments in the builder after migration.
>
> After update run `bench migrate` to apply database changes and data migration. Then open each format in the builder and verify that the layout is correct. Some fields may need to be re-dragged or reconfigured due to changes in field properties and layout structure.

## Alpha 3 Testing Request

Feature work is frozen for alpha 3. Please test existing workflows and report bugs, regressions, confusing behavior, and documentation gaps.

- Test DocType print preview and PDF generation with real documents.
- Test the visual format builder: drag fields, configure tables, save, reload, reset, and export/import formats.
- Test Branding Profile Builder, including logo, letterhead, typography, margins, and QR placement.
- Test Raw Typst mode and reusable Typst blocks.
- Test QR and document-code flows where applicable. Regulatory QR support especially needs feedback from users in tax-regulated regions because the maintainer cannot validate real-world tax QR requirements locally; the maintainer's country does not currently have tax-related document QR regulations. Please test whether QR Regulatory Profiles, Fiscal Credentials, Document Code Profiles, and generated payloads can model your local authority requirements, invoice fields, environment rules, and verification expectations. If your region requires additional fields for QR generation, please report the required field names, data types, source documents, validation rules, and example payload structure where possible.
- Test report preview and report PDF generation, but treat reports as **WIP**. Report support is still being stabilized and may change before beta. Contract support is also **WIP**.
- Include Frappe version, Typst version, browser, console errors, server traceback, and reproduction steps when opening issues.

> [!NOTE]
> This README describes the current alpha architecture at a high level. For exact migration details and edge-case behavior, prefer the checked-in patches and tests as the source of truth.

## Project Status

**Alpha / Work in progress.** Expect frequent changes while features are still settling.

Crispy Print is a next-generation document publishing engine for ERPNext built around deterministic rendering, structured document composition, and publication-grade PDF generation. Instead of treating business documents as browser pages exported to PDF, Crispy Print treats them as formal documents with stable pagination, precise layout control, reusable branding systems, and machine-verifiable document workflows. Built on [Typst](https://typst.app/), Crispy Print moves ERP printing beyond fragile HTML print pipelines into a modern, regulation-ready publishing architecture designed for invoices, quotations, vouchers, contracts, compliance documents, technical reports, and future digital business-document ecosystems.

**Why Typst instead of HTML/CSS?** Typst provides superior PDF typography, precise layout control, and professional typesetting features that are difficult to achieve with browser-based rendering. Perfect for invoices, reports, certificates, and other print-critical documents.

## Why Crispy Print Exists

For more than a decade, ERP printing systems across the industry have largely relied on HTML templates, browser rendering, wkhtmltopdf, and print-specific CSS workarounds. While functional, these approaches introduced long-standing problems that businesses and developers learned to tolerate:

- Unstable pagination and broken page breaks
- Inconsistent PDF rendering across engines and environments
- Layout drift after browser, CSS, or wkhtmltopdf changes
- Weak typography and fragile headers/footers
- Difficult long-table handling
- Unreliable absolute positioning for regulated or pre-printed forms
- Browser-dependent output that is hard to audit or reproduce

Crispy Print is designed to solve these problems at the architecture level by converting ERP data into a structured document model and rendering it through Typst as a real document, not as a simulated browser print page.

## What Makes Crispy Print Different

- **Deterministic PDF rendering** - The same input should produce stable output without browser-layout unpredictability.
- **Publication-grade document composition** - Clean typography, consistent spacing, precise alignment, and professional business-document output.
- **Structured rendering pipeline** - ERP data is transformed into a structured print model before Typst renders the final document.
- **True document engine architecture** - Built around document composition principles rather than browser-print workflows.
- **Stable multi-page layouts** - Designed for invoices, quotations, reports, vouchers, and technical documents with predictable pagination.
- **Precise layout control** - Suitable for invoices, certificates, regulatory forms, vouchers, compliance documents, and branded output.
- **Reusable branding profiles** - Centralized company styling, typography, page setup, letterhead, logo, QR, and table presentation settings.
- **Regulatory QR abstraction** - A foundation for machine-verifiable business documents and evolving compliance requirements.
- **Modern programmable publishing stack** - Uses Typst for structured, programmable, deterministic business-document generation.
- **Designed for ERP workflows** - Focused on operational business documents rather than generic desktop publishing.

## Technical Value For Admins

- **Server-side rendering through Typst CLI** keeps document generation consistent across user browsers.
- **Permission-aware APIs** respect Frappe read/write access for documents, formats, reports, Typst blocks, and document-code workflows.
- **Controlled asset handling** restricts Typst image/file inputs to approved site/app asset roots and rejects traversal, symlinks, external URLs, and unsafe duplicate filenames.
- **Rate-limited compile and report endpoints** reduce accidental server overload during heavy preview or PDF generation.
- **Compile caching** reduces repeated Typst work for unchanged preview inputs.
- **Centralized Branding Profiles** let admins enforce company-wide visual identity without editing every print format.
- **Manual release-gating friendly** workflows use `bench build`, `bench migrate`, `bench run-tests`, and `pre-commit` without requiring CI.
- **Auditable document-code foundation** supports QR/regulatory profile configuration separately from layout templates.

## Architectural Direction

Most ERP systems approach printing as:

```text
ERP Data -> HTML -> Browser -> PDF
```

Crispy Print instead approaches printing as:

```text
ERP Data -> Structured Document Model -> Typst -> Deterministic Business Document
```

This distinction changes layout stability, rendering quality, pagination behavior, compliance extensibility, document reliability, and long-term maintainability.

## Long-Term Vision

Crispy Print is not intended to be just another print designer. The long-term goal is to provide ERPNext with modern business-document infrastructure capable of supporting:

- Publication-grade invoices, quotations, vouchers, contracts, and compliance documents
- Digitally signed PDFs and archival workflows
- Machine-verifiable business documents
- Reusable enterprise branding systems
- Compliance-ready document workflows
- Technical and engineering documentation
- Future electronic-document ecosystems

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Font Configuration](#font-configuration)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Testing](#testing)
- [Development](#development)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Deterministic Typst Rendering Pipeline** - Converts Frappe documents into structured Typst sources and server-rendered PDF/SVG output.
- **Visual Document Composition Builder** - Drag-and-drop builder for DocType print formats with sections, columns, fields, tables, images, QR elements, and custom Typst blocks.
- **Native PDF Generation** - Uses the Typst CLI for publication-grade PDF generation instead of browser printing or wkhtmltopdf.
- **Live SVG Preview** - Server-rendered preview flow for format design, document previews, and report previews without relying on browser print layout.
- **Reusable Branding Profiles** - Centralized page, typography, table, logo, letterhead, QR, and spacing settings for consistent company-wide document output.
- **Branding Profile Builder** - Dedicated visual builder for reusable presentation systems with generated Typst preview and controlled profile publication.
- **Crispy Print Workspace** - Desk workspace with grouped shortcuts and cards for builders, core format records, reusable libraries, issued documents, reports, and regulatory setup.
- **Reusable Typst Blocks** - Governed snippets for repeatable custom document fragments, scoped by category and linked DocType usage.
- **DocType-Aware Format Registry** - Crispy Format records link formats to target DocTypes, format types, branding profiles, custom builders, and generated Typst.
- **Report Format Infrastructure (WIP)** - Report-linked formats with Basic/Advanced modes, column selection, filters, chart assets, and guarded raw Typst overrides.
- **Contract Format Foundation (WIP)** - Contract format support is reserved for future structured contract publishing workflows.
- **Regulatory QR Layer** - QR Regulatory Profiles, Fiscal Credentials, and helper APIs for building machine-verifiable fiscal and compliance QR payloads.
- **Document Code Infrastructure** - Document Code Profiles and Rules for deterministic reference codes, naming patterns, and compliance-oriented document identifiers.
- **Permission-Aware API Surface** - Versioned Frappe APIs with read/write permission checks, manager-only operations, and rate limits around expensive compile paths.
- **Controlled Asset Resolution** - Typst image assets resolve through approved site/app roots with traversal, symlink, external URL, and duplicate-basename protections.
- **Compile Caching and Preview Optimizations** - Short-lived Typst compile cache, document fetch cache, report preview consolidation, lazy page bundles, SVG rerender avoidance, and bounded undo snapshots.
- **Import, Export, and Migration Support** - Structured format import/export, schema validation, backfill patches, and compatibility tests for evolving format data.
- **Typed Frontend Architecture** - Vue 3 and TypeScript modules for builder state, report state, presentation settings, Typst translation, workers, and sanitization utilities.

## Requirements

### Typst CLI (Required)

**Typst must be installed on your system before installing the app.**

#### macOS (Homebrew)
```bash
brew install typst
```

#### Linux (Ubuntu/Debian) & Windows WSL
```bash
curl -L -o typst.tar.xz https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz
tar -xf typst.tar.xz
sudo mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/
```

> **Windows users:** Frappe requires WSL. Install Typst inside your WSL environment using the Linux commands above.

Or download from [Typst Releases](https://github.com/typst/typst/releases)

#### Verify Installation
```bash
typst --version
# Should output: typst 0.11.0 or higher
```

### Frappe Compatibility

- **Frappe:** v15 or later (all Python/Node.js dependencies already satisfied)
- **Python dependency:** `segno` (installed with the app; used as the temporary Python QR-only SVG fallback)
- **Typst barcode package:** Zebra `0.1.0` is vendored with the app for QR Code and DataMatrix rendering through Typst.

## Installation

### 1. Install Typst CLI

See [Requirements](#requirements) above - Typst must be installed first.

### 2. Get and Install the App

```bash
cd ~/frappe-bench
bench get-app https://github.com/agatho-daemon/crispy_print --branch develop
bench --site your-site install-app crispy_print
bench restart
```

### 3. Verify Installation

```bash
# Check app is installed
bench --site your-site list-apps | grep crispy_print

# Test Typst integration
bench --site your-site console
```
```python
>>> from crispy_print.api.v1 import get_typst_local_fonts
>>> fonts = get_typst_local_fonts()
>>> print(len(fonts), "fonts available")
```

### 4. Build Assets (Development Only)

If you're developing the app:

```bash
cd apps/crispy_print/crispy_print/public/js
yarn install
cd ~/frappe-bench
bench build --app crispy_print
```

## Quick Start

### Workspace

After installation, open the **Crispy Print** workspace from Desk or visit:

```text
/app/crispy-print
```

The workspace groups the main builder pages, format records, branding profiles, reusable Typst blocks, issued-document tracking, report templates, and regulatory setup records. The print preview page is intentionally not shown as a standalone workspace link because it expects document or report route context.

### Creating Your First Print Format

> ⚠️ **CRITICAL:** You must set at least one format as **Default** for a DocType. The Typst print button appears on document forms **only when a default format exists** for that DocType.

Recommended setup order:

1. Create or select a **Crispy Branding Profile** for company-wide page, typography, letterhead, logo, table, and QR defaults.
2. Create a **Crispy Format** for the target DocType.
3. Design the layout in the builder, attach the branding profile, save, and test with real documents.
4. Configure document-code or regulatory QR profiles only if the document workflow needs compliance-oriented identifiers.

**Step-by-step:**

1. **Create a new format**
   - Navigate to: **Desk** → **Crispy Print** → **Crispy Formats**
   - Click **New**
   - Enter **Name** (e.g., "Sales Invoice Modern")
   - Select **DocType** (e.g., "Sales Invoice")
   - Select **Module** (e.g., "Crispy Print")
   - **Save**

2. **Set as default** ⚠️ **(Required for button to appear!)**
   - Check the **"Set as Default"** checkbox
   - **Save** again

3. **Design your layout**
   - Click **Open Builder** button
   - **Add sections:** Click "+ Add Section"
   - **Drag fields:** From right pane to layout grid
   - **Configure fields:** Click field to edit label, style, alignment
   - **Add tables:** Drag table fields (e.g., "items") for line items
   - **Adjust columns:** Split sections into 1-4 columns

4. **Configure page settings** (left sidebar)
   - **Paper Size:** A4, Letter, etc.
   - **Margins:** Adjust spacing
   - **Fonts:** Select font family
   - **Branding Profile:** Apply reusable company presentation settings
   - **Letterhead / Logo:** Use Frappe Letter Head, uploaded assets, or branding profile defaults
   - **QR / Document Code:** Enable only when the target workflow requires verification or compliance metadata

5. **Save and test**
   - Click **Save**
   - Open any document of that DocType (e.g., Sales Invoice)
   - Look for **Typst** button in toolbar (top-right)
   - Click to preview and download PDF

### Using Your Print Format

Once a default format exists, the **Typst** button appears automatically on all documents of that DocType.

**From Document:**
1. Open document (e.g., SI-2024-001)
2. Click **Typst** button in toolbar
3. Preview opens with your default format
4. Click **Download PDF**

**Direct URL:**
```
/app/crispy-print-preview/{doctype}/{docname}/{format_name}
```

## Usage

### Print Format Workflow

The typical workflow for using Crispy Print:

1. **Create or select Branding Profile** -> define reusable page, typography, table, logo, letterhead, and QR defaults
2. **Create Crispy Format** -> select format type and target DocType/report
3. **Design in builder** -> compose sections, fields, tables, assets, QR elements, and Typst blocks
4. **Save and set default** -> enable the Typst button for that DocType
5. **Open document** -> click `Typst` -> preview and download PDF

### Report Builder Workflow (Dual Mode)

For `Crispy Format Type = Report`, builder now supports two editing modes:

- **Basic mode**: non-technical controls generate a managed Typst report template
- **Advanced mode**: direct Raw Typst editing

Key behavior:

1. **Basic to Advanced** is always allowed.
2. **Advanced to Basic** only unlocks full Basic editing when the template is still Basic-managed.
3. If custom Raw Typst changes are detected, Basic opens in **read-only** with options to:
   - stay in Advanced mode, or
   - reset/regenerate the Basic template.

This keeps report editing accessible while protecting advanced customizations.

Reports are still **WIP** in alpha 3. Treat the current report flow as a stabilization target for testing, not as a final report publishing contract.

### Branding Profile Workflow

Branding Profiles centralize presentation settings that should not be duplicated across every format:

1. Create a **Crispy Branding Profile** for the company.
2. Configure page size, margins, typography, table style, letterhead, logo, and QR defaults.
3. Open the Branding Profile Builder to preview the generated Typst specimen.
4. Attach the profile to Crispy Formats that should inherit the same presentation system.

### Letterhead, Headers, And Footers

Crispy Print does not treat headers and footers as mandatory separate HTML-style blocks. That separation comes from legacy browser-print workflows where letterheads were often just images placed at the top of a page and headers/footers had to be managed as separate template regions.

Crispy Print uses Typst and SVG/PDF-oriented composition instead. A letterhead can be a full-page SVG asset sized exactly to the document page, with the header, footer, watermark, borders, legal text, brand marks, and other static elements already composed into the page background.

For many business documents, the recommended model is:

```text
Full-page SVG letterhead/background
+ structured Typst document content
+ optional dynamic QR, document code, signatures, tables, and totals
-> deterministic PDF/SVG output
```

Use separate Crispy Typst Blocks for headers, footers, or repeated sections only when those elements are dynamic, conditional, or data-driven. Static brand furniture usually belongs in the page-sized letterhead/background asset or Branding Profile.

### Document Code and Regulatory QR Workflow

Use this layer only when documents need deterministic identifiers or machine-verifiable compliance payloads:

1. Create a **Crispy QR Regulatory Profile** for the relevant authority/country behavior.
2. Add **Crispy Fiscal Credential** records for company/environment-specific identity values.
3. Configure **Crispy Document Code Profile** and related rules.
4. Use QR or document-code fields in the format or branding profile.

### Advanced: Creating Formats Without Default

You can create multiple formats for the same DocType without setting them as default:

- Access via direct URL: `/app/crispy-print-preview/{doctype}/{docname}/{format_name}`
- Or programmatically via API (see [API Reference](#api-reference))

### Common Layout Recipes

**Invoice with Logo and Table:**
1. Section 1 (2 columns): Company logo left, Invoice details right
2. Section 2: Customer information
3. Section 3: Items table (drag "items" table field)
4. Section 4: Totals (align right)
5. Section 5 (footer): Terms and conditions

**Certificate:**
1. Enable letterhead background
2. Section 1: Centered title
3. Section 2: Recipient name (large font)
4. Section 3: Certificate text
5. Section 4: Signatures (3 columns)
6. Add QR code in corner for verification

**Report with Branded Page Background:**
1. Use a Branding Profile or full-page SVG background for static report furniture
2. Section 1: Dynamic report title and date
3. Section 2: Summary metrics (4 columns)
4. Section 3: Data table
5. Section 4: Charts or dynamic visual sections where applicable

## Font Configuration

### Bundled Fonts

The app automatically includes fonts from `crispy_print/public/vendor/typst/`. These fonts are available to all print formats without additional configuration.

### System Fonts

Typst automatically discovers system fonts. On Linux, it searches standard directories like `/usr/share/fonts` and `~/.local/share/fonts`.

### Custom Fonts

To add custom fonts outside the Frappe bench:

#### Option 1: Environment Variable (Recommended)

Add to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.profile`):

```bash
export TYPST_FONT_PATHS="/path/to/custom/fonts:/another/font/path"
```

Then restart your bench:
```bash
bench restart
```

#### Option 2: Typst Font Directory

Set the dedicated Typst font path (the official Typst CLI env var; accepts
multiple colon-separated directories):

```bash
export TYPST_FONT_PATHS="$HOME/.fonts/typst"
```

Create the directory and add fonts:
```bash
mkdir -p ~/.fonts/typst
cp /path/to/font.ttf ~/.fonts/typst/
```

#### Frappe Site Configuration

You can also configure the Typst binary path in `site_config.json`:

```json
{
  "TYPST_BIN": "/usr/local/bin/typst"
}
```

### Font Discovery

The app's `get_typst_local_fonts()` API method returns all available fonts by running:
```bash
typst fonts
```

This includes:
- System fonts
- Fonts in `TYPST_FONT_PATHS`
- Bundled fonts from `crispy_print/public/vendor/typst/`

## Known Limitations

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

### Letterhead & Branding

- **Letterhead Source**: Frappe Letter Head documents and uploaded assets are supported, but full letterhead authoring remains outside Crispy Print.
- **Absolute Branding Placement**: Logo and QR offsets are explicit numeric positioning controls.

### Data & Compatibility

- **LTR Languages Only**: Builder UI and text direction currently support left-to-right languages only (English, Spanish, French, etc.). RTL support (Arabic, Hebrew) not yet implemented. Multi-language content is possible via Raw Typst Mode if document fields contain the target language data.
- **No Jinja Support**: Crispy Print uses structured layouts and Typst, not Frappe Print Format Jinja templates.
- **No Python Scripts**: Formats do not execute custom Python code.
- **Import/Export Scope**: Format import/export exists, but cross-site migration should still be tested carefully in alpha.
- **No Version History**: Previous versions of formats are not stored.

### Performance

- **First Compile Cost**: Initial Typst compilation can take longer than cached repeat previews.
- **SVG Preview Size**: Multi-page SVG previews can be memory-intensive in the browser.
- **Font Loading**: Large custom font collections may slow down font discovery.
- **Report Preview Cost**: Report previews may execute report data loading plus Typst compilation.

## Roadmap

### Future Features

The following areas are planned or under active stabilization:

- [ ] Expand Crispy Typst Block as the Typst-native replacement component layer for reusable field renderers, table blocks, address blocks, QR/regulatory blocks, headers, footers, signatures, payment sections, and custom document components
- [ ] Batch printing from list view
- [ ] Progress indicator for multi-document compilation
- [ ] Configurable batch size limits
- [ ] Multi-language format support
- [ ] Report publishing stabilization
- [ ] Contract authoring workflow
- [ ] Add Crispy Issued Document registry for immutable issued snapshots, opaque verification tokens, artifact tracking, revocation/supersession state, and future signature workflows
- [ ] Add trust-event and regulatory-submission child tables for future signature, certificate, timestamp, authority submission, and validation workflows after feedback from regulated regions
- [ ] Format version history
- [ ] PDF/A, digital-signature, and archival workflow research
- [ ] Machine-verifiable document workflow extensions

## Troubleshooting

### Typst Not Found

```
Error running typst fonts: [Errno 2] No such file or directory: 'typst'
```

**Solution:** Install Typst CLI (see Requirements section)

### Fonts Not Showing

**Check available fonts:**

```bash
typst fonts
```

From Frappe:

```bash
bench --site your-site execute crispy_print.api.v1.get_typst_local_fonts
```

If expected fonts are missing:

1. Verify the font is installed on the server running the bench.
2. Check `TYPST_FONT_PATHS` if fonts are stored outside system font directories.
3. Restart the bench after changing font paths.

### Format Not Appearing in Document

If Typst button doesn't show or format isn't available:

1. **Verify installation:**
   ```bash
   bench --site your-site list-apps | grep crispy_print
   ```

2. **Check format has layout_json:**
   - Open Crispy Format document
   - Ensure it was saved via builder (not manually created)

3. **Check default selection:**
   - At least one format must be marked default for the target DocType
   - Non-default formats can still be opened by direct preview URL

4. **Verify permissions:**
   - User needs read access to Crispy Format doctype
   - Check Role Permission Manager

5. **Check browser console** for API errors

### Compilation Errors

**"Typst compiler not found"**

Solution: Install Typst CLI (see [Requirements](#requirements))

**"Compilation timed out"**

Causes:
- Server under heavy load
- Infinite loop in raw Typst code

Solutions:
- Simplify layout
- Check raw Typst syntax

**"Letterhead image not found"**

Causes:
- Letter Head document doesn't have image field
- Image file deleted from /files/

Solution:
- Re-upload letterhead image
- Verify file path in Letter Head document

### Slow PDF Generation

If PDF generation takes more than 5 seconds:

1. Reduce layout complexity where possible.
2. Limit preview rows for reports and large child tables.
3. Compress large letterhead/logo images.
4. Check server CPU, memory, and Typst process contention.
5. Repeat the same preview once to distinguish first-compile cost from cached compile behavior.

### Preview Not Updating

If changes don't appear in preview:

1. Use the preview refresh control after Raw Typst changes.
2. Clear browser cache: `Ctrl+Shift+R` or `Cmd+Shift+R` on macOS.
3. Clear Frappe cache: `bench clear-cache && bench clear-website-cache`.
4. Rebuild app assets: `bench build --app crispy_print`.
5. Check browser console and server logs for API errors.

### Debug Mode

Enable debug logging:

```python
# In site_config.json
{
    "developer_mode": 1,
    "logging": 2
}
```

Check logs:
```bash
tail -f sites/your-site/logs/frappe.log
```

## FAQ

**Q: Can I use Crispy Print with ERPNext?**  
A: Yes. It is designed for ERPNext/Frappe document workflows such as invoices, quotations, vouchers, and other business documents.

**Q: Does it work offline?**  
A: Users need access to the Frappe server. Typst runs server-side and fonts should be installed locally on that server or bundled with the app.

**Q: Can I export formats between sites?**  
A: Yes, format import/export exists. In alpha, verify imported formats carefully because related assets, branding profiles, and compliance records may need site-specific setup.

**Q: How do I customize fonts?**  
A: Add fonts to system, set `TYPST_FONT_PATHS` environment variable, then restart bench. See [Font Configuration](#font-configuration).

**Q: Can I use custom Typst functions?**  
A: Yes, in Raw Typst mode or reusable Typst blocks. Syntax errors surface during compilation.

**Q: What's the difference from Print Designer?**  
A: Print Designer uses HTML/CSS/Jinja browser-oriented rendering. Crispy Print uses structured layouts and Typst for deterministic document rendering.

**Q: Can I mix Jinja and Typst?**  
A: No. Crispy Print uses JSON layouts, not Jinja templates.

**Q: Is it production-ready?**  
A: It is in alpha. Use it for testing and non-critical workflows until the beta readiness criteria are met.

**Q: How do I report bugs?**  
A: Open an issue on GitHub with Frappe version, Typst version, and error logs.

**Q: Does it support multi-language?**  
A: Builder UI and default flow target LTR languages. Advanced language behavior may be possible through Typst, but full multilingual/RTL support is not complete.

## Testing

This app includes comprehensive test coverage:

- **343 tests/test methods** (175 frontend + 168 backend)
- **Test frameworks:** Vitest (frontend), Frappe Test Runner (backend)

Some backend integration tests depend on site fixtures and optional Typst CLI integration settings.

## Development

### Frontend Dependencies

For TypeScript/Vue IntelliSense in VS Code and the color picker bundle (`@simonwep/pickr`):

```bash
cd apps/crispy_print/crispy_print/public/js
yarn install
```

This installs local dependencies used by the frontend bundle:
- `package.json`, `yarn.lock` - Type dependencies
- `tsconfig.json` - TypeScript configuration
- `node_modules/` - Type definitions

**Note:** Required for building.

### Building

```bash
# Build the app
bench build --app crispy_print

# Clear cache after changes
bench clear-cache && bench clear-website-cache

# Development workflow
bench start  # Run with auto-reload enabled
```

### Running Tests

**Frontend Tests (TypeScript/Vue):**

```bash
cd apps/crispy_print/crispy_print/public/js

# Run all tests
yarn test:unit

# Run specific batch
yarn test:unit:batch6

# Watch mode
yarn test:unit -- --watch
```

**Backend Tests (Python):**

```bash
# Run all tests
bench --site your-site run-tests --app crispy_print

# Run specific module
bench --site your-site run-tests --module crispy_print.tests.test_api

# Run DocType tests
bench --site your-site run-tests --doctype "Crispy Format"
```

**Test Coverage:**
- **Frontend:** 175 tests across 52 test files
- **Backend:** 168 test methods across 16 test files
- **Total:** 343 tests/test methods

Some backend integration tests depend on site fixtures and optional Typst CLI integration settings.

### Vue Component Guidelines

All Vue components use `<style scoped>` blocks. CSS is automatically extracted and inlined:

```vue
<template>
  <div class="my-component">Content</div>
</template>

<script setup lang="ts">
// Component logic with Composition API
</script>

<style scoped>
/* Scoped styles - automatically inlined */
.my-component {
  padding: 1rem;
}
</style>
```

For dynamically created DOM (e.g., `.typst-page` elements), apply styles via JavaScript:

```typescript
const page = document.createElement("div")
page.className = "typst-page"
page.style.marginBottom = "1.5rem"
page.style.boxShadow = "0 4px 12px rgba(148, 163, 184, 0.25)"
```

## Architecture

### Build System

This app uses **Frappe v15's native esbuild bundler** - no separate Vite or webpack setup required.

- **Main Builder Bundle:** `crispy_print/public/js/crispy_print.bundle.js`
- **Preview Bundle:** `crispy_print/public/js/crispy_preview.bundle.js`
- **Desk Button Bundle:** `crispy_print/public/js/report_button.bundle.js`
- **Build Command:** `bench build --app crispy_print`
- **Loading Model:** Lightweight desk hooks plus page-specific builder/preview bundles
- **Plugin:** Uses `frappe-vue-style` to automatically inline Vue SFC styles

### Current Product Structure

This alpha structure is documented here for orientation only. It is expected to move into dedicated docs before beta so the README can stay focused on installation, testing, and release status.

```
crispy_print/
├── crispy_print/
│   ├── hooks.py                          # Frappe hooks, fixtures, desk assets
│   ├── api/
│   │   └── v1/                           # Versioned backend API surface
│   │       ├── compile.py                # Typst compile, cache, asset controls
│   │       ├── docs.py                   # Document fetch and print data helpers
│   │       ├── formats.py                # Crispy Format query/import/export APIs
│   │       ├── branding_profiles.py      # Branding Profile APIs
│   │       ├── reports.py                # Report preview/rendering APIs
│   │       ├── document_codes.py         # Document-code generation APIs
│   │       ├── qr_regulatory_profiles.py # Regulatory QR profile APIs
│   │       ├── fiscal_credentials.py     # Fiscal credential APIs
│   │       └── security.py               # Shared API validation helpers
│   ├── public/
│   │   ├── js/
│   │   │   ├── crispy_print.bundle.js    # Format Builder entry
│   │   │   ├── crispy_preview.bundle.js  # Print Preview entry
│   │   │   ├── report_button.bundle.js   # Desk integration entry
│   │   │   ├── api/                      # Typed Frappe/Crispy API clients
│   │   │   ├── components/               # Reusable Vue components
│   │   │   ├── composables/              # Builder/report/settings stores
│   │   │   ├── pages/
│   │   │   │   ├── CrispyPFB.vue         # Format Builder shell
│   │   │   │   ├── CrispyPP.vue          # Print Preview shell
│   │   │   │   ├── CbpBuilder.vue        # Branding Profile Builder shell
│   │   │   │   └── cbpBuilderTypst.ts    # Branding Typst generation
│   │   │   ├── typst/
│   │   │   │   ├── JSONToTypst.ts        # Layout-to-Typst translator
│   │   │   │   ├── branding.ts           # Branding Profile Typst helpers
│   │   │   │   ├── setupWorker.ts        # Worker orchestration
│   │   │   │   └── worker*.ts            # Compile/autocomplete/PDF workers
│   │   │   └── utils/
│   │   │       ├── layout.ts             # Layout model and helpers
│   │   │       ├── reportState.ts        # Report builder state helpers
│   │   │       ├── presentation_settings.ts
│   │   │       └── safeSvg.ts            # Preview SVG sanitization
│   │   └── vendor/typst/                 # Bundled fonts (optional)
│   ├── doctype/
│   │   ├── crispy_format/                # Format registry and generated Typst
│   │   ├── crispy_branding_profile/      # Reusable presentation profile
│   │   ├── crispy_typst_block/           # Reusable Typst snippet library
│   │   ├── crispy_qr_regulatory_profile/ # Compliance QR profile
│   │   ├── crispy_fiscal_credential/     # Fiscal/compliance identity data
│   │   ├── crispy_document_code_profile/ # Document-code strategy
│   │   ├── crispy_document_code_rule/    # Document-code rule rows
│   │   └── crispy_format_reports/        # Report links for formats
│   ├── page/
│   │   ├── crispy_format_builder/        # Format Builder Desk page
│   │   ├── crispy_print_preview/         # Print Preview Desk page
│   │   └── cbp_builder/                  # Branding Profile Builder page
│   └── workspace/
│       └── crispy_print/                 # Crispy Print Desk workspace
├── fixtures/
│   └── crispy_format.json                # Demo/seed formats
├── patches/                             # Schema/data backfill patches
├── dev_utils/
│   └── perf_benchmarks.py                # Local benchmark helper
├── pyproject.toml                        # Python dependencies & config
└── README.md
```

### Key Components

**Pages:**
- **Crispy Format Builder** (`/app/crispy-format-builder`) - Main document builder for DocType, Report (WIP), and Contract (WIP) formats.
- **Crispy Print Preview** (`/app/crispy-print-preview/{doctype}/{docname}/{format}`) - Server-rendered document preview and PDF workflow.
- **Crispy Branding Profile Builder** (`/app/cbp-builder`) - Dedicated builder for reusable page, typography, branding, table, and QR presentation profiles.

**Workspace:**
- **Crispy Print** (`/app/crispy-print`) - Desk workspace for builder shortcuts, core records, reusable libraries, issued-document tracking, reports, and regulatory setup.

**Core Files:**

Backend:
- **`api/v1/__init__.py`** - Whitelisted v1 RPC facade used by Frappe clients.
- **`api/v1/compile.py`** - Server-side Typst compile flow, short-lived cache, asset resolution, and preview/PDF output.
- **`api/v1/docs.py`** - Permission-aware document fetch and formatted-value preparation.
- **`api/v1/formats.py`** - Format listing, import/export, conflict detection, builder mode, and report-format lookup.
- **`api/v1/branding_profiles.py`** - Branding Profile read/write APIs used by the profile builder and format preview flow.
- **`api/v1/reports.py`** - Report sample data, Typst source generation, combined preview compilation, and report PDF helpers.
- **`api/v1/document_codes.py`** - Document-code resolution and generation for regulatory/compliance workflows.
- **`api/v1/security.py`** - Shared permission checks, rate limits, path validation, and RPC input hardening.

Frontend:
- **`CrispyPFB.vue`** - Main format builder shell with visual layout, raw Typst, report, and settings surfaces.
- **`CbpBuilder.vue`** - Branding Profile Builder shell for presentation-system authoring.
- **`CrispyPP.vue`** - Preview shell with format selection and compile/download controls.
- **`useStore.ts`, `useReportStore.ts`, `useSettingsStore.ts`** - State modules for document layout, report modes, and presentation settings.
- **`JSONToTypst.ts`, `branding.ts`, `cbpBuilderTypst.ts`** - Typst generation paths for formats and branding profile specimens.
- **`safeSvg.ts`** - Browser-side SVG sanitization before preview injection.

Data model:
- **`Crispy Format`** - Format registry for DocType, Report, and Contract format records.
- **`Crispy Branding Profile`** - Reusable company presentation profile.
- **`Crispy Typst Block`** - Governed reusable Typst snippet library.
- **`Crispy QR Regulatory Profile`**, **`Crispy Fiscal Credential`**, **`Crispy Document Code Profile`**, and **`Crispy Document Code Rule`** - Compliance-oriented document identity and verification layer.

## API Reference

The public RPC surface is exposed through versioned whitelisted methods:

```text
crispy_print.api.v1.<endpoint>
```

For endpoint arguments and return shapes, see:

- `docs/api-reference.md`
- `docs/typst-cookbook.md`

Key endpoint groups:

- **Compile and fonts:** `get_typst_local_fonts`, `compile_typst`
- **Documents and formats:** `get_formatted_doc`, `get_crispy_format`, `get_crispy_formats_for_doctype`, `export_crispy_format`, `import_crispy_format`
- **Branding:** `get_branding_profiles`, `get_branding_profile_presentation_settings`
- **Reports:** `get_available_formats`, `get_sample_report_data`, `get_report_typst_source`, `compile_report_preview`, `generate_report_pdf`
- **Compliance and verification:** `resolve_document_code`, `generate_document_code`, `get_qr_regulatory_profiles`, `get_fiscal_credential_status`
- **Issued document scaffolding:** `get_issued_document`, `get_issued_document_by_token`, `verify_issued_document_token`, `create_issued_document_snapshot`

Example:

```javascript
await frappe.call({
  method: "crispy_print.api.v1.compile_typst",
  args: {
    typst_source: "#set page(paper: \"a4\")\n= Hello Typst",
    output_format: "svg",
  },
})
```

## Contributing

Before submitting changes, install and run the local quality checks:

```bash
cd apps/crispy_print
pre-commit install
pre-commit run --all-files
cd crispy_print/public/js
yarn test:unit
cd ~/frappe-bench
bench --site your-site run-tests --app crispy_print
```

Configured quality tools:

- **ruff** - Python linting and formatting
- **eslint** - JavaScript/TypeScript linting
- **prettier** - Code formatting
- **pyupgrade** - Python syntax modernization

GitHub Actions workflows are present in the repository but are not used for release gating yet. Tests are currently run manually using `yarn test:unit`, `bench run-tests`, and `pre-commit run --all-files`.

Keep feature changes small during the alpha 3 freeze unless they directly fix release-blocking bugs.

## License

MIT

## Credits

Built with the assistance of various AI tools. Special thanks to:

[![Typst](https://img.shields.io/badge/Typst-239DAD?style=for-the-badge&logo=typst&logoColor=white)](https://typst.app/)
[![Frappe](https://img.shields.io/badge/Frappe-0089FF?style=for-the-badge&logo=frappe&logoColor=white)](https://frappeframework.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
