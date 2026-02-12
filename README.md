# Crispy Print

Modern print format designer for Frappe using the [Typst](https://typst.app/) typesetting system. Build PDF‑native print formats with a Vue 3 visual builder and real-time preview.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-96%20passing-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Frappe](https://img.shields.io/badge/frappe-v15+-orange.svg)](https://frappeframework.com/)

## Project Status

**Alpha / Work in progress.** Expect frequent changes while features are still settling.

> **Why Typst instead of HTML/CSS?** Typst provides superior PDF typography, precise layout control, and professional typesetting features that are difficult to achieve with browser-based rendering. Perfect for invoices, reports, certificates, and other print-critical documents.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Font Configuration](#font-configuration)
- [Architecture](#architecture)
- [Development](#development)
- [API Reference](#api-reference)
- [Known Limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Visual Print Format Builder** - Drag-and-drop interface for designing print layouts
- **Real-time Typst Preview** - See PDF output as you design with live SVG preview
- **Native PDF Generation** - High-quality PDFs via Typst CLI (no browser printing)
- **DocType Integration** - Create custom formats for any Frappe DocType
- **Letterhead Support** - Use Letter Head documents with automatic image handling
- **Logo Support** - Add company logo to page.
- **Custom Fonts** - Support for system fonts, custom fonts, and bundled fonts
- **Print Preview Page** - Dedicated preview page for testing formats with actual documents
- **QR Code Integration** - Automatic QR code generation for documents
- **Raw Typst Mode** - Advanced users can write Typst markup directly
- **Dual-Mode Report Builder** - Basic visual controls for report templates with Advanced Raw Typst mode for full customization
- **Report Mode Guardrails** - Safe Basic/Advanced switching with signature checks to prevent accidental overwrite of custom Typst

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
>>> from crispy_print.api import get_typst_local_fonts
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

### Creating Your First Print Format

> ⚠️ **CRITICAL:** You must set at least one format as **Default** for a DocType. The Typst print button appears on document forms **only when a default format exists** for that DocType.

**Step-by-step:**

1. **Create a new format**
   - Navigate to: **Desk** → **Crispy Print** → **Crispy Format**
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
   - **Letterhead:** Optional background image
   - **QR Code:** Enable for verification

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
/app/crispy-print/{doctype}/{docname}/{format_name}
```

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

Set the dedicated Typst font directory:

```bash
export TYPST_FONT_DIR="$HOME/.fonts/typst"
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

## Architecture

### Build System

This app uses **Frappe v15's native esbuild bundler** - no separate Vite or webpack setup required.

- **Bundle Entry:** `crispy_print/public/js/crispy_print.bundle.js`
- **Build Command:** `bench build --app crispy_print`
- **Output:** Single JavaScript bundle with inlined CSS (~1.7MB)
- **Plugin:** Uses `frappe-vue-style` to automatically inline Vue SFC styles

### Project Structure

```
crispy_print/
├── crispy_print/
│   ├── api.py                            # Whitelisted API methods
│   ├── hooks.py                          # App hooks
│   ├── public/
│   │   ├── js/
│   │   │   ├── crispy_print.bundle.js    # Main entry (builder)
│   │   │   ├── crispy_preview.bundle.js  # Preview page entry
│   │   │   ├── components/               # Reusable Vue components
│   │   │   ├── composables/              # Vue composables (useStore)
│   │   │   ├── pages/
│   │   │   │   ├── CrispyPFB.vue         # Print Format Builder
│   │   │   │   └── CrispyPP.vue          # Print Preview
│   │   │   ├── typst/
│   │   │   │   ├── createTypstWorker.ts  # Web worker factory
│   │   │   │   ├── setupWorker.ts        # Worker orchestration
│   │   │   │   ├── JSONToTypst.ts        # Layout → Typst translator
│   │   │   │   └── worker.ts             # Typst compilation worker
│   │   │   └── utils/
│   │   │       ├── layout.ts             # Layout type definitions
│   │   │       └── formatLoader.ts       # Format data utilities
│   │   └── vendor/typst/                 # Bundled fonts (optional)
│   ├── doctype/
│   │   └── crispy_format/                # Crispy Format DocType
│   └── page/
│       ├── crispy_print_builder/         # Builder page (Frappe desk)
│       └── typst_print/                  # Preview page (Frappe desk)
├── pyproject.toml                        # Python dependencies & config
└── README.md
```

### Key Components

**Pages:**
- **Crispy Format Builder** (`/app/crispy-format-builder`) - 4-pane builder; DocType uses visual layout, Report supports Basic + Advanced Raw Typst modes
- **Crispy Print Preview** (`/app/crispy-print/{doctype}/{docname}/{format}`) - Document preview page

**Core Files:**
- **`api.py`** - Backend API: Typst compilation, font discovery, letterhead handling
- **`CrispyPFB.vue`** - Main builder component with drag-drop layout editor
- **`CrispyPP.vue`** - Preview component with format/settings controls
- **`useStore.ts`** - Centralized state management (layout, page settings, metadata)
- **`setupWorker.ts`** - Typst worker lifecycle and compilation orchestration
- **`JSONToTypst.ts`** - Translates JSON layout structure to Typst markup
- **`worker.ts`** - Web Worker for async Typst compilation via API
- **`formatLoader.ts`** - Utilities for loading Crispy Format documents

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
- **Frontend:** 67 tests across 27 test files (100% passing)
- **Backend:** 29 tests across 2 test files (100% passing)
- **Total:** 96 tests

See [TEST_COVERAGE.md](TEST_COVERAGE.md) for details.

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

## Usage

### Print Format Workflow

The typical workflow for using Crispy Print:

1. **Create format** → Design in builder → Save
2. **Set as default** → To enable Typst button for DocType
3. **Open document** → Click `typst` button → Download PDF

### Report Builder Workflow (Dual Mode)

For `Crispy Format Type = Report`, builder now supports two editing modes:

- **Basic mode**: non-technical controls generate a managed Typst report template
- **Advanced mode**: direct Raw Typst editing

Key behavior:

1. **Basic → Advanced** is always allowed.
2. **Advanced → Basic** only unlocks full Basic editing when the template is still Basic-managed.
3. If custom Raw Typst changes are detected, Basic opens in **read-only** with options to:
   - stay in Advanced mode, or
   - reset/regenerate the Basic template.

This keeps report editing accessible while protecting advanced customizations.

### Advanced: Creating Formats Without Default

You can create multiple formats for the same DocType without setting them as default:

- Access via direct URL: `/app/crispy-print/{doctype}/{docname}/{format_name}`
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

**Report with Headers:**
1. Configure page header in settings
2. Section 1: Report title and date
3. Section 2: Summary metrics (4 columns)
4. Section 3: Data table
5. Section 4: Charts (if using HTML fields)

## API Reference

### Python API (Whitelisted Methods)

All methods are accessible via `frappe.call()` from client-side.

#### `get_typst_local_fonts()`

Returns list of available font families.

```python
@frappe.whitelist()
def get_typst_local_fonts() -> list[str]
```

**Returns:** `list[str]` - Font family names  
**Example:**
```python
fonts = frappe.call('crispy_print.api.get_typst_local_fonts')
# ['EB Garamon', 'Roboto', 'Liberation Sans', ...]
```

---

#### `compile_typst()`

Compiles Typst source to PDF or SVG.

```python
@frappe.whitelist()
def compile_typst(
    typst_source: str,
    output_format: str = "svg",
    letterhead_image: str = None,
    qr_data: str = None,
    qr_filename: str = None
) -> dict
```

**Parameters:**
- `typst_source` (str, required) - Typst markup code
- `output_format` (str) - "pdf" or "svg" (default: "svg")
- `letterhead_image` (str) - Path to letterhead image (e.g., "/files/letterhead.png")
- `qr_data` (str) - Data to encode in QR code
- `qr_filename` (str) - QR SVG filename

**Returns:** `dict`
```python
# PDF format:
{
    "success": True,
    "format": "pdf",
    "pdf_data": "base64_encoded_pdf_string"
}

# SVG format:
{
    "success": True,
    "format": "svg",
    "svg_pages": ["<svg>...</svg>", "<svg>...</svg>"],
    "page_count": 2
}
```

**Raises:** `frappe.ValidationError` if compilation fails

**Example:**
```python
result = frappe.call('crispy_print.api.compile_typst',
    typst_source='#set page(paper: "a4")\n= Hello Typst',
    output_format='pdf'
)
pdf_bytes = base64.b64decode(result['pdf_data'])
```

---

#### `get_formatted_doc()`

Returns document with server-side formatted field values.

```python
@frappe.whitelist()
def get_formatted_doc(doctype: str, name: str) -> dict
```

**Parameters:**
- `doctype` (str, required) - DocType name
- `name` (str, required) - Document name

**Returns:** `dict` - Document with formatted fields (currency, dates, etc.)

**Example:**
```python
doc = frappe.call('crispy_print.api.get_formatted_doc',
    doctype='Sales Invoice',
    name='SI-2024-001'
)
# doc['grand_total'] is now formatted as "1,234.56"
```

---

#### `get_crispy_formats_for_doctype()`

Get all Crispy Formats for a DocType.

```python
@frappe.whitelist()
def get_crispy_formats_for_doctype(doctype: str) -> list[dict]
```

**Returns:** `list[dict]` - List of format names and DocTypes

---

#### `get_default_doctypes()`

Get DocTypes that have default Crispy Formats set.

```python
@frappe.whitelist()
def get_default_doctypes() -> list[str]
```

**Returns:** `list[str]` - List of DocType names

---

#### `get_default_report_builder_config()`

Returns canonical backend defaults for report Basic mode controls.

```python
@frappe.whitelist()
def get_default_report_builder_config(generic_report_type: str | None = None) -> dict
```

**Parameters:**
- `generic_report_type` (str, optional) - e.g. `"Grid"`, `"Tree"`, `"Summary"`, `"Minimal"`

**Returns:** `dict`
```python
{
    "mode": "basic",
    "preset": "grid",              # or tree/summary/minimal
    "show_filters": True,
    "show_footer_total": True,
    "header_fill": "#B3D7FF",
    "header_text_weight": "bold",
    "font_family": "Inter 18pt",
    "font_size_pt": 9,
    "row_striping": False,
    "row_stripe_fill": "#F8FBFF",
    "column_align_strategy": "auto",
    "table_inset_x_pt": 8,
    "table_inset_y_pt": 6,
    "table_stroke_top_pt": 1,
    "table_stroke_body_pt": 0.5,
    "raw_signature": None
}
```

Used by the frontend as the server-side single source of truth for report builder defaults.

---

### JavaScript API

These functions are available globally in the builder and preview pages.

#### `window.mountCrispyPrint()`

Mounts the Vue 3 print format builder app.

```javascript
window.mountCrispyPrint(containerId: string, formatName: string): void
```

**Used internally by:** Frappe page loader

---

#### `window.setupWorker()`

Initializes the Typst compilation web worker.

```javascript
window.setupWorker(
    formatName: string,
    previewContainer: HTMLElement,
    adapter: object
): () => void
```

**Returns:** Teardown function to cleanup worker

**Used internally by:** Preview page

## Known Limitations

As an **alpha release**, Crispy Print has several known limitations:

### System & Dependencies

- **Typst CLI Required**: Must be installed separately; app won't work without it
- **Frappe v15+ Only**: Not  tested for compatibility with older Frappe versions
- **Server-Side Rendering**: All PDF compilation happens on the server (no client-side rendering)
- **Font Discovery**: Depends on system font configuration and `TYPST_FONT_PATHS` environment variable

### Layout Builder

- **Limited Field Types**: Currently supports basic fields; complex custom fields may not render correctly
- **Fixed Grid System**: 4-column layout structure cannot be customized
- **No Conditional Visibility**: Cannot hide/show elements based on document conditions
- **Report Basic Mode Scope**: Basic mode intentionally covers common report patterns; complex custom report logic still requires Advanced Raw Typst mode

### Typst Integration

- **Raw Typst Mode Limitations**: 
  - Requires knowledge of Typst syntax
  - No visual preview while editing raw code
  - Syntax errors not caught until compilation
  - 🔄 **Tip:** Use the **Refresh** button in the preview pane to recompile after editing raw Typst code
- **QR Code Format**: Only SVG format supported (no PNG/bitmap QR codes)
- **Table Styling**: Limited compared to full Typst table capabilities

### PDF Generation

- **Browser Preview**: SVG rendering in browser preview (actual PDF downloads are native Typst output)
- **Image Formats**: Letterhead images must be in formats supported by Typst (PNG, JPEG, SVG)
- **No Real-Time Collaboration**: Multiple users cannot edit the same format simultaneously
- **Text Editor / HTML Fields**: Content is converted to plain text (HTML stripped) before rendering

### Letterhead & Branding

- **No Built-in Letterhead Editor**: Must use existing Frappe Letter Head documents
- **Fixed Branding Position**: Logo and QR code placements use absolute positioning

### Data & Compatibility

- **LTR Languages Only**: Builder UI and text direction currently support left-to-right languages only (English, Spanish, French, etc.). RTL support (Arabic, Hebrew) not yet implemented. Multi-language content is possible via Raw Typst Mode if document fields contain the target language data.
- **No Jinja Support**: Completely different from standard Frappe Print Formats - uses JSON layouts instead of Jinja templates
- **No Python Scripts**: Cannot execute custom Python code like standard Print Formats
- **Export Only**: Formats cannot be imported/exported between sites (yet)
- **No Version History**: Previous versions of formats are not stored

### Performance

- **Web Worker Compilation**: Initial compilation may take 2-3 seconds for complex layouts
- **SVG Preview Size**: Multi-page SVG previews can be memory-intensive in browser
- **Font Loading**: Large custom font collections may slow down font discovery API

### Roadmap

#### Future Features (Not Yet Implemented)

The following features are planned but not yet available:

- [ ] Support Frappe Format Field Templates in Typst output
-  Native rendering with safe fallback for unsupported legacy templates
- [ ] Batch printing from list view
- [ ] Progress indicator for multi-document compilation
- [ ] Configurable batch size limits
- [x] Custom page break controls
- [ ] Multi-language format support
- [x] Format import/export
- [x] Advanced table styling options
- [ ] Client-side PDF rendering
- [ ] Format version history
- [ ] ~~Template variable/expression support~~

## Troubleshooting

### Typst Not Found

```
Error running typst fonts: [Errno 2] No such file or directory: 'typst'
```

**Solution:** Install Typst CLI (see Requirements section)

### Fonts Not Showing

**Check available fonts:**
``# Format Not Appearing in Document

If Typst button doesn't show or format isn't available:

1. **Verify installation:**
   ```bash
   bench --site your-site list-apps | grep crispy_print
   ```

2. **Check format has layout_json:**
   - Open Crispy Format document
   - Ensure it was saved via builder (not manually created)

3. **Verify permissions:**
   - User needs read access to Crispy Format doctype
   - Check Role Permission Manager

4. **Check browser console** for API errors

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
A: Yes! It's designed for ERPNext and supports Sales Invoice, Purchase Invoice, Quotation, etc.

**Q: Does it work offline?**  
A: PDF compilation requires server access (runs Typst CLI server-side). Preview requires internet for fonts.

**Q: Can I export formats between sites?**  
A: Not yet. Planned for future release. Currently, you need to recreate formats on each site.

**Q: How do I customize fonts?**  
A: Add fonts to system, set `TYPST_FONT_PATHS` environment variable, then restart bench. See [Font Configuration](#font-configuration).

**Q: Can I use custom Typst functions?**  
A: Yes, in Raw Typst mode. But be careful - syntax errors will break compilation.

**Q: What's the difference from Print Designer?**  
A: Print Designer uses HTML/CSS/Jinja. Crispy Print uses Typst for better PDF quality. They're completely separate systems.

**Q: Can I mix Jinja and Typst?**  
A: No. Crispy Print uses JSON layouts, not Jinja templates.

**Q: Is it production-ready?**  
A: It's in alpha. Use for non-critical documents. Test thoroughly before production use.

**Q: How do I report bugs?**  
A: Open an issue on GitHub with Frappe version, Typst version, and error logs.

**Q: Does it support multi-language?**  
A: Not yet. Single language per format. Multi-language support is planned.

## Testing

This app includes comprehensive test coverage:

- **96 total tests** (67 frontend + 29 backend)
- **100% pass rate**
- **Test frameworks:** Vitest (frontend), Frappe Test Runner (backend)

See [TEST_COVERAGE.md](TEST_COVERAGE.md) for detailed coverage report.

## Code Quality

This app uses pre-commit hooks for code quality:

```bash
cd apps/crispy_print
pre-commit install
```

**Linters configured:**
- **ruff** - Python linting and formatting
- **eslint** - JavaScript linting
- **prettier** - Code formatting
- **pyupgrade** - Python syntax modernization

## CI/CD

This project has pre-configured GitHub Actions workflows (currently disabled):
- **CI** - Would run 90 unit tests on `develop` branch
- **Linters** - Would run [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on PRs

**Currently:** Tests are run manually by developers using `yarn test:unit` (frontend) and `bench run-tests` (backend).

If PDF generation takes more than 5 seconds:

1. **Reduce document complexity**: Simplify layouts with fewer nested elements
2. **Limit table rows**: Consider pagination for large tables (100+ rows)
3. **Optimize images**: Use compressed letterhead images (< 1MB)
4. **Check server resources**: Ensure adequate CPU/memory on server

### Preview Not Updating

If changes don't appear in preview:

1. Clear browser cache: `Ctrl+Shift+R` (or `Cmd+Shift+R` on macOS)
2. Clear Frappe cache: `bench clear-cache && bench clear-website-cache`
3. Rebuild app: `bench build --app crispy_print`
4. Check browser console for JavaScript errors

## Contributing

This app uses `pre-commit` for code quality:

```bash
cd apps/crispy_print
pre-commit install
```

**Linters configured:**
- **ruff** - Python linting and formatting
- **eslint** - JavaScript linting
- **prettier** - Code formatting
- **pyupgrade** - Python syntax modernization

## CI/CD

GitHub Actions workflows:
- **CI** - Runs unit tests on `develop` branch
- **Linters** - Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on PRs

## License

MIT

## Credits

Built with the assistance of various AI tools. Special thanks to:

[![Typst](https://img.shields.io/badge/Typst-239DAD?style=for-the-badge&logo=typst&logoColor=white)](https://typst.app/)
[![Frappe](https://img.shields.io/badge/Frappe-0089FF?style=for-the-badge&logo=frappe&logoColor=white)](https://frappeframework.com/)
[![Vue.js](https://img.shields.io/badge/Vue.js-4FC08D?style=for-the-badge&logo=vuedotjs&logoColor=white)](https://vuejs.org/)

---

**Star this repo if you find it useful!** ⭐
