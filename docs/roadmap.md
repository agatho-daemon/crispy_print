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

### Future Features

The following areas are planned or under active stabilization:

- [ ] Expand Crispy Typst Block as the Typst-native replacement component layer for reusable field renderers, table blocks, address blocks, QR/regulatory blocks, headers, footers, signatures, payment sections, and custom document components
- [ ] Batch printing from list view
- [ ] Progress indicator for multi-document compilation
- [ ] Configurable batch size limits
- [x] Complete multi-language document rendering across the builder UI,
  managed DocType formats, and Basic reports, including language/region,
  RTL text, localized labels/dates, and stable LTR accounting values
- [ ] Complete report renderer acceptance testing for generic, receivable/payable, financial statement, General Ledger, and Bank Reconciliation families
- [ ] Validate report layouts with representative filters, empty and large datasets, multi-page output, charts, branding, RTL, and supported PDF standards
- [ ] Stabilize report publishing after renderer-family acceptance criteria pass
- [ ] Contract authoring workflow
- [ ] Signature, certificate, timestamp, and authority-submission workflows building on the issued-document trust-event and regulatory-submission tables, after feedback from regulated regions
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
- [ ] Compact table presets for common invoice, service, tax, and
  serial/batch layouts
- [ ] Crispy Template publish notes/history with active/retired versions and
  snapshot-hash visibility
- [ ] Saved Report preview presets
- [ ] Export bundles containing formats, Branding Profiles, Typst Blocks, and
  related configuration
- [ ] Import dry-run summaries for creates, overwrites, renames, and skips
