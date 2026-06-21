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

### Future Features

The following areas are planned or under active stabilization:

- [ ] Expand Crispy Typst Block as the Typst-native replacement component layer for reusable field renderers, table blocks, address blocks, QR/regulatory blocks, headers, footers, signatures, payment sections, and custom document components
- [ ] Batch printing from list view
- [ ] Progress indicator for multi-document compilation
- [ ] Configurable batch size limits
- [ ] Multi-language document rendering (per-format `default_print_language` and UI translations exist; render-time language switching and RTL not yet wired)
- [ ] Report publishing stabilization
- [ ] Contract authoring workflow
- [ ] Signature, certificate, timestamp, and authority-submission workflows building on the issued-document trust-event and regulatory-submission tables, after feedback from regulated regions
- [ ] Builder-side draft format version history
- [ ] Digital-signature and archival workflows beyond PDF/A
- [ ] Machine-verifiable document workflow extensions
