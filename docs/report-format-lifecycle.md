# Report Format Lifecycle

Report output has a different lifecycle from issued business documents. Crispy
Print uses immutable templates for approved report layouts and lightweight
report-output audit records for output history, but reports never create
Crispy Issued Document (CID) records.

## Lifecycle stages

### 1. Draft format

A `Crispy Format` is the editable authoring record. Report Builder saves update
this draft in place; individual draft edits are not versioned.

Builder preview is allowed to use the draft directly so designers can iterate.
It is not evidence that the format has been approved for operational use.

### 2. Compatibility review

Before publication, the report format must:

- target exactly one enabled Report through **Selected Reports**;
- use the current Basic report generator signature, or use intentional Advanced
  Raw Typst;
- contain the current acknowledged upstream renderer fingerprint;
- belong to the company used for publication.

One frozen template cannot target several reports. Use separate report formats
when reports need independent approval and version histories.

See [Upstream ERPNext Report Compatibility](upstream-report-compatibility.md)
for the fingerprint review and acknowledgement process.

### 3. Published template

Publishing creates an immutable, Approved `Crispy Template` snapshot. It freezes
the Typst source, layout, effective presentation settings, company, report
target, PDF standard, package/render facts, version, and snapshot hash.

- A **minor** bump is appropriate for compatible visual or presentation
  changes that preserve the report's accounting interpretation.
- A **major** bump is appropriate for intentional structural or semantic
  changes requiring fresh operational acceptance.
- Publishing an active version supersedes the previous active version in the
  same report, source-format, and company scope.
- Superseded and retired templates remain as immutable history and cannot be
  deleted through normal document operations.

Templates preserve approved layout history. They do not freeze the report's
business rows because every execution may use different filters and live ERP
data.

### 4. Preview, view, print, and download

Ordinary preview and view compilation does not create an audit record. The
standalone runtime recompiles a successful download with
`output_action="download"` and records a metadata-only report output event.
API callers can request the same behavior for an explicit print compile with
`output_action="print"`. The browser toolbar's current Print action reuses the
already compiled preview PDF and therefore does not create a separate audit
record.

Audited download and print events are stored as immutable
`Crispy Report Output Audit` records,
linked to the selected `Crispy Format`. The event records:

- report, format, renderer, and action;
- acknowledged renderer fingerprint;
- active template name, version, and snapshot hash when one exists;
- SHA-256 of the canonical filter payload, without storing filter values;
- SHA-256 of the generated PDF;
- PDF standard, page count, and returned row count;
- user and event time.

No report rows, generated Typst source, PDF binary, or raw filter values are
stored in this audit record.

## Why reports do not use CID

CID represents an issued business document with a stable source identity and
historical issuance state. A report is a query result produced from filters and
live data; treating every report download as an issued document would create
misleading issuance semantics and excessive persistent data.

The report output audit answers the narrower audit question: who requested
which report output, with which approved layout facts and output hashes. It
does not claim that the report was legally issued, signed, submitted, or
historically reproducible from stored row data.

## Default-format precedence

When no format is explicitly selected, Crispy Print resolves report formats in
this order:

1. exact selected-report format for the effective company;
2. exact selected-report global format;
3. compatible renderer-wide format for the effective company;
4. compatible renderer-wide global format;
5. generic company format;
6. generic global format.

Within each level, a format marked **Default** wins; remaining ties are ordered
by format name. An explicit user selection always wins over the automatic
default for that request.

Company-specific formats therefore take priority over global fallback only
within the same targeting level. An exact global format is preferred over a
company renderer-wide fallback because it was deliberately authored for that
report.

## Generator and renderer migrations

A generator signature or renderer fingerprint change never rewrites an
existing published template:

- active and historical templates retain their frozen source and hash;
- draft Basic formats with an old generator signature must be opened and saved
  in the Report Builder to regenerate;
- a changed upstream renderer must complete compatibility review and
  fingerprint acknowledgement;
- new publication is blocked until both checks pass;
- migration does not seed report formats or publish templates automatically.

This separates historical preservation from future approval. Existing frozen
templates remain inspectable, while new versions cannot accidentally bless
stale generated code or unreviewed ERPNext changes.

## Operational checklist

1. Create or edit one company-scoped format for one report.
2. Run representative preview fixtures.
3. Resolve compatibility warnings.
4. Save the current generated Basic source, or review Advanced Typst.
5. Publish a minor or major immutable template version.
6. Make it active only after acceptance.
7. Confirm default resolution for company and global scopes.
8. Perform a test download and inspect the linked report-output audit metadata.
9. Retire or supersede templates; do not delete history.
