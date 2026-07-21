from __future__ import annotations

import json

import frappe


def execute():
	if not frappe.db.table_exists("Crispy Format"):
		return
	columns = set(frappe.db.get_table_columns("Crispy Format"))
	if "raw_typst" not in columns:
		return

	if "is_advanced" in columns:
		frappe.db.sql(
			"""
			update `tabCrispy Format`
			set raw_typst = if(
				coalesce(raw_typst, 0) = 1 or coalesce(is_advanced, 0) = 1,
				1,
				0
			)
			where crispy_format_type = 'Report'
			"""
		)

	_normalize_persisted_report_modes()


def _normalize_persisted_report_modes() -> None:
	rows = frappe.db.sql(
		"""
		select name, raw_typst, presentation_settings
		from `tabCrispy Format`
		where crispy_format_type = 'Report'
		""",
		as_dict=True,
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
		frappe.db.set_value(
			"Crispy Format",
			row.name,
			"presentation_settings",
			json.dumps(settings, separators=(",", ":")),
			update_modified=False,
		)
