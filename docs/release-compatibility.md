# Release and Compatibility Gates

_Part of the [Crispy Print documentation](README.md)._

Crispy Print treats compatibility as evidence attached to a specific commit,
not as a permanent claim about a moving Frappe branch. A release candidate is
ready for engineering sign-off only when every automated gate below passes for
that exact commit.

## Supported Matrix

| Target | Frappe/ERPNext | Payments | Python | Node | Required evidence |
| --- | --- | --- | --- | --- | --- |
| Frappe/ERPNext v15 | `version-15` | `version-15` | 3.11 | 24.18.0 | Clean install, repeated migration, backend suite, asset build |
| Frappe/ERPNext v16 | `version-16` | `version-16` | 3.14 | 24.18.0 | Clean install, repeated migration, backend suite, asset build |
| Frappe/ERPNext dev-17 | `develop` | `develop` | 3.14 | 24.18.0 | Clean install, repeated migration, backend suite, asset build |

The development target is moving. A passing dev-17 result applies only to the
upstream revisions resolved by that CI run and must be repeated before each
release.

The server workflow in `.github/workflows/ci.yml` creates a fresh MariaDB site
for every matrix entry, installs the matching official Payments and ERPNext
branches before Crispy Print, migrates twice to expose non-idempotent patches,
builds only Crispy Print's production assets, and runs the complete backend
application suite. Payments is an ERPNext test/runtime companion app in these
benches; it is not a Crispy Print package dependency and is not installed by a
normal Crispy Print installation. The workflow must not use Bench's implicit
default Frappe branch.

## Release-Candidate Checklist

For the exact candidate commit:

1. Require all three **Server** matrix jobs and the **Frappe Linter** workflow
   to pass.
2. Run the full frontend suite, strict TypeScript, pre-commit, and the
   production Bench asset build with Node 24.18.0 and Yarn Classic 1.22.x.
3. Run the opt-in real-Typst integration suite with Typst 0.15+, `pdftoppm`,
   and `pdftotext`.
4. Run the authenticated RTL and QR Playwright suites on a disposable site;
   inspect retained failure artifacts rather than committing them.
5. On a clean acceptance site, export and import representative schema-v4
   formats, publish a template, change its source format, and confirm the
   frozen snapshot and hash remain unchanged.
6. Capture the installed Frappe/ERPNext versions and the upstream Report
   renderer compatibility snapshots described in
   [Upstream Report Compatibility](upstream-report-compatibility.md).
7. Confirm that Arabic changes made after Agathodaemon's native review on
   2026-07-28 have received renewed review where affected. Complete native
   Persian linguistic review and professional jurisdiction review for every
   regulatory profile claimed as production-ready. Automated engineering tests
   cannot approve these gates.

Typical local engineering commands are:

```bash
pre-commit run --all-files
yarn test:unit
yarn --cwd crispy_print/public/js typecheck:strict
CRISPY_PRINT_RUN_TYPST_INTEGRATION=1 \
  yarn --cwd crispy_print/public/js vitest run \
  tests/batch19/rtlCompile.integration.test.ts
bench --site your-disposable-site run-tests --app crispy_print
bench build --app crispy_print
```

Frappe v16 and dev-17 use `/desk`; v15 uses `/app`. Compatibility browser
jobs must set `CRISPY_E2E_DESK_PREFIX=/desk` for v16/dev-17. Set
`CRISPY_E2E_SKIP_SCREENSHOTS=1` only for cross-version functional smoke tests:
the repository-owned visual baselines belong to the authoritative v15
viewport. HTTPS development sites with local certificates are supported by the
Playwright configuration; production certificate validation is a separate
deployment concern.

Use a disposable site for clean-install acceptance:

```bash
bench new-site crispy-release.local \
  --db-root-password 'local-root-password' \
  --admin-password 'local-admin-password'
bench get-app --branch version-15 payments https://github.com/frappe/payments.git
bench --site crispy-release.local install-app payments
bench --site crispy-release.local install-app erpnext
bench --site crispy-release.local install-app crispy_print
bench --site crispy-release.local migrate
bench --site crispy-release.local migrate
```

Never place database, Administrator, or browser credentials in the repository,
shell history, screenshots, or retained test artifacts.

Select `version-16` for Payments on a v16 bench and `develop` on a dev-17
bench. Keep these branch choices explicit: the moving Payments `develop`
branch is not a substitute for `version-16`.

## Current Engineering Evidence

The 2026-07-28 local v15 run used Frappe 15.116.0, ERPNext 15.118.0,
Node 24.18.0, Yarn 1.22.22, and Typst 0.15.1. Two consecutive migrations,
the production asset build, strict TypeScript, 283 default frontend tests,
the clean-site backend suite, and two real-Typst RTL/PDF tests passed. The
authenticated RTL matrix and all 9 Custom/Regulatory QR browser, decoding, and
PDF-parity checks also passed.

Disposable v15, v16, and dev-17 sites were then created on independent local
benches, Payments was pinned to the matching branch, and installation plus
two consecutive migrations succeeded. The same uncommitted primary source then
passed all 461 backend tests on each runtime (5 optional skips per runtime).
Functional RTL browser smoke on both v16 and dev-17 passed 8 cases covering
Arabic/Persian UI and documents, mixed UI/document direction, physical LTR
controls, keyboard/drag behavior, multipage output, and the deterministic
Report fixture; the opt-in published-template case was skipped because those
disposable fixtures were not published.

Focused Custom/Regulatory QR browser smoke also passed 7 cases on each
compatibility target. The runs covered English, Arabic, and Persian Custom QR
editing, exact ordered fields on Purchase Invoice, machine-decoded Custom QR
final-PDF parity, a genuinely resolved and validated regulatory profile, and
the editable legacy Basic QR warning and save block. Delivery Note and Payment
Entry cases were skipped because those two disposable compatibility fixtures
were unavailable; the primary v15 run passed the complete 9-case matrix.

Compatibility testing of uncommitted primary changes may use the v15 checkout
through `PYTHONPATH` without dirtying the compatibility clones, but that is
development evidence only. The final release claim still requires all CI jobs
to pass the exact committed candidate SHA.

The tracked source was 15.37 MiB in this audit. No `node_modules`,
`test-results`, Playwright report, screenshot-baseline, or root `tmp` content
was tracked. Those development-only directories remain ignored and are not
part of normal Bench installation.

Local credentials, site database names, and generated test data are deliberately
not recorded in this repository. Compatibility evidence must identify the
framework, ERPNext, Payments, and Crispy revisions without embedding secrets.
