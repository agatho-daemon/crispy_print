# Architecture

_Part of the [Crispy Print documentation](README.md)._

### Build System

This app uses **Frappe's native esbuild bundler** - no separate Vite or webpack setup required.

- **Main Builder Bundle:** `crispy_print/public/js/crispy_print.bundle.js`
- **Preview Bundle:** `crispy_print/public/js/crispy_preview.bundle.js`
- **Typst Block Builder Bundle:** `crispy_print/public/js/ctb_builder.bundle.js`
- **Desk Button Bundle:** `crispy_print/public/js/report_button.bundle.js`
- **Print Engine Adapter:** `crispy_print/public/js/crispy_print_engine.js`
- **Build Command:** `bench build --app crispy_print`
- **Loading Model:** Lightweight desk hooks plus page-specific builder/preview bundles
- **Plugin:** Uses `frappe-vue-style` to automatically inline Vue SFC styles

### Current Product Structure

This beta structure is documented here for orientation only. It is expected to keep evolving during beta stabilization.

```
crispy_print/
├── crispy_print/
│   ├── hooks.py                          # Frappe hooks and desk assets
│   ├── install.py                        # Install-time setup helpers
│   ├── json_utils.py                     # Shared JSON parsing/coercion helpers
│   ├── letterhead_lifecycle.py           # Letter Head lifecycle fields and validation
│   ├── config/
│   │   └── __init__.py                   # Frappe config package marker
│   ├── examples/
│   │   └── formats/                      # Company-neutral sample format catalog
│   ├── api/
│   │   └── v1/                           # Versioned backend API surface
│   │       ├── compile.py                # Typst compile, cache, asset controls
│   │       ├── docs.py                   # Document fetch and print data helpers
│   │       ├── formats.py                # Crispy Format query/import/export APIs
│   │       ├── sample_formats.py         # File-based sample catalog APIs
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
│   │   │   ├── crispy_print_engine.js    # Frappe Print Engine adapter
│   │   │   ├── ctb_builder.bundle.js     # Typst Block Builder entry
│   │   │   ├── report_button.bundle.js   # Desk integration entry
│   │   │   ├── api/                      # Typed Frappe/Crispy API clients
│   │   │   ├── components/               # Reusable Vue components
│   │   │   ├── composables/              # Builder/report/settings stores
│   │   │   ├── pages/
│   │   │   │   ├── CrispyPFB.vue         # Format Builder shell
│   │   │   │   ├── CrispyPP.vue          # Print Preview shell
│   │   │   │   ├── CbpBuilder.vue        # Branding Profile Builder shell
│   │   │   │   ├── CtbBuilder.vue        # Typst Block Builder shell
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
│   │   └── vendor/
│   │       ├── fonts/                    # Bundled fonts
│   │       └── typst/                    # Bundled Typst packages
│   ├── crispy_print/                     # Inner Frappe module package
│   │   ├── doctype/
│   │   │   ├── crispy_format/                # Format registry and generated Typst
│   │   │   ├── crispy_branding_profile/      # Reusable presentation profile
│   │   │   ├── crispy_typst_block/           # Reusable Typst snippet library
│   │   │   ├── crispy_qr_regulatory_profile/ # Compliance QR profile
│   │   │   ├── crispy_fiscal_credential/     # Fiscal/compliance identity data
│   │   │   ├── crispy_document_code_profile/ # Document-code strategy
│   │   │   ├── crispy_document_code_rule/    # Document-code rule rows
│   │   │   ├── crispy_format_reports/        # Report links for formats
│   │   │   ├── crispy_template/              # Frozen approved render contract
│   │   │   ├── crispy_issued_document/       # Issued-document registry (CID) + child tables
│   │   │   └── crispy_print_settings/        # Global font, render, and print policy (Single)
│   │   ├── page/
│   │   │   ├── crispy_format_builder/        # Format Builder Desk page
│   │   │   ├── crispy_print_preview/         # Print Preview Desk page
│   │   │   └── cbp_builder/                  # Branding Profile Builder page
│   │   └── workspace/
│   │       ├── crispy/                       # Frappe v15 Crispy Desk workspace
│   │       └── crispy_studio/                # Frappe v16+/dev-17 Crispy Studio workspace
│   ├── workspace_sidebar/
│   │   └── crispy_studio.json            # Frappe v16+/dev-17 curated Crispy Studio sidebar export
│   ├── desktop_icon/
│   │   ├── crispy_print.json             # Frappe v16+/dev-17 Crispy Print app icon export
│   │   └── crispy_studio.json            # Frappe v16+/dev-17 Crispy Studio sidebar link icon export
│   ├── templates/
│   │   └── pages/                        # Frappe website template package
│   ├── translations/                     # App translation CSV files
│   └── tests/                            # Backend API/helper tests
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

**Frappe Print Engine adapter:**

- **`crispy_print_engine.js`** registers `crispy_print` with `frappe.ui.form.register_print_engine` when the proposed Frappe Print Engine extension is present.
- The adapter passes document route context through `frappe.route_options` and opens `crispy-print-preview` directly.
- `install.ensure_print_engine()` creates or repairs the `crispy_print` Print Engine record only when the Frappe Print Engine DocType and controller are available, so standard Frappe installations continue using the existing Typst button path.

**Workspace:**

- **Crispy Studio** (`/desk/crispy-studio` on v16+, `/app/crispy` on v15) - Desk workspace for builder shortcuts, core records, reusable libraries, issued-document tracking, reports, regulatory setup, and settings.

**Core Files:**

Backend:

- **`api/v1/__init__.py`** - Stable whitelisted v1 RPC facade used by Frappe clients. Public method paths stay here while each endpoint declares an auditable facade policy for rate limiting, permissions, delegated deeper checks, or explicit low-risk exemptions.
- **`api/v1/compile.py`** - Server-side Typst compile flow, short-lived cache, asset resolution, and preview/PDF output.
- **`api/v1/images.py`** - Private image listing helpers for builder image fields.
- **`api/v1/docs.py`** - Permission-aware document fetch and formatted-value preparation using an explicit render-field payload contract for previews.
- **`api/v1/formats.py`** - Format listing, import/export, conflict detection, builder mode, and report-format lookup.
- **`api/v1/sample_formats.py`** - Company-neutral sample catalog listing and explicit format creation from app-owned examples.
- **`api/v1/branding_profiles.py`** - Branding Profile read/write APIs used by the profile builder and format preview flow.
- **`api/v1/reports.py`** - Report sample data, Typst source generation, combined preview compilation, and report PDF helpers.
- **`report_renderers.py`** - Report-family registry, renderer compatibility, curated sections, and upstream structural-source fingerprints. Report rendering remains WIP pending full acceptance testing.
- **`report_charts.py`** - Stable chart-spec normalization, accounting chart limits, accessibility summaries, theme normalization, and deterministic Lilaq/Frappe-SVG/omission policy.
- **`@local/crispy-charts:0.1.1`** - The only report-template chart API. It wraps vendored Lilaq 0.6.0 and compiles exclusively through the application package path.
- **`api/v1/document_codes.py`** - Document-code resolution and generation for regulatory/compliance workflows.
- **`api/v1/company_context.py`** - Shared company extraction, presentation-settings company parsing, and final effective-company resolution for backend render paths.
- **`api/v1/_common.py`** - Small shared API helpers for string cleanup, truth coercion, version parsing, and target-company validation.
- **`api/v1/security.py`** - Shared permission checks, endpoint policy decorators, rate limits, path validation, and RPC input hardening.
- **`crispy_print.permissions`** - Company User Permission-aware query conditions and target-company authorization helpers for company-scoped Crispy records.
- **`crispy_print.defaults`** - Shared one-default-per-scope enforcement using database advisory locks and batched clearing for defaultable Crispy records.
- **`crispy_print.render_contract`** - Shared render-contract field registry used by format export/import/duplicate paths and template snapshot, immutability, and hash logic.
- **`crispy_print.template_resolution`** - Shared Crispy Template resolver for target filtering, company/global fallback, effective-date filtering, version ordering, explicit-template validation, and list/result payload projection.

Frontend:

- **`CrispyPFB.vue`** - Main format builder shell with visual layout, raw Typst, report, and settings surfaces.
- **`CbpBuilder.vue`** - Branding Profile Builder shell for presentation-system authoring.
- **`CrispyPP.vue`** - Preview shell with format selection and compile/download controls.
- **`crispy_print_engine.js`** - Lightweight optional adapter for Frappe's proposed pluggable print engine handoff.
- **`useStore.ts`, `useReportStore.ts`, `useSettingsStore.ts`** - State modules for document layout, report modes, and presentation settings.
- **`JSONToTypst.ts`, `branding.ts`, `cbpBuilderTypst.ts`** - Typst generation paths for formats and branding profile specimens.
- **`safeSvg.ts`** - Browser-side SVG sanitization before preview injection.

Data model:

- **`Crispy Format`** - Format registry for DocType, Report, and Contract format records.
- **`Crispy Template`** - Frozen, versioned approved render contract published from a Crispy Format.
- **`Crispy Issued Document`** - Immutable issued-document registry (CID) with verification tokens and revocation/supersession state, plus artifact, trust-event, and regulatory-submission child tables.
- **`Crispy Branding Profile`** - Reusable company presentation profile, including semantic report-theme tokens that do not depend on a specific report family.
- **`Crispy Typst Block`** - Governed reusable Typst snippet library with generated snake_case reference keys, major/minor versions, company-aware override support, and a preview-only authoring builder.
- **Report renderer fields on `Crispy Format`** - `report_scope`, `report_renderer`, linked report rows, and source fingerprint replace the removed `Crispy Generic Report` classification model.
- **`Crispy Print Settings`** - Single DocType for global font, rendering, and print-policy configuration.
- **`Crispy QR Regulatory Profile`**, **`Crispy Fiscal Credential`**, **`Crispy Document Code Profile`**, and **`Crispy Document Code Rule`** - Compliance-oriented document identity and verification layer.

Sample data policy:

- **No production `Crispy Format` fixtures** - The app intentionally does not export `Crispy Format` records through `hooks.py` fixtures.
- **No report-format seeding** - Renderer metadata and native templates ship as application code, but installation and migration do not create report formats for any company.
- **`examples/formats/`** - Curated sample payloads are app-owned JSON files and become site data only when a user creates a format from the builder Examples dialog or sample catalog API.
- **`dev_utils/`** - Rich local demo-data generation remains developer-only and is not treated as production app surface.

Permission policy:

- **Company User Permissions** - Non-manager users with Company User Permission records are restricted to matching company-scoped Crispy Print records in list/report queries.
- **Compatibility default** - Users without Company User Permission records keep existing unrestricted visibility, which avoids breaking single-company or unconfigured beta sites.
- **Manager bypass** - `System Manager` and `Crispy Print Manager` bypass company query filters and can perform cross-company duplication.
- **Designer authoring** - `Crispy Print Designer` can author mutable design records and publish templates from writable formats, while still using the same Company User Permission boundaries as other non-manager users.

Default policy:

- **One default per scope** - `Crispy Format` and `Crispy Branding Profile` use a shared advisory-lock helper when setting defaults.
- **Dynamic format scopes** - Report resolution considers exact linked reports, company/global scope, compatible renderer formats, and generic fallbacks; linked report defaults compete when their report rows overlap.

Render payload policy:

- **Layered presentation** - Effective report presentation resolves through system, Branding Profile, renderer, explicit format override, and runtime layers. Report structure remains separate from brand identity.

- **Requested fields first** - Builder preview requests only the document fields referenced by the current layout or raw Typst source before loading the source document.
- **Safe essentials** - `get_formatted_doc` always includes `doctype`, `name`, `docstatus`, `modified`, and the Crispy print context needed by render helpers.
- **Legacy compatibility** - Callers that omit `fields` still receive the older broad formatted document payload during the compatibility window.
- **Document-code preview gate** - Document Code Profile QR preview is opt-in per request and skips custom-method rules in preview/read contexts.
