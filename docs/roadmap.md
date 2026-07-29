# Roadmap

_Part of the [Crispy Print documentation](README.md)._

### Recently Added

- [x] Crispy Print Settings for global font configuration, render timeout, and draft/cancelled print policy
- [x] Per-format PDF Standard selection (PDF/A-2u default, plus PDF/A-3u, PDF/A-4, PDF 1.7, PDF 2.0)
- [x] Company-aware format/template resolution with company-scoped defaults
- [x] Crispy Template frozen approved render contracts with snapshot-hash versioning
- [x] Crispy Issued Document (CID) registry with verification tokens, artifact tracking, trust-event and regulatory-submission child tables, and revocation/supersession state
- [x] Frappe v16 curated Workspace Sidebar
- [x] Fully template-driven document preview
- [x] Beta 2 report publishing architecture for generic, receivable/payable, financial statement, General Ledger, and Bank Reconciliation families
- [x] Custom Document QR with ordered exact-field payloads, safe live DocType
  field selection, payload size diagnostics, and strict separation from
  registry-backed Regulatory Document Codes
- [x] Explicit legacy Basic QR compatibility: editable settings require manual
  reconfiguration while frozen published templates retain their prior output
- [x] Curated compact table presets for invoice items, service rows, tax rows,
  serial/batch rows, and compact POS rows, using exact live child-DocType
  fieldnames and logical RTL-aware ordering
- [x] Read-only Crispy Template publication history with active/superseded
  state, notes, versions, and snapshot-hash visibility
- [x] Non-mutating Crispy Format import dry runs with exact create, overwrite,
  rename, skip, warning, target-name, and permission-blocker summaries, plus
  explicit actions and browser-verified side-effect-free cancellation

### Required Before v1

These are release gates rather than optional feature expansion:

- [x] Complete multi-language document rendering across the builder UI,
  managed DocType formats, and Basic reports, including language/region,
  RTL text, localized labels/dates, and stable LTR accounting values
- [ ] Complete report renderer acceptance testing for generic, receivable/payable, financial statement, General Ledger, and Bank Reconciliation families
- [ ] Validate report layouts with representative filters, empty and large datasets, multi-page output, charts, branding, RTL, and supported PDF standards
- [ ] Stabilize report publishing after renderer-family acceptance criteria pass
- [x] Complete Custom and Regulatory QR engineering acceptance across export/import,
  publication/freeze, real QR scanning, preview/final PDF parity, permissions,
  value types, RTL interfaces, legacy blocking, and representative DocTypes
- [x] Complete native Arabic linguistic review. Agathodaemon reviewed Arabic
  on 2026-07-28 across the translated UI and representative RTL document/PDF
  acceptance output
- [ ] Complete native Persian linguistic review
- [ ] Complete jurisdiction-specific professional review for supported
  regulatory profiles
- [ ] Pass clean-install, migration, build, and smoke-test matrices on supported
  Frappe v15, v16, and current dev-17 targets. The explicit three-branch CI
  clean-install matrix and deterministic test bootstrap are in place; all jobs
  and focused compatibility smoke tests must pass for the release candidate
  commit before this gate is checked.
- [x] Accept the core v1 Payment Entry, remittance, inventory movement,
  Journal Entry, statement/aging, and in-scope POS formats

### Future Added Features

These features may be added after v1 without weakening the v1 render,
compatibility, or regulatory contracts:

- [ ] Expand Crispy Typst Block as the Typst-native replacement component layer for reusable field renderers, table blocks, address blocks, QR/regulatory blocks, headers, footers, signatures, payment sections, and custom document components
- [ ] Batch/list-view printing with multi-document progress and configurable
  batch limits
- [ ] Visual conditional layout visibility
- [ ] Contract authoring workflow
- [ ] Signature, certificate, timestamp, trust-chain, and authority-submission workflows building on the issued-document trust-event and regulatory-submission tables, after feedback from regulated regions
- [ ] Builder-side draft format version history
- [ ] Digital-signature and archival workflows beyond PDF/A
- [ ] Machine-verifiable document workflow extensions
- [ ] Extend Custom Document QR with explicit child-table/aggregation rules,
  custom labels, format overrides, payload templates, and JSON payloads
- [ ] Add operational QR use cases for document lookup, assets, items,
  serial/batch records, warehouses, tools, projects, sites, and shipments
- [ ] Add signed/revocable lookup URLs, minimal public payloads, and
  permission-aware scan actions that require normal ERPNext validation and user
  confirmation
- [x] Compact table presets for common invoice, service, tax, and
  serial/batch layouts
- [x] Crispy Template publish notes/history with active/retired versions and
  snapshot-hash visibility
- [ ] Saved Report preview presets
- [ ] Export bundles containing formats, Branding Profiles, Typst Blocks, and
  related configuration
- [x] Import dry-run summaries for creates, overwrites, renames, and skips,
  with explicit overwrite/copy actions and side-effect-free dismissal
- [ ] Resolve frozen Crispy Template snapshots for Report runtime after its
  report-template contract is finalized
- [ ] Full-document PDF search and enhanced semantic accessibility
- [ ] Real-time collaborative format editing
- [ ] Broader native chart coverage
- [ ] Consider hiding Check/boolean fields from default field discovery and
  generated layouts, with an explicit “Show boolean fields” opt-in and
  printable Yes/No, checkbox, or checkmark presentation. Existing authored and
  frozen layouts must remain unchanged.

### Future Business-Format Coverage

- [ ] Contracts, service reports, and completion certificates
- [ ] Salary Slip, Leave Application, and employment-letter templates
- [ ] Project summaries and Timesheet/Worklog output
- [ ] Asset handover/tag sheets and maintenance documents
- [ ] Work Order, BOM, and Production Plan formats
- [ ] Inspection and Non-Conformance Report formats
