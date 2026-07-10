import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1._common import clean, parse_version, require_target_company, truthy


class TestApiCommonHelpers(FrappeTestCase):
	def test_clean_strips_and_normalizes_empty_values(self):
		self.assertEqual(clean("  Acme  "), "Acme")
		self.assertEqual(clean(None), "")
		self.assertEqual(clean(42), "42")

	def test_truthy_matches_existing_api_coercion(self):
		for value in (True, 1, "1", "true", "TRUE", " yes ", "on"):
			self.assertTrue(truthy(value))
		for value in (False, 0, None, "", "0", "false", "no", "off"):
			self.assertFalse(truthy(value))

	def test_parse_version_preserves_fallback_behavior(self):
		self.assertEqual(parse_version("2.10"), (2, 10))
		self.assertEqual(parse_version("7"), (7, 0))
		self.assertEqual(parse_version("bad.3"), (0, 3))
		self.assertEqual(parse_version("3.bad"), (3, 0))
		self.assertEqual(parse_version(None), (0, 0))

	def test_require_target_company_validates_blank_and_missing_company(self):
		with self.assertRaises(frappe.ValidationError):
			require_target_company("")

		with self.assertRaises(frappe.ValidationError):
			require_target_company("Missing Common Helper Company")

	def test_require_target_company_accepts_existing_company(self):
		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("No Company records available")

		self.assertEqual(require_target_company(f" {company} "), company)
