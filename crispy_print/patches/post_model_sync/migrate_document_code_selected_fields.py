from __future__ import annotations

from typing import Any

import frappe

from crispy_print.json_utils import parse_json_list_or_object
from crispy_print.qr_registry import get_allowed_qr_field_keys, get_qr_field_definition


def execute() -> None:
	if not frappe.db.table_exists("Crispy Document Code Field"):
		return

	for name in frappe.get_all(
		"Crispy Document Code Profile",
		filters={"content_source": "Selected Fields"},
		pluck="name",
	):
		doc = frappe.get_doc("Crispy Document Code Profile", name)
		if doc.selected_fields or not doc.selected_fields_json:
			continue

		source_doctype = _single_target_doctype(doc)
		if not source_doctype:
			continue

		try:
			selected = parse_json_list_or_object(doc.selected_fields_json, "Selected Fields JSON")
			rows = _selected_field_rows(source_doctype, selected)
		except Exception:
			continue

		if not rows:
			continue

		for row in rows:
			doc.append("selected_fields", row)
		doc.save(ignore_permissions=True)


def _single_target_doctype(doc: Any) -> str | None:
	doctypes = {
		str(rule.document_type or "").strip()
		for rule in doc.document_rules or []
		if str(rule.document_type or "").strip()
	}
	if len(doctypes) != 1:
		return None
	return next(iter(doctypes))


def _selected_field_rows(source_doctype: str, selected: Any) -> list[dict[str, Any]]:
	allowed = get_allowed_qr_field_keys(source_doctype)
	rows: list[dict[str, Any]] = []
	if isinstance(selected, dict):
		items = [(str(output_key), str(field_key)) for output_key, field_key in selected.items()]
	else:
		items = [("", str(field_key)) for field_key in selected or []]

	for output_key, field_key in items:
		if field_key not in allowed:
			continue
		definition = get_qr_field_definition(source_doctype, field_key)
		rows.append(
			{
				"source_doctype": source_doctype,
				"field_key": field_key,
				"output_key": output_key,
				"label": definition.get("label"),
				"source_path": definition.get("path"),
				"source": definition.get("source"),
				"datatype": definition.get("datatype"),
				"purpose": definition.get("purpose"),
			}
		)
	return rows
