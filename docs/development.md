# Development & Testing

_Part of the [Crispy Print documentation](README.md)._

## Testing

This app includes comprehensive test coverage:

- **449 tests/test methods** (187 frontend + 262 backend)
- **Test frameworks:** Vitest (frontend), Frappe Test Runner (backend)

Some backend integration tests depend on site fixtures and optional Typst CLI integration settings.

Sample Crispy Formats are not exported through Frappe fixtures. Keep curated
examples as company-neutral JSON files under `crispy_print/examples/formats/` and
load them through the Sample Format Catalog APIs. Do not re-add
`fixtures = [{"dt": "Crispy Format"}]` or a production `fixtures/crispy_format.json`
file for demo data; rich local demo generation belongs in `crispy_print/dev_utils/`.

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

- **Frontend:** 187 tests across 52 test files
- **Backend:** 262 test methods across 22 test files
- **Total:** 449 tests/test methods

Some backend integration tests depend on site fixtures and optional Typst CLI integration settings.

**Sample format catalog checks:**

```bash
bench --site your-site run-tests --app crispy_print --module crispy_print.tests.api.test_sample_formats
cd apps/crispy_print/crispy_print/public/js
yarn vitest run tests/batch15/formatImportExportApi.test.ts tests/batch16/crispyPFBLayout.test.ts tests/batch18/sampleFormatsDialog.test.ts
```

### QR Field Registry Checks

QR/document-code selected fields use a repo-owned backend registry and Frappe child rows. After registry or selected-field model changes, run:

```bash
bench --site your-site execute crispy_print.dev_utils.qr_registry_smoke.run
bench --site your-site run-tests --app crispy_print --module crispy_print.tests.qr_registry.test_loader
bench --site your-site run-tests --app crispy_print --module crispy_print.crispy_print.doctype.crispy_document_code_profile.test_crispy_document_code_profile
bench --site your-site run-tests --app crispy_print --module crispy_print.tests.api.test_document_codes
```

Run `bench migrate` when DocType metadata or migration patches change. The selected-fields migration converts safe legacy `selected_fields_json` values into `Crispy Document Code Field` child rows when a single target DocType can be inferred.

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
const page = document.createElement("div");
page.className = "typst-page";
page.style.marginBottom = "1.5rem";
page.style.boxShadow = "0 4px 12px rgba(148, 163, 184, 0.25)";
```
