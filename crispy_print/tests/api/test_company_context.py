import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.company_context import (
	extract_presentation_settings_company,
	extract_source_company,
	resolve_effective_company,
)


class TestEffectiveCompanyResolution(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company_a = "CP Context Company A"
		self.company_b = "CP Context Company B"

	def tearDown(self):
		frappe.db.rollback()

	def test_source_document_company_wins_over_report_and_explicit_company(self):
		company = resolve_effective_company(
			source_doc={"company": self.company_a},
			report_filters={"company": self.company_b},
			explicit_company=self.company_b,
		)

		self.assertEqual(company, self.company_a)

	def test_report_company_wins_over_explicit_company(self):
		company = resolve_effective_company(
			report_filters={"company": self.company_a},
			explicit_company=self.company_b,
		)

		self.assertEqual(company, self.company_a)

	def test_explicit_company_is_used_without_source_or_report_company(self):
		company = resolve_effective_company(explicit_company=self.company_b)

		self.assertEqual(company, self.company_b)

	def test_extract_presentation_settings_company_prefers_branding_company(self):
		company = extract_presentation_settings_company(
			{
				"branding": {
					"company": self.company_a,
					"logo": {"company": self.company_b},
				}
			}
		)

		self.assertEqual(company, self.company_a)

	def test_extract_presentation_settings_company_falls_back_to_logo_company(self):
		company = extract_presentation_settings_company(
			{
				"branding": {
					"company": "",
					"logo": {"company": self.company_b},
				}
			}
		)

		self.assertEqual(company, self.company_b)

	def test_extract_presentation_settings_company_accepts_json_string(self):
		company = extract_presentation_settings_company('{"branding":{"company":"CP Context Company A"}}')

		self.assertEqual(company, self.company_a)

	def test_extract_presentation_settings_company_ignores_invalid_input(self):
		self.assertIsNone(extract_presentation_settings_company("{invalid json"))
		self.assertIsNone(extract_presentation_settings_company(["not", "a", "dict"]))

	def test_extract_source_company_prefers_source_company(self):
		company = extract_source_company(
			{
				"company": self.company_a,
				"presentation_settings": {"branding": {"company": self.company_b}},
			}
		)

		self.assertEqual(company, self.company_a)

	def test_extract_source_company_uses_presentation_settings_when_source_company_is_blank(self):
		company = extract_source_company(
			{
				"company": "",
				"presentation_settings": {"branding": {"logo": {"company": self.company_b}}},
			}
		)

		self.assertEqual(company, self.company_b)
