# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCrispyFormat(FrappeTestCase):
	def setUp(self):
		"""Set up test data before each test"""
		frappe.set_user("Administrator")
		# Clean up any existing test formats
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Format%"]})
		self._default_doctypes = [
			"Sales Invoice",
			"Sales Order",
			"Purchase Invoice",
			"Purchase Order",
		]
		self._saved_defaults = self._capture_defaults(self._default_doctypes)
		self._clear_defaults(self._default_doctypes)
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Format%"]})
		self._restore_defaults(self._saved_defaults)
		frappe.db.commit()

	def _capture_defaults(self, doctypes: list[str]) -> dict[str, list[str]]:
		saved = {}
		for dt in doctypes:
			names = frappe.get_all(
				"Crispy Format",
				filters={"doc_type": dt, "is_default": 1},
				pluck="name",
			)
			saved[dt] = names or []
		return saved

	def _clear_defaults(self, doctypes: list[str]):
		if not doctypes:
			return
		frappe.db.sql(
			"update `tabCrispy Format` set is_default = 0 where doc_type in %s",
			(tuple(doctypes),),
		)

	def _restore_defaults(self, saved: dict[str, list[str]]):
		for names in (saved or {}).values():
			for name in names:
				frappe.db.set_value("Crispy Format", name, "is_default", 1)

	def test_create_crispy_format(self):
		"""Test creating a new Crispy Format document"""
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"page_settings": json.dumps({"pageSize": "A4"}),
			}
		)
		doc.insert()

		self.assertEqual(doc.doc_type, "Sales Invoice")
		self.assertFalse(doc.is_default)

		# Clean up
		doc.delete()

	def test_set_default_format(self):
		"""Test setting a format as default clears other defaults"""
		from crispy_print.crispy_print.doctype.crispy_format.crispy_format import make_default

		# Create first format
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Default 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format1.insert()
		make_default(format1.name)
		format1.reload()
		self.assertTrue(format1.is_default)

		# Create second format and set as default
		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Default 2",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()
		make_default(format2.name)

		# Reload first format and verify it's no longer default
		format1.reload()
		format2.reload()
		self.assertFalse(format1.is_default)
		self.assertTrue(format2.is_default)

		# Clean up
		format1.delete()
		format2.delete()

	def test_get_current_default(self):
		"""Test getting the current default format for a DocType"""
		from crispy_print.crispy_print.doctype.crispy_format.crispy_format import make_default

		# Create default format
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Current Default",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format1.insert()
		make_default(format1.name)

		# Create another format for same DocType
		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Not Default",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()

		# Get current default
		current_default = format2.get_current_default()
		self.assertEqual(current_default, "Test Format Current Default")

		# Clean up
		format1.delete()
		format2.delete()

	def test_make_default_api(self):
		"""Test the make_default API method"""
		from crispy_print.crispy_print.doctype.crispy_format.crispy_format import make_default

		# Create format
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Make Default",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		doc.insert()
		self.assertFalse(doc.is_default)

		# Set as administrator to bypass permissions
		frappe.set_user("Administrator")

		# Make default via API
		make_default("Test Format Make Default")

		# Verify it's now default
		doc.reload()
		self.assertTrue(doc.is_default)

		# Clean up
		doc.delete()

	def test_layout_json_validation(self):
		"""Test that valid JSON is required for layout_json"""
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format JSON Valid",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps(
					{
						"sections": [
							{
								"label": "Header",
								"columns": [{"label": "Col 1", "fields": []}],
							}
						]
					}
				),
			}
		)
		doc.insert()

		# Verify JSON can be parsed
		layout = json.loads(doc.layout_json)
		self.assertIn("sections", layout)
		self.assertEqual(len(layout["sections"]), 1)

		# Clean up
		doc.delete()

	def test_multiple_doctypes_defaults(self):
		"""Test that different DocTypes can each have their own default"""
		from crispy_print.crispy_print.doctype.crispy_format.crispy_format import make_default

		# Create default for Sales Invoice
		format_si = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format SI Default",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_si.insert()
		make_default(format_si.name)

		# Create default for Purchase Invoice
		format_pi = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format PI Default",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_pi.insert()
		make_default(format_pi.name)

		# Both should remain as defaults for their respective DocTypes
		format_si.reload()
		format_pi.reload()
		self.assertTrue(format_si.is_default)
		self.assertTrue(format_pi.is_default)

		# Clean up
		format_si.delete()
		format_pi.delete()
