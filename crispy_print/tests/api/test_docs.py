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

	def test_get_formatted_doc_normalizes_html_for_all_string_fields(self):
		"""Any formatted string field should be plain text in Typst payload."""
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			check_permission=mock.Mock(),
			as_dict=lambda: {"name": "DOC-1", "address_display": "&lt;p&gt;Line 1&lt;br&gt;Line 2&lt;/p&gt;"},
		)
		mock_meta = SimpleNamespace(
			fields=[SimpleNamespace(fieldname="address_display", fieldtype="Text", options=None)]
		)

		with (
			mock.patch("crispy_print.api.v1.docs.frappe.get_doc", return_value=mock_doc),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", return_value=mock_meta),
			mock.patch(
				"crispy_print.api.v1.docs.frappe.format",
				return_value="&lt;p&gt;Line 1&lt;br&gt;&lt;br /&gt;Line 2&lt;/p&gt;",
			),
			mock.patch("crispy_print.api.v1.docs.validate_document_print_policy", return_value={}),
		):
			out = get_formatted_doc("Any", "DOC-1", qr_source_mode="document_code_profile")

		self.assertEqual(out["address_display"], "Line 1\nLine 2")
		mock_doc.check_permission.assert_called_once_with("read")

	def test_get_formatted_doc_with_requested_fields_returns_render_payload_only(self):
		"""Requested fields should not leak unrelated doc.as_dict() values."""
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			doctype="Sales Invoice",
			name="SINV-1",
			check_permission=mock.Mock(),
			as_dict=lambda: {
				"doctype": "Sales Invoice",
				"name": "SINV-1",
				"docstatus": 1,
				"modified": "2026-07-10 10:00:00",
				"customer": "Acme",
				"grand_total": 42,
				"owner": "private@example.com",
				"_assign": "[]",
			},
		)
		mock_meta = SimpleNamespace(
			fields=[
				SimpleNamespace(fieldname="customer", fieldtype="Data", options=None, hidden=0),
				SimpleNamespace(fieldname="grand_total", fieldtype="Currency", options=None, hidden=0),
			]
		)

		with (
			mock.patch("crispy_print.api.v1.docs.frappe.get_doc", return_value=mock_doc),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", return_value=mock_meta),
			mock.patch("crispy_print.api.v1.docs.frappe.format", side_effect=lambda value, *a, **k: value),
			mock.patch(
				"crispy_print.api.v1.docs.validate_document_print_policy",
				return_value={"can_print": True},
			),
		):
			out = get_formatted_doc("Sales Invoice", "SINV-1", fields=["customer", "owner", "_assign"])

		self.assertEqual(out["doctype"], "Sales Invoice")
		self.assertEqual(out["name"], "SINV-1")
		self.assertEqual(out["docstatus"], 1)
		self.assertEqual(out["modified"], "2026-07-10 10:00:00")
		self.assertEqual(out["customer"], "Acme")
		self.assertEqual(out["__crispy_print_context"], {"can_print": True})
		self.assertNotIn("grand_total", out)
		self.assertNotIn("owner", out)
		self.assertNotIn("_assign", out)

	def test_get_formatted_doc_with_requested_child_fields_limits_child_columns(self):
		"""Requested table paths should return only requested child columns."""
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			doctype="Sales Invoice",
			name="SINV-1",
			check_permission=mock.Mock(),
			as_dict=lambda: {
				"doctype": "Sales Invoice",
				"name": "SINV-1",
				"items": [
					{
						"item_code": "ITEM-1",
						"description": "Hidden details",
						"qty": 2,
						"rate": 5,
					}
				],
			},
		)
		parent_meta = SimpleNamespace(
			fields=[
				SimpleNamespace(fieldname="items", fieldtype="Table", options="Sales Invoice Item", hidden=0)
			]
		)
		child_meta = SimpleNamespace(
			fields=[
				SimpleNamespace(fieldname="item_code", fieldtype="Data", options=None, hidden=0),
				SimpleNamespace(fieldname="description", fieldtype="Text", options=None, hidden=0),
				SimpleNamespace(fieldname="qty", fieldtype="Float", options=None, hidden=0),
				SimpleNamespace(fieldname="rate", fieldtype="Currency", options=None, hidden=0),
			]
		)

		def mock_get_meta(doctype):
			return child_meta if doctype == "Sales Invoice Item" else parent_meta

		with (
			mock.patch("crispy_print.api.v1.docs.frappe.get_doc", return_value=mock_doc),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", side_effect=mock_get_meta),
			mock.patch("crispy_print.api.v1.docs.frappe.format", side_effect=lambda value, *a, **k: value),
			mock.patch("crispy_print.api.v1.docs.validate_document_print_policy", return_value={}),
		):
			out = get_formatted_doc("Sales Invoice", "SINV-1", fields='["items.item_code","items.qty"]')

		self.assertEqual(out["items"], [{"item_code": "ITEM-1", "qty": 2}])

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
			mock.patch("crispy_print.api.v1.docs.validate_document_print_policy", return_value={}),
		):
			out = get_formatted_doc("Any", "DOC-1", qr_source_mode="document_code_profile")

		self.assertEqual(out["items"][0]["description"], "raw value")
		self.assertEqual(out["items"][0]["qty"], "formatted:2")
		mock_doc.check_permission.assert_called_once_with("read")

	def test_get_formatted_doc_does_not_run_document_code_preview_without_explicit_allow(self):
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
			mock.patch("crispy_print.api.v1.docs.validate_document_print_policy", return_value={}),
			mock.patch("crispy_print.api.v1.docs.get_preferred_document_code_for_doc") as get_preferred,
		):
			out = get_formatted_doc("Any", "DOC-1", qr_source_mode="document_code_profile")

		self.assertNotIn("__crispy_document_code", out)
		get_preferred.assert_not_called()

	def test_get_formatted_doc_attaches_safe_document_code_preview_when_allowed(self):
		from types import SimpleNamespace

		from crispy_print.api.v1.docs import get_formatted_doc

		mock_doc = SimpleNamespace(
			check_permission=mock.Mock(),
			as_dict=lambda: {"name": "DOC-1"},
		)
		mock_meta = SimpleNamespace(fields=[])
		mock_profile = SimpleNamespace(check_permission=mock.Mock())

		with (
			mock.patch(
				"crispy_print.api.v1.docs.frappe.get_doc",
				side_effect=[mock_doc, mock_profile],
			),
			mock.patch("crispy_print.api.v1.docs.frappe.get_meta", return_value=mock_meta),
			mock.patch("crispy_print.api.v1.docs.validate_document_print_policy", return_value={}),
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
			) as get_preferred,
		):
			out = get_formatted_doc(
				"Any",
				"DOC-1",
				qr_source_mode="document_code_profile",
				allow_document_code_preview=1,
			)

		self.assertEqual(out["__crispy_document_code"]["encoded_value"], "ENCODED-QR")
		self.assertEqual(out["__crispy_document_code"]["profile_name"], "Profile-1")
		self.assertNotIn("payload", out["__crispy_document_code"])
		get_preferred.assert_called_once_with(mock_doc, allow_custom_methods=False)
		mock_profile.check_permission.assert_called_once_with("read")
