# Usage

_Part of the [Crispy Print documentation](README.md)._

### Print Format Workflow

The typical workflow for using Crispy Print:

1. **Create or select Branding Profile** -> define reusable page, typography, table, logo, letterhead, and QR defaults
2. **Create Crispy Format** -> select format type and target DocType/report
3. **Design in builder** -> compose sections, fields, tables, assets, QR elements, and Typst blocks
4. **Save and set default** -> enable the Typst button for that DocType
5. **Open document** -> click `Typst` -> preview and download PDF

### Output Settings: PDF Standard And Print Policy

Each Crispy Format exposes a **PDF Standard** control. It defaults to **PDF/A-2u** for archival business documents; **PDF/A-3u** suits embedded machine-readable payloads (XML/JSON), and **PDF 1.7**, **PDF 2.0**, and **PDF/A-4** are available for non-archival or authority-specific needs. PDF/A embeds fonts, so selected fonts must permit embedding/subsetting.

Site-wide print behavior is governed by **Crispy Print Settings** (see [Font Configuration](fonts.md)):

- **Allow Print for Draft** (with optional **Always Add Draft Heading**)
- **Allow Print for Cancelled**
- **Render Timeout Seconds** for each Typst render or font-discovery command

### Company Scope And Approved Templates

Crispy Print is company-aware end to end:

- Format, template, branding profile, and Typst block resolution is filtered and ordered by **Company**, with company-scoped default selection.
- A **Crispy Template** is a frozen, approved render contract published from a Crispy Format. It stores an immutable snapshot, snapshot-hash version, PDF standard, and Typst/Zebra/barcode facts, and supports company-specific templates with fallback to global templates.
- A **Crispy Issued Document** (CID) records an immutable issued snapshot linked to a frozen template, exposing non-sensitive verification metadata and an opaque verification token, with revocation/supersession state.

### Report Builder Workflow (Dual Mode)

For `Crispy Format Type = Report`, builder now supports two editing modes:

- **Basic mode**: non-technical controls generate a managed Typst report template
- **Advanced mode**: direct Raw Typst editing

Key behavior:

1. **Basic to Advanced** is always allowed.
2. **Advanced to Basic** only unlocks full Basic editing when the template is still Basic-managed.
3. If custom Raw Typst changes are detected, Basic opens in **read-only** with options to:
   - stay in Advanced mode, or
   - reset/regenerate the Basic template.

This keeps report editing accessible while protecting advanced customizations.

Reports are still **WIP** in alpha 3. Treat the current report flow as a stabilization target for testing, not as a final report publishing contract.

### Branding Profile Workflow

Branding Profiles centralize presentation settings that should not be duplicated across every format:

1. Create a **Crispy Branding Profile** for the company.
2. Configure page size, margins, typography, table style, letterhead, logo, and QR defaults.
3. Open the Branding Profile Builder to preview the generated Typst specimen.
4. Attach the profile to Crispy Formats that should inherit the same presentation system.

### Compact Table Labels

For narrow item tables, compact table mode can render each item column as collapsed
cell content with configurable labels. Use compact labels when the printed cell
needs a clearer field name than the source DocField label or when space is too
tight for a normal multi-column item table.

### Builder Health And Preview Diagnostics

The builder settings pane includes a collapsed **Diagnostics** section that flags common
setup problems before preview or publish, including missing format, DocType, or
company setup, default-format status, unsupported PDF standards, branding profile
context, unavailable configured fonts, raw/report Typst source state, stale
generated report Typst, unresolved Typst Blocks, and unsaved changes.

Use **Diagnostics** in runtime preview to inspect the resolved format/template
context, company, branding profile, PDF standard, Typst version, page count,
render time, cache-hit state, and raw Typst mode.

### Letterhead, Headers, And Footers

Crispy Print does not treat headers and footers as mandatory separate HTML-style blocks. That separation comes from legacy browser-print workflows where letterheads were often just images placed at the top of a page and headers/footers had to be managed as separate template regions.

Crispy Print uses Typst and SVG/PDF-oriented composition instead. A letterhead can be a full-page SVG asset sized exactly to the document page, with the header, footer, watermark, borders, legal text, brand marks, and other static elements already composed into the page background.

When Crispy Print is installed, it extends Frappe **Letter Head** records with lifecycle metadata and validation. The Branding Profile and builder flows use this metadata to filter selectable letterheads by company, active status, approval state, effective dates, and supersession.

For many business documents, the recommended model is:

```text
Full-page SVG letterhead/background
+ structured Typst document content
+ optional dynamic QR, document code, signatures, tables, and totals
-> deterministic PDF/SVG output
```

Use separate Crispy Typst Blocks for headers, footers, or repeated sections only when those elements are dynamic, conditional, or data-driven. Static brand furniture usually belongs in the page-sized letterhead/background asset or Branding Profile.

### Document Code and Regulatory QR Workflow

Use this layer only when documents need deterministic identifiers or machine-verifiable compliance payloads:

1. Create a **Crispy QR Regulatory Profile** for the relevant authority/country behavior.
2. Add **Crispy Fiscal Credential** records for company/environment-specific identity values.
3. Configure **Crispy Document Code Profile** and related rules.
4. Use QR or document-code fields in the format or branding profile.

### Advanced: Creating Formats Without Default

You can create multiple formats for the same DocType without setting them as default:

- Access via direct URL: `/app/crispy-print-preview/{doctype}/{docname}/{format_name}`
- Or programmatically via API (see [API Reference](api-reference.md))

### Common Layout Recipes

**Invoice with Logo and Table:**

1. Section 1 (2 columns): Company logo left, Invoice details right
2. Section 2: Customer information
3. Section 3: Items table (drag "items" table field)
4. Section 4: Totals (align right)
5. Section 5 (footer): Terms and conditions

**Certificate:**

1. Enable letterhead background
2. Section 1: Centered title
3. Section 2: Recipient name (large font)
4. Section 3: Certificate text
5. Section 4: Signatures (3 columns)
6. Add QR code in corner for verification

**Report with Branded Page Background:**

1. Use a Branding Profile or full-page SVG background for static report furniture
2. Section 1: Dynamic report title and date
3. Section 2: Summary metrics (4 columns)
4. Section 3: Data table
5. Section 4: Charts or dynamic visual sections where applicable
