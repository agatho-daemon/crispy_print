# Font Configuration

_Part of the [Crispy Print documentation](README.md)._

### Bundled Fonts

The app automatically includes fonts from `crispy_print/public/vendor/fonts/`. These fonts are available to all print formats without additional configuration.

### System Fonts

System font discovery is governed by the **Enable System Fonts** toggle in Crispy Print Settings (off by default). When enabled, Typst discovers system fonts — on Linux it searches standard directories like `/usr/share/fonts` and `~/.local/share/fonts`. Ensure any system fonts you rely on permit PDF embedding/subsetting, which PDF/A output requires.

### Custom Fonts

There are two ways to add fonts beyond the bundled set.

#### Option 1: Upload via Crispy Print Settings (Recommended)

Open **Crispy Print Settings**, enable **Enable Uploaded Fonts**, and use **Upload Font** to add fonts to the site's private Crispy Print font directory. Click **Refresh Font List** to re-run discovery. This requires no shell access and is scoped per site.

#### Option 2: `TYPST_FONT_PATHS` Environment Variable

`TYPST_FONT_PATHS` is the official Typst CLI variable for additional font directories (colon/semicolon-separated). Crispy Print forwards it to Typst when set. Add it to your shell profile (`~/.bashrc`, `~/.zshrc`, or `~/.profile`):

```bash
export TYPST_FONT_PATHS="/path/to/custom/fonts:$HOME/.fonts/typst"
```

Create directories and add fonts as needed:

```bash
mkdir -p ~/.fonts/typst
cp /path/to/font.ttf ~/.fonts/typst/
```

Then restart your bench so the worker process picks up the variable:

```bash
bench restart
```

#### Typst Binary Path

You can also pin the Typst binary path in `site_config.json`:

```json
{
  "TYPST_BIN": "/usr/local/bin/typst"
}
```

### Font Discovery

The app's `get_typst_local_fonts()` API method returns all available fonts by running:

```bash
typst fonts
```

This includes:

- Bundled fonts from `crispy_print/public/vendor/fonts/`
- Uploaded site fonts (when **Enable Uploaded Fonts** is on)
- System fonts (when **Enable System Fonts** is on)
- Fonts in `TYPST_FONT_PATHS`

### Crispy Print Settings (Global)

The single **Crispy Print Settings** DocType (System Manager only) centralizes font and rendering controls:

**Font Settings**

- **Enable Uploaded Fonts** - include fonts uploaded to the site's private Crispy Print font directory (created automatically on install).
- **Enable System Fonts** - allow Typst to discover system fonts (ensure they permit PDF embedding/subsetting).
- **Font Search Paths** - read-only view of the resolved font directories Crispy Print passes to Typst.
- **Upload Font** / **Refresh Font List** - add fonts and re-run discovery.

**Rendering Policy**

- **Render Timeout Seconds** - maximum seconds per Typst render or font-discovery command (default `60`).
- **Allow Print for Draft** (with optional **Always Add Draft Heading**) and **Allow Print for Cancelled** - control whether draft/cancelled documents may be printed.
