import re
from datetime import date, datetime

import frappe


def _build_typst_document(
	format_doc,
	data_dict: dict,
	variable_name: str = "doc",
	header_block: str | None = None,
	footer_block: str | None = None,
	page_settings_block: str | None = None,
	preamble_override: str | None = None,
) -> str:
	"""
	Build a complete Typst document from a Crispy Format and data.

	Args:
		format_doc: Crispy Format doc
		data_dict: Data to inject (converted to Typst dictionary)
		variable_name: Typst variable name for data (default: "doc")
		header_block: Optional header block (used for letterhead)
		footer_block: Optional footer block
		page_settings_block: Optional #set page() block
		preamble_override: Optional full preamble override for reports

	Returns:
		str: Full Typst source
	"""
	sections: list[str] = []

	typst_data = _python_to_typst_dict(data_dict)

	# 1. Preamble (set rules, imports, helper functions)
	if preamble_override:
		sections.append(f"// Preamble override\n{preamble_override}")
	if format_doc.typst_preamble:
		sections.append(f"// Preamble\n{format_doc.typst_preamble}")

	# 2. Data variable definition
	sections.append(f"\n// Data injection\n#let {variable_name} = {typst_data}")

	# 3. Default header/footer blocks (safe no-op)
	sections.append("\n#let header_block = []")
	sections.append("#let footer_block = []")

	# 4. Header block (can be overridden for letterhead)
	if header_block:
		sections.append(f"\n// Header (with letterhead)\n{header_block}")
	elif format_doc.doc_header:
		sections.append(f"\n// Header\n{format_doc.doc_header}")

	# 5. Footer block (can be overridden)
	if footer_block:
		sections.append(f"\n// Footer (custom)\n{footer_block}")
	elif format_doc.doc_footer:
		sections.append(f"\n// Footer\n{format_doc.doc_footer}")

	# 6. Page settings block (optional)
	if page_settings_block:
		sections.append(f"\n// Page settings\n{page_settings_block}")

	# 7. Main template code
	sections.append(f"\n// Main template\n{format_doc.typst_code}")

	return "\n".join(sections)


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_typst_string(value: str) -> str:
	value = value.replace("\\\\", "\\\\\\\\")
	value = value.replace('"', '\\"')
	value = value.replace("\n", "\\n")
	return f'"{value}"'


def _format_typst_key(key: str) -> str:
	if _IDENT_RE.match(key):
		return key
	return _quote_typst_string(key)


def _python_to_typst_dict(data: dict | list | str | int | float | bool | None) -> str:
	"""
	Convert Python data structures to Typst dictionary/array syntax.

	Example:
		{"title": "Report", "total": 100, "items": ["A", "B"]}
		→ '(title: "Report", total: 100, items: ("A", "B"))'
	"""

	def serialize_value(val):
		if val is None:
			return "none"
		elif isinstance(val, bool):
			return "true" if val else "false"
		elif isinstance(val, int | float):
			return str(val)
		elif isinstance(val, str):
			return _quote_typst_string(val)
		elif isinstance(val, date | datetime):
			return f'"{val.isoformat()}"'
		elif isinstance(val, list):
			return "(" + ", ".join(serialize_value(item) for item in val) + ")"
		elif isinstance(val, dict):
			items = []
			for k, v in val.items():
				raw_key = str(k)
				safe_key = frappe.scrub(raw_key).replace("-", "_")
				key = _format_typst_key(safe_key if safe_key else raw_key)
				items.append(f"{key}: {serialize_value(v)}")
			return "(" + ", ".join(items) + ")"
		else:
			# Fallback: convert to string
			return _quote_typst_string(f"{val!s}")

	return serialize_value(data)
