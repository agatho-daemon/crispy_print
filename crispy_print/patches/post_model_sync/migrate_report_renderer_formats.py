from __future__ import annotations

import json

import frappe

from crispy_print.report_renderers import (
	get_source_fingerprint,
	infer_renderer_for_reports,
	infer_report_renderer,
)

STYLE_BY_LEGACY_TYPE = {
	"Grid": "Standard",
	"Tree": "Standard",
	"Summary": "Summary Focus",
	"Minimal": "Minimal",
}


def execute():
	if not frappe.db.table_exists("Crispy Format"):
		return
	legacy_columns = {row[0] for row in frappe.db.sql("desc `tabCrispy Format`")}
	if not {"is_generic", "generic_report_type"}.issubset(legacy_columns):
		return

	names = frappe.get_all("Crispy Format", filters={"crispy_format_type": "Report"}, pluck="name")
	for name in names:
		doc = frappe.get_doc("Crispy Format", name)
		legacy_generic, legacy_type = frappe.db.sql(
			"select is_generic, generic_report_type from `tabCrispy Format` where name=%s",
			name,
		)[0]
		legacy_generic = bool(legacy_generic)
		reports = [row.report for row in doc.get("report") or [] if row.report and not row.disabled]
		groups: dict[str, list[str]] = {}
		for report in reports:
			groups.setdefault(infer_report_renderer(report), []).append(report)

		if legacy_generic:
			doc.report_scope = "All Compatible Reports"
			doc.report_renderer = "generic_report"
			doc.set("report", [])
			_set_report_style(doc, STYLE_BY_LEGACY_TYPE.get(legacy_type, "Standard"))
		elif len(groups) <= 1:
			doc.report_scope = "Selected Reports"
			doc.report_renderer = infer_renderer_for_reports(reports)
		else:
			first_renderer = sorted(groups)[0]
			doc.report_scope = "Selected Reports"
			doc.report_renderer = first_renderer
			doc.set("report", [{"report": report, "disabled": 0} for report in groups[first_renderer]])
			for renderer in sorted(groups)[1:]:
				_clone_renderer_group(doc, renderer, groups[renderer])

		fingerprint = get_source_fingerprint(doc.report_renderer).get("fingerprint")
		doc.report_source_fingerprint = fingerprint
		doc.flags.ignore_validate = True
		doc.save(ignore_permissions=True)

	if frappe.db.exists("DocType", "Crispy Generic Report"):
		frappe.delete_doc("DocType", "Crispy Generic Report", force=True, ignore_permissions=True)


def _set_report_style(doc, style: str) -> None:
	try:
		settings = json.loads(doc.presentation_settings or "{}")
	except (TypeError, json.JSONDecodeError):
		settings = {}
	settings.setdefault("report", {})["layout_style"] = style
	doc.presentation_settings = json.dumps(settings, separators=(",", ":"))


def _clone_renderer_group(source, renderer: str, reports: list[str]) -> None:
	data = source.as_dict(no_nulls=False)
	for key in ("name", "creation", "modified", "modified_by", "owner", "docstatus", "idx"):
		data.pop(key, None)
	data["doctype"] = "Crispy Format"
	data["report_scope"] = "Selected Reports"
	data["report_renderer"] = renderer
	data["report_source_fingerprint"] = get_source_fingerprint(renderer).get("fingerprint")
	data["is_default"] = 0
	data["report"] = [{"report": report, "disabled": 0} for report in reports]
	base = f"{source.name} - {renderer.replace('_', ' ').title()}"[:130]
	name = base
	index = 2
	while frappe.db.exists("Crispy Format", name):
		name = f"{base[:124]} {index}"
		index += 1
	data["name"] = name
	doc = frappe.get_doc(data)
	doc.flags.ignore_validate = True
	doc.insert(ignore_permissions=True)
