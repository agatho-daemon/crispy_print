from __future__ import annotations

import frappe

from crispy_print.patches.post_model_sync.seed_report_renderer_formats import (
	_default_typst,
	_format_name,
	_is_test_company,
)
from crispy_print.report_renderers import RENDERERS


def execute():
	"""Replace only the emergency template used by the original renderer seed.

	Existing formats that were edited by a designer are deliberately left alone.
	"""
	template = _default_typst()
	if template == "#text(data.title)":
		return

	for company in frappe.get_all("Company", pluck="name"):
		if _is_test_company(company):
			continue
		for renderer in RENDERERS:
			if renderer.key == "custom":
				continue
			name = _format_name(renderer.label, company)
			if frappe.db.get_value("Crispy Format", name, "typst_code") == "#text(data.title)":
				frappe.db.set_value("Crispy Format", name, "typst_code", template, update_modified=False)
