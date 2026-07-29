# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import base64

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.document_codes import (
	generate_document_code,
	get_preferred_document_code_for_doc,
	resolve_document_code,
)


def rule_matches_test_company(doc, profile, rule):
	return getattr(doc, "abbr", None) == "DCR"


class TestDocumentCodes(FrappeTestCase):
	def setUp(self):
		self.company = self._ensure_company()
		self.regulatory_profile = self._make_regulatory_profile()
		self.fiscal_credential = self._make_fiscal_credential()

	def tearDown(self):
		frappe.db.rollback()

	def test_resolve_document_code_returns_live_regulatory_and_fiscal_links(self):
		profile = self._make_profile(
			profile_name="DCR Regulatory Profile",
			code_purpose="Regulatory",
			regulatory_profile=self.regulatory_profile,
			fiscal_credential=self.fiscal_credential,
			encoder_key="zatca_tlv",
			field_mapping_json='{"seller_name":"company_name","company_code":"abbr"}',
			document_rules=[
				{
					"document_type": "Company",
					"document_role": "Other",
					"condition_type": "Filter JSON",
					"condition_json": '{"abbr":"DCR"}',
					"priority": 10,
				}
			],
		)

		out = resolve_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Regulatory",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["profile_name"], profile.name)
		self.assertEqual(out["regulatory_profile"]["name"], self.regulatory_profile)
		self.assertEqual(out["fiscal_credential"]["name"], self.fiscal_credential)
		self.assertEqual(out["encoder_key"], "zatca_tlv")
		self.assertEqual(out["field_mapping"]["seller_name"], "company_name")
		self.assertEqual(len(out["matched_rules"]), 1)

	def test_preferred_profile_does_not_leak_caught_no_match_messages(self):
		profile = self._make_profile(
			profile_name="DCR Preferred Sandbox",
			environment="Sandbox",
			code_purpose="Regulatory",
			regulatory_profile=self.regulatory_profile,
			fiscal_credential=None,
			encoder_key="zatca_tlv",
			field_mapping_json='{"seller_name":"company_name","company_code":"abbr"}',
			document_rules=[
				{
					"document_type": "Company",
					"document_role": "Other",
					"condition_type": "Filter JSON",
					"condition_json": '{"abbr":"DCR"}',
					"priority": 10,
				}
			],
		)
		doc = frappe.get_doc("Company", self.company)
		frappe.local.message_log = [{"message": "pre-existing"}]

		out = get_preferred_document_code_for_doc(
			doc,
			purposes=("Regulatory",),
			environments=("Production", "Sandbox"),
		)

		self.assertEqual(out["profile_name"], profile.name)
		self.assertEqual(frappe.local.message_log, [{"message": "pre-existing"}])

	def test_generate_document_code_builds_selected_fields_payload(self):
		profile = self._make_profile(
			profile_name="DCR Selected Fields",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			content_source="Selected Fields",
			payload_format="JSON",
			output_encoding="Plain Text",
			selected_fields_json='["company_name","abbr"]',
			field_mapping_json='{"company_name":"company","abbr":"code"}',
			encoder_key="custom",
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Other",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["payload"], {"company": self.company, "code": "DCR"})
		self.assertEqual(out["encoded_value"], '{"company":"DCR Test Company","code":"DCR"}')

	def test_generate_document_code_builds_child_selected_fields_payload(self):
		profile = self._make_profile(
			profile_name="DCR Child Selected Fields",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			content_source="Selected Fields",
			payload_format="JSON",
			output_encoding="Plain Text",
			encoder_key="custom",
			selected_fields=[
				{
					"source_doctype": "Company",
					"field_key": "company_name",
					"output_key": "company",
				},
				{
					"source_doctype": "Company",
					"field_key": "abbr",
					"output_key": "code",
				},
			],
			document_rules=[
				{
					"document_type": "Company",
					"document_role": "Other",
					"condition_type": "Filter JSON",
					"condition_json": '{"abbr":"DCR"}',
					"priority": 10,
				}
			],
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Other",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["payload"], {"company": self.company, "code": "DCR"})
		self.assertEqual(out["encoded_value"], '{"company":"DCR Test Company","code":"DCR"}')

	def test_generate_document_code_renders_verification_url(self):
		profile = self._make_profile(
			profile_name="DCR Verification URL",
			code_purpose="Portal Link",
			regulatory_profile=None,
			fiscal_credential=None,
			content_source="Verification URL",
			payload_format="URL",
			output_encoding="Plain Text",
			encoder_key="url",
			verification_url_template="https://verify.test/{{ doc.name }}?abbr={{ doc.abbr }}",
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Portal Link",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["payload"], "https://verify.test/DCR Test Company?abbr=DCR")
		self.assertEqual(out["encoded_value"], out["payload"])

	def test_regulatory_tlv_base64_with_utf8_source_returns_ascii_payload(self):
		profile = self._make_profile(
			profile_name="DCR Regulatory TLV Base64",
			code_purpose="Regulatory",
			regulatory_profile=self.regulatory_profile,
			fiscal_credential=None,
			content_source="Payload Template",
			payload_template='{"seller_name":"شركة دسر","total":"د.ك 32,000.000"}',
			payload_format="TLV",
			output_encoding="Base64",
			encoder_key="zatca_tlv",
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Regulatory",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertTrue(out["encoded_value"].isascii())
		base64.b64decode(out["encoded_value"], validate=True)

	def test_regulatory_tlv_plain_text_passes_because_tlv_output_is_base64_ascii(self):
		plain_text_profile = self._make_regulatory_profile_with_encoding(
			"DCR Test Plain Text QR Profile",
			"Plain Text",
		)
		profile = self._make_profile(
			profile_name="DCR Regulatory TLV Plain Text",
			code_purpose="Regulatory",
			regulatory_profile=plain_text_profile,
			fiscal_credential=None,
			content_source="Payload Template",
			payload_template='{"seller_name":"شركة دسر","total":"د.ك 32,000.000"}',
			payload_format="TLV",
			output_encoding="Plain Text",
			encoder_key="zatca_tlv",
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Regulatory",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertTrue(out["encoded_value"].isascii())
		base64.b64decode(out["encoded_value"], validate=True)

	def test_regulatory_plain_text_rejects_utf8_final_payload_by_default(self):
		plain_text_profile = self._make_regulatory_profile_with_encoding(
			"DCR Test Plain Text QR Profile",
			"Plain Text",
		)
		profile = self._make_profile(
			profile_name="DCR Regulatory UTF8 Plain Text",
			code_purpose="Regulatory",
			regulatory_profile=plain_text_profile,
			fiscal_credential=None,
			content_source="Static Text",
			payload_template="total: د.ك 32,000.000",
			payload_format="Plain Text",
			output_encoding="Plain Text",
			encoder_key="custom",
		)

		with self.assertRaises(frappe.ValidationError):
			generate_document_code(
				doctype="Company",
				name=self.company,
				code_purpose="Regulatory",
				environment="Production",
				profile_name=profile.name,
			)

	def test_regulatory_plain_text_allows_utf8_with_explicit_encoder_setting(self):
		plain_text_profile = self._make_regulatory_profile_with_encoding(
			"DCR Test Plain Text QR Profile",
			"Plain Text",
		)
		profile = self._make_profile(
			profile_name="DCR Regulatory UTF8 Plain Text Allowed",
			code_purpose="Regulatory",
			regulatory_profile=plain_text_profile,
			fiscal_credential=None,
			content_source="Static Text",
			payload_template="total: د.ك 32,000.000",
			payload_format="Plain Text",
			output_encoding="Plain Text",
			encoder_key="custom",
			encoder_settings_json='{"allow_utf8_final_payload":true}',
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Regulatory",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["encoded_value"], "total: د.ك 32,000.000")

	def test_non_regulatory_plain_text_allows_utf8_final_payload(self):
		profile = self._make_profile(
			profile_name="DCR Other UTF8 Plain Text",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			content_source="Static Text",
			payload_template="total: د.ك 32,000.000",
			payload_format="Plain Text",
			output_encoding="Plain Text",
			encoder_key="custom",
		)

		out = generate_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Other",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["encoded_value"], "total: د.ك 32,000.000")

	def test_payload_template_invalid_json_raises_validation_error(self):
		profile = self._make_profile(
			profile_name="DCR Invalid Rendered JSON",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			content_source="Payload Template",
			payload_template="{bad",
			payload_format="JSON",
			output_encoding="Plain Text",
			encoder_key="custom",
		)

		with self.assertRaisesRegex(frappe.ValidationError, "Rendered Payload Template"):
			generate_document_code(
				doctype="Company",
				name=self.company,
				code_purpose="Other",
				environment="Production",
				profile_name=profile.name,
			)

	def test_auto_selects_matching_profile(self):
		self._make_profile(
			profile_name="DCR Non Matching",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			priority=50,
			document_rules=[
				{
					"document_type": "User",
					"document_role": "Other",
					"condition_type": "Always",
					"priority": 100,
				}
			],
		)
		matching = self._make_profile(
			profile_name="DCR Matching",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			priority=20,
			document_rules=[
				{
					"document_type": "Company",
					"document_role": "Other",
					"condition_type": "Always",
					"priority": 100,
				}
			],
		)

		out = resolve_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Other",
			environment="Production",
		)

		self.assertEqual(out["profile_name"], matching.name)

	def test_custom_method_rules_are_supported(self):
		profile = self._make_profile(
			profile_name="DCR Custom Method",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			document_rules=[
				{
					"document_type": "Company",
					"document_role": "Other",
					"condition_type": "Custom Method",
					"condition_expression": "crispy_print.tests.api.test_document_codes.rule_matches_test_company",
					"priority": 10,
				}
			],
		)

		out = resolve_document_code(
			doctype="Company",
			name=self.company,
			code_purpose="Other",
			environment="Production",
			profile_name=profile.name,
		)

		self.assertEqual(out["profile_name"], profile.name)
		self.assertEqual(len(out["matched_rules"]), 1)

	def test_preferred_document_code_can_skip_custom_method_rules_for_preview(self):
		self._make_profile(
			profile_name="DCR Preview Custom Method Only",
			code_purpose="Other",
			regulatory_profile=None,
			fiscal_credential=None,
			document_rules=[
				{
					"document_type": "Company",
					"document_role": "Other",
					"condition_type": "Custom Method",
					"condition_expression": "crispy_print.tests.api.test_document_codes.rule_matches_test_company",
					"priority": 10,
				}
			],
		)
		doc = frappe.get_doc("Company", self.company)

		out = get_preferred_document_code_for_doc(
			doc,
			purposes=("Other",),
			environments=("Production",),
			allow_custom_methods=False,
		)

		self.assertIsNone(out)

	def _ensure_company(self):
		company = "DCR Test Company"
		if not frappe.db.exists("Company", company):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": company,
					"abbr": "DCR",
					"default_currency": "KWD",
					"country": "Kuwait",
				}
			).insert(ignore_permissions=True)
		return company

	def _make_regulatory_profile(self):
		name = "DCR Test QR Profile"
		if frappe.db.exists("Crispy QR Regulatory Profile", name):
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy QR Regulatory Profile",
				"profile_name": name,
				"enabled": 1,
				"authority_code": "DCR-AUTH",
				"standard": "ZATCA TLV",
				"payload_format": "TLV",
				"output_encoding": "Base64",
				"error_correction": "Medium",
				"encoder_key": "zatca_tlv",
			}
		).insert(ignore_permissions=True)
		return name

	def _make_regulatory_profile_with_encoding(self, name: str, output_encoding: str):
		if frappe.db.exists("Crispy QR Regulatory Profile", name):
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy QR Regulatory Profile",
				"profile_name": name,
				"enabled": 1,
				"authority_code": "DCR-AUTH",
				"standard": "Custom",
				"payload_format": "TLV",
				"output_encoding": output_encoding,
				"error_correction": "Medium",
				"encoder_key": "custom",
			}
		).insert(ignore_permissions=True)
		return name

	def _make_fiscal_credential(self):
		name = "DCR Test Credential"
		if frappe.db.exists("Crispy Fiscal Credential", name):
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy Fiscal Credential",
				"credential_name": name,
				"enabled": 1,
				"company": self.company,
				"authority_code": "DCR-AUTH",
				"regulatory_profile": self.regulatory_profile,
				"environment": "Production",
			}
		).insert(ignore_permissions=True)
		return name

	def _make_profile(self, profile_name: str, document_rules: list[dict] | None = None, **overrides):
		values = {
			"doctype": "Crispy Document Code Profile",
			"profile_name": profile_name,
			"enabled": 1,
			"company": self.company,
			"environment": "Production",
			"code_purpose": "Other",
			"code_format": "QR Code",
			"code_symbology": "QR Code",
			"payload_format": "JSON",
			"output_encoding": "Plain Text",
			"content_source": "Encoder",
			"encoder_key": "custom",
			"priority": 100,
		}
		values.update(overrides)
		doc = frappe.get_doc(values)
		for rule in document_rules or []:
			doc.append("document_rules", rule)
		doc.insert(ignore_permissions=True)
		return doc
