# Overview & Vision

_Part of the [Crispy Print documentation](README.md)._

## Why Crispy Print Exists

For more than a decade, ERP printing systems across the industry have largely relied on HTML templates, browser rendering, wkhtmltopdf, and print-specific CSS workarounds. While functional, these approaches introduced long-standing problems that businesses and developers learned to tolerate:

- Unstable pagination and broken page breaks
- Inconsistent PDF rendering across engines and environments
- Layout drift after browser, CSS, or wkhtmltopdf changes
- Weak typography and fragile headers/footers
- Difficult long-table handling
- Unreliable absolute positioning for regulated or pre-printed forms
- Browser-dependent output that is hard to audit or reproduce

Crispy Print is designed to solve these problems at the architecture level by converting ERP data into a structured document model and rendering it through Typst as a real document, not as a simulated browser print page.

## What Makes Crispy Print Different

- **Deterministic PDF rendering** - The same input should produce stable output without browser-layout unpredictability.
- **Publication-grade document composition** - Clean typography, consistent spacing, precise alignment, and professional business-document output.
- **Structured rendering pipeline** - ERP data is transformed into a structured print model before Typst renders the final document.
- **True document engine architecture** - Built around document composition principles rather than browser-print workflows.
- **Stable multi-page layouts** - Designed for invoices, quotations, reports, vouchers, and technical documents with predictable pagination.
- **Precise layout control** - Suitable for invoices, certificates, regulatory forms, vouchers, compliance documents, and branded output.
- **Reusable branding profiles** - Centralized company styling, typography, page setup, letterhead, logo, QR, and table presentation settings.
- **Regulatory QR abstraction** - A foundation for machine-verifiable business documents and evolving compliance requirements.
- **Modern programmable publishing stack** - Uses Typst for structured, programmable, deterministic business-document generation.
- **Designed for ERP workflows** - Focused on operational business documents rather than generic desktop publishing.

## Technical Value For Admins

- **Server-side rendering through Typst CLI** keeps document generation consistent across user browsers.
- **Permission-aware APIs** respect Frappe read/write access for documents, formats, reports, Typst blocks, and document-code workflows.
- **Controlled asset handling** restricts Typst image/file inputs to approved site/app asset roots and rejects traversal, symlinks, external URLs, and unsafe duplicate filenames.
- **Rate-limited compile and report endpoints** reduce accidental server overload during heavy preview or PDF generation.
- **Compile caching** reduces repeated Typst work for unchanged preview inputs.
- **Centralized Branding Profiles** let admins enforce company-wide visual identity without editing every print format.
- **Manual release-gating friendly** workflows use `bench build`, `bench migrate`, `bench run-tests`, and `pre-commit` without requiring CI.
- **Auditable document-code foundation** supports QR/regulatory profile configuration separately from layout templates.

## Architectural Direction

Most ERP systems approach printing as:

```text
ERP Data -> HTML -> Browser -> PDF
```

Crispy Print instead approaches printing as:

```text
ERP Data -> Structured Document Model -> Typst -> Deterministic Business Document
```

This distinction changes layout stability, rendering quality, pagination behavior, compliance extensibility, document reliability, and long-term maintainability.

## Long-Term Vision

Crispy Print is not intended to be just another print designer. The long-term goal is to provide ERPNext with modern business-document infrastructure capable of supporting:

- Publication-grade invoices, quotations, vouchers, contracts, and compliance documents
- Digitally signed PDFs and archival workflows
- Machine-verifiable business documents
- Reusable enterprise branding systems
- Compliance-ready document workflows
- Technical and engineering documentation
- Future electronic-document ecosystems
