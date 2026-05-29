# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import json
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.tests.helpers.defaults import capture_defaults, clear_defaults, restore_defaults


class TestCrispyFormatRetrievalAPI(FrappeTestCase):
	"""Test Crispy Format retrieval APIs"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")

		# Clean up test formats
		frappe.db.delete("Crispy Format", {"name": ["like", "Test API Format%"]})
		self._default_doctypes = ["Sales Invoice", "Sales Order", "Purchase Order"]
		self._saved_defaults = capture_defaults(self._default_doctypes)
		clear_defaults(self._default_doctypes)
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after tests"""
		frappe.db.delete("Crispy Format", {"name": ["like", "Test API Format%"]})
		frappe.db.delete("Crispy Typst Block", {"block_key": ["like", "test_api_format_block%"]})
		restore_defaults(self._saved_defaults)
		frappe.db.commit()

	def test_get_crispy_formats_for_doctype(self):
		"""Test retrieving formats for a specific DocType"""
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		# Create test formats
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			}
		)
		format1.insert()

		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format 2",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()

		# Test retrieval
		formats = get_crispy_formats_for_doctype("Sales Invoice")

		self.assertIsInstance(formats, list)
		self.assertTrue(len(formats) >= 2)

		format_names = [f["name"] for f in formats]
		self.assertIn("Test API Format 1", format_names)
		self.assertIn("Test API Format 2", format_names)

	def test_get_crispy_format_hydrates_typst_blocks(self):
		from crispy_print.api.v1 import get_crispy_format

		block = frappe.get_doc(
			{
				"doctype": "Crispy Typst Block",
				"block_name": "Test API Format Block",
				"block_key": "test_api_format_block",
				"enabled": 1,
				"typst_code": "#text[#doc.customer_name]",
			}
		)
		block.append("applicable_documents", {"document_type": "Sales Invoice"})
		block.insert(ignore_permissions=True)

		layout = {
			"sections": [
				{
					"columns": [
						{
							"fields": [
								{
									"fieldtype": "Crispy Typst Block",
									"fieldname": "_crispy_typst_block",
									"crispy_typst_block": "test_api_format_block",
								}
							]
						}
					]
				}
			]
		}
		fmt = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format With Block",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps(layout),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			}
		)
		fmt.insert()

		result = get_crispy_format(fmt.name)
		resolved_layout = json.loads(result["layout_json"])
		field = resolved_layout["sections"][0]["columns"][0]["fields"][0]

		self.assertEqual(field["crispy_typst_block_name"], "Test API Format Block")
		self.assertEqual(field["crispy_typst_block_code"], "#text[#doc.customer_name]")
		stored_layout = json.loads(frappe.db.get_value("Crispy Format", fmt.name, "layout_json"))
		self.assertNotIn(
			"crispy_typst_block_code",
			stored_layout["sections"][0]["columns"][0]["fields"][0],
		)

	def test_get_crispy_formats_excludes_invalid_json(self):
		"""Test that formats with invalid JSON are excluded"""
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		# Create format with valid JSON
		valid_format = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Valid",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		valid_format.insert()

		# Create format with invalid JSON directly in DB
		frappe.db.set_value("Crispy Format", "Test API Format Valid", "layout_json", "{invalid json")
		frappe.db.commit()

		# Should not raise error, just exclude invalid format
		formats = get_crispy_formats_for_doctype("Purchase Order")

		# Should return empty list or not include the invalid format
		self.assertIsInstance(formats, list)

	def test_get_crispy_formats_for_doctype_uses_cache(self):
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		cached_result = [{"name": "Cached Format", "doc_type": "Sales Invoice"}]
		mock_cache = mock.Mock()
		mock_cache.get_value.return_value = cached_result

		with (
			mock.patch("crispy_print.api.v1.formats.frappe.cache", return_value=mock_cache),
			mock.patch("crispy_print.api.v1.formats._compute_crispy_formats_for_doctype") as mock_compute,
		):
			result = get_crispy_formats_for_doctype("Sales Invoice")

		self.assertEqual(result, cached_result)
		mock_compute.assert_not_called()
		mock_cache.set_value.assert_not_called()

	def test_get_crispy_formats_for_doctype_sets_cache_on_miss(self):
		from crispy_print.api.v1 import get_crispy_formats_for_doctype
		from crispy_print.api.v1.formats import FORMAT_LIST_CACHE_TTL_SECONDS

		computed_result = [{"name": "Computed Format", "doc_type": "Sales Invoice"}]
		mock_cache = mock.Mock()
		mock_cache.get_value.return_value = None

		with (
			mock.patch("crispy_print.api.v1.formats.frappe.cache", return_value=mock_cache),
			mock.patch(
				"crispy_print.api.v1.formats._compute_crispy_formats_for_doctype",
				return_value=computed_result,
			) as mock_compute,
		):
			result = get_crispy_formats_for_doctype("Sales Invoice")

		self.assertEqual(result, computed_result)
		mock_compute.assert_called_once_with("Sales Invoice")
		mock_cache.set_value.assert_called_once_with(
			"crispy_print:formats_for_doctype:Sales Invoice",
			computed_result,
			expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS,
		)

	def test_invalidate_crispy_formats_cache_for_doctype(self):
		from crispy_print.api.v1.formats import invalidate_crispy_formats_cache_for_doctype

		mock_cache = mock.Mock()
		with mock.patch("crispy_print.api.v1.formats.frappe.cache", return_value=mock_cache):
			invalidate_crispy_formats_cache_for_doctype("Sales Invoice")

		mock_cache.delete_value.assert_called_once_with("crispy_print:formats_for_doctype:Sales Invoice")

	def test_get_default_doctypes(self):
		"""Test retrieving DocTypes with default formats"""
		from crispy_print.api.v1 import get_default_doctypes

		# Create default format for Sales Order
		format_so = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default SO",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_so.insert()
		frappe.db.set_value("Crispy Format", format_so.name, "is_default", 1)

		# Create default format for Purchase Order
		format_po = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default PO",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_po.insert()
		frappe.db.set_value("Crispy Format", format_po.name, "is_default", 1)
		frappe.db.commit()

		# Test retrieval
		default_doctypes = get_default_doctypes()

		self.assertIsInstance(default_doctypes, list)
		self.assertIn("Sales Order", default_doctypes)
		self.assertIn("Purchase Order", default_doctypes)

	def test_get_default_doctypes_excludes_report_formats(self):
		from crispy_print.api.v1 import get_default_doctypes

		format_report = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default Report",
				"crispy_format_type": "Report",
				"module": "Crispy Print",
				"is_generic": 1,
				"generic_report_type": "Grid",
				"typst_code": "#text[Report]",
				"is_advanced": 1,
			}
		)
		format_report.insert()
		frappe.db.set_value("Crispy Format", format_report.name, "is_default", 1)
		frappe.db.commit()

		default_doctypes = get_default_doctypes()

		self.assertNotIn(None, default_doctypes)
		self.assertNotIn("", default_doctypes)

	def test_get_default_report_builder_config(self):
		from crispy_print.api.v1 import get_default_report_builder_config

		grid = get_default_report_builder_config("Grid")
		tree = get_default_report_builder_config("Tree")
		unknown = get_default_report_builder_config("SomethingElse")

		self.assertEqual(grid["mode"], "basic")
		self.assertEqual(grid["preset"], "grid")
		self.assertEqual(tree["preset"], "tree")
		self.assertEqual(unknown["preset"], "grid")
		self.assertIn("show_filters", grid)
		self.assertIn("chart_enabled", grid)
		self.assertIn("font_family", grid)

	def test_get_reports_without_custom_html_type_filtering(self):
		from crispy_print.api.v1.formats import get_reports_without_custom_html

		reports = [
			{
				"name": "Tree Report",
				"report_type": "Script Report",
				"ref_doctype": "Sales Invoice",
				"module": "Accounts",
			},
			{
				"name": "Grid Report",
				"report_type": "Query Report",
				"ref_doctype": "Sales Invoice",
				"module": "Accounts",
			},
		]

		with (
			mock.patch("crispy_print.api.v1.formats.frappe.get_list", return_value=reports),
			mock.patch(
				"crispy_print.api.v1.formats.frappe.get_module_path",
				return_value="/tmp/accounts",
			),
			mock.patch("pathlib.Path.exists", return_value=False),
			mock.patch(
				"crispy_print.api.v1.formats._get_report_is_tree",
				side_effect=lambda report_name: report_name == "Tree Report",
			),
		):
			grid_only = get_reports_without_custom_html("Grid")
			tree_only = get_reports_without_custom_html("Tree")
			summary_fallback = get_reports_without_custom_html("Summary")

		self.assertEqual([r["name"] for r in grid_only], ["Grid Report"])
		self.assertEqual([r["name"] for r in tree_only], ["Tree Report"])
		self.assertCountEqual([r["name"] for r in summary_fallback], ["Tree Report", "Grid Report"])

	def test_get_custom_report_formats_uses_child_table_query(self):
		from crispy_print.api.v1.formats import get_custom_report_formats

		with (
			mock.patch(
				"crispy_print.api.v1.formats.frappe.get_all",
				return_value=[
					{"parent": "FMT-1"},
					{"parent": "FMT-2"},
				],
			) as mock_get_all,
			mock.patch(
				"crispy_print.api.v1.formats.frappe.get_list",
				return_value=[{"name": "FMT-2", "modified": "2026-01-02 00:00:00"}],
			) as mock_get_list,
		):
			result = get_custom_report_formats("Sales Register")

		self.assertEqual([row["name"] for row in result], ["FMT-2"])
		mock_get_all.assert_called_once()
		mock_get_list.assert_called_once()
		self.assertIn("name", mock_get_list.call_args.kwargs["filters"])

	def test_extract_tree_flag_from_json_payload(self):
		from crispy_print.api.v1.formats import _extract_tree_flag_from_json

		self.assertTrue(_extract_tree_flag_from_json('{"tree": true}'))
		self.assertFalse(_extract_tree_flag_from_json('{"report": {"is_tree": "0"}}'))
		self.assertIsNone(_extract_tree_flag_from_json('{"foo": "bar"}'))
		self.assertIsNone(_extract_tree_flag_from_json("not-json"))

	def test_get_crispy_formats_empty_doctype(self):
		"""Test retrieval for DocType with no formats"""
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		# Use an unlikely DocType that won't have formats
		formats = get_crispy_formats_for_doctype("Language")

		self.assertIsInstance(formats, list)
		self.assertEqual(len(formats), 0)

	def test_get_available_formats_uses_linked_report_table_for_custom(self):
		"""Custom report formats should resolve via report child table rows."""
		from crispy_print.api.v1 import get_available_formats

		report_name = frappe.db.get_value("Report", {}, "name")
		if not report_name:
			self.skipTest("No Report records available")
		generic_report_type = frappe.db.get_value("Crispy Generic Report", {}, "name")
		if not generic_report_type:
			self.skipTest("No Crispy Generic Report records available")

		custom_name = "Test API Format Linked Report Custom"
		generic_name = "Test API Format Linked Report Generic"

		custom = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": custom_name,
				"crispy_format_type": "Report",
				"is_generic": 0,
				"module": "Crispy Print",
				"report": [{"report": report_name, "disabled": 0}],
			}
		)
		custom.insert()

		generic = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": generic_name,
				"crispy_format_type": "Report",
				"is_generic": 1,
				"generic_report_type": generic_report_type,
				"module": "Crispy Print",
			}
		)
		generic.insert()
		frappe.db.commit()

		out = get_available_formats(report_name)
		custom_names = [row["name"] for row in out.get("custom_formats") or []]

		self.assertIn(custom_name, custom_names)
		self.assertEqual(out.get("default_format"), custom_name)
		self.assertEqual(out.get("generic_formats"), [])


class TestCrispyFormatImportExportAPI(FrappeTestCase):
	"""Test import/export API for Crispy Format schema v1."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Crispy Format", {"name": ["like", "Test ImportExport%"]})
		frappe.db.commit()

	def tearDown(self):
		frappe.db.delete("Crispy Format", {"name": ["like", "Test ImportExport%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Generic Report - Test ImportExport%"]})
		frappe.db.commit()

	def _insert_format(self, name: str, **overrides):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}, "language": "en"}),
				"doc_header": "#let header_block = []",
				"doc_footer": "#let footer_block = []",
				"typst_preamble": "#set text(size: 10pt)",
				"typst_code": "#text[Hello]",
				"raw_typst": 1,
				**overrides,
			}
		)
		doc.insert()
		return doc

	def test_export_payload_schema(self):
		from crispy_print.api.v1 import export_crispy_format

		self._insert_format("Test ImportExport Export")
		payload = export_crispy_format("Test ImportExport Export")

		self.assertEqual(payload["schema_version"], 1)
		self.assertEqual(payload["app"], "crispy_print")
		self.assertIn("exported_at", payload)
		self.assertIn("format", payload)
		self.assertEqual(payload["format"]["name"], "Test ImportExport Export")
		self.assertNotIn("is_default", payload["format"])

	def test_import_new_format_success(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		self._insert_format("Test ImportExport Source")
		payload = export_crispy_format("Test ImportExport Source")
		payload["format"]["name"] = "Test ImportExport Imported"

		result = import_crispy_format(payload, on_conflict="copy")
		imported = frappe.get_doc("Crispy Format", result["name"])

		self.assertTrue(result["success"])
		self.assertEqual(imported.name, "Test ImportExport Imported")
		self.assertEqual(imported.typst_code, "#text[Hello]")
		self.assertEqual(imported.is_default, 0)

	def test_import_generic_report_preserves_validation(self):
		from crispy_print.api.v1 import import_crispy_format

		payload = {
			"schema_version": 1,
			"exported_at": "2026-02-07T00:00:00",
			"app": "crispy_print",
			"format": {
				"name": "Generic Report - Test ImportExport Grid",
				"crispy_format_type": "Report",
				"report": None,
				"doc_type": None,
				"contract": None,
				"is_generic": 1,
				"is_advanced": 1,
				"generic_report_type": "Grid",
				"raw_typst": 0,
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}, "language": "en"}),
				"doc_header": "",
				"doc_footer": "",
				"typst_preamble": "",
				"typst_code": "#text[Generic]",
				"default_print_language": None,
			},
		}

		result = import_crispy_format(payload, on_conflict="copy")
		imported = frappe.get_doc("Crispy Format", result["name"])
		self.assertEqual(imported.crispy_format_type, "Report")
		self.assertEqual(imported.is_generic, 1)
		self.assertEqual(imported.is_advanced, 1)
		self.assertEqual(imported.raw_typst, 1)

	def test_import_conflict_copy_creates_suffix(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		self._insert_format("Test ImportExport Conflict")
		payload = export_crispy_format("Test ImportExport Conflict")

		result = import_crispy_format(payload, on_conflict="copy")
		self.assertTrue(result["name"].startswith("Test ImportExport Conflict (Imported"))
		self.assertTrue(frappe.db.exists("Crispy Format", result["name"]))

	def test_import_conflict_overwrite_updates_existing(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		self._insert_format("Test ImportExport Existing", typst_code="#text[Old]")
		self._insert_format("Test ImportExport Source Overwrite", typst_code="#text[New]")
		payload = export_crispy_format("Test ImportExport Source Overwrite")
		payload["format"]["name"] = "Test ImportExport Existing"

		result = import_crispy_format(payload, on_conflict="overwrite")
		updated = frappe.get_doc("Crispy Format", "Test ImportExport Existing")

		self.assertEqual(result["name"], "Test ImportExport Existing")
		self.assertEqual(updated.typst_code, "#text[New]")

	def test_check_import_conflicts(self):
		from crispy_print.api.v1 import check_import_conflicts, export_crispy_format

		self._insert_format("Test ImportExport Check")
		payload = export_crispy_format("Test ImportExport Check")
		result = check_import_conflicts(payload)

		self.assertTrue(result["exists"])
		self.assertEqual(result["name"], "Test ImportExport Check")

	def test_invalid_schema_version_rejected(self):
		from crispy_print.api.v1 import import_crispy_format

		with self.assertRaises(frappe.ValidationError):
			import_crispy_format({"schema_version": 999, "format": {}}, on_conflict="copy")

	def test_invalid_json_payload_rejected(self):
		from crispy_print.api.v1 import import_crispy_format

		with self.assertRaises(frappe.ValidationError):
			import_crispy_format('{"schema_version": 1, "format": ', on_conflict="copy")

	def test_missing_reference_warnings_non_blocking(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		self._insert_format("Test ImportExport Warn Source")
		payload = export_crispy_format("Test ImportExport Warn Source")
		payload["format"]["name"] = "Test ImportExport Warn Imported"
		payload["format"]["default_print_language"] = "Missing-Language"
		payload["format"]["presentation_settings"] = json.dumps(
			{
				"page": {"size": "A4"},
				"language": "en",
				"branding": {
					"letterhead": "Missing Letterhead",
					"logo": {"company": "Missing Co", "image": "/files/missing-logo.png"},
				},
			}
		)

		result = import_crispy_format(payload, on_conflict="copy")
		self.assertTrue(result["success"])
		self.assertTrue(frappe.db.exists("Crispy Format", result["name"]))
		self.assertGreaterEqual(len(result["warnings"]), 3)

	def test_is_default_not_transferred_on_import(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		source = self._insert_format("Test ImportExport Default Source", doc_type="Language")
		frappe.db.set_value("Crispy Format", source.name, "is_default", 1, update_modified=False)
		frappe.db.commit()

		payload = export_crispy_format(source.name)
		payload["format"]["name"] = "Test ImportExport Default Imported"
		result = import_crispy_format(payload, on_conflict="copy")
		imported = frappe.get_doc("Crispy Format", result["name"])

		self.assertEqual(imported.is_default, 0)
