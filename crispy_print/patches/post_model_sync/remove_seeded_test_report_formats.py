import frappe

from crispy_print.patches.post_model_sync.seed_report_renderer_formats import (
	_format_name,
	_is_test_company,
)
from crispy_print.report_renderers import RENDERERS


def execute():
	for company in frappe.get_all("Company", pluck="name"):
		if not _is_test_company(company):
			continue
		for renderer in RENDERERS:
			name = _format_name(renderer.label, company)
			if frappe.db.exists("Crispy Format", name):
				frappe.delete_doc("Crispy Format", name, force=True, ignore_permissions=True)
