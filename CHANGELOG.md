# Changelog

All notable changes to Crispy Print will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Ignored local Zed editor and Pyright configuration files.

### Changed

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

### Fixed

- Avoided using the app icon hook on Frappe 16 and newer.
- Added Crispy Print app tile permission checks so the app tile is only shown to users with access.
- Fixed compact item print output to collapse item columns in compact table layouts.

### Tests

- Tightened the report button unit test to assert the exact `crispy-print-preview` route.
- Added backend coverage for Crispy Print/Crispy Studio Desktop Icon and Workspace Sidebar lifecycle contracts.
- Added tests for PDF standards, company-scoped template/render behavior, frozen render contracts, Duplicate for Company format/template flows, render settings, Typst version validation, preview diagnostics metadata, and compact table label/metadata rendering.

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

[0.1.0-alpha.3]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.3
[0.1.0-alpha.2]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.1
