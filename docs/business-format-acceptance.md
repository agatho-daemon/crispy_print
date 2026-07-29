# Core v1 Business-Format Acceptance

_Part of the [Crispy Print documentation](README.md)._

Crispy Print ships company-neutral starter formats for the core day-to-day
business documents below. Samples are application JSON files; installation and
migration never create company records or formats automatically. A designer
creates an editable company-scoped copy through the builder **Examples**
dialog.

| Starter | Target | Accepted use |
| --- | --- | --- |
| Payment Entry Voucher | Payment Entry | Customer receipt and supplier payment voucher |
| Remittance Advice | Payment Entry | Supplier remittance/payment advice |
| Stock Entry Movement | Stock Entry | Internal movement, consumption, and manufacture-entry presentation |
| Material Request Requisition | Material Request | Purchase/material requisition |
| Journal Entry Voucher | Journal Entry | General, cash, and petty-cash voucher presentation |
| Statement of Account | General Ledger | Period statement/account activity |
| Accounts Receivable Aging | Accounts Receivable | Customer aging output |
| Accounts Payable Aging | Accounts Payable | Supplier aging output |
| POS Invoice Thermal | POS Invoice | 80 mm thermal receipt |
| POS Invoice A4 | POS Invoice | Full-page invoice |

## Acceptance evidence

The repository verifies this catalog at four levels:

- backend tests prove that every catalog entry has a valid sample, targets live
  ERPNext metadata, creates a company-scoped format, and retains its declared
  page profile;
- frontend tests generate Typst from all managed layouts and validate the
  Report renderer bindings and repeating report headers;
- opt-in integration tests compile the managed documents and the 80 mm Raw
  Typst receipt with the real Typst binary;
- authenticated Playwright checks render customer/supplier payments,
  remittance, stock movement, requisition, ordinary and cash/petty-cash Journal
  Entries, both POS variants, and all three accounting reports into PDF.js
  canvases.

Run the disposable-site browser seed:

```bash
bench --site fdev.local execute \
  crispy_print.dev_utils.business_formats_e2e.seed \
  --kwargs '{"test_user_password":"<temporary-password>"}'
```

Use the returned document names as the `CRISPY_V1_E2E_*` variables described
in `CODEX_HANDOFF.md`, then run:

```bash
yarn --cwd e2e playwright test business-formats.spec.ts
```

Restore the site afterward:

```bash
bench --site fdev.local execute \
  crispy_print.dev_utils.business_formats_e2e.cleanup
bench --site fdev.local execute \
  crispy_print.dev_utils.rtl_e2e.disable_test_user
```

The seed is for disposable development/test sites only. Cleanup is deliberately
scoped to fixed Crispy v1 fixture names and draft records.

## Acceptance boundary

This gate proves that the starter formats load, generate valid Typst, compile,
and render representative ERPNext records. It does not replace the separate
production-report gate for customized reports, every filter combination,
empty/very large datasets, charts, branding variants, RTL combinations, or
every supported PDF standard. Native Persian and jurisdiction-specific
professional reviews also remain separate release gates.
