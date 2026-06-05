import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.company_context import resolve_effective_company


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
