# Troubleshooting & FAQ

_Part of the [Crispy Print documentation](README.md)._

## Troubleshooting

### Typst Not Found

```
Error running typst fonts: [Errno 2] No such file or directory: 'typst'
```

**Solution:** Install Typst CLI (see [Requirements](../README.md#requirements))

### Fonts Not Showing

**Check available fonts:**

```bash
typst fonts
```

From Frappe:

```bash
bench --site your-site execute crispy_print.api.v1.get_typst_local_fonts
bench --site your-site execute crispy_print.api.v1.get_typst_font_faces
```

If expected fonts are missing:

1. If the font was uploaded through Crispy Print Settings, verify **Enable Uploaded Fonts** is on.
2. Click **Refresh Font List** after uploading or replacing font files.
3. Verify the font is installed on the server running the bench when using system fonts.
4. Check `TYPST_FONT_PATHS` if fonts are stored outside bundled, uploaded, or system font directories.
5. Restart the bench after changing font paths.

If a selected font family appears but a weight or style renders with a fallback
font, check `get_typst_font_faces`. The builder only offers weights/styles Typst
reports for the selected family; unusual internal font naming may still require
choosing the closest available face and verifying the preview.

### Format Not Appearing in Document

If Typst button doesn't show or format isn't available:

1. **Verify installation:**

   ```bash
   bench --site your-site list-apps | grep crispy_print
   ```

2. **Check format has layout_json:**
   - Open Crispy Format document
   - Ensure it was saved via builder (not manually created)

3. **Check default selection:**
   - At least one format must be marked default for the target DocType
   - Non-default formats can still be opened by direct preview URL

4. **Verify permissions:**
   - User needs read access to Crispy Format doctype
   - Check Role Permission Manager

5. **Check browser console** for API errors

### Compilation Errors

**"Typst compiler not found"**

Solution: Install Typst CLI (see [Requirements](../README.md#requirements))

**"Compilation timed out"**

Causes:

- Server under heavy load
- Infinite loop in raw Typst code

Solutions:

- Simplify layout
- Check raw Typst syntax

**"Letterhead image not found"**

Causes:

- Letter Head document doesn't have image field
- Image file deleted from /files/

Solution:

- Re-upload letterhead image
- Verify file path in Letter Head document

### Docker and reverse-proxy deployment errors

#### PDF viewer fails to load a JavaScript module

**Symptom:** The browser reports `Failed to fetch dynamically imported module`,
or rejects a PDF.js module because of its content type. A file can return HTTP
200 and still be rejected by the browser.

Current builds publish the PDF.js module and its worker as versioned `.js`
assets. Both must be served with a JavaScript content type. This avoids requiring
an `.mjs` mapping on servers that already serve `.js` correctly. Rebuild app
assets and reload the browser after upgrading.

For older builds, inspect both responses using your actual site URL:

```bash
curl -I https://your-site/assets/crispy_print/vendor/pdfjs/pdf.min.mjs
curl -I https://your-site/assets/crispy_print/vendor/pdfjs/pdf.worker.min.mjs
```

A JavaScript content type, such as `text/javascript` or `application/javascript`,
is required. `application/octet-stream` is not sufficient for browser modules.
Keep `X-Content-Type-Options: nosniff` enabled.

For Nginx, ask the deployment administrator to add `mjs` to the **existing**
JavaScript entry in the `mime.types` file used by the effective configuration.
For example, extend `application/javascript js;` to
`application/javascript js mjs;`. Use the content type already present in that
configuration. Do not add a replacement `types` block inside a `server` or
`location` block: it can replace inherited mappings for CSS, images, and fonts.
Validate and reload Nginx using the deployment's normal procedure. Check both
response headers again. Other servers or proxies need the equivalent mapping.

#### Preview reports an HTTP error without a compilation diagnostic

**Symptom:** A preview request fails with HTTP 500, or shows a server request
error instead of a useful Typst diagnostic. Ordinary Frappe saves may also fail.
This suggests a shared request-handling problem, but does not identify its cause.

1. Record the HTTP status and request time from the browser Network panel.
2. Inspect the application and reverse-proxy logs for that request.
3. Check for log entries containing `client_body_temp`, a configured body-temp
   path, or `Permission denied`.
4. Inspect the effective Nginx `client_body_temp_path` if the logs identify a
   temporary-file failure.
5. Check that the Nginx runtime user can traverse the parent directories and
   write to the configured directory.
6. Correct ownership, permissions, or volume configuration through the deployment
   administrator, then repeat the failed request.

Nginx can buffer larger request bodies to disk before forwarding them. A small
request can succeed while a larger preview fails. Verify the correction with a
request large enough to use the body-temp directory. Make directory setup
persistent across container recreation. Do not assume a fixed path or user ID,
and do not use world-writable permissions as a general fix.

The reporter of issue #8 observed an ownership change after running `nginx -t`
as root in their custom non-root container. Treat this as a deployment-specific
observation. Check directory ownership after administrative operations if the
logs show permission failures; do not assume every Nginx installation behaves
this way.

HTTP status hints are not diagnoses:

- **413:** Check request-size limits in the server or proxy.
- **502:** Check backend availability, logs, and invalid backend responses.
- **503:** Check maintenance state and server capacity.
- **504:** Check backend response time and proxy timeout settings.
- **500:** Inspect the application and proxy logs for the actual error.

Crispy Print does not change Nginx directory permissions. A generic HTTP error
cannot prove that the request failed before reaching the application. Genuine
Frappe error messages are shown when available; raw HTML and developer tracebacks
are not used as preview diagnostics.

### Slow PDF Generation

If PDF generation takes more than 5 seconds:

1. Reduce layout complexity where possible.
2. Limit preview rows for reports and large child tables.
3. Compress large letterhead/logo images.
4. Check server CPU, memory, and Typst process contention.
5. Repeat the same preview once to distinguish first-compile cost from cached compile behavior.

### Preview Not Updating

If changes don't appear in preview:

1. Use the preview refresh control after Raw Typst changes.
2. Clear browser cache: `Ctrl+Shift+R` or `Cmd+Shift+R` on macOS.
3. Clear Frappe cache: `bench clear-cache && bench clear-website-cache`.
4. Rebuild app assets: `bench build --app crispy_print`.
5. Check browser console and server logs for API errors.

### Debug Mode

Enable debug logging:

```python
# In site_config.json
{
    "developer_mode": 1,
    "logging": 2
}
```

Check logs:

```bash
tail -f sites/your-site/logs/frappe.log
```

## FAQ

**Q: Can I use Crispy Print with ERPNext?**  
A: Yes. It is designed for ERPNext/Frappe document workflows such as invoices, quotations, vouchers, and other business documents.

**Q: Does it work offline?**  
A: Users need access to the Frappe server. Typst runs server-side and fonts should be installed locally on that server or bundled with the app.

**Q: Can I export formats between sites?**  
A: Yes, format import/export exists. In beta, verify imported formats carefully because related assets, branding profiles, and compliance records may need site-specific setup.

**Q: Where did the sample `Crispy Format` fixtures go?**
A: Sample formats are no longer installed through Frappe fixtures. Use **Crispy Format Builder → Examples** to create a company-scoped format from app-owned examples in `crispy_print/examples/formats/`. The old `fixtures/crispy_format.json` path was removed to avoid importing company-specific demo data into production sites.

**Q: How do I customize fonts?**  
A: Prefer uploading fonts through Crispy Print Settings for site-scoped fonts. For server-wide fonts, install them on the system or set `TYPST_FONT_PATHS`, then restart bench. See [Font Configuration](fonts.md).

**Q: Can I use custom Typst functions?**  
A: Yes, in Raw Typst mode or reusable Typst blocks. Syntax errors surface during compilation.

**Q: What's the difference from Print Designer?**  
A: Print Designer uses HTML/CSS/Jinja browser-oriented rendering. Crispy Print uses structured layouts and Typst for deterministic document rendering.

**Q: Can I mix Jinja and Typst?**  
A: No. Crispy Print uses JSON layouts, not Jinja templates.

**Q: Is it production-ready?**  
A: It is in beta. Use it for testing and controlled non-critical workflows until the stable release criteria are met.

**Q: How do I report bugs?**  
A: Open an issue on GitHub with Frappe version, Typst version, and error logs.

**Q: Does it support multi-language?**  
A: Crispy Print includes gettext UI catalogs for Arabic, German, Spanish, Persian, French, Hindi, Indonesian, Italian, Brazilian Portuguese, Russian, Thai, Turkish, Vietnamese, and Simplified Chinese. These catalogs began as machine-assisted translations. Arabic received native linguistic review from Agathodaemon on 2026-07-28. Arabic and Persian both have end-to-end RTL engineering coverage across the builder, managed DocType/Report output, and PDFs, but Persian and the other catalogs remain contribution-ready starting points for native review. Hebrew and Urdu are recognized by the direction engine but do not ship catalogs. See [Translations](translations.md) and [Report Preview and Output](report-preview-and-output.md#language-rtl-and-accounting-values).

### RTL text is square boxes or falls back incorrectly

1. Verify the selected company font contains Arabic/Persian glyphs.
2. Run Typst font discovery and confirm `Noto Naskh Arabic` or
   `Noto Sans Arabic` is available after the selected font.
3. Rebuild assets and restart Bench after changing `TYPST_FONT_PATHS`.
4. Inspect the compiled PDF's embedded-font list; PDF/A output must embed the
   resolved faces.

### UI and document flow in different directions

This is expected when the Frappe user language differs from the format's print
language. The user language mirrors application chrome; the print language
controls preview/PDF content. If the wrong document direction is shown, inspect
the format's effective language and company/branding defaults rather than
changing the Desk language.
