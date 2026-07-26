# Report Preview and Output

Crispy Print treats a report preview as a live query result rendered through an
approved or draft report format. It is not an issued business document, and it
never creates a Crispy Issued Document (CID).

This guide covers filter transfer, retained preview data, pagination,
localization, PDF.js behavior, and operational limits. For authoring and
publishing policy, see [Report Format Lifecycle](report-format-lifecycle.md).

## Opening a report preview

The **Crispy Print** action on an ERPNext report copies the report's current
filter values into the standalone preview route. Query Report values, including
dates, checkboxes, links, multi-select values, and report-specific options, are
serialized as data rather than reconstructed from labels.

The selected `Crispy Format` company is authoritative. If the report exposes a
Company filter, Crispy Print displays that exact company name as read-only and
does not allow route or browser state to substitute another company.

Changing any report input invalidates the retained result. The user must choose
**Run Preview** again before compiling with the new inputs. Presentation-only
changes do not rerun the ERPNext report.

## Retained result and security boundary

**Run Preview** executes the ERPNext report once and stores the complete
normalized result in Frappe's expiring cache for 15 minutes. The browser
receives a random snapshot handle and lightweight metadata, not a second copy
of every report row.

Each handle is bound to:

- the report name;
- the session user that created it;
- a random identifier for the originating preview tab;
- the effective company;
- the 15-minute cache lifetime.

Every reuse rechecks Report read permission and current Company User
Permissions. A missing or expired snapshot, another user or tab, a changed
session, or lost report/company permission fails closed and asks the user to
run the preview again.

Snapshots are execution caches only. Crispy Print does not store their rows in
`File`, application-error logs, `Crispy Report Output Audit`, or CID records.

Builder-only choices such as columns, widths, filter display, summaries,
totals, typography, layout, and presentation are projected over the retained
result. Compile requests made while another compile is running are coalesced so
only the latest genuinely changed presentation intent is replayed.

## Complete result and Typst input

Crispy Print does not apply a default row, column, payload, or long-cell
truncation limit. The complete ERPNext result is retained unless an API caller
explicitly supplies `limit`.

During compilation, normalized rows are written to a private temporary
`crispy-report-data.json` file and loaded through Typst `json()`. The data is
not embedded in the generated Typst source or exposed as a public asset. Its
content hash participates in compile-cache identity, and the temporary file is
removed with the compile workspace.

## Basic report pagination contract

Generator version 4 applies the following rules to managed Basic report
formats:

- report table headers repeat on every page;
- group and section headings are full-width, non-breakable, and kept with the
  following content where possible;
- subtotal, calculation, and grand-total rows do not split across pages;
- detail rows remain breakable so unusually long descriptions can continue
  rather than overflow;
- the row before a subtotal or grand total is kept with that total where
  possible;
- the report header and branding footer repeat through the page shell;
- the footer shows localized `Page current / total`;
- selected orientation and explicit column widths remain authoritative.

Existing frozen templates are not rewritten when the generator changes. Open
and save the Basic format, complete compatibility review, then publish a new
template version to adopt the current pagination contract.

## Language, RTL, and accounting values

Basic report generation consumes the effective presentation language. Arabic,
Persian, Hebrew, and Urdu language prefixes select RTL report text and textual
table columns while numeric and currency cells remain explicitly LTR.

The generator:

- passes Typst language and region separately;
- uses the selected font followed by Arabic and Inter fallbacks;
- preserves Typst bidirectional shaping for mixed Arabic/English text;
- translates report labels through Frappe;
- reformats retained Date, Datetime, and Time values for the selected language;
- keeps currency precision, minus signs, and page-number digits stable.

Accounting output currently uses the Latin `latn` numbering system
intentionally. Arabic-Indic digits are not selected implicitly from the
document language.

The same direction contract now applies to the builder UI, managed DocType
formats, Basic reports, previews, and final PDF compilation. Interface language
and effective print language remain independent, while accounting values and
other identifier-like content stay explicitly LTR.

## PDF.js preview behavior

Complete report previews compile the same PDF artifact used by output actions.
The packaged PDF.js worker parses it locally, while the viewer retains only a
five-page window around the current viewport.

For each retained page, the viewer creates:

- a device-pixel-ratio-capped canvas for visual output; and
- a matching PDF.js text layer for native text selection and copy.

Canvas backing stores and text-layer DOM are cleared when a page leaves the
window. Placeholder canvases remain at `0 x 0`, avoiding the browser's default
offscreen canvas allocation on reports with hundreds of pages. Canvas and text
layer use the same PDF viewport and shared preview-stage zoom. Each retained
text-layer container receives PDF.js's required `--scale-factor` from that
page's actual viewport before text rendering, keeping glyph positioning aligned
with the canvas without relying on a global or hard-coded scale.

The text layer provides selection and copy only. Full-document search indexing
and enhanced semantic screen-reader navigation are intentionally deferred
unless user demand justifies those separate features. Mixed-direction copied
text still follows the ordering encoded in the PDF and should be checked for
the intended Arabic/English layout.

## Output actions and audit history

Preview and ordinary view compilation create no persistent audit record.
Runtime downloads recompile with `output_action="download"` and create an
immutable `Crispy Report Output Audit` containing hashes and lifecycle metadata
only. API callers can request an audited print compile with
`output_action="print"`. The current browser Print button reuses the compiled
preview PDF and does not create another audit event.

The audit record contains no report rows, raw filter values, Typst source, or
PDF binary and never creates a CID. See
[Report Format Lifecycle](report-format-lifecycle.md#4-preview-view-print-and-download)
for the recorded fields and publication relationship.

## Large-report operations

Lazy page rendering bounds browser canvas and text-layer work, but it does not
reduce ERPNext execution time, Typst compilation time, PDF transfer size, or
PDF page-metadata parsing. Very large reports can still be expensive.

The current benchmark recommends future binary transfer near an 8 MiB PDF
threshold and bounded background compilation when early signals exceed roughly
5,000 rows or 10 MiB of normalized JSON. These are starting thresholds from one
real workload, not enforced product limits. See
[Report Preview Operational Benchmark](report-performance-benchmark.md).

## Acceptance checklist

Before approving a report format, test:

1. required, optional, boolean, date, link, and multi-select filters;
2. empty, ordinary, grouped, subtotal-heavy, and final-total results;
3. narrow and wide column sets plus long values;
4. first, middle, and last pages of a multi-page PDF;
5. repeated headers, group boundaries, subtotals, and footer page numbers;
6. negative, zero, and high-precision currency values;
7. target language, RTL direction, mixed text, and embedded fonts;
8. text selection and copied values at Fit, 100%, and manual zoom;
9. chart rendering and fallback diagnostics where applicable;
10. download audit metadata, browser Print behavior, and the absence of CID
    creation.
