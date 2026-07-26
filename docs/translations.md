# Translations

_Part of the [Crispy Print documentation](README.md)._

Crispy Print uses GNU gettext catalogs under `crispy_print/locale/`. The
application source is English, `main.pot` is the generated source catalog, and
each PO file contains one locale's translations.

## Included locales

| Language | Locale | Catalog |
| --- | --- | --- |
| Arabic | `ar` | `ar.po` |
| German | `de` | `de.po` |
| Spanish | `es` | `es.po` |
| Persian | `fa` | `fa.po` |
| French | `fr` | `fr.po` |
| Hindi | `hi` | `hi.po` |
| Indonesian | `id` | `id.po` |
| Italian | `it` | `it.po` |
| Brazilian Portuguese | `pt_BR` | `pt_BR.po` |
| Russian | `ru` | `ru.po` |
| Thai | `th` | `th.po` |
| Turkish | `tr` | `tr.po` |
| Vietnamese | `vi` | `vi.po` |
| Simplified Chinese | `zh` | `zh.po` |

The initial catalogs provide complete coverage of the 1,542 messages currently
extracted into `main.pot`. They combine existing Frappe/ERPNext community
translations with machine-assisted translations for Crispy Print-specific
strings.

Complete catalog coverage does not mean every translation has received native
review. Contributors are encouraged to improve terminology, tone, and clarity.
Accounting, regulatory, certificate, fiscal, and issued-document terminology
deserves particular care.

## Runtime scope and RTL

The PO catalogs translate the Crispy Print application interface and other
strings passed through Frappe's translation APIs. Interface and output
directions are deliberately independent:

- The Frappe user language controls the builder and preview interface.
- The format's effective print language controls the preview and compiled PDF.
- Field semantics control value isolation inside the document.

Arabic and Persian are the engineering acceptance locales. Hebrew and Urdu use
the same generic direction engine but do not yet ship catalogs or native
acceptance coverage. Managed DocType and Report output sets Typst language,
region, and base direction; identifiers and accounting values stay LTR while
prose follows the document direction. Latin accounting digits remain the
default.

- Builder panels, menus, dialogs, drawers, focus order, and directional icons
  mirror in RTL.
- The page canvas, Typst source, coordinates, dimensions, filenames, URLs,
  hashes, color values, and numeric controls remain physical LTR islands.
- Mixed Arabic/Persian and Latin prose is shaped by Typst under the document
  direction.
- A successful gettext validation does not prove that a translated string fits
  its control, that an RTL panel is positioned correctly, or that a PDF uses an
  appropriate font.

Native Arabic/Persian review of linguistic, accounting, and regulatory output
is a production-release gate. It is intentionally not a code-merge gate.

See [Report Preview and Output](report-preview-and-output.md#language-rtl-and-accounting-values)
and [Known Limitations](limitations.md) for the wider rendering contract.

## Contributing

Translations can be contributed through normal pull requests; an external
translation-management service is not required.

1. Edit the existing `crispy_print/locale/<locale>.po` file with a gettext
   editor such as Poedit, Weblate, or a text editor.
2. Change `msgstr` values only. Do not edit `main.pot` by hand.
3. Preserve placeholders such as `{0}`, `{1}`, and `%s`.
4. Preserve HTML tags and all literal content inside `<code>` elements.
5. Keep Crispy Print, Typst, ERPNext, Frappe, PDF, SVG, QR, JSON, XML, API, URL,
   and DocType unchanged unless the locale has a well-established convention.
6. Remove a `fuzzy` flag only after reviewing the translation against its
   current English source and UI context.
7. State whether the contribution is native-reviewed and identify areas that
   still need product or regulatory review.

New locales should use a standard Frappe/Babel locale code and must be generated
from the current POT catalog rather than copied from another language:

```bash
bench create-po-file <locale> --app crispy_print
```

## Updating catalogs

When application strings change:

```bash
bench generate-pot-file --app crispy_print
bench update-po-files --app crispy_print
```

`generate-pot-file` extracts the current source strings into `main.pot`.
`update-po-files` adds new messages to every PO file, retains matching
translations, and removes obsolete catalog entries. Review the resulting diff
before translating the new or changed entries.

## Validation and compilation

Validate all PO files with GNU gettext:

```bash
find apps/crispy_print/crispy_print/locale -maxdepth 1 -name '*.po' -print0 \
  | xargs -0 -n 1 msgfmt --check --check-format -o /dev/null
```

Then compile the runtime MO files:

```bash
bench compile-po-to-mo --app crispy_print --force
```

Translation pull requests should also confirm:

- every PO catalog matches the current `main.pot` message and context set;
- no translated message is empty;
- source and translation contain the same runtime placeholders;
- source and translation preserve the same HTML tag structure;
- `<code>` contents remain byte-for-byte unchanged; and
- no temporary machine-translation tokens remain in output.

Compiled MO files are generated under `sites/assets/locale/` and are not
committed to the application repository.
