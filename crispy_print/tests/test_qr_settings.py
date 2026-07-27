from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

import frappe

from crispy_print.qr_settings import validate_editable_qr_settings


class TestCustomQrSettings(TestCase):
	def setUp(self):
		self.meta = SimpleNamespace(
			fields=[
				SimpleNamespace(fieldname="customer_name", fieldtype="Data", hidden=0),
				SimpleNamespace(fieldname="grand_total", fieldtype="Currency", hidden=0),
				SimpleNamespace(fieldname="items", fieldtype="Table", hidden=0),
				SimpleNamespace(fieldname="secret", fieldtype="Password", hidden=0),
			]
		)

	def validate(self, qr):
		with patch("frappe.get_meta", return_value=self.meta):
			validate_editable_qr_settings({"qr": qr}, "Sales Invoice")

	def test_accepts_exact_ordered_fieldname_strings(self):
		self.validate(
			{
				"enabled": True,
				"sourceMode": "custom",
				"fields": ["grand_total", "name", "customer_name"],
			}
		)

	def test_rejects_legacy_basic_mode_for_editable_formats(self):
		with self.assertRaises(frappe.ValidationError):
			self.validate({"enabled": True, "sourceMode": "basic", "fields": ["name"]})

	def test_rejects_objects_duplicates_unknown_and_unsafe_fields(self):
		for fields in (
			[{"fieldname": "name"}],
			["name", "name"],
			["missing"],
			["items"],
			["secret"],
		):
			with self.subTest(fields=fields), self.assertRaises(frappe.ValidationError):
				self.validate({"enabled": True, "sourceMode": "custom", "fields": fields})

	def test_ignores_disabled_and_regulatory_field_lists(self):
		self.validate({"enabled": False, "sourceMode": "basic", "fields": []})
		self.validate(
			{
				"enabled": True,
				"sourceMode": "document_code_profile",
				"fields": ["not_used"],
			}
		)
