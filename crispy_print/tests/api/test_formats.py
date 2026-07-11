# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt
# pyright: reportArgumentType=false, reportAttributeAccessIssue=false

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

	def _ensure_company(self, name="Test API Format Company", abbr="TAFC"):
		if not frappe.db.exists("Company", name):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": name,
					"abbr": abbr,
					"default_currency": "USD",
				}
			).insert(ignore_permissions=True)
		return name

	def _insert_doctype_format(
		self,
		name: str,
		doctype: str = "Sales Invoice",
		company: str | None = None,
		is_default: int = 0,
		layout: dict | None = None,
	):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"crispy_format_type": "DocType",
				"doc_type": doctype,
				"company": company,
				"module": "Crispy Print",
				"is_default": is_default,
				"layout_json": json.dumps(layout or {"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			}
		)
		doc.insert()
		return doc

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
		self.assertIn("company", formats[0])
		self.assertIn("is_default", formats[0])

	def test_get_crispy_formats_for_doctype_filters_and_orders_by_company(self):
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		company = self._ensure_company("Test API Format Company A", "TAFCA")
		other_company = self._ensure_company("Test API Format Company B", "TAFCB")
		self._insert_doctype_format("Test API Format Company Exact", company=company)
		self._insert_doctype_format("Test API Format Company Other", company=other_company)
		global_format = self._insert_doctype_format("Test API Format Company Global", company=company)
		frappe.db.set_value("Crispy Format", global_format.name, "company", "", update_modified=False)
		frappe.db.commit()

		formats = get_crispy_formats_for_doctype("Sales Invoice", company=company)

		names = [row["name"] for row in formats]
		self.assertIn("Test API Format Company Exact", names)
		self.assertIn("Test API Format Company Global", names)
		self.assertNotIn("Test API Format Company Other", names)
		self.assertLess(
			names.index("Test API Format Company Exact"),
			names.index("Test API Format Company Global"),
		)

	def test_get_crispy_formats_for_doctype_company_filter_excludes_invalid_json(self):
		from crispy_print.api.v1 import get_crispy_formats_for_doctype

		company = self._ensure_company("Test API Format Company Invalid", "TAFCI")
		valid = self._insert_doctype_format("Test API Format Company Valid JSON", company=company)
		invalid = self._insert_doctype_format("Test API Format Company Invalid JSON", company=company)
		frappe.db.set_value("Crispy Format", invalid.name, "layout_json", "{invalid json")
		frappe.db.commit()

		formats = get_crispy_formats_for_doctype("Sales Invoice", company=company)
		names = [row["name"] for row in formats]

		self.assertIn(valid.name, names)
		self.assertNotIn(invalid.name, names)

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

	def test_get_crispy_format_hydrates_typst_blocks_for_effective_company(self):
		from crispy_print.api.v1 import get_crispy_format

		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("No Company records available")
		self._insert_typst_block(
			block_key="test_api_format_block_company_context",
			block_name="Test API Format Global Company Context Block",
			typst_code="#text[global]",
		)
		self._insert_typst_block(
			block_key="test_api_format_block_company_context",
			block_name="Test API Format Scoped Company Context Block",
			company=company,
			typst_code="#text[company]",
		)

		layout = {
			"sections": [
				{
					"columns": [
						{
							"fields": [
								{
									"fieldtype": "Crispy Typst Block",
									"fieldname": "_crispy_typst_block",
									"crispy_typst_block": "test_api_format_block_company_context",
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
				"name": "Test API Format Company Context Block",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps(layout),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			}
		)
		fmt.insert()

		result = get_crispy_format(fmt.name, company=company)
		field = json.loads(result["layout_json"])["sections"][0]["columns"][0]["fields"][0]

		self.assertEqual(result["effective_company"], company)
		self.assertEqual(field["crispy_typst_block_name"], "Test API Format Scoped Company Context Block")
		self.assertEqual(field["crispy_typst_block_code"], "#text[company]")

	def test_duplicate_crispy_format_for_company_preserves_layout_and_retargets_settings(self):
		from crispy_print.api.v1 import duplicate_crispy_format_for_company

		source_company = self._ensure_company("Test API Format Duplicate Source", "TAFDS")
		target_company = self._ensure_company("Test API Format Duplicate Target", "TAFDT")
		layout = {"sections": [{"label": "Frozen", "columns": []}]}
		fmt = self._insert_doctype_format(
			"Test API Format Duplicate Source Format",
			company=source_company,
			is_default=1,
			layout=layout,
		)
		fmt.presentation_settings = json.dumps(
			{
				"page": {"size": "A4"},
				"branding": {"company": source_company, "logo": {"company": source_company}},
			}
		)
		fmt.save()

		result = duplicate_crispy_format_for_company(fmt.name, target_company)
		clone = frappe.get_doc("Crispy Format", result["name"])
		settings = json.loads(clone.presentation_settings)

		self.assertEqual(result["source_name"], fmt.name)
		self.assertEqual(clone.company, target_company)
		self.assertFalse(clone.is_default)
		self.assertEqual(json.loads(clone.layout_json), layout)
		self.assertEqual(settings["branding"]["company"], target_company)
		self.assertEqual(settings["branding"]["logo"]["company"], target_company)

	def test_duplicate_insert_checks_target_company_access_before_insert(self):
		from crispy_print.api.v1 import formats

		with (
			mock.patch("crispy_print.api.v1.formats._ensure_create_permission"),
			mock.patch(
				"crispy_print.api.v1.formats._require_target_company",
				return_value="Blocked Company",
			),
			mock.patch(
				"crispy_print.api.v1.formats.ensure_company_access",
				side_effect=frappe.PermissionError,
			) as ensure_access,
			mock.patch("crispy_print.api.v1.formats.frappe.get_doc") as get_doc,
		):
			self.assertRaises(
				frappe.PermissionError,
				formats._insert_format_duplicate_for_company,
				{"name": "Test API Format Blocked Duplicate"},
				target_company="Blocked Company",
				source_name="Test API Format Source",
			)

		ensure_access.assert_called_once_with("Blocked Company", doctype="Crispy Format")
		get_doc.assert_not_called()

	def test_get_crispy_format_includes_pdf_standard(self):
		from crispy_print.api.v1 import get_crispy_format

		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("No Company records available")

		fmt = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format PDF Standard",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"company": company,
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
				"pdf_standard": "PDF/A-3u",
			}
		)
		fmt.insert()

		result = get_crispy_format(fmt.name)

		self.assertEqual(result["pdf_standard"], "PDF/A-3u")
		self.assertEqual(result["company"], company)

	def _insert_typst_block(
		self,
		block_key: str,
		block_name: str,
		typst_code: str,
		company: str | None = None,
	):
		block = frappe.get_doc(
			{
				"doctype": "Crispy Typst Block",
				"block_name": block_name,
				"block_key": block_key,
				"company": company,
				"enabled": 1,
				"typst_code": typst_code,
			}
		)
		block.append("applicable_documents", {"document_type": "Sales Invoice"})
		block.insert(ignore_permissions=True)
		return block

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
		mock_compute.assert_called_once_with("Sales Invoice", company=None)
		mock_cache.set_value.assert_any_call(
			"crispy_print:formats_for_doctype:Sales Invoice",
			computed_result,
			expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS,
		)
		mock_cache.set_value.assert_any_call(
			"crispy_print:formats_for_doctype:Sales Invoice:cache_keys",
			["crispy_print:formats_for_doctype:Sales Invoice"],
			expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS,
		)

	def test_get_crispy_formats_for_doctype_uses_company_cache_key(self):
		from crispy_print.api.v1 import get_crispy_formats_for_doctype
		from crispy_print.api.v1.formats import FORMAT_LIST_CACHE_TTL_SECONDS

		computed_result = [
			{
				"name": "Computed Company Format",
				"doc_type": "Sales Invoice",
				"company": "Acme",
				"is_default": 1,
			}
		]
		mock_cache = mock.Mock()
		mock_cache.get_value.return_value = None

		with (
			mock.patch("crispy_print.api.v1.formats.frappe.cache", return_value=mock_cache),
			mock.patch(
				"crispy_print.api.v1.formats._compute_crispy_formats_for_doctype",
				return_value=computed_result,
			) as mock_compute,
		):
			result = get_crispy_formats_for_doctype("Sales Invoice", company="Acme")

		self.assertEqual(result, computed_result)
		mock_compute.assert_called_once_with("Sales Invoice", company="Acme")
		mock_cache.get_value.assert_any_call(
			"crispy_print:formats_for_doctype:Sales Invoice:company:Acme",
			expires=True,
		)
		mock_cache.set_value.assert_any_call(
			"crispy_print:formats_for_doctype:Sales Invoice:company:Acme",
			computed_result,
			expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS,
		)
		mock_cache.set_value.assert_any_call(
			"crispy_print:formats_for_doctype:Sales Invoice:cache_keys",
			["crispy_print:formats_for_doctype:Sales Invoice:company:Acme"],
			expires_in_sec=FORMAT_LIST_CACHE_TTL_SECONDS,
		)

	def test_invalidate_crispy_formats_cache_for_doctype(self):
		from crispy_print.api.v1.formats import invalidate_crispy_formats_cache_for_doctype

		mock_cache = mock.Mock()
		mock_cache.get_value.return_value = [
			"crispy_print:formats_for_doctype:Sales Invoice",
			"crispy_print:formats_for_doctype:Sales Invoice:company:Acme",
		]
		with mock.patch("crispy_print.api.v1.formats.frappe.cache", return_value=mock_cache):
			invalidate_crispy_formats_cache_for_doctype("Sales Invoice")

		mock_cache.delete_value.assert_any_call("crispy_print:formats_for_doctype:Sales Invoice")
		mock_cache.delete_value.assert_any_call("crispy_print:formats_for_doctype:Sales Invoice:company:Acme")
		mock_cache.delete_value.assert_any_call("crispy_print:formats_for_doctype:Sales Invoice:cache_keys")

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
				"report_scope": "All Compatible Reports",
				"report_renderer": "generic_report",
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

		grid = get_default_report_builder_config("generic_report")
		financial = get_default_report_builder_config("financial_statement")
		unknown = get_default_report_builder_config("custom")

		self.assertEqual(grid["mode"], "basic")
		self.assertEqual(grid["preset"], "grid")
		self.assertEqual(financial["renderer"], "financial_statement")
		self.assertEqual(unknown["preset"], "grid")
		self.assertIn("show_filters", grid)
		self.assertIn("chart_enabled", grid)
		self.assertIn("font_family", grid)

	def test_get_available_formats_filters_custom_report_formats_by_company(self):
		from crispy_print.api.v1 import get_available_formats

		reports = frappe.get_all("Report", pluck="name", limit=1, order_by="name asc")
		if not reports:
			self.skipTest("No Report records available")
		report = reports[0]
		company = self._ensure_company("Test API Format Report Company A", "TAFRCA")
		other_company = self._ensure_company("Test API Format Report Company B", "TAFRCB")

		exact = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Report Exact",
				"crispy_format_type": "Report",
				"company": company,
				"module": "Crispy Print",
				"is_generic": 0,
				"layout_json": json.dumps({"sections": []}),
			}
		)
		exact.append("report", {"report": report})
		exact.insert()
		other = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Report Other",
				"crispy_format_type": "Report",
				"company": other_company,
				"module": "Crispy Print",
				"is_generic": 0,
				"layout_json": json.dumps({"sections": []}),
			}
		)
		other.append("report", {"report": report})
		other.insert()
		global_format = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Report Global",
				"crispy_format_type": "Report",
				"company": company,
				"module": "Crispy Print",
				"is_generic": 0,
				"layout_json": json.dumps({"sections": []}),
			}
		)
		global_format.append("report", {"report": report})
		global_format.insert()
		frappe.db.set_value("Crispy Format", global_format.name, "company", "", update_modified=False)
		frappe.db.commit()

		filtered = get_available_formats(report, company=company)
		filtered_names = [row["name"] for row in filtered["formats"]]
		unfiltered = get_available_formats(report)
		unfiltered_names = [row["name"] for row in unfiltered["formats"]]

		self.assertIn(exact.name, filtered_names)
		self.assertIn(global_format.name, filtered_names)
		self.assertNotIn(other.name, filtered_names)
		self.assertLess(filtered_names.index(exact.name), filtered_names.index(global_format.name))
		# Omitting company uses the user's default company; formats from unrelated
		# companies must never leak into discovery.
		self.assertNotIn(other.name, unfiltered_names)
		self.assertEqual(filtered["default_format"], exact.name)

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
		custom_name = "Test API Format Linked Report Custom"
		generic_name = "Test API Format Linked Report Generic"

		custom = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": custom_name,
				"crispy_format_type": "Report",
				"report_scope": "Selected Reports",
				"report_renderer": "generic_report",
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
				"report_scope": "All Compatible Reports",
				"report_renderer": "generic_report",
				"module": "Crispy Print",
			}
		)
		generic.insert()
		frappe.db.commit()

		out = get_available_formats(report_name)
		custom_names = [row["name"] for row in out.get("formats") or []]

		self.assertIn(custom_name, custom_names)
		self.assertEqual(out.get("default_format"), custom_name)
		self.assertIn(generic_name, custom_names)


class TestCrispyFormatImportExportAPI(FrappeTestCase):
	"""Test import/export API for Crispy Format schema v1."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Crispy Template", {"source_crispy_format": ["like", "Test ImportExport%"]})
		frappe.db.delete("Crispy Template", {"template_name": ["like", "Test ImportExport%"]})
		frappe.db.delete("Crispy Template", {"name": ["like", "test_importexport_%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Test ImportExport%"]})
		frappe.db.commit()

	def tearDown(self):
		frappe.db.delete("Crispy Template", {"source_crispy_format": ["like", "Test ImportExport%"]})
		frappe.db.delete("Crispy Template", {"template_name": ["like", "Test ImportExport%"]})
		frappe.db.delete("Crispy Template", {"name": ["like", "test_importexport_%"]})
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

		self.assertEqual(payload["schema_version"], 2)
		self.assertEqual(payload["app"], "crispy_print")
		self.assertIn("exported_at", payload)
		self.assertIn("format", payload)
		self.assertEqual(payload["format"]["name"], "Test ImportExport Export")
		self.assertNotIn("is_default", payload["format"])
		self.assertIn("metadata", payload)
		self.assertIn("company", payload["metadata"])
		self.assertIn("templates", payload["metadata"])

	def test_export_payload_includes_template_metadata(self):
		from crispy_print.api.v1 import export_crispy_format

		source = self._insert_format("Test ImportExport Export Template")
		template = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": "Test ImportExport Template",
				"source_crispy_format": source.name,
				"company": source.company,
				"status": "Approved",
				"is_active": 1,
			}
		)
		template.insert(ignore_permissions=True)

		payload = export_crispy_format(source.name)
		templates = payload["metadata"]["templates"]

		self.assertEqual(templates[0]["name"], template.name)
		self.assertEqual(templates[0]["template_name"], template.template_name)
		self.assertEqual(templates[0]["company"], source.company)

	def test_import_new_format_success(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		company = frappe.db.get_value("Company", {}, "name")
		if not company:
			self.skipTest("No Company records available")

		self._insert_format("Test ImportExport Source", company=company, pdf_standard="PDF/A-3u")
		payload = export_crispy_format("Test ImportExport Source")
		payload["format"]["name"] = "Test ImportExport Imported"

		result = import_crispy_format(payload, on_conflict="copy")
		imported = frappe.get_doc("Crispy Format", result["name"])

		self.assertTrue(result["success"])
		self.assertEqual(imported.name, "Test ImportExport Imported")
		self.assertEqual(imported.typst_code, "#text[Hello]")
		self.assertEqual(imported.company, company)
		self.assertEqual(imported.pdf_standard, "PDF/A-3u")
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
		self.assertEqual(imported.report_scope, "All Compatible Reports")
		self.assertEqual(imported.report_renderer, "generic_report")
		self.assertEqual(imported.is_advanced, 1)
		self.assertEqual(imported.raw_typst, 1)

	def test_import_old_payload_without_metadata_is_compatible(self):
		from crispy_print.api.v1 import import_crispy_format

		payload = {
			"schema_version": 1,
			"exported_at": "2026-02-07T00:00:00",
			"app": "crispy_print",
			"format": {
				"name": "Test ImportExport Old Payload",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			},
		}

		result = import_crispy_format(payload, on_conflict="copy")
		imported = frappe.get_doc("Crispy Format", result["name"])

		self.assertTrue(result["success"])
		self.assertEqual(imported.name, "Test ImportExport Old Payload")
		self.assertTrue(imported.company)

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

	def test_import_rejects_unsupported_format_fields_even_with_metadata(self):
		from crispy_print.api.v1 import import_crispy_format

		payload = {
			"schema_version": 1,
			"metadata": {"company": {"name": "Ignored Metadata Company"}},
			"format": {
				"name": "Test ImportExport Unsupported Field",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"layout_json": json.dumps({"sections": []}),
				"unsupported_field": "nope",
			},
		}

		with self.assertRaises(frappe.ValidationError):
			import_crispy_format(payload, on_conflict="copy")

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

	def test_import_metadata_reference_warnings_non_blocking(self):
		from crispy_print.api.v1 import export_crispy_format, import_crispy_format

		self._insert_format("Test ImportExport Metadata Warn Source")
		payload = export_crispy_format("Test ImportExport Metadata Warn Source")
		payload["format"]["name"] = "Test ImportExport Metadata Warn Imported"
		payload["metadata"] = {
			"company": {"name": "Missing Metadata Company", "abbr": "MMC"},
			"templates": [{"name": "Missing Metadata Template"}],
		}

		result = import_crispy_format(payload, on_conflict="copy")

		self.assertTrue(result["success"])
		self.assertTrue(frappe.db.exists("Crispy Format", result["name"]))
		self.assertTrue(any("Missing Metadata Company" in warning for warning in result["warnings"]))
		self.assertTrue(any("Missing Metadata Template" in warning for warning in result["warnings"]))

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
