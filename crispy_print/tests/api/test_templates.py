from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.templates import can_resolve_crispy_template_for_document


class TestTemplatesApi(FrappeTestCase):
	def test_can_resolve_crispy_template_for_document_returns_true_when_resolver_succeeds(self):
		with mock.patch("crispy_print.api.v1.templates.get_resolved_crispy_template_for_document"):
			self.assertTrue(
				can_resolve_crispy_template_for_document(
					source_doctype="Sales Invoice",
					source_docname="SINV-1",
				)
			)

	def test_can_resolve_crispy_template_for_document_returns_false_for_missing_template(self):
		with mock.patch(
			"crispy_print.api.v1.templates.get_resolved_crispy_template_for_document",
			side_effect=frappe.ValidationError("No active Crispy Template found"),
		):
			self.assertFalse(
				can_resolve_crispy_template_for_document(
					source_doctype="Sales Invoice",
					source_docname="SINV-1",
				)
			)
