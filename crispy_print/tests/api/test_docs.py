# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestFormattedDocAPI(FrappeTestCase):
	"""Test document formatting API"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")

	def test_get_formatted_doc(self):
		"""Test document field formatting with User doctype (minimal dependencies)"""
		from crispy_print.api.v1 import get_formatted_doc

		# Use User doctype which has minimal dependencies
		if not frappe.db.exists("User", "Administrator"):
			self.skipTest("Administrator user not found")

		# Get formatted document
		doc_data = get_formatted_doc("User", "Administrator")

		self.assertIsInstance(doc_data, dict)
		self.assertEqual(doc_data["name"], "Administrator")
		self.assertIn("email", doc_data)

	def test_get_formatted_doc_with_table(self):
		"""Test formatting of child table fields using User with roles"""
		from crispy_print.api.v1 import get_formatted_doc

		doc_data = get_formatted_doc("User", "Administrator")

		# Verify roles table is present
		self.assertIn("roles", doc_data)
		roles = doc_data.get("roles") or []

		if roles and len(roles) > 0:
			self.assertIsInstance(roles, list)
			self.assertIsInstance(roles[0], dict)

	def test_get_formatted_doc_invalid_doctype(self):
		"""Test error handling for invalid doctype"""
		from crispy_print.api.v1 import get_formatted_doc

		with self.assertRaises(Exception):
			get_formatted_doc("Invalid DocType", "TEST-001")

	def test_get_formatted_doc_invalid_name(self):
		"""Test error handling for non-existent document"""
		from crispy_print.api.v1 import get_formatted_doc

		with self.assertRaises(Exception):
			get_formatted_doc("User", "NON-EXISTENT-USER-12345")
