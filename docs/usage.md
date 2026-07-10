# Usage

_Part of the [Crispy Print documentation](README.md)._

### Print Format Workflow

The typical workflow for using Crispy Print:

1. **Create or select Branding Profile** -> define reusable page, typography, table, logo, letterhead, and QR defaults
2. **Create Crispy Format** -> select format type and target DocType/report
3. **Design in builder** -> compose sections, fields, tables, private images, QR elements, and Typst blocks
4. **Save and set default** -> enable the Typst button for that DocType
5. **Open document** -> click `Typst` -> preview and download PDF

### Sample Format Catalog

Crispy Print ships starter examples as app-owned JSON files under
`crispy_print/examples/formats/`. These files are not Frappe fixtures and are not
inserted during install or migrate.

Use the builder **Examples** dialog when you want to create a real format from a
sample:

1. Open **Crispy Format Builder**.
2. Expand the left **Fields** pane if it is collapsed.
3. Click **Examples**.
4. Select a sample format.
5. Choose the target **Company**.
6. Optionally change the format name and mark it as default.
7. Click **Create Format**.

The created record is a normal company-scoped **Crispy Format**. It can be saved,
edited, published as a Crispy Template, exported, duplicated for another company,
or deleted like any user-created format.

Current samples include regular builder starters for Sales Invoice, Quotation,
and Purchase Order, plus a Raw Typst **Receipt Voucher** sample for Payment Entry.

> **Fixture removal note:** older beta builds shipped sample `Crispy Format`
> records through `fixtures/crispy_format.json`. That fixture path has been
> removed intentionally. Existing sites keep any records that were already
> imported, but new installs and migrations no longer create or overwrite sample
> formats automatically.

### Frappe Print Engine Integration

Crispy Print includes an optional adapter for the proposed Frappe Print Engine extension. That upstream change is intended to loosen Frappe's hardcoded native print flow by letting apps register client-renderer print engines.

When the Frappe extension and its controller are present:

1. Crispy Print creates or repairs a `crispy_print` **Print Engine** record during install/sync.
2. The engine points to `/assets/crispy_print/js/crispy_print_engine.js`.
3. The client script registers `crispy_print` with `frappe.ui.form.register_print_engine`.
4. If **Print Settings → Default Print Engine** is set to **Crispy Print**, Frappe's native **Print** action routes the document to `crispy-print-preview`.

The existing **Typst** document button is unchanged and remains the supported entry point on standard Frappe installations where the Print Engine extension is not available.

### Output Settings: PDF Standard And Print Policy

Each Crispy Format exposes a **PDF Standard** control. It defaults to **PDF/A-2u** for archival business documents; **PDF/A-3u** suits embedded machine-readable payloads (XML/JSON), and **PDF 1.7**, **PDF 2.0**, and **PDF/A-4** are available for non-archival or authority-specific needs. PDF/A embeds fonts, so selected fonts must permit embedding/subsetting.

Site-wide print behavior is governed by **Crispy Print Settings** (see [Font Configuration](fonts.md)):

- **Allow Print for Draft** (with optional **Always Add Draft Heading**)
- **Allow Print for Cancelled**
- **Render Timeout Seconds** for each Typst render or font-discovery command

### Company Scope And Approved Templates

Crispy Print is company-aware end to end:

- Format, template, branding profile, and Typst block resolution is filtered and ordered by **Company**, with company-scoped default selection.
- Company-scoped Crispy Print list/report surfaces honor Frappe **Company User Permission** records for non-manager users. If a user has no Company User Permissions, Crispy Print preserves the existing unrestricted behavior for compatibility.
- **System Manager** and **Crispy Print Manager** users bypass company query filters by design.
- **Crispy Print Designer** users can author formats, branding profiles, Typst blocks, and document-code profiles, and can publish frozen Crispy Templates from formats they can write. Designers remain bound by Company User Permissions and do not receive manager-only maintenance or cross-company bypass privileges.
- Cross-company format/sample/template duplication requires the user to be a manager or have access to the target Company before Crispy Print performs internal backend inserts.
- A **Crispy Template** is a frozen, approved render contract published from a Crispy Format. It stores an immutable snapshot, snapshot-hash version, PDF standard, and Typst/Zebra/barcode facts, and supports company-specific templates with fallback to global templates.
- A **Crispy Issued Document** (CID) records an immutable issued snapshot linked to a frozen template, exposing non-sensitive verification metadata and an opaque verification token, with revocation/supersession state.

### Reusable Typst Blocks

Use **Crispy Typst Block** records for governed Typst snippets that are reused across formats, such as dynamic headers, footers, signatures, payment sections, regulatory fragments, or other data-driven document components.

- **Block Name** is the designer-facing label.
- **Reference Key** is generated from Block Name using snake_case, for example `Invoice Header` becomes `invoice_header`.
- **Version** defaults to `1.0` and uses a major/minor format.
- The document ID combines the generated reference key and version, for example `invoice_header-v1.0`.

Layouts continue to reference blocks by Reference Key so company-specific block overrides can share the same key as a global block.

Raw Typst authors reference a reusable block by its Crispy Typst Block document ID, for example `#crispy_block("invoice_header-v1.0")`. Raw compile source only inlines block bodies that are actually referenced by `crispy_block("...")`.

Open the **Crispy Typst Block Builder** from a block form to edit the Typst code with live SVG preview. Click **Refresh** or press **Command/Ctrl-Enter** to compile after every change. The builder keeps preview page controls separate from the reusable block contract: the default preview uses A4 with `2.5cm` margins so document blocks, tables, grids, and long text render in a realistic page width. Turn on auto-size preview only for compact self-sizing blocks; Typst containers without explicit widths can stretch poorly on an auto-width page.

The builder's unsaved indicator tracks only **Typst Code** changes. Page size, margin, orientation, and default-preview toggles are authoring controls for the current preview and do not mark the reusable block as unsaved.

### Raw Typst Document Formats

Raw Typst mode is intended for authors who want to own the Typst source directly.
In this mode, builder presentation controls that would inject print behavior, page
settings, typography, or table settings are hidden. The preview compiles only when
the author clicks **Refresh** or presses **Command/Ctrl-Enter**.

The code editor still provides document data and small helpers:

- Dropping a document field inserts `#doc.fieldname`.
- Dropping **Crispy Typst Block** inserts `#crispy_block("")`.
- Dropping **Crispy Image** inserts `#crispy_image("")`.
- `crispy_block("block-document-id")` resolves reusable blocks by the Crispy Typst Block document ID.
- `crispy_image("filename.svg", width: 20mm)` resolves uploaded private files by filename.

Raw image filenames are resolved only from the site's private file directory. Public
paths, absolute paths, nested paths, URLs, traversal, unsupported extensions, and
missing files are rejected.

This is a working beta authoring path. Crispy Print still injects the document data
dictionary and the minimal helper definitions required for `crispy_block()` and
`crispy_image()`, but page setup, placement, typography, tables, headers, and
footers belong to the raw Typst source.

### Regular Builder Images And Typography

In regular builder mode, **Crispy Image** opens a panel for selecting or uploading a
private image and setting the rendered size. Placement remains part of the visual
layout, header/footer, preamble, or Raw Typst source depending on where the image is
used.

Typography controls use Typst-discovered font metadata. The family dropdown uses
Typst's canonical family names, while the style and weight dropdowns are restricted
to the faces available for that selected family. This avoids selecting a weight or
style that would compile with a fallback font.

### Duplicate For Company

Use **Duplicate** in the builder preview pane when the same document design should be reused for another company without manually rebuilding layout, typography, tables, Typst code, or print behavior.

- **Current Format** clones the saved Crispy Format to the target company, preserves layout/settings, clears inherited default status unless explicitly requested, and retargets company-scoped presentation fields such as branding company and logo company.
- **Template Snapshot** clones a frozen Crispy Template snapshot to another company by first creating a target-company Crispy Format from the template's immutable snapshot fields, then publishing a new target-company template from that cloned format.
- **Frozen Snapshot** mode is the recommended template duplication mode when the approved template content must remain stable even if the original source Crispy Format has changed since publication.
- **Current Format** mode for templates intentionally uses the template's current source Crispy Format, so it should be selected only when the latest saved format state is desired instead of the previously approved snapshot.

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

Reports are in beta stabilization. Treat the current report flow as a testing target for real report layouts, while expecting refinements before a stable report publishing contract.

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
context, multiple default Branding Profile candidates, unavailable configured
fonts, raw/report Typst source state, stale generated report Typst, unresolved
Typst Blocks, and unsaved changes.

Branding Profile defaults are treated as selection priority, not a hard
one-default-per-company rule. If imported or manually edited data leaves multiple
default profiles for a company, Diagnostics reports it and the user can still pick
the profile that fits the current format.

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
- Open through the optional Frappe Print Engine handoff when the site is running the proposed Frappe print-engine extension and Crispy Print is selected as the default engine.
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
