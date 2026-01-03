"""Crispy Print - Typst-based print format builder for Frappe"""

__version__ = "0.0.1"

# Expose API methods for convenience
from crispy_print.api import (
	compile_typst,
	get_crispy_formats_for_doctype,
	get_default_doctypes,
	get_formatted_doc,
	get_typst_local_fonts,
)

__all__ = [
	"compile_typst",
	"get_crispy_formats_for_doctype",
	"get_default_doctypes",
	"get_formatted_doc",
	"get_typst_local_fonts",
]
