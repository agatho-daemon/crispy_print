# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCrispyDocumentCodeProfile(FrappeTestCase):
	def setUp(self):
		self.company = self._ensure_company()
		self.regulatory_profile = self._make_regulatory_profile()
		self.fiscal_credential = self._make_fiscal_credential()

	def tearDown(self):
		frappe.db.rollback()

	def test_regulatory_profiles_require_linked_regulatory_profile(self):
		doc = self._new_profile(code_purpose="Regulatory", regulatory_profile=None)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_verification_url_source_requires_template(self):
		doc = self._new_profile(
			code_purpose="Portal Link",
			content_source="Verification URL",
			regulatory_profile=None,
			verification_url_template=None,
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_signature_requires_credential_and_method(self):
		doc = self._new_profile(
			requires_signature=1,
			fiscal_credential=None,
			signature_method=None,
			regulatory_profile=self.regulatory_profile,
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_apply_regulatory_profile_defaults(self):
		doc = self._new_profile(
			regulatory_profile=self.regulatory_profile,
			payload_format=None,
			output_encoding=None,
			error_correction=None,
			encoder_key=None,
			encoder_settings_json=None,
			verification_url_template=None,
			requires_verification_url=0,
			include_hash=0,
		)
		doc.insert()

		self.assertEqual(doc.payload_format, "TLV")
		self.assertEqual(doc.output_encoding, "Base64")
		self.assertEqual(doc.error_correction, "High")
		self.assertEqual(doc.encoder_key, "zatca_tlv")
		self.assertEqual(doc.verification_url_template, "https://verify.example/{{ doc.name }}")
		self.assertEqual(int(doc.requires_verification_url), 1)
		self.assertEqual(int(doc.include_hash), 1)
		self.assertEqual(doc.encoder_settings_json, '{"issuer":"ACME"}')

	def test_rejects_mismatched_fiscal_credential_company(self):
		other_company = self._ensure_company("CDP Other Company", "CDOC")
		other_credential = self._make_fiscal_credential(
			name="CDP Other Credential",
			company=other_company,
		)
		doc = self._new_profile(
			regulatory_profile=self.regulatory_profile,
			fiscal_credential=other_credential,
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_invalid_json_fields(self):
		doc = self._new_profile(
			regulatory_profile=self.regulatory_profile,
			field_mapping_json='["bad"]',
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_normalizes_child_rule_priority_order(self):
		doc = self._new_profile(regulatory_profile=self.regulatory_profile)
		doc.append(
			"document_rules",
			{
				"document_type": "Sales Invoice",
				"document_role": "Invoice",
				"priority": 200,
				"condition_type": "Always",
			},
		)
		doc.append(
			"document_rules",
			{
				"document_type": "Sales Invoice",
				"document_role": "Invoice",
				"priority": 50,
				"condition_type": "Always",
			},
		)
		doc.insert()

		self.assertEqual([row.priority for row in doc.document_rules], [50, 200])

	def _new_profile(self, **overrides):
		values = {
			"doctype": "Crispy Document Code Profile",
			"profile_name": f"CDP Test Profile {frappe.generate_hash(length=6)}",
			"enabled": 1,
			"company": self.company,
			"environment": "Sandbox",
			"code_purpose": "Regulatory",
			"regulatory_profile": self.regulatory_profile,
			"fiscal_credential": self.fiscal_credential,
			"code_format": "QR Code",
			"code_symbology": "QR Code",
			"payload_format": "TLV",
			"output_encoding": "Plain Text",
			"error_correction": "Medium",
			"content_source": "Encoder",
			"encoder_key": "custom",
			"priority": 100,
		}
		values.update(overrides)
		return frappe.get_doc(values)

	def _ensure_company(self, company_name: str = "CDP Test Company", abbr: str = "CDPT"):
		if not frappe.db.exists("Company", company_name):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": company_name,
					"abbr": abbr,
					"default_currency": "KWD",
				}
			).insert(ignore_permissions=True)
		return company_name

	def _make_regulatory_profile(self):
		name = "CDP Test QR Profile"
		if frappe.db.exists("Crispy QR Regulatory Profile", name):
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy QR Regulatory Profile",
				"profile_name": name,
				"enabled": 1,
				"authority_code": "CDP-AUTH",
				"standard": "ZATCA TLV",
				"payload_format": "TLV",
				"output_encoding": "Base64",
				"error_correction": "High",
				"include_hash": 1,
				"requires_online_verification": 1,
				"verification_url_template": "https://verify.example/{{ doc.name }}",
				"encoder_key": "zatca_tlv",
				"encoder_settings_json": '{"issuer":"ACME"}',
			}
		).insert(ignore_permissions=True)
		return name

	def _make_fiscal_credential(self, name: str = "CDP Test Credential", company: str | None = None):
		if frappe.db.exists("Crispy Fiscal Credential", name):
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy Fiscal Credential",
				"credential_name": name,
				"enabled": 1,
				"company": company or self.company,
				"authority_code": "CDP-AUTH",
				"regulatory_profile": self.regulatory_profile,
				"environment": "Sandbox",
			}
		).insert(ignore_permissions=True)
		return name
