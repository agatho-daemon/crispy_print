from __future__ import annotations

import json

import frappe
from frappe.query_builder.functions import Coalesce
from pypika.terms import Case


def execute():
	if not frappe.db.table_exists("Crispy Format"):
		return
	columns = set(frappe.db.get_table_columns("Crispy Format"))
	if "raw_typst" not in columns:
		return

	if "is_advanced" in columns:
		formats = frappe.qb.DocType("Crispy Format")
		advanced = (Coalesce(formats.raw_typst, 0) == 1) | (Coalesce(formats.is_advanced, 0) == 1)
		(
			frappe.qb.update(formats)
			.set(formats.raw_typst, Case().when(advanced, 1).else_(0))
			.where(formats.crispy_format_type == "Report")
			.run()
		)

	_normalize_persisted_report_modes()


def _normalize_persisted_report_modes() -> None:
	formats = frappe.qb.DocType("Crispy Format")
	rows = (
		frappe.qb.from_(formats)
		.select(formats.name, formats.raw_typst, formats.presentation_settings)
		.where(formats.crispy_format_type == "Report")
		.run(as_dict=True)
	)
	for row in rows:
		try:
			settings = json.loads(row.presentation_settings or "{}")
		except (TypeError, json.JSONDecodeError):
			continue
		if not isinstance(settings, dict):
			continue
		report = settings.get("report")
		if not isinstance(report, dict):
			continue
		mode = "advanced" if row.raw_typst else "basic"
		if report.get("mode") == mode:
			continue
		report["mode"] = mode
		(
			frappe.qb.update(formats)
			.set(formats.presentation_settings, json.dumps(settings, separators=(",", ":")))
			.where(formats.name == row.name)
			.run()
		)
