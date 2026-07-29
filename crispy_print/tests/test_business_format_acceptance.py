import json

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.business_format_acceptance import CORE_V1_BUSINESS_FORMATS


class TestCoreV1BusinessFormatAcceptance(FrappeTestCase):
	def test_every_core_v1_contract_has_a_catalog_sample(self):
		from crispy_print.api.v1.sample_formats import get_sample_format, list_sample_formats

		catalog = {row["id"]: row for row in list_sample_formats()}
		for spec in CORE_V1_BUSINESS_FORMATS:
			self.assertIn(spec.sample_id, catalog)
			payload = get_sample_format(spec.sample_id)
			format_data = payload["format"]
			self.assertEqual(format_data["crispy_format_type"], spec.target_type)
			if spec.target_type == "DocType":
				self.assertEqual(format_data["doc_type"], spec.target)
			else:
				self.assertIn(
					spec.target,
					[row.get("report") for row in format_data.get("report") or []],
				)

	def test_doctype_samples_use_real_top_level_fields_and_tables(self):
		from crispy_print.api.v1.sample_formats import get_sample_format

		for spec in CORE_V1_BUSINESS_FORMATS:
			if spec.target_type != "DocType":
				continue
			meta = frappe.get_meta(spec.target)
			payload = get_sample_format(spec.sample_id)
			layout = json.loads(payload["format"]["layout_json"])
			fields = [
				field
				for section in layout.get("sections") or []
				for column in section.get("columns") or []
				for field in column.get("fields") or []
			]
			fieldnames = {field.get("fieldname") for field in fields}
			for fieldname in spec.required_fields:
				self.assertIn(fieldname, fieldnames, f"{spec.sample_id} omits {fieldname}")
				self.assertIsNotNone(meta.get_field(fieldname), f"{spec.target}.{fieldname} is unavailable")
			for fieldname in spec.required_tables:
				self.assertIn(fieldname, fieldnames, f"{spec.sample_id} omits table {fieldname}")
				self.assertEqual(meta.get_field(fieldname).fieldtype, "Table")

	def test_page_profiles_match_the_acceptance_contract(self):
		from crispy_print.api.v1.sample_formats import get_sample_format

		for spec in CORE_V1_BUSINESS_FORMATS:
			settings = json.loads(get_sample_format(spec.sample_id)["format"]["presentation_settings"])
			page_size = str((settings.get("page") or {}).get("size") or "").lower()
			self.assertEqual(page_size, spec.page_size)
			self.assertFalse((settings.get("qr") or {}).get("enabled"))
