from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.formats import EXPORT_FIELDS, MAX_IMPORT_FIELD_BYTES
from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	IMMUTABLE_AFTER_INSERT_FIELDS,
	SNAPSHOT_HASH_FIELDS_V1,
	SNAPSHOT_HASH_FIELDS_V2,
)
from crispy_print.render_contract import (
	FORMAT_EXPORT_FIELDS,
	FORMAT_IMPORT_FIELD_MAX_BYTES,
	TEMPLATE_IMMUTABLE_AFTER_INSERT_FIELDS,
	TEMPLATE_SNAPSHOT_FIELD_MAP,
	TEMPLATE_SNAPSHOT_HASH_FIELDS_V1,
	TEMPLATE_SNAPSHOT_HASH_FIELDS_V2,
)


class TestRenderContractRegistry(FrappeTestCase):
	def test_format_api_field_lists_are_derived_from_render_contract_registry(self):
		self.assertEqual(EXPORT_FIELDS, list(FORMAT_EXPORT_FIELDS))
		self.assertEqual(MAX_IMPORT_FIELD_BYTES, FORMAT_IMPORT_FIELD_MAX_BYTES)

	def test_template_contract_field_lists_are_derived_from_render_contract_registry(self):
		self.assertEqual(IMMUTABLE_AFTER_INSERT_FIELDS, TEMPLATE_IMMUTABLE_AFTER_INSERT_FIELDS)
		self.assertEqual(SNAPSHOT_HASH_FIELDS_V1, TEMPLATE_SNAPSHOT_HASH_FIELDS_V1)
		self.assertEqual(SNAPSHOT_HASH_FIELDS_V2, TEMPLATE_SNAPSHOT_HASH_FIELDS_V2)

	def test_snapshot_field_map_covers_render_payload_fields(self):
		template_fields = {template_field for _, template_field in TEMPLATE_SNAPSHOT_FIELD_MAP}

		self.assertIn("layout_json", template_fields)
		self.assertIn("presentation_settings_json", template_fields)
		self.assertIn("typst_code", template_fields)
		self.assertIn("pdf_standard", template_fields)
		self.assertIn("source_doctype", template_fields)
		self.assertIn("source_report", template_fields)
		self.assertIn("source_contract", template_fields)

	def test_v2_hash_extends_v1_hash_with_render_fact_fields(self):
		v1_fields = set(TEMPLATE_SNAPSHOT_HASH_FIELDS_V1)
		v2_fields = set(TEMPLATE_SNAPSHOT_HASH_FIELDS_V2)

		self.assertTrue(v1_fields < v2_fields)
		self.assertEqual(
			v2_fields - v1_fields,
			{"snapshot_hash_version", "zebra_version", "barcode_symbology"},
		)
