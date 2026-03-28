# Changelog

All notable changes to Crispy Print will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0-alpha.2] - 2026-03-28

### Changed
- Bumped app version to `0.1.0-alpha.2`.

## [0.1.0-alpha.1] - 2025-01-03

### ⚠️ Alpha Release Warning
This is an early alpha release. Expect bugs and breaking changes. Not recommended for production use.

### Added
- Visual layout builder with drag-and-drop interface (Vue 3)
- Typst compilation engine for PDF/SVG generation
- Real-time preview with mock and live document data
- Letterhead integration (foreground/background modes)
- QR code field support
- Table rendering with customizable columns
- Page settings (size, orientation, margins)
- Typography controls (fonts, sizes, weights, colors)
- Multi-format support per DocType with default format selection
- Format cloning and import/export functionality
- Comprehensive test suite (90 tests: 61 frontend + 29 backend)

### System Requirements
- Frappe Framework v15+
- Typst CLI 0.11.0+
- Python 3.10+
- Node.js 18+ (for development)
- MariaDB/PostgreSQL

### Known Limitations
See [README.md - Known Limitations](README.md#known-limitations) for full list.

### Dependencies
- `@simonwep/pickr` ^1.9.1 (color picker)
- Vue 3, Pinia (state management)
- Vite, Vitest (testing)

[0.1.0-alpha.2]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.2
[0.1.0-alpha.1]: https://github.com/agatho-daemon/crispy_print/releases/tag/v0.1.0-alpha.1
