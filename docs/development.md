# Development & Testing

_Part of the [Crispy Print documentation](README.md)._

## Testing

This app includes comprehensive test coverage:

- **438 tests/test methods** (187 frontend + 251 backend)
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

- **Frontend:** 187 tests across 52 test files
- **Backend:** 251 test methods across 21 test files
- **Total:** 438 tests/test methods

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
const page = document.createElement("div");
page.className = "typst-page";
page.style.marginBottom = "1.5rem";
page.style.boxShadow = "0 4px 12px rgba(148, 163, 184, 0.25)";
```
