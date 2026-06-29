# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.qr_registry import (
	get_allowed_qr_field_keys,
	get_business_field_set,
	get_qr_fields,
	get_qr_registry_metadata,
	validate_qr_field_selection,
)


class TestQrRegistryLoader(FrappeTestCase):
	def test_metadata_lists_registry_dimensions(self):
		metadata = get_qr_registry_metadata()

		self.assertEqual(metadata["version"], 1)
		self.assertIn("Sales Invoice", metadata["doctypes"])
		self.assertIn("ZATCA", metadata["authorities"])
		self.assertIn("inventory_traceability", metadata["business_field_sets"])

	def test_get_fields_filters_by_authority(self):
		out = get_qr_fields("Sales Invoice", authority_code="ZATCA")
		keys = {field["key"] for field in out["fields"]}

		self.assertIn("company", keys)
		self.assertIn("grand_total", keys)
		self.assertIn("items.serial_no", keys)
		self.assertNotIn("rounded_total", keys)
		self.assertEqual(out["authority"]["key"], "ZATCA")

	def test_business_field_set_returns_registry_keys(self):
		field_set = get_business_field_set("inventory_traceability")

		self.assertEqual(field_set["doctype"], "Sales Invoice")
		self.assertIn("items.serial_no", field_set["fields"])

	def test_validate_rejects_unknown_fields(self):
		with self.assertRaises(frappe.ValidationError):
			validate_qr_field_selection("Sales Invoice", ["company", "owner.password"])

	def test_allowed_keys_are_limited_to_authority_when_provided(self):
		keys = get_allowed_qr_field_keys("Sales Invoice", authority_code="ZATCA")

		self.assertIn("company", keys)
		self.assertNotIn("rounded_total", keys)
