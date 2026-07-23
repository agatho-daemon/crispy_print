import re
from datetime import date, datetime

import frappe

from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	get_applicable_typst_blocks,
)


def _build_typst_document(
	format_doc,
	data_dict: dict | None,
	variable_name: str = "doc",
	header_block: str | None = None,
	footer_block: str | None = None,
	presentation_settings_block: str | None = None,
	preamble_override: str | None = None,
	data_file: str | None = None,
) -> str:
	"""
	Build a complete Typst document from a Crispy Format and data.

	Args:
		format_doc: Crispy Format doc
		data_dict: Data to inject (converted to Typst dictionary)
		variable_name: Typst variable name for data (default: "doc")
		header_block: Optional header block (used for letterhead)
		footer_block: Optional footer block
		presentation_settings_block: Optional #set page() block
		preamble_override: Optional full preamble override for reports

	Returns:
		str: Full Typst source
	"""
	sections: list[str] = []

	typst_data = _python_to_typst_dict(data_dict or {})
	is_raw_typst = _is_raw_typst_format(format_doc)

	# 1. Data variable definition
	data_expression = f'json("{data_file}")' if data_file else typst_data
	sections.append(f"\n// Data injection\n#let {variable_name} = {data_expression}")

	if is_raw_typst:
		sections.append(f"\n{_build_raw_typst_helpers(format_doc, format_doc.typst_code or '')}")
	else:
		# 2. Default header/footer blocks (safe no-op)
		sections.append("\n#let header_block = []")
		sections.append("#let footer_block = []")

		# 3. Preamble (set rules, imports, helper functions)
		if preamble_override:
			sections.append(f"\n// Preamble override\n{preamble_override}")
		if format_doc.typst_preamble:
			sections.append(f"\n// Preamble\n{format_doc.typst_preamble}")

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

		# 6. Presentation settings block (optional)
		if presentation_settings_block:
			sections.append(f"\n// Presentation settings\n{presentation_settings_block}")

	# 7. Main template code
	sections.append(f"\n// Main template\n{format_doc.typst_code}")

	return "\n".join(sections)


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_CRISPY_BLOCK_RE = re.compile(r'crispy_block\(\s*"([^"\n]+)"')
_TYPST_KEYWORDS = frozenset(
	{
		"and",
		"as",
		"auto",
		"break",
		"context",
		"continue",
		"else",
		"export",
		"false",
		"for",
		"if",
		"import",
		"in",
		"include",
		"let",
		"none",
		"not",
		"or",
		"return",
		"set",
		"show",
		"true",
		"while",
	}
)


def _is_raw_typst_format(format_doc) -> bool:
	return bool(getattr(format_doc, "raw_typst", 0))


def _quote_typst_string(value: str) -> str:
	out: list[str] = []
	for char in str(value):
		codepoint = ord(char)
		if char == "\\":
			out.append("\\\\")
		elif char == '"':
			out.append('\\"')
		elif char == "\n":
			out.append("\\n")
		elif char == "\r":
			out.append("\\r")
		elif char == "\t":
			out.append("\\t")
		elif codepoint < 0x20 or codepoint == 0x7F:
			out.append(f"\\u{codepoint:04x}")
		else:
			out.append(char)
	return f'"{"".join(out)}"'


def _extract_crispy_block_ids(typst_source: str) -> set[str]:
	return {
		str(match.group(1) or "").strip()
		for match in _CRISPY_BLOCK_RE.finditer(typst_source or "")
		if str(match.group(1) or "").strip()
	}


def _build_raw_typst_helpers(format_doc, typst_source: str = "") -> str:
	referenced_block_ids = _extract_crispy_block_ids(typst_source)
	blocks = []
	doctype = getattr(format_doc, "doc_type", None)
	if doctype:
		blocks = get_applicable_typst_blocks(
			doctype,
			enabled_only=True,
			company=getattr(format_doc, "company", None),
		)

	lines = [
		"// Crispy Raw Typst helpers",
		"#let crispy_image(filename, ..args) = image(filename, ..args)",
		"#let crispy_blocks = (",
	]
	for block in blocks:
		name = str(block.get("name") or "").strip()
		code = str(block.get("typst_code") or "").strip()
		if not referenced_block_ids or name not in referenced_block_ids:
			continue
		if not name or not code:
			continue
		lines.append(f"  {_quote_typst_string(name)}: [")
		lines.append(code)
		lines.append("  ],")
	lines.extend(
		[
			")",
			"#let crispy_block(id) = {",
			"  let block = crispy_blocks.at(id, default: none)",
			'  if block == none { panic("Crispy Typst Block not found: " + str(id)) }',
			"  block",
			"}",
		]
	)
	return "\n".join(lines)


def _format_typst_key(key: str) -> str:
	if _IDENT_RE.match(key) and key not in _TYPST_KEYWORDS:
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
			seen_keys: set[str] = set()
			for k, v in val.items():
				raw_key = str(k)
				safe_key = frappe.scrub(raw_key).replace("-", "_")
				candidate_key = safe_key if safe_key else raw_key
				if candidate_key in seen_keys:
					key = _quote_typst_string(raw_key)
				else:
					key = _format_typst_key(candidate_key)
					seen_keys.add(candidate_key)
				items.append(f"{key}: {serialize_value(v)}")
			return "(" + ", ".join(items) + ")"
		else:
			# Fallback: convert to string
			return _quote_typst_string(f"{val!s}")

	return serialize_value(data)
