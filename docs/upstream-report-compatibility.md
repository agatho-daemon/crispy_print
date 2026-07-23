# Upstream ERPNext Report Compatibility

Crispy Print report renderers depend on the structure of upstream Frappe and
ERPNext reports. An upgrade can change a report without causing a compilation
error, so compatibility must be reviewed deliberately before a new upstream
version is declared supported.

## What is checked automatically

Renderer metadata contains a compatibility review covering:

- installed Frappe and ERPNext versions and major-version support;
- the existence and enabled state of every report assigned to the renderer;
- renamed custom reports that reference a missing standard report;
- non-standard or reference-report records that may override expected behavior;
- a composite SHA-256 fingerprint of the relevant HTML, JavaScript, JSON, and
  Python report sources;
- the stored fingerprint from the last accepted review.

The source fingerprint intentionally covers more than the print HTML. Filter
definitions commonly live in JavaScript, while columns, grouping, totals, and
accounting rules commonly live in Python. Changing any reviewed file therefore
produces `review_required`.

Supported upstream majors are Frappe/ERPNext 15, 16, and the current
development 17 line. A supported major is not automatically an accepted patch:
source or structural drift still requires review.

## Structural snapshots

Source changes indicate that review is needed, but the review should compare
actual report output as well. The development utility captures a privacy-safe
contract containing no report rows:

- filter names used by the fixture;
- returned column fieldnames, labels, and field types;
- total-row flags;
- grouping and hierarchy metadata keys;
- chart type;
- renderer family and installed versions;
- a deterministic contract fingerprint.

Capture one snapshot for every representative filter scenario:

```bash
bench --site fdev.local execute \
  crispy_print.dev_utils.upstream_report_compatibility.capture \
  --kwargs '{
    "report": "General Ledger",
    "filters": {
      "company": "Example Company",
      "from_date": "2026-01-01",
      "to_date": "2026-12-31"
    }
  }'
```

Store reviewed snapshots with the release evidence or test fixture that owns
the sample data. Compare snapshots with
`compare_snapshots(expected, current)`. A difference identifies removed and
added filters, columns, semantic row keys, total behavior, chart type, or
renderer classification.

## Review procedure

Perform this process after an ERPNext/Frappe update, when a fingerprint warning
appears, or when an installed application replaces a Report record.

1. Record the exact Frappe, ERPNext, and Crispy Print versions.
2. Run renderer metadata and resolve every registry issue.
3. Review the upstream source diff for filters, columns, totals, grouping,
   indentation, charts, and empty-result behavior.
4. Capture and compare structural snapshots for representative fixtures.
5. Run the focused renderer and report API test suites.
6. Compile representative PDFs for normal, empty, grouped, total-heavy,
   negative/zero, wide-column, and multi-page results.
7. Inspect the PDFs against the ERPNext report view.
8. Record intentional version-specific differences in release notes and
   regression fixtures.
9. Only after acceptance, acknowledge the new composite fingerprint.

Acknowledgement is explicit and requires write permission on the Report
format:

```javascript
await frappe.call({
  method:
    "crispy_print.api.v1.acknowledge_report_renderer_compatibility",
  type: "POST",
  args: { format_name: "My General Ledger Format" },
});
```

Acknowledgement does not modify the renderer or suppress registry/version
issues. It records only that the current source set has been reviewed.

## Renamed reports

Do not silently map an unfamiliar renamed report to an accounting renderer.
Confirm that its output contract is equivalent, add the new name to the
renderer registry, retain the old name only while the upstream version still
provides it, and add tests for both intended version branches.

A custom Report whose `reference_report` points to a missing standard report is
reported as a rename candidate, not accepted automatically.

## Custom application overrides

A report with `is_standard != "Yes"` or a `reference_report` is treated as a
custom override. The generic renderer remains the safe default until the
override's filters, columns, totals, grouping, and permissions have been
reviewed.

Custom applications may legitimately extend a report. In that case, keep a
site-specific structural snapshot and repeat the compatibility review whenever
either ERPNext or the custom application changes.

## Version-specific policy

- Keep shared behavior in the renderer when report contracts are equivalent.
- Add a narrow, tested version branch only when upstream contracts genuinely
  differ.
- Do not branch only on version when feature or field detection is sufficient.
- Never drop unknown columns, totals, or grouping rows silently.
- Treat a compiling PDF as necessary but insufficient evidence.

The compatibility warning is deliberately advisory: it prevents silent trust
in changed accounting output while allowing designers to inspect and repair a
format.
