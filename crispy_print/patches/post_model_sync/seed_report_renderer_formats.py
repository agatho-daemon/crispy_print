from __future__ import annotations

import json
from pathlib import Path

import frappe

from crispy_print.report_renderers import RENDERERS, get_renderer_metadata, get_source_fingerprint


def execute():
	companies = frappe.get_all("Company", pluck="name")
	if not companies:
		return
	template = _default_typst()
	for company in companies:
		if _is_test_company(company):
			continue
		for renderer in RENDERERS:
			if renderer.key == "custom":
				continue
			name = _format_name(renderer.label, company)
			if frappe.db.exists("Crispy Format", name):
				continue
			selected = bool(renderer.reports)
			metadata = get_renderer_metadata(renderer.key)
			doc = frappe.get_doc(
				{
					"doctype": "Crispy Format",
					"name": name,
					"company": company,
					"crispy_format_type": "Report",
					"report_scope": "Selected Reports" if selected else "All Compatible Reports",
					"report_renderer": renderer.key,
					"report_source_fingerprint": get_source_fingerprint(renderer.key).get("fingerprint"),
					"report": [{"report": report, "disabled": 0} for report in renderer.reports],
					"is_advanced": 0,
					"raw_typst": 0,
					"is_default": 1,
					"typst_code": template,
					"presentation_settings": json.dumps(
						{
							"page": {"orientation": "landscape"},
							"report": {
								"mode": "basic",
								"renderer": renderer.key,
								"layout_style": "Standard",
								"sections": metadata["sections"],
							},
						},
						separators=(",", ":"),
					),
				}
			)
			doc.insert(ignore_permissions=True)


def _format_name(label: str, company: str) -> str:
	return f"{label} - {company}"[:140]


def _is_test_company(company: str) -> bool:
	value = company.strip().lower()
	return value.startswith("test ") or value.startswith("_test ")


def _default_typst() -> str:
	path = Path(frappe.get_app_path("crispy_print")).parent / "REPORT_TEMPLATE_DEFAULT.typ"
	return path.read_text(encoding="utf-8") if path.is_file() else "#text(data.title)"
