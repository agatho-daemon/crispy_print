# This entire project is a work in progress, including this README 

## Crispy Print

A Frappe v15+ app that provides a modern print format designer using [Typst](https://typst.app/) - a modern typesetting system. Build beautiful, PDF-native print formats with a Vue 3-powered visual builder and real-time preview.

### Features

- **Visual Print Format Builder** - Drag-and-drop interface for designing print layouts
- **Real-time Typst Preview** - See PDF output as you design with live SVG preview
- **Native PDF Generation** - High-quality PDFs via Typst CLI (no browser printing)
- **DocType Integration** - Create custom formats for any Frappe DocType
- **Letterhead Support** - Use Letter Head documents with automatic image handling
- **Custom Fonts** - Support for system fonts, custom fonts, and bundled fonts
- **Print Preview Page** - Dedicated preview page for testing formats with actual documents

## Requirements

### System Dependencies

**Typst CLI** must be installed on your system:

#### macOS (via Homebrew)
```bash
brew install typst
```

#### Ubuntu/Debian
```bash
# Install from official releases
wget https://github.com/typst/typst/releases/latest/download/typst-x86_64-unknown-linux-musl.tar.xz
tar -xf typst-x86_64-unknown-linux-musl.tar.xz
sudo mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/
```

#### Verify Installation
```bash
typst --version
```

### Python Dependencies

This app requires Frappe v15 or later. All Python dependencies are managed via `pyproject.toml`.

## Installation

Install using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/agatho-daemon/crispy_print --branch develop
bench install-app crispy_print
bench restart
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
- **Crispy Print Builder** (`/app/crispy-print-builder`) - Visual layout editor with 4-column grid
- **Typst Print Preview** (`/app/typst-print/{doctype}/{docname}/{format}`) - Document preview page

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

### IDE Type Support (Optional)

For TypeScript/Vue IntelliSense in VS Code:

```bash
cd apps/crispy_print/crispy_print/public/js
yarn install
```

This installs local type definitions for IDE support only. These files are gitignored:
- `package.json`, `yarn.lock` - Type dependencies
- `tsconfig.json` - TypeScript configuration
- `node_modules/` - Type definitions

**Note:** Not required for building - only for IDE autocomplete.

### Building

```bash
# Build the app
bench build --app crispy_print

# Clear cache after changes
bench clear-cache && bench clear-website-cache

# Development workflow
bench start  # Run with auto-reload enabled
```

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

### Creating a Print Format

1. Navigate to **Crispy Format** list
2. Click **New**
3. Select a **DocType**
4. Click **Open Builder** to launch the visual editor
5. Design your layout using the drag-drop interface
6. Save the format

### Using a Print Format

1. Open any document (e.g., Sales Invoice)
2. Click **Print** dropdown
3. Select your Crispy Format
4. Preview and download PDF

### Print Preview Page

Direct link to preview page:
```
/app/typst-print/{doctype}/{docname}/{format_name}
```

Example:
```
/app/typst-print/Sales%20Invoice/SI-2024-001/My%20Custom%20Format
```

## API Reference

### Python API

**`crispy_print.api.get_typst_local_fonts()`**
- Returns list of font families available to Typst
- Includes system fonts, custom fonts, and bundled fonts

**`crispy_print.api.compile_typst_to_pdf(typst_code, letterhead_image=None)`**
- Compiles Typst markup to PDF
- Handles letterhead image copying to temp directory
- Returns base64-encoded PDF or error details

### JavaScript API

**`window.mountCrispyPrint(containerId, formatName)`**
- Mounts the print format builder Vue app
- Used by Frappe page loader

**`window.setupWorker(formatName, previewContainer, adapter)`**
- Initializes Typst compilation worker
- Returns teardown function

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

**Add custom fonts:**
```bash
export TYPST_FONT_PATHS="/path/to/fonts"
bench restart
```

### Letterhead Not Rendering

Check browser console for:
```
[Typst Translator] No letterhead found: LetterheadName
```

**Solution:** Ensure Letter Head document has an `image` field with valid file path.

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

#
