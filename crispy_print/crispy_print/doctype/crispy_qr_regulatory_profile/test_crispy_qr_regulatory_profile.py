# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.qr_regulatory_profiles import (
	get_qr_regulatory_profile,
	get_qr_regulatory_profiles,
)


class TestCrispyQRRegulatoryProfile(FrappeTestCase):
	def tearDown(self):
		frappe.db.rollback()

	def test_requires_verification_url_template_when_online_verification_enabled(self):
		doc = self._new_profile(requires_online_verification=1)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_invalid_encoder_settings_json(self):
		doc = self._new_profile(encoder_settings_json="{invalid")

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_non_object_encoder_settings_json(self):
		doc = self._new_profile(encoder_settings_json='["not", "object"]')

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_lists_enabled_profiles_only_by_default(self):
		enabled = self._insert_profile(profile_name="QRRP Enabled", enabled=1)
		self._insert_profile(profile_name="QRRP Disabled", enabled=0)

		rows = get_qr_regulatory_profiles()

		self.assertIn(enabled.name, {row["name"] for row in rows})
		self.assertNotIn("QRRP Disabled", {row["name"] for row in rows})

	def test_get_profile_returns_public_profile_fields(self):
		doc = self._insert_profile(encoder_settings_json='{"issuer": "test"}')

		row = get_qr_regulatory_profile(doc.name)

		self.assertEqual(row["name"], doc.name)
		self.assertEqual(row["encoder_key"], "custom")
		self.assertIn("encoder_settings_json", row)

	def _new_profile(self, **overrides):
		values = {
			"doctype": "Crispy QR Regulatory Profile",
			"profile_name": "QRRP Test Profile",
			"enabled": 1,
			"authority_code": "QRRP-AUTH",
			"standard": "Custom",
			"payload_format": "TLV",
			"output_encoding": "Base64",
			"error_correction": "Medium",
			"encoder_key": "custom",
		}
		values.update(overrides)
		return frappe.get_doc(values)

	def _insert_profile(self, **overrides):
		doc = self._new_profile(**overrides)
		doc.insert(ignore_permissions=True)
		return doc
