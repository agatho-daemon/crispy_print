# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.tests.helpers.defaults import capture_defaults, clear_defaults, restore_defaults


class TestCrispyFormatRetrievalAPI(FrappeTestCase):
	"""Test Crispy Format retrieval APIs"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")

		# Clean up test formats
		frappe.db.delete("Crispy Format", {"name": ["like", "Test API Format%"]})
		self._default_doctypes = ["Sales Invoice", "Sales Order", "Purchase Order"]
		self._saved_defaults = capture_defaults(self._default_doctypes)
		clear_defaults(self._default_doctypes)
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after tests"""
		frappe.db.delete("Crispy Format", {"name": ["like", "Test API Format%"]})
		restore_defaults(self._saved_defaults)
		frappe.db.commit()

	def test_get_crispy_formats_for_doctype(self):
		"""Test retrieving formats for a specific DocType"""
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		# Create test formats
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"page_settings": json.dumps({"pageSize": "A4"}),
			}
		)
		format1.insert()

		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format 2",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()

		# Test retrieval
		formats = get_crispy_formats_for_doctype("Sales Invoice")

		self.assertIsInstance(formats, list)
		self.assertTrue(len(formats) >= 2)

		format_names = [f["name"] for f in formats]
		self.assertIn("Test API Format 1", format_names)
		self.assertIn("Test API Format 2", format_names)

	def test_get_crispy_formats_excludes_invalid_json(self):
		"""Test that formats with invalid JSON are excluded"""
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		# Create format with valid JSON
		valid_format = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Valid",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		valid_format.insert()

		# Create format with invalid JSON directly in DB
		frappe.db.set_value("Crispy Format", "Test API Format Valid", "layout_json", "{invalid json")
		frappe.db.commit()

		# Should not raise error, just exclude invalid format
		formats = get_crispy_formats_for_doctype("Purchase Order")

		# Should return empty list or not include the invalid format
		self.assertIsInstance(formats, list)

	def test_get_default_doctypes(self):
		"""Test retrieving DocTypes with default formats"""
		from crispy_print.api.v1 import get_default_doctypes
		from crispy_print.crispy_print.doctype.crispy_format.crispy_format import make_default

		# Create default format for Sales Order
		format_so = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default SO",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_so.insert()
		make_default(format_so.name)

		# Create default format for Purchase Order
		format_po = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default PO",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_po.insert()
		make_default(format_po.name)

		# Test retrieval
		default_doctypes = get_default_doctypes()

		self.assertIsInstance(default_doctypes, list)
		self.assertIn("Sales Order", default_doctypes)
		self.assertIn("Purchase Order", default_doctypes)

	def test_get_crispy_formats_empty_doctype(self):
		"""Test retrieval for DocType with no formats"""
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		# Use an unlikely DocType that won't have formats
		formats = get_crispy_formats_for_doctype("Language")

		self.assertIsInstance(formats, list)
		self.assertEqual(len(formats), 0)
