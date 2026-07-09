# Crispy Print

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status](https://img.shields.io/badge/status-beta-blue)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Frappe](https://img.shields.io/badge/frappe-v15%2Fv16%2Fdev--17-orange.svg)](https://frappeframework.com/)

> [!CAUTION]
>
> # MAJOR UPDATE
>
> ## This release will break existing formats.
>
> This is due to changes in fields representation in the backend and exchange of that data between Python and TS/JS parts along with Typst translation logic. Please backup your formats before pulling this update.
>
> A migration patch is provided to convert existing formats to the new structure, but complex custom layouts may require manual adjustments in the builder after migration.
>
> Typst CLI `0.15.0` or newer is required because Crispy Print ships variable fonts, and Typst supports variable fonts starting in `0.15.0`. Upgrade Typst before running previews, PDF generation, or migration verification; older Typst versions are rejected at compile time.
>
> After update run `bench migrate` to apply database changes and data migration. Then open each format in the builder and verify that the layout is correct. Some fields may need to be re-dragged or reconfigured due to changes in field properties and layout structure.

## Beta 1 Testing Request

Crispy Print `0.2.0-beta.1` is the first beta release, tested against Frappe v15, Frappe v16, and current dev-17 as of 2026-07-01. Please test existing workflows and report bugs, regressions, confusing behavior, and documentation gaps.

- Test DocType print preview and PDF generation with real documents.
- Test the visual format builder: drag fields, configure tables, save, reload, reset, and export/import formats.
- Test Branding Profile Builder, including logo, letterhead, typography, margins, and QR placement.
- Test Raw Typst mode, private image helpers, reusable Typst blocks, regular-mode image insertion, and font/typography controls.
- Test QR and document-code flows where applicable. Regulatory QR support especially needs feedback from users in tax-regulated regions because the maintainer cannot validate real-world tax QR requirements locally; the maintainer's country does not currently have tax-related document QR regulations. Please test whether QR Regulatory Profiles, Fiscal Credentials, Document Code Profiles, and generated payloads can model your local authority requirements, invoice fields, environment rules, and verification expectations. If your region requires additional fields for QR generation, please report the required field names, data types, source documents, validation rules, and example payload structure where possible.
- Test report preview and report PDF generation, but treat report support as a beta stabilization area. Contract support is still foundation-level and remains **WIP**.
- Include Frappe version, Typst version, browser, console errors, server traceback, and reproduction steps when opening issues.

> [!NOTE]
> This README describes the current beta architecture at a high level. For exact migration details and edge-case behavior, prefer the checked-in patches and tests as the source of truth.

## Project Status

**Beta / stabilization.** Core document-format workflows are ready for broader testing, while report and contract workflows are still being refined.

Crispy Print is a next-generation document publishing engine for ERPNext built around deterministic rendering, structured document composition, and publication-grade PDF generation. Instead of treating business documents as browser pages exported to PDF, Crispy Print treats them as formal documents with stable pagination, precise layout control, reusable branding systems, and machine-verifiable document workflows. Built on [Typst](https://typst.app/), Crispy Print moves ERP printing beyond fragile HTML print pipelines into a modern, regulation-ready publishing architecture designed for invoices, quotations, vouchers, contracts, compliance documents, technical reports, and future digital business-document ecosystems.

**Why Typst instead of HTML/CSS?** Typst provides superior PDF typography, precise layout control, and professional typesetting features that are difficult to achieve with browser-based rendering. Perfect for invoices, reports, certificates, and other print-critical documents.

## Why Crispy Print

ERP printing has long relied on HTML templates, browser rendering, and wkhtmltopdf, which leads to unstable pagination, inconsistent PDF output, layout drift, weak typography, and browser-dependent results that are hard to audit. Crispy Print solves these at the architecture level by converting ERP data into a structured document model and rendering it through Typst as a real document:

```text
ERP Data -> Structured Document Model -> Typst -> Deterministic Business Document
```

This delivers deterministic PDF rendering, publication-grade composition, stable multi-page layouts, precise control for regulatory forms, reusable branding profiles, and a regulatory QR foundation for machine-verifiable documents.

For the full vision, technical value for admins, architectural direction, and long-term goals, see [Overview & Vision](docs/overview.md).

## Features

- **Deterministic Typst Rendering Pipeline** - Converts Frappe documents into structured Typst sources and server-rendered PDF/SVG output.
- **Visual Document Composition Builder** - Drag-and-drop builder for DocType print formats with sections, columns, fields, tables, private images, QR elements, and custom Typst blocks.
- **Native PDF Generation** - Uses the Typst CLI for publication-grade PDF generation instead of browser printing or wkhtmltopdf.
- **Live SVG Preview** - Server-rendered preview flow for format design, document previews, and report previews without relying on browser print layout.
- **Frappe Print Engine Adapter** - Registers Crispy Print as a client-renderer print engine when the proposed Frappe Print Engine extension is available, allowing Frappe's Print button to hand document printing directly to the Typst preview route.
- **Reusable Branding Profiles** - Centralized page, typography, table, logo, letterhead, QR, and spacing settings for consistent company-wide document output.
- **Branding Profile Builder** - Dedicated visual builder for reusable presentation systems with generated Typst preview and controlled profile publication.
- **Crispy Print Workspace** - Desk workspace with grouped shortcuts and cards for builders, core format records, reusable libraries, issued documents, reports, and regulatory setup.
- **Reusable Typst Blocks** - Governed snippets for repeatable custom document fragments, scoped by category and linked DocType usage, with generated snake_case reference keys, explicit major/minor versions, and a dedicated compile/preview builder.
- **DocType-Aware Format Registry** - Crispy Format records link formats to target DocTypes, format types, branding profiles, custom builders, and generated Typst.
- **Sample Format Catalog** - Ships company-neutral example formats as app files and lets users explicitly create company-scoped Crispy Formats from the builder Examples dialog, including a Raw Typst receipt voucher sample.
- **Company-Scoped Rendering** - Format, template, branding profile, and Typst block resolution is company-aware, with company-scoped default selection and cache invalidation.
- **Approved Render Contracts (Crispy Template)** - Publish frozen, versioned approved render snapshots from a Crispy Format with snapshot-hash versioning, PDF standard, and Typst/Zebra/barcode facts, including company-specific templates with fallback to global templates.
- **Duplicate for Company** - Clone a Crispy Format or frozen Crispy Template snapshot to another company while preserving layout/content, retargeting company-scoped presentation settings, and optionally publishing a target-company template from the frozen snapshot.
- **Crispy Issued Document Registry (CID)** - Immutable issued-document snapshots linked to frozen templates, with opaque verification tokens, render-hash facts, artifact tracking, trust-event and regulatory-submission child tables, and revocation/supersession state.
- **Per-Format PDF Standard** - Output standard selection with a PDF/A-2u default plus PDF/A-3u, PDF/A-4, PDF 1.7, and PDF 2.0.
- **Global Print Settings** - Crispy Print Settings DocType for font configuration (uploaded/system fonts, search paths, font discovery refresh), render timeout, and draft/cancelled print policy.
- **Report Format Infrastructure (Beta)** - Report-linked formats with Basic/Advanced modes, column selection, filters, chart assets, and guarded raw Typst overrides.
- **Contract Format Foundation (WIP)** - Contract format support is reserved for future structured contract publishing workflows.
- **Regulatory QR Layer** - QR Regulatory Profiles, Fiscal Credentials, and helper APIs for building machine-verifiable fiscal and compliance QR payloads.
- **Document Code Infrastructure** - Document Code Profiles and Rules for deterministic reference codes, naming patterns, and compliance-oriented document identifiers.
- **Permission-Aware API Surface** - Versioned Frappe APIs with read/write permission checks, manager-only operations, and rate limits around expensive compile paths.
- **Controlled Asset Resolution** - Typst image assets resolve through approved site/app roots with traversal, symlink, external URL, and duplicate-basename protections; Raw Typst `crispy_image()` intentionally resolves private uploaded image filenames only.
- **Compile Caching and Preview Optimizations** - Short-lived Typst compile cache, document fetch cache, report preview consolidation, lazy page bundles, SVG rerender avoidance, and bounded undo snapshots.
- **Builder and Preview Diagnostics** - Collapsed builder checks plus runtime preview diagnostics for resolved format/template context, Typst version, render timing, page count, and cache state.
- **Import, Export, Samples, and Migration Support** - Structured format import/export, explicit sample creation, schema validation, backfill patches, and compatibility tests for evolving format data.
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
# Should output: typst 0.15.0 or higher
```

Crispy Print ships variable fonts to avoid maintaining separate font files for every style and weight. Typst CLI `0.15.0` or newer is required for variable font support.

### Frappe Compatibility

- **Frappe:** v15, v16, and current dev-17 as tested on 2026-07-01 (all Python/Node.js dependencies already satisfied)
- **Frappe v15:** Uses the classic `/app/crispy` workspace route and v15-compatible Desk assets.
- **Frappe v16/dev-17:** Ships a curated **Crispy Studio** Workspace Sidebar so newer Desk renders grouped app navigation (Builders, Formats, Reports, Branding, Issued Documents, Regulatory, Settings) instead of relying on the auto-generated sidebar. The v16+ **Crispy Print** app tile uses Frappe's native `add_to_apps_screen` `has_permission` parameter to hide the tile from website-only users and show it only to users with read access to user-facing Crispy Print records.
- **Frappe dev-17:** Supported on the current development branch tested for this beta; retest before production use because dev-17 is still moving.
- **Frappe Print Engine integration:** Crispy Print includes a guarded adapter for the proposed Frappe Print Engine DocType and `Print Settings.default_print_engine` flow. On sites where that Frappe PR is installed and the Print Engine controller is available, Crispy Print creates a `crispy_print` engine record and Frappe's Print button can route directly to `crispy-print-preview`. On standard Frappe sites without that PR, the adapter is skipped and the existing Typst button remains the supported entry point.
- **Python dependency:** `segno` (installed with the app; used as the QR-only SVG generator)
- **Typst barcode package:** Zebra `0.1.0` is vendored with the app and used for DataMatrix rendering through Typst.

## Installation

### 1. Install Typst CLI

See [Requirements](#requirements) above - Typst must be installed first.

### 2. Get and Install the App

```bash
cd ~/frappe-bench
bench get-app https://github.com/agatho-daemon/crispy_print --branch v0.2.0-beta.1
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

After installation, open the **Crispy Print** app from Desk. It opens the **Crispy Studio** workspace/sidebar on supported Frappe versions. You can also visit:

```text
/desk/crispy-studio
```

On Frappe v15, the legacy workspace route is `/app/crispy`.

The workspace groups the main builder pages, format records, templates, branding profiles, reusable Typst blocks, issued-document tracking, report templates, regulatory setup records, and settings. On Frappe v16+, the **Crispy Studio** sidebar also exposes the Print Preview page for direct access, although normal document previews are usually opened from the document or report route context.

### Creating Your First Print Format

> ⚠️ **Required:** Set one **Crispy Format** as **Default** for the DocType so the document form can show the **Typst** button. Then publish an **Approved** and **Active** **Crispy Template** from that format; runtime preview and PDF output use the frozen template snapshot.

> [!IMPORTANT]
> Crispy Print no longer ships `Crispy Format` records as Frappe fixtures. The previous `fixtures/crispy_format.json` sample-data path has been removed so installs and migrations do not import company-specific demo formats into production sites. Use the builder **Examples** dialog to create sample formats explicitly for a selected company.

Recommended setup order:

1. Create or select a **Crispy Branding Profile** for company-wide page, typography, letterhead, logo, table, and QR defaults.
2. Create a **Crispy Format** for the target DocType.
3. Design the layout in the builder, attach the branding profile, save, and test with real documents.
4. Configure document-code or regulatory QR profiles only if the document workflow needs compliance-oriented identifiers.

**Start from an example:**

1. Open **Crispy Format Builder**.
2. Expand the left **Fields** pane if it is collapsed.
3. Click **Examples**.
4. Pick a sample such as **Sales Invoice Starter**, **Quotation Starter**, **Purchase Order Starter**, or **Receipt Voucher Raw Typst**.
5. Select the target **Company**, optionally rename the format, and choose whether to set it as default.
6. Click **Create Format**. Crispy Print creates a normal company-scoped `Crispy Format` record and routes the builder to it.

Examples are stored in `crispy_print/examples/formats/` as company-neutral JSON payloads. They are hints and starter templates, not production defaults, and they are never installed automatically.

**Step-by-step:**

1. **Create a new format**
   - Navigate to: **Desk** → **Crispy Print** → **Crispy Formats**
   - Click **New**
   - Enter **Name** (e.g., "Sales Invoice Modern")
   - Select **Company** (**required** — formats and templates are company-scoped)
   - Select **DocType** (e.g., "Sales Invoice")
   - Select **Module** (e.g., "Crispy Print")
   - Optionally set **PDF Standard** (defaults to PDF/A-2u)
   - **Save**

2. **Set as default** ⚠️ **(Required for the document button)**
   - Check the **"Set as Default"** checkbox
   - **Save** again

3. **Design your layout**
   - Click **Open Builder** button
   - **Add sections:** Click "+ Add Section"
   - **Drag fields:** From right pane to layout grid
   - **Configure fields:** Click field to edit label, style, alignment
   - **Add tables:** Drag table fields (e.g., "items") for line items
   - **Compact item tables:** Use compact table labels when narrow table cells need clearer field names in print output
   - **Adjust columns:** Split sections into 1-4 columns

4. **Configure page settings** (left sidebar)
   - **Paper Size:** A4, Letter, etc.
   - **Margins:** Adjust spacing
   - **Fonts:** Select font family, style, and weight. Weight/style menus are limited to the faces Typst reports for the selected family.
   - **Branding Profile:** Apply reusable company presentation settings
   - **Letterhead / Logo:** Use Frappe Letter Head, uploaded assets, or branding profile defaults
   - **QR / Document Code:** Enable only when the target workflow requires verification or compliance metadata

**Reusable Typst Blocks:**

- Create **Crispy Typst Block** records for governed Typst snippets that should be reused across formats.
- The **Reference Key** is generated from **Block Name** using snake_case, for example `Invoice Header` becomes `invoice_header`.
- New blocks default to version `1.0`; document IDs include the reference key and version, for example `invoice_header-v1.0`.
- Open **Crispy Typst Block Builder** from the block form to edit Typst code and refresh a live SVG preview. Preview page settings are authoring-only; only Typst Code changes mark the builder unsaved.

**Raw Typst Mode:**

- Raw Typst mode gives the author control of the Typst source and hides builder presentation controls that would otherwise generate page, print behavior, typography, or table code.
- Document fields dropped into the code editor insert `#doc.fieldname`; Crispy fields insert code snippets such as `#crispy_block("")` and `#crispy_image("")`.
- Reusable blocks are referenced by document ID, for example `#crispy_block("invoice_header-v1.0")`; only referenced block code is injected into the compile source.
- Private uploaded images can be referenced with `#crispy_image("logo.svg", width: 20mm)`.
- Raw code changes compile only when clicking **Refresh** or pressing **Command/Ctrl-Enter**.

These are working beta behaviors. Treat Raw Typst as the author-owned path: Crispy Print still injects document data and helper definitions needed to compile, but page setup, placement, typography, tables, headers, and footers are owned by the raw source.

5. **Save and publish a template**
   - Click **Save**
   - In the builder, publish a **Crispy Template** from the format
   - Mark the template **Approved** and **Active** for the target company/document context

6. **Test document preview**
   - Open any document of that DocType (e.g., Sales Invoice)
   - Look for **Typst** button in toolbar (top-right)
   - Click to preview and download PDF

7. **Reuse across companies when needed**
   - In the builder preview pane, click **Duplicate**.
   - Choose **Current Format** to clone the saved format layout/settings to another company.
   - Choose **Template Snapshot** to preserve an approved frozen Crispy Template snapshot, create a target-company format from that snapshot, and publish a target-company template.
   - Use snapshot mode when the approved template must remain byte-for-byte stable apart from company-scoped presentation fields.

**Diagnostics:**

- In the builder, open **Presentation → Diagnostics** to review passive setup checks for format/DocType/company setup, default-format status, PDF standard, branding profile context, multiple default Branding Profile candidates, unavailable configured fonts, raw/report Typst source state, stale generated report Typst, unresolved Typst Blocks, and unsaved changes.
- In runtime preview, use **Diagnostics** to inspect the resolved format/template context, company, branding profile, PDF standard, Typst version, page count, render time, compile-cache state, and raw Typst mode.

### Using Your Print Format

Once a default format exists, the **Typst** button appears automatically on saved documents of that DocType. The preview itself requires an approved active **Crispy Template** for the document's company/context; without one, the preview page reports that no approved template is available.

When the proposed Frappe Print Engine extension is present and **Print Settings → Default Print Engine** is set to **Crispy Print**, Frappe's native **Print** action can also open the same Crispy preview route. This integration is intentionally additive: the existing **Typst** button still works and remains the compatibility path for standard Frappe installations.

The document preview is fully **template-driven**: it renders from the active resolved template/format for the document's company. Manual preview overrides, the approved-snapshot toggle, and the standalone print-settings header/reset action have been removed; help now lives in the Template section, and the template selector displays canonical template IDs.

**From Document:**

1. Open document (e.g., SI-2024-001)
2. Click **Typst** button in toolbar
3. Preview opens with the resolved active template for that document context
4. Click **Download PDF**

### Issued Documents and Historical Reprints

Runtime PDF actions create or reuse a **Crispy Issued Document** (CID) entry for the generated business document. Preview rendering alone does not create a CID; CID creation happens only when a PDF action such as view, download, or print succeeds.

- CID entries are issued records, not drafts. They store the final generated Typst source, a persisted SHA-256 `typst_source_hash`, the frozen template reference, and canonical render metadata.
- Duplicate issuance is guarded by the backend using source document, frozen template, and `typst_source_hash`. Repeating the same PDF action for the same generated Typst source returns the existing CID instead of creating a duplicate.
- Historical reprints should be performed from the **Crispy Issued Document** form using the CID PDF actions. CID reprint compiles the stored Typst source directly and does not resolve the latest template or create another CID.
- Published **Crispy Templates** freeze the layout, Typst, branding settings, letterhead/template text, PDF standard, Typst/Zebra/barcode facts, and snapshot hash. CID freezes the final document-specific Typst source used at issuance time.
- Crispy Print intentionally does not snapshot every referenced file into the database. Site operators should retain mutable referenced assets, especially company logos and image assets, if exact historical visual replay is required. Letterhead/template text should be stored in the template fields before publishing; binary logo retention remains an operational responsibility in this beta.

**Direct URL:**

```
/app/crispy-print-preview/{doctype}/{docname}/{format_name}
```

## Documentation

Detailed guides live in the [`docs/`](docs/README.md) directory:

- [Overview & Vision](docs/overview.md) - Why Crispy Print exists, what makes it different, and the long-term direction.
- [Usage](docs/usage.md) - Print, report, branding, letterhead, document-code workflows, and layout recipes.
- [Font Configuration](docs/fonts.md) - Bundled, system, uploaded, and custom fonts plus global Crispy Print Settings.
- [Architecture](docs/architecture.md) - Build system, product structure, key components, and data model.
- [Known Limitations](docs/limitations.md) - Current beta constraints.
- [Roadmap](docs/roadmap.md) - Recently added features and planned work.
- [Troubleshooting & FAQ](docs/troubleshooting.md) - Common issues, fixes, and frequently asked questions.
- [Development & Testing](docs/development.md) - Local setup, building, running tests, and component guidelines.
- [API Reference](docs/api-reference.md) - Whitelisted v1 endpoints, arguments, and return shapes.
- [Typst Cookbook](docs/typst-cookbook.md) - Practical Typst snippets for filters, summaries, charts, tables, and totals.

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

Keep feature changes small during the beta 1 stabilization period unless they directly fix release-blocking bugs.

## License

MIT

## Credits

Built with the assistance of various AI tools. Special thanks to:

[![Typst](https://img.shields.io/badge/Typst-239DAD?style=for-the-badge&logo=typst&logoColor=white)](https://typst.app/)
[![Frappe](https://img.shields.io/badge/Frappe-0089FF?style=for-the-badge&logo=frappe&logoColor=white)](https://frappeframework.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)
