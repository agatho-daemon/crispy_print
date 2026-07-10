# Changelog

All notable changes to Crispy Print will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Working Beta Changes

- Raw Typst document authoring is now a working beta path for authors who want full Typst control: builder-owned presentation controls are hidden, raw code refresh is explicit, and compile helpers are constrained to the author-facing raw API.
- Regular builder image insertion, private uploaded image lookup, font-face-aware typography controls, and menu layering fixes are working beta changes intended for real template testing during stabilization.

### Added

- Added a file-based **Sample Format Catalog** under `crispy_print/examples/formats/` so example formats can ship with the app without being installed as site data.
- Added builder **Examples** workflow for creating a company-scoped Crispy Format from a curated sample only when a user explicitly chooses it.
- Added sample catalog APIs: `list_sample_formats`, `get_sample_format`, and `create_format_from_sample`.
- Added starter samples for Sales Invoice, Quotation, Purchase Order, and a Raw Typst Payment Entry receipt voucher.
- Added an optional Frappe Print Engine adapter in preparation for a Frappe PR that loosens the hardcoded native print flow and allows apps to register print engine entry points.
- Added `crispy_print/public/js/crispy_print_engine.js` to register `crispy_print` through `frappe.ui.form.register_print_engine` and route document print handoffs directly to `crispy-print-preview`.
- Added install/sync setup that creates or repairs the `crispy_print` Print Engine record when the Frappe Print Engine DocType and controller are available.
- Added raw Typst authoring helpers for private images and reusable Typst blocks, including `crispy_image("filename")` and `crispy_block("block-document-id")`.
- Added a Crispy Image picker for regular builder mode with private image search, upload, and size controls.
- Added font-face discovery metadata so typography controls can show only the styles and weights available for the selected font family.

### Changed

- Removed automatic `Crispy Format` fixture shipping. Sample formats now live as app-owned JSON examples and are copied into site data only through the explicit Examples workflow.
- Tightened company permission boundaries for company-scoped Crispy Print records. Branding Profile reads now use permission-aware list/read checks, and Duplicate/Create-from-Sample target-company inserts require manager access or matching Company User Permission access before internal `ignore_permissions=True` writes run.
- Added explicit, auditable facade policies to all whitelisted `crispy_print.api.v1` endpoints so rate limits, permission gates, delegated deeper checks, and low-risk exemptions are declared consistently.
- Hardened `get_formatted_doc` into an explicit render-payload endpoint. Builder previews now request only referenced document fields, child-table payloads are narrowed to requested columns, and Document Code Profile QR preview requires an explicit allow flag while skipping custom-method rules.
- Centralized one-default-per-scope enforcement for Crispy Format and Crispy Branding Profile through a shared advisory-lock helper, reducing race windows while preserving existing default scope behavior.
- Centralized Crispy Template resolution into a shared backend service so list, preview, render, publish-adjacent, and issued-document paths use one target/company/effective-date/version ordering rule set.
- Centralized render-contract field mapping so Crispy Format export/import/duplicate fields and Crispy Template snapshot, immutability, and snapshot-hash fields are derived from one registry.
- Updated Crispy Print Preview to consume document context from `frappe.route_options` when opened through the optional Frappe print-engine handoff, while preserving direct route segment fallback.
- Updated preview lifecycle handling to unmount the existing Vue preview before mounting a new document preview.
- Changed Raw Typst mode to be author-controlled: presentation/page/table/typography controls are hidden in the builder, raw code changes no longer auto-compile, and refresh happens through the Refresh button or Command/Ctrl-Enter.
- Changed raw Typst block helper generation so only blocks referenced by `crispy_block("...")` are inlined into the compile source.
- Changed the field palette to separate Crispy Fields from document fields and keep generic Crispy Typst Block and Crispy Image entries above the document metadata fields.
- Changed builder menus to render through a shared floating-menu path so nested menus stay above layout content.
- Changed bundled font organization so Inter lives under `public/vendor/fonts/Inter/` instead of duplicate parent-folder copies.

### Fixed

- Fixed stale preview reuse when opening multiple documents in the same Desk session by clearing consumed `frappe.route_options` and remounting the preview for each new document/format context.
- Fixed uploaded site font discovery by passing absolute private font directories to Typst.
- Fixed duplicate font-family entries caused by combining Typst-reported family names with filename-derived fallback names.
- Fixed typography fallback caused by selecting unavailable weights or styles for a chosen font family.
- Fixed regular-mode preview refresh behavior around keystroke-heavy controls by keeping invalid intermediate values from compiling until they become valid.
- Fixed Raw Typst helper source generation so reusable block bodies are not injected unless referenced by `crispy_block("...")`.
- Fixed raw private image handling so `crispy_image()` resolves only approved private uploaded filenames and rejects public paths, traversal, nested paths, URLs, unsupported extensions, and missing files.
- Fixed optional Print Engine setup and tests so sites without the future Print Engine controller skip that integration path instead of failing.

### Removed

- Removed the production `fixtures/` sample data path, including the old `fixtures/crispy_format.json` file and `fixtures = [{"dt": "Crispy Format"}]` hook.
- Removed company-specific demo/sample data from the install/migrate surface. Existing sites keep their already-created `Crispy Format` records, but future installs and migrations no longer import or overwrite sample formats automatically.

### Tests

- Added backend and frontend coverage for the Sample Format Catalog, explicit sample creation, fixture removal, and builder Examples flow.
- Added backend coverage for Company User Permission query conditions, manager bypass, Branding Profile read checks, and target-company duplicate authorization.
- Added backend coverage that audits every whitelisted v1 facade endpoint for explicit policy metadata and checks representative rate/permission gates.
- Added backend and frontend coverage for requested-field formatted document payloads, child-table narrowing, document-code preview gating, and worker cache separation by field set.
- Added backend coverage for shared default locking/clearing behavior and Crispy Format/Branding Profile default-scope delegation.
- Added backend coverage for shared Crispy Template resolver target validation, company/global fallback parity, effective-date filtering, and explicit-template validation.
- Current frontend gate: `yarn test:unit` passed 223 tests across 57 test files.
- Current backend gate: `bench --site fdev.local run-tests --app crispy_print` passed 342 tests with 2 skipped.

## [0.2.0-beta.1] - 2026-07-01

### Beta Release Notes

- First beta release for Frappe v15, Frappe v16, and current dev-17 as tested on 2026-07-01.
- Typst CLI `0.15.0` or newer is required.
- Report support is available for beta testing, with Basic and Advanced report format flows still subject to refinement.
- Contract format support remains foundation-level and is not yet a final contract-authoring workflow.

### Added

- Added a public **Crispy Print** Desk workspace with grouped shortcuts and cards for builders, core records, reusable library records, issued-document tracking, reports, and regulatory setup.
- Added the Crispy Print workspace icon to the Desk icon sprite hook.
- Added Frappe v16 Desktop Icon exports for the hidden Crispy Print app tile and visible Crispy Studio sidebar link.
- Added the Crispy Print desktop icon and workspace configuration.
- Added Frappe v16 app/sidebar metadata for Crispy Print.
- Added PDF standards support for Typst PDF output.
- Added company-scoped Crispy Template render paths.
- Added company-aware format/template resolution with scoped defaults.
- Added stable company-scoped frozen render contracts, including template snapshot and letterhead lifecycle support.
- Added configurable render settings, typography controls, site font directory setup, and bundled variable fonts.
- Added configurable labels for compact table cells so compact item output can show clearer field names.
- Added one-click **Duplicate for Company** support in the builder for cloning Crispy Formats or frozen Crispy Template snapshots to another company, including target-company presentation retargeting and snapshot-preserving template duplication.
- Added a collapsed builder Diagnostics section for missing format/DocType/company setup, default-format status, unsupported PDF standards, branding profile context, multiple default Branding Profile candidates, unavailable configured fonts, raw/report Typst source state, stale generated report Typst, unresolved Typst Blocks, and unsaved changes.
- Added runtime preview diagnostics with resolved format/template, company, branding profile, PDF standard, Typst version, render time, page count, cache-hit metadata, and raw Typst mode.
- Added automatic Crispy Typst Block reference-key generation from the block name using snake_case naming.
- Added a **Crispy Typst Block Builder** page for editing reusable block Typst code with live SVG preview, preview-only page settings, and a dedicated lazy-loaded Desk bundle.
- Added canonical lowercase Crispy Template IDs and a migration patch to rename existing templates so template document names and runtime template keys match.
- Added immutable Crispy Template delete protection through DocType permissions and a backend delete guard.
- Added issued-document creation from successful runtime PDF actions, storing final generated Typst source and a persisted SHA-256 `typst_source_hash`.
- Added backend CID idempotency so repeated issuance of the same source document, frozen template, and Typst source hash returns the existing CID.
- Added CID PDF reprint actions that compile the stored Typst source directly for view, download, and print without resolving templates or creating another CID.
- Ignored local Zed editor and Pyright configuration files.

### Changed

- Bumped app version to `0.2.0-beta.1`.
- Renamed the print preview Desk Page route from `/app/crispy-print` to `/app/crispy-print-preview` so `/app/crispy-print` can cleanly belong to the Crispy Print workspace.
- Updated document and report preview buttons to route to `crispy-print-preview`.
- Updated README route references and component documentation for the new workspace and preview page route.
- Renamed the Frappe v16 Workspace Sidebar export from **Crispy Print** to **Crispy Studio** to avoid a Desktop Icon name collision with the app tile.
- Split the README into focused `docs/` topic files and formatted documentation with Prettier.
- Refreshed README and docs for Frappe v16 app navigation.
- Require Typst 0.15.0 or newer so variable font support is available.
- Refined the Crispy Print preview template workflow.
- Updated Typst compile responses to include optional diagnostics metadata for preview troubleshooting.
- Aligned license metadata and log formatting fallbacks.
- Refined compact item table value metadata used by Typst rendering and field extraction.
- Changed new Crispy Typst Block document IDs to use the generated reference key and `v1.0`-style version suffixes, with numeric duplicate suffixes only for document ID collisions.
- Changed Crispy Typst Block versions to default to `1.0` and validate as major/minor values.
- Changed Crispy Typst Block Builder dirty-state tracking so the page is marked unsaved only when Typst code changes; preview page settings remain authoring-only.
- Changed direct Print Preview access to open a context-selection modal for DocType previews, with graceful guidance for report and contract preview states.
- Simplified the Crispy Typst Block Builder to focus on page settings and Typst code editing, leaving identity metadata on the DocType form and letting editor/preview panes scroll independently.
- Changed Crispy Issued Document snapshot creation to create issued records with `Issued` issuance status, `Valid` integrity status, and `issued_at` instead of draft registry entries.
- Changed Crispy Issued Document snapshot creation to rely on source-document read permission instead of requiring Crispy Print Manager permission.

### Fixed

- Avoided using the app icon hook on Frappe 16 and newer.
- Added Crispy Print app tile permission checks so the app tile is only shown to users with access.
- Fixed compact item print output to collapse item columns in compact table layouts.
- Fixed a caught Typst page-size bug where UI labels such as `Letter` compiled to invalid paper names like `letter` instead of Typst identifiers such as `us-letter`; US paper aliases now resolve consistently across block previews, document generation, preview workers, and preview sizing.

### Known Limitations

- CID historical reprints compile the stored Typst source. Crispy Print does not snapshot every referenced binary asset into the database; operators should retain mutable referenced files, especially company logos and image assets, when exact historical visual replay is required.

### Tests

- Tightened the report button unit test to assert the exact `crispy-print-preview` route.
- Added backend coverage for Crispy Print/Crispy Studio Desktop Icon and Workspace Sidebar lifecycle contracts.
- Added Crispy Typst Block tests for generated reference keys, `1.0` version normalization, versioned document IDs, and numeric duplicate suffixes.
- Added tests for PDF standards, company-scoped template/render behavior, frozen render contracts, Duplicate for Company format/template flows, render settings, Typst version validation, preview diagnostics metadata, and compact table label/metadata rendering.
- Added tests for canonical Crispy Template IDs, template delete protection, CID issued snapshot creation, Typst source hashing, CID idempotency, and CID stored-source PDF rendering.
- Current backend gate: `bench --site fdev.local run-tests --app crispy_print` passed 277 tests with 2 skipped.

## [0.1.0-alpha.3] - 2026-05-28

### Alpha Release Warning

- Feature work is frozen for alpha 3 so testers can focus on regressions, data migration issues, and workflow gaps before beta.
- Report support is still WIP. Report preview and report PDF generation are available for testing, but behavior and templates may still change before beta.

### Added

- Added **Crispy Branding Profile** for reusable company/page/typography/table/branding/QR presentation settings.
- Added **Crispy Branding Profile Builder** page with visual controls for page setup, typography, tables, logo, letterhead, QR placement, and code-only Typst preview.
- Added automatic default branding profile provisioning after install and via a post-model-sync backfill patch.
- Added **Crispy Typst Block** and **Crispy Typst Block Applicable Document** for reusable Typst snippets that can be inserted into builder layouts.
- Added report-format support through linked report rows and generic/custom report format selection.
- Added dual-mode report builder support: Basic visual mode for common report layouts and Advanced Raw Typst mode for custom templates.
- Added **Crispy QR Regulatory Profile**, **Crispy Fiscal Credential**, **Crispy Document Code Profile**, and **Crispy Document Code Rule** for document-code and regulatory QR workflows.
- Added **Crispy Issued Document** as a foundation DocType for future immutable issued-document snapshots, opaque verification tokens, artifact tracking, revocation/supersession state, and verification summaries.
- Added **Crispy Issued Document Artifact** child table for future archival PDF, PDF/A, rendered SVG, XML/JSON payload, signature, certificate, authority receipt, and related artifact storage.
- Added **Crispy Issued Document Trust Event** child table scaffold for future signature, certificate, timestamp, validation, revocation-check, and trust-chain events.
- Added **Crispy Issued Document Regulatory Submission** child table scaffold for future authority submission, sandbox validation, response payload, authority reference, and submission-status workflows.
- Added document-code APIs for resolving and generating encoded document values.
- Added QR regulatory profile and fiscal credential API helpers.
- Added issued-document API scaffolding for reading CID records, resolving verification tokens, returning minimal verification summaries, and reserving the future snapshot-creation API shape.
- Added report preview source/compile API flow, including `compile_report_preview`.
- Added safer SVG sanitization utilities and tests for preview rendering.
- Added dedicated Typst worker helper modules for compilation, PDF actions, document loading, autocomplete, escaping, and setup cleanup.
- Added performance benchmark helper at `crispy_print.dev_utils.perf_benchmarks.run`.
- Added many frontend and backend tests covering branding profiles, document codes, Typst blocks, reports, workers, SVG safety, and US series fixes.

### Changed

- Bumped app version to `0.1.0-alpha.3`.
- Reworked presentation settings from page-specific settings into a broader normalized presentation-settings model.
- Updated existing Crispy Format behavior to support Branding Profiles, report formats, Advanced/Basic report mode state, and Typst block resolution.
- Updated Crispy Issued Document artifact modeling from flat parent attachment fields to child-table artifact rows so future multi-artifact, multi-page, signature, certificate, and authority receipt workflows can evolve without a parent-schema redesign.
- Updated report preview and report PDF flows to support report filters, column selection, charts, branding assets, and Typst overrides.
- Updated preview compilation to use filtered document fields and normalized image assets.
- Updated report format lookup to avoid loading every candidate format document when resolving custom report formats.
- Updated Desk asset loading so heavy Crispy builder/preview bundles are lazy-loaded on Crispy pages instead of loaded globally on every Desk page.
- Updated README for alpha 3 testing, current test counts, and manual CI/release-gating status.
- Updated test configuration and TypeScript strict coverage for newer frontend modules.

### Security

- Added shared API security helpers for permission checks and rate limiting.
- Added rate limits to compile, report, QR/document-code, format-list, and parity endpoints.
- Hardened Typst compilation asset handling with path traversal checks, allowed asset roots, symlink rejection, external/data URL rejection, duplicate basename detection, and safer file copying.
- Limited Typst source, chart SVG, QR payload, inline data URI, import, and report payload sizes.
- Added safer chart SVG extraction/validation and fallback handling.
- Added SVG sanitization for preview rendering.
- Restricted report parity checks and sensitive helper APIs behind manager/read permissions.

### Performance

- Added short-lived Typst compile result caching keyed by source, output format, assets, chart SVG, QR data, Typst binary, and font context.
- Combined report preview source generation and SVG compilation into one API request for report preview workflows.
- Reduced global Desk page load weight by lazy-loading the heavy Crispy Vue bundles only when builder/preview pages are opened.
- Avoided repeated SVG DOM replacement when rendered preview page content is unchanged.
- Added byte capping for frontend undo history snapshots.
- Added document fetch caching for preview worker document loading.

### Fixed

- Fixed several raw Typst, Typst escaping, image asset, worker lifecycle, and preview race-condition edge cases.
- Fixed report builder mode synchronization and report selector behavior.
- Fixed format import/export and format-loader error handling edge cases.
- Fixed document payload formatting for HTML/Text Editor fields and child-table formatter failures.
- Fixed compile cache fallback so mocked or unresolved asset paths still follow the normal compile asset-copy path.

### Tests

- Current frontend suite: 175 tests across 52 test files.
- Current backend suite: 168 test methods across 16 test files.
- Added module-level backend coverage for the new DocTypes and APIs.
- Added worker, SVG safety, report preview, report builder, document-code, and branding-profile frontend/backend tests.

### Known Limitations

- Reports remain WIP for alpha 3 and need focused tester feedback before beta.
- Crispy Issued Document, issued-document artifacts, trust events, and regulatory submissions are foundation scaffolding only. Their field structure and usage are placeholders until feedback is collected from users in regulated tax/QR regions.
- QR-related DocTypes and CID regulatory/trust fields need real-world validation from regulated regions before their structure, required fields, payload mapping, and usage guidance are finalized.
- Full `bench --site <site> run-tests --app crispy_print` may depend on site/ERPNext test fixtures; module-level Crispy tests are the current reliable manual release check.

### Breaking / Migration Notes

- This alpha changes the presentation settings and builder data model. Back up existing formats before updating.
- Run `bench migrate` after updating so new DocTypes and backfill patches are applied.
- Open migrated formats in the builder and verify layout, table columns, branding, QR settings, and raw Typst snippets before using them for important documents.

## [0.1.0-alpha.2] - 2026-03-28

### Changed

- Bumped app version to `0.1.0-alpha.2`.

## [0.1.0-alpha.1] - 2025-01-03

### ⚠️ Alpha Release Warning

This is an early alpha release. Expect bugs and breaking changes. Not recommended for production use.

### Added

- Visual layout builder with drag-and-drop interface (Vue 3)
- Typst compilation engine for PDF/SVG generation
- Real-time preview with mock and live document data
- Letterhead integration (foreground/background modes)
- QR code field support
- Table rendering with customizable columns
- Page settings (size, orientation, margins)
- Typography controls (fonts, sizes, weights, colors)
- Multi-format support per DocType with default format selection
- Format cloning and import/export functionality
- Comprehensive test suite (90 tests: 61 frontend + 29 backend)

### System Requirements

- Frappe Framework v15+
- Typst CLI 0.11.0+
- Python 3.10+
- Node.js 18+ (for development)
- MariaDB/PostgreSQL

### Known Limitations

See [README.md - Known Limitations](README.md#known-limitations) for full list.

### Dependencies

- `@simonwep/pickr` ^1.9.1 (color picker)
- Vue 3, Pinia (state management)
- Vite, Vitest (testing)

[0.2.0-beta.1]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.2.0-beta.1
[0.1.0-alpha.3]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.3
[0.1.0-alpha.2]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.1
