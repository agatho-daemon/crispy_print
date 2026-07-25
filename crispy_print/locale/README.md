# Crispy Print translations

`main.pot` is the source catalog generated from the application. Each `<locale>.po`
file contains translations for one language and can be edited with any gettext
editor, including Weblate, Poedit, or Crowdin.

For the locale list, review status, RTL scope, maintenance commands, and complete
contribution policy, see [`docs/translations.md`](../../docs/translations.md).

## Contributing

1. Edit the existing PO file for your locale. Do not edit `main.pot` by hand.
2. Preserve placeholders such as `{0}`, `%s`, HTML tags, and text inside `<code>`.
3. Keep product and technical names such as Crispy Print, Typst, ERPNext, Frappe,
   PDF, QR, JSON, and API unchanged unless the locale has an established convention.
4. Remove a `fuzzy` flag only after reviewing that entry.
5. Validate and compile your changes:

   ```console
   bench update-po-files --app crispy_print --locale <locale>
   bench compile-po-to-mo --app crispy_print --locale <locale> --force
   ```

Machine-assisted translations are intended as a complete starting point. Native
speakers are encouraged to improve terminology, tone, and regulatory language.

When application strings change, regenerate and synchronize the catalogs:

```console
bench generate-pot-file --app crispy_print
bench update-po-files --app crispy_print
```
