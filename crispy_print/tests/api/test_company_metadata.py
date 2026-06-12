import json
from pathlib import Path

from frappe.tests.utils import FrappeTestCase

DOCTYPE_JSON_ROOT = Path(__file__).resolve().parents[2] / "crispy_print" / "doctype"


class TestCompanyListMetadata(FrappeTestCase):
	def test_company_scoped_doctypes_expose_company_standard_filter(self):
		for doctype in (
			"crispy_branding_profile",
			"crispy_document_code_profile",
			"crispy_fiscal_credential",
			"crispy_format",
			"crispy_issued_document",
			"crispy_template",
			"crispy_typst_block",
		):
			path = DOCTYPE_JSON_ROOT / doctype / f"{doctype}.json"
			payload = json.loads(path.read_text(encoding="utf-8"))
			company_field = next(
				(field for field in payload.get("fields", []) if field.get("fieldname") == "company"),
				None,
			)

			self.assertIsNotNone(company_field, doctype)
			self.assertEqual(company_field.get("in_list_view"), 1, doctype)
			self.assertEqual(company_field.get("in_standard_filter"), 1, doctype)
