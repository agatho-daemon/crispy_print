# Development & Testing

_Part of the [Crispy Print documentation](README.md)._

## Testing

This app includes comprehensive test coverage:

- **279 frontend tests** across 67 Vitest files (2 opt-in Typst integration tests)
- **446 backend tests** in the complete Frappe application suite (5 skipped in the latest RTL verification run)
- **Test frameworks:** Vitest (frontend), Frappe Test Runner (backend)

Some backend integration tests depend on site fixtures and optional Typst CLI integration settings.

### RTL browser and PDF checks

The Playwright suite uses deterministic Chromium, a 1440×1000 viewport, and
`Asia/Kuwait`. Seed or prepare the named RTL format, then run:

```bash
yarn --cwd e2e install
yarn --cwd e2e playwright install chromium

bench --site your-site execute crispy_print.dev_utils.rtl_e2e.seed

CRISPY_E2E_BASE_URL=http://fdev.local:8000 \
CRISPY_E2E_USER=Administrator \
CRISPY_E2E_PASSWORD=admin \
CRISPY_E2E_FORMAT_AR="Crispy RTL E2E Arabic" \
CRISPY_E2E_FORMAT_FA="Crispy RTL E2E Persian" \
CRISPY_E2E_FORMAT_EN="Crispy RTL E2E English" \
CRISPY_E2E_FORMAT_MULTIPAGE="Crispy RTL E2E Multipage" \
CRISPY_E2E_FORMAT_REPORT="Crispy RTL E2E Report" \
CRISPY_E2E_DOCNAME="ACC-SINV-..." \
yarn test:e2e
```

The default seed creates language-specific Arabic, Persian, and English
formats, plus deterministic multipage and General Ledger report formats. It
also configures a basic QR payload. It never combines Arabic and Persian labels
in one document.

For a disposable test site, the seed can create or refresh a dedicated
least-surprise browser user without placing credentials in the repository:

```bash
bench --site your-site execute crispy_print.dev_utils.rtl_e2e.seed \
  --kwargs '{"test_user_password": "local-secret"}'

# After the browser run:
bench --site your-site execute crispy_print.dev_utils.rtl_e2e.disable_test_user
```

The dedicated user is opt-in and is never created during app installation or a
normal seed run.

The seed does not activate a frozen Crispy Template by default. On a disposable
acceptance site only, pass `--kwargs '{"publish": 1}'` to publish the Arabic
fixture and supply its returned template ID through `CRISPY_E2E_TEMPLATE`.
Publishing may supersede another active Sales Invoice template for the same
company, so never enable this on a production or shared-authoring site.

The isolated `e2e/package.json` is intentionally not installed by Bench during
normal Crispy Print installation. Chromium is downloaded only by the explicit
`yarn playwright install chromium` command. Screenshots, reports, traces, and
other browser output are local ignored artifacts rather than application
assets.

### Custom and Regulatory QR acceptance

Run this only on a disposable development site. The seed is idempotent, uses
existing draft/submitted ERPNext documents, creates isolated Crispy Formats,
and labels its ZATCA profile as non-certifying:

```bash
bench --site your-site execute \
  crispy_print.dev_utils.rtl_e2e.seed_qr_acceptance \
  --kwargs '{"publish": 1, "test_user_password": "local-secret"}'
```

Copy the returned document names into the browser matrix:

```bash
CRISPY_E2E_BASE_URL=https://your-site \
CRISPY_E2E_USER=crispy-rtl-e2e@local.test \
CRISPY_E2E_PASSWORD=local-secret \
CRISPY_QR_E2E_SALES_INVOICE=ACC-SINV-... \
CRISPY_QR_E2E_PURCHASE_INVOICE=ACC-PINV-... \
CRISPY_QR_E2E_DELIVERY_NOTE=MAT-DN-... \
CRISPY_QR_E2E_PAYMENT_ENTRY=ACC-PAY-... \
yarn --cwd e2e playwright test qr.spec.ts
```

The suite verifies exact field order, English/Arabic/Persian editor behavior,
cross-DocType rendering, legacy save blocking, live regulatory-profile
resolution, real QR decoding, and preview-source/final-PDF payload equality.
It uses `@zxing/library`, `pngjs`, and `pdftoppm` only inside the isolated E2E
toolchain. PDFs, rendered PNGs, traces, and failure screenshots remain under
ignored `test-results/` paths. Disable the test user afterward with
`crispy_print.dev_utils.rtl_e2e.disable_test_user`.

The bundled ZATCA registry/profile fixture proves the implementation path; it
does not constitute jurisdictional certification.

Use `yarn test:e2e:update` to generate local screenshots for visual review.
The acceptance matrix covers Arabic and Persian UI roots, localized fixture
labels, portal direction, keyboard and drag interaction, physical LTR
canvas/editor islands, multipage output, a deterministic RTL report, and an
optional published-template final preview. Typst integration tests assert
negative-sign order, document metadata, mixed-direction values, font
fallbacks, schema compatibility, and DocType/Report parity. Production release
additionally requires native Arabic/Persian review.

Sample Crispy Formats are not exported through Frappe fixtures. Keep curated
examples as company-neutral JSON files under `crispy_print/examples/formats/` and
load them through the Sample Format Catalog APIs. Do not re-add
`fixtures = [{"dt": "Crispy Format"}]` or a production `fixtures/crispy_format.json`
file for demo data; rich local demo generation belongs in `crispy_print/dev_utils/`.

## Development

### Required Toolchain

- Node.js `24.18.0` LTS (pinned by `.node-version`)
- Yarn `1.22.22` Classic
- Python `3.10+`
- Typst CLI `0.15.0+`

Yarn Modern is not supported by the Frappe v15 build workflow used for Beta 2.

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

**Beta 2 release validation:**

- **Frontend:** 269 tests across 63 test files
- **Backend:** 439 tests, 5 skipped, 0 failures
- **Additional gates:** TypeScript checks, pre-commit, ESLint, Prettier, complete Bench asset build, and real-browser DocType/Report preview and printing smoke tests

Some backend integration tests depend on site fixtures and optional Typst CLI integration settings.

### Translation Catalog Checks

Crispy Print stores its source catalog and translated catalogs under
`crispy_print/locale/`. After changing translatable source strings, regenerate the
POT file and synchronize every PO catalog:

```bash
bench generate-pot-file --app crispy_print
bench update-po-files --app crispy_print
```

Validate gettext syntax and runtime formatting before committing translation
changes:

```bash
find apps/crispy_print/crispy_print/locale -maxdepth 1 -name '*.po' -print0 \
  | xargs -0 -n 1 msgfmt --check --check-format -o /dev/null
bench compile-po-to-mo --app crispy_print --force
```

PO changes must preserve runtime placeholders, HTML tags, and the contents of
`<code>` elements. See the [translation guide](translations.md) for the included
locales, contribution policy, and native-review expectations.

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
