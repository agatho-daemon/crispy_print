# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCrispyDocumentCodeRule(FrappeTestCase):
	def test_filter_json_condition_requires_json(self):
		doc = self._new_rule(condition_type="Filter JSON", condition_json=None)

		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	def test_expression_condition_requires_expression(self):
		doc = self._new_rule(condition_type="Python Expression", condition_expression=None)

		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	def test_rejects_invalid_override_json(self):
		doc = self._new_rule(field_mapping_json_override='["bad"]')

		self.assertRaises(frappe.ValidationError, doc.run_method, "validate")

	def test_always_condition_clears_condition_fields(self):
		doc = self._new_rule(
			condition_type="Always",
			condition_json='{"status":"Draft"}',
			condition_expression="doc.status == 'Draft'",
		)

		doc.run_method("validate")

		self.assertFalse(doc.condition_json)
		self.assertFalse(doc.condition_expression)

	def _new_rule(self, **overrides):
		values = {
			"doctype": "Crispy Document Code Rule",
			"document_type": "Sales Invoice",
			"document_role": "Invoice",
			"enabled": 1,
			"required": 1,
			"condition_type": "Filter JSON",
			"condition_json": '{"docstatus": 1}',
			"priority": 100,
		}
		values.update(overrides)
		return frappe.get_doc(values)
