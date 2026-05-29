# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, now_datetime

from crispy_print.api.v1.fiscal_credentials import (
	get_fiscal_credential_doc,
	get_fiscal_credential_secret,
	get_fiscal_credential_status,
)


class TestCrispyFiscalCredential(FrappeTestCase):
	def setUp(self):
		self.company = self._ensure_company()
		self.profile = self._make_profile()

	def tearDown(self):
		frappe.db.rollback()

	def test_rejects_invalid_validity_window(self):
		doc = self._new_credential(
			valid_from=now_datetime(),
			valid_until=add_days(now_datetime(), -1),
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_duplicate_enabled_credential(self):
		self._insert_credential()
		duplicate = self._new_credential(credential_name="CFC Test Duplicate")

		self.assertRaises(frappe.ValidationError, duplicate.insert)

	def test_allows_disabled_duplicate_credential(self):
		self._insert_credential()
		duplicate = self._new_credential(credential_name="CFC Test Duplicate", enabled=0)
		duplicate.insert()

		self.assertEqual(duplicate.enabled, 0)

	def test_allows_same_profile_in_different_environment(self):
		self._insert_credential(environment="Sandbox")
		production = self._new_credential(
			credential_name="CFC Test Production",
			environment="Production",
		)
		production.insert()

		self.assertEqual(production.environment, "Production")

	def test_status_returns_active_credential_without_secrets(self):
		doc = self._insert_credential(api_token="secret-token")

		status = get_fiscal_credential_status(
			company=self.company,
			regulatory_profile=self.profile,
			environment="Sandbox",
		)

		self.assertTrue(status["exists"])
		self.assertTrue(status["valid"])
		self.assertEqual(status["credential"]["name"], doc.name)
		self.assertNotIn("api_token", status["credential"])
		self.assertNotIn("api_client_secret", status["credential"])
		self.assertNotIn("private_key_password", status["credential"])

	def test_status_ignores_expired_credential(self):
		self._insert_credential(
			valid_from=add_days(now_datetime(), -20),
			valid_until=add_days(now_datetime(), -1),
		)

		status = get_fiscal_credential_status(
			company=self.company,
			regulatory_profile=self.profile,
			environment="Sandbox",
		)

		self.assertTrue(status["exists"])
		self.assertFalse(status["valid"])
		self.assertIn("expired", " ".join(status["warnings"]).lower())

	def test_resolver_returns_active_doc(self):
		doc = self._insert_credential()

		resolved = get_fiscal_credential_doc(
			company=self.company,
			regulatory_profile=self.profile,
			environment="Sandbox",
		)

		self.assertEqual(resolved.name, doc.name)

	def test_secret_helper_rejects_non_secret_fields(self):
		doc = self._insert_credential()

		self.assertRaises(frappe.ValidationError, get_fiscal_credential_secret, doc.name, "api_client_id")

	def _ensure_company(self):
		company = "CFC Test Company"
		existing = frappe.get_all("Company", pluck="name", limit=1)
		if existing:
			return existing[0]

		if not frappe.db.exists("Company", company):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": company,
					"abbr": "CFTC",
					"default_currency": "KWD",
				}
			).insert(ignore_permissions=True)
		return company

	def _make_profile(self):
		name = "CFC Test QR Profile"
		if frappe.db.exists("Crispy QR Regulatory Profile", name):
			return name

		frappe.get_doc(
			{
				"doctype": "Crispy QR Regulatory Profile",
				"profile_name": name,
				"enabled": 1,
				"authority_code": "CFC-AUTH",
				"standard": "Custom",
				"payload_format": "TLV",
				"output_encoding": "Base64",
				"error_correction": "Medium",
				"encoder_key": "custom",
			}
		).insert(ignore_permissions=True)
		return name

	def _new_credential(self, **overrides):
		values = {
			"doctype": "Crispy Fiscal Credential",
			"credential_name": "CFC Test Credential",
			"enabled": 1,
			"company": self.company,
			"authority_code": "CFC-AUTH",
			"regulatory_profile": self.profile,
			"environment": "Sandbox",
		}
		values.update(overrides)
		return frappe.get_doc(values)

	def _insert_credential(self, **overrides):
		doc = self._new_credential(**overrides)
		doc.insert(ignore_permissions=True)
		return doc
