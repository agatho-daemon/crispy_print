# Architecture

_Part of the [Crispy Print documentation](README.md)._

### Build System

This app uses **Frappe's native esbuild bundler** - no separate Vite or webpack setup required.

- **Main Builder Bundle:** `crispy_print/public/js/crispy_print.bundle.js`
- **Preview Bundle:** `crispy_print/public/js/crispy_preview.bundle.js`
- **Desk Button Bundle:** `crispy_print/public/js/report_button.bundle.js`
- **Build Command:** `bench build --app crispy_print`
- **Loading Model:** Lightweight desk hooks plus page-specific builder/preview bundles
- **Plugin:** Uses `frappe-vue-style` to automatically inline Vue SFC styles

### Current Product Structure

This alpha structure is documented here for orientation only. It is expected to keep evolving before beta.

```
crispy_print/
├── crispy_print/
│   ├── hooks.py                          # Frappe hooks, fixtures, desk assets
│   ├── install.py                        # Install-time setup helpers
│   ├── json_utils.py                     # Shared JSON parsing/coercion helpers
│   ├── letterhead_lifecycle.py           # Letter Head lifecycle fields and validation
│   ├── config/
│   │   └── __init__.py                   # Frappe config package marker
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
│   │   └── vendor/
│   │       ├── fonts/                    # Bundled fonts (optional)
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
│   │   │   ├── crispy_generic_report/        # Generic report definition
│   │   │   ├── crispy_template/              # Frozen approved render contract
│   │   │   ├── crispy_issued_document/       # Issued-document registry (CID) + child tables
│   │   │   └── crispy_print_settings/        # Global font, render, and print policy (Single)
│   │   ├── page/
│   │   │   ├── crispy_format_builder/        # Format Builder Desk page
│   │   │   ├── crispy_print_preview/         # Print Preview Desk page
│   │   │   └── cbp_builder/                  # Branding Profile Builder page
│   │   └── workspace/
│   │       └── crispy_print/                 # Crispy Print Desk workspace
│   ├── workspace_sidebar/
│   │   └── crispy_print.json             # Frappe v16 curated sidebar export
│   ├── desktop_icon/
│   │   └── crispy_print.json             # Frappe v16 app/category icon export
│   ├── templates/
│   │   └── pages/                        # Frappe website template package
│   ├── translations/                     # App translation CSV files
│   └── tests/                            # Backend API/helper tests
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

- **Crispy Print** (`/desk/crispy-print` on v16+, `/app/crispy-print` on v15) - Desk workspace for builder shortcuts, core records, reusable libraries, issued-document tracking, reports, regulatory setup, and settings.

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
- **`Crispy Template`** - Frozen, versioned approved render contract published from a Crispy Format.
- **`Crispy Issued Document`** - Immutable issued-document registry (CID) with verification tokens and revocation/supersession state, plus artifact, trust-event, and regulatory-submission child tables.
- **`Crispy Branding Profile`** - Reusable company presentation profile.
- **`Crispy Typst Block`** - Governed reusable Typst snippet library.
- **`Crispy Generic Report`** - Generic report definition for report-type formats.
- **`Crispy Print Settings`** - Single DocType for global font, rendering, and print-policy configuration.
- **`Crispy QR Regulatory Profile`**, **`Crispy Fiscal Credential`**, **`Crispy Document Code Profile`**, and **`Crispy Document Code Rule`** - Compliance-oriented document identity and verification layer.
