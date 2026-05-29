# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

from unittest import mock

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

	def test_get_formatted_doc_requires_doctype_and_name(self):
		"""Missing doctype/name should be rejected early."""
		from crispy_print.api.v1 import get_formatted_doc

		with self.assertRaises(Exception):
			get_formatted_doc("", "Administrator")

		with self.assertRaises(Exception):
			get_formatted_doc("User", "")

	def test_get_formatted_doc_strips_html_for_html_and_text_editor_fields(self):
		"""Top-level HTML/Text Editor fields should be plain text in Typst payload."""
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			check_permission=mock.Mock(),
			as_dict=lambda: {"name": "DOC-1", "notes": "<p>Hello</p>"},
		)
		mock_meta = SimpleNamespace(
			fields=[SimpleNamespace(fieldname="notes", fieldtype="HTML", options=None)]
		)

		with (
			mock.patch("crispy_print.api.v1.docs.frappe.get_doc", return_value=mock_doc),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", return_value=mock_meta),
			mock.patch("crispy_print.api.v1.docs.frappe.format", return_value="<p>Hello</p>"),
			mock.patch("crispy_print.api.v1.docs.frappe.utils.strip_html", return_value="Hello"),
		):
			out = get_formatted_doc("Any", "DOC-1", qr_source_mode="document_code_profile")

		self.assertEqual(out["notes"], "Hello")
		mock_doc.check_permission.assert_called_once_with("read")

	def test_get_formatted_doc_keeps_raw_value_when_child_format_fails(self):
		"""Child-table formatter errors should not break payload generation."""
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			check_permission=mock.Mock(),
			as_dict=lambda: {
				"name": "DOC-1",
				"items": [{"description": "raw value", "qty": 2}],
			},
		)
		parent_meta = SimpleNamespace(
			fields=[SimpleNamespace(fieldname="items", fieldtype="Table", options="Child")]
		)
		child_meta = SimpleNamespace(
			fields=[
				SimpleNamespace(fieldname="description", fieldtype="Data", options=None),
				SimpleNamespace(fieldname="qty", fieldtype="Float", options=None),
			]
		)

		def mock_get_meta(doctype):
			return child_meta if doctype == "Child" else parent_meta

		def mock_format(value, df, doc=None, translated=False):
			if df.fieldname == "description":
				raise RuntimeError("format failed")
			return f"formatted:{value}"

		with (
			mock.patch("crispy_print.api.v1.docs.frappe.get_doc", return_value=mock_doc),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", side_effect=mock_get_meta),
			mock.patch("crispy_print.api.v1.docs.frappe.format", side_effect=mock_format),
		):
			out = get_formatted_doc("Any", "DOC-1", qr_source_mode="document_code_profile")

		self.assertEqual(out["items"][0]["description"], "raw value")
		self.assertEqual(out["items"][0]["qty"], "formatted:2")
		mock_doc.check_permission.assert_called_once_with("read")

	def test_get_formatted_doc_attaches_document_code_preview_when_available(self):
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			check_permission=mock.Mock(),
			as_dict=lambda: {"name": "DOC-1"},
		)
		mock_meta = SimpleNamespace(fields=[])

		with (
			mock.patch("crispy_print.api.v1.docs.frappe.get_doc", return_value=mock_doc),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", return_value=mock_meta),
			mock.patch(
				"crispy_print.api.v1.docs.get_preferred_document_code_for_doc",
				return_value={
					"code_purpose": "Regulatory",
					"environment": "Production",
					"profile_name": "Profile-1",
					"code_format": "QR Code",
					"code_symbology": "QR Code",
					"payload": {"name": "DOC-1"},
					"encoded_value": "ENCODED-QR",
				},
			),
		):
			out = get_formatted_doc("Any", "DOC-1", qr_source_mode="document_code_profile")

		self.assertEqual(out["__crispy_document_code"]["encoded_value"], "ENCODED-QR")
		self.assertEqual(out["__crispy_document_code"]["profile_name"], "Profile-1")
