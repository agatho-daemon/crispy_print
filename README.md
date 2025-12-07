# This entire project is a work in progress, including this README 

### Crispy Print

A Frappe App that uses Typst CLI engine with Vue 3 based frontend to format DocType print formats.

## Architecture

This app uses **Frappe's native esbuild system** to bundle Vue 3 components, eliminating the need for a separate Vite build process.

### Build System

- **Bundle Entry:** `crispy_print/public/js/crispy_print.bundle.js`
- **Build Command:** `bench build --app crispy_print`
- **Output:** Single JavaScript bundle with inlined CSS (~1.7MB)
- **Plugin:** Uses `frappe-vue-style` to automatically inline Vue SFC styles

The app follows the same architecture as Frappe's Print Format Builder Beta.

### Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch develop
bench install-app crispy_print
```

### Development Setup

#### IDE Type Support (Optional)

For TypeScript/Vue intellisense in VSCode, install type definitions:

```bash
cd apps/crispy_print/crispy_print/public/js
yarn install
```

This installs local type definitions for IDE support only. These files are gitignored:
- `package.json` - Type dependencies
- `yarn.lock` - Lock file  
- `tsconfig.json` - TypeScript config
- `node_modules/` - Type definitions

**Note:** These are **not required** for building - only for IDE autocomplete and type checking.

#### Building

```bash
# Build the Vue bundle
bench build --app crispy_print

# Clear cache after changes
bench clear-cache
```

### Project Structure

```
crispy_print/
├── crispy_print/
│   ├── public/
│   │   ├── js/
│   │   │   ├── crispy_print.bundle.js    # Entry point
│   │   │   ├── components/               # Vue components
│   │   │   ├── composables/              # Vue composables (store)
│   │   │   ├── pages/                    # Page components
│   │   │   ├── typst/                    # Typst integration
│   │   │   └── utils/                    # Layout utilities
│   │   └── css/                          # (not used - styles in Vue SFCs)
│   ├── doctype/
│   │   └── crispy_format/                # Custom DocType
│   ├── page/
│   │   └── crispy_print_builder/         # Frappe page loader
│   └── hooks.py                          # App hooks
└── README.md
```

### Vue Component Guidelines

All Vue components use `<style scoped>` blocks. The CSS is automatically extracted and inlined by Frappe's build system:

```vue
<template>
  <!-- component markup -->
</template>

<script>
// component logic
</script>

<style scoped>
/* Component-specific styles - automatically inlined */
.my-component {
  /* styles */
}
</style>
```

For dynamically created DOM elements (like `.typst-page`), apply styles directly via JavaScript:

```typescript
const element = document.createElement("div")
element.style.marginBottom = "1.5rem"
element.style.boxShadow = "0 4px 12px rgba(148, 163, 184, 0.25)"
```

### Key Files

- **`crispy_print.bundle.js`** - Main entry point, exports `window.mountCrispyPrint()`
- **`hooks.py`** - Defines `app_include_js = "crispy_print.bundle.js"`
- **`CrispyPFB.vue`** - Main page component with 4-column grid layout
- **`useStore.ts`** - Centralized state management (layout, settings, meta)
- **`setupWorker.ts`** - Typst compilation orchestration
- **`JSONToTypst.ts`** - Translates layout JSON to Typst markup

### Contributing

This app uses `pre-commit` for code formatting and linting. Please [install pre-commit](https://pre-commit.com/#installation) and enable it for this repository:

```bash
cd apps/crispy_print
pre-commit install
```

Pre-commit is configured to use the following tools for checking and formatting your code:

- ruff
- eslint
- prettier
- pyupgrade

### CI

This app can use GitHub Actions for CI. The following workflows are configured:

- CI: Installs this app and runs unit tests on every push to `develop` branch.
- Linters: Runs [Frappe Semgrep Rules](https://github.com/frappe/semgrep-rules) and [pip-audit](https://pypi.org/project/pip-audit/) on every pull request.


### License

mit
