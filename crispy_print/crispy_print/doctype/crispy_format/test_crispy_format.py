# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import json
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase


class TestCrispyFormat(FrappeTestCase):
	def setUp(self):
		"""Set up test data before each test"""
		frappe.set_user("Administrator")
		# Clean up any existing test formats
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Format%"]})
		self._default_doctypes = [
			"Sales Invoice",
			"Sales Order",
			"Purchase Invoice",
			"Purchase Order",
		]
		self._saved_defaults = self._capture_defaults(self._default_doctypes)
		self._clear_defaults(self._default_doctypes)
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after each test"""
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Format%"]})
		self._restore_defaults(self._saved_defaults)
		frappe.db.commit()

	def _capture_defaults(self, doctypes: list[str]) -> dict[str, list[str]]:
		saved = {}
		for dt in doctypes:
			names = frappe.get_all(
				"Crispy Format",
				filters={"doc_type": dt, "is_default": 1},
				pluck="name",
			)
			saved[dt] = names or []
		return saved

	def _clear_defaults(self, doctypes: list[str]):
		if not doctypes:
			return
		frappe.db.sql(
			"update `tabCrispy Format` set is_default = 0 where doc_type in %s",
			(tuple(doctypes),),
		)

	def _restore_defaults(self, saved: dict[str, list[str]]):
		for names in (saved or {}).values():
			for name in names:
				frappe.db.set_value("Crispy Format", name, "is_default", 1)

	def _set_default(self, name: str):
		doc = frappe.get_doc("Crispy Format", name)
		doc.is_default = 1
		doc.save()

	def _get_default_company(self) -> str | None:
		return (
			frappe.defaults.get_user_default("Company")
			or frappe.defaults.get_user_default("company")
			or frappe.defaults.get_global_default("company")
			or frappe.db.get_single_value("Global Defaults", "default_company")
		)

	def _ensure_company(self, name="Test Format Company", abbr="TFC"):
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

	def _new_format(self, name: str, **values):
		data = {
			"doctype": "Crispy Format",
			"name": name,
			"crispy_format_type": "DocType",
			"doc_type": "Sales Invoice",
			"module": "Crispy Print",
			"layout_json": json.dumps({"sections": []}),
			"presentation_settings": json.dumps({"page": {"size": "A4"}}),
		}
		data.update(values)
		return frappe.get_doc(data)

	def test_create_crispy_format(self):
		"""Test creating a new Crispy Format document"""
		default_company = self._get_default_company()
		if not default_company:
			self.skipTest("No default Company configured")

		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			}
		)
		doc.insert()

		self.assertEqual(doc.doc_type, "Sales Invoice")
		self.assertEqual(doc.company, default_company)
		self.assertFalse(doc.is_default)

		# Clean up
		doc.delete()

	def test_raw_typst_hides_author_owned_form_fields(self):
		json_path = frappe.get_app_path(
			"crispy_print",
			"crispy_print",
			"doctype",
			"crispy_format",
			"crispy_format.json",
		)
		with open(json_path, encoding="utf-8") as handle:
			meta = json.load(handle)
		fields = {field["fieldname"]: field for field in meta["fields"]}
		self.assertEqual(fields["print_behavior_section"].get("depends_on"), "eval:!doc.raw_typst")
		self.assertEqual(fields["typst_preamble"].get("depends_on"), "eval:!doc.raw_typst")
		self.assertEqual(fields["doc_header"].get("depends_on"), "eval:!doc.raw_typst")
		self.assertEqual(fields["doc_footer"].get("depends_on"), "eval:!doc.raw_typst")

	def test_company_is_required_when_no_default_can_be_resolved(self):
		"""Test server validation blocks company-less formats without a configured default."""
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format No Company",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
			}
		)
		doc.company = None
		original_get_single_value = frappe.db.get_single_value

		def get_single_value_without_default_company(doctype, fieldname, *args, **kwargs):
			if doctype == "Global Defaults" and fieldname == "default_company":
				return None
			return original_get_single_value(doctype, fieldname, *args, **kwargs)

		with (
			mock.patch("frappe.defaults.get_user_default", return_value=None),
			mock.patch("frappe.defaults.get_global_default", return_value=None),
			mock.patch.object(
				frappe.db,
				"get_single_value",
				side_effect=get_single_value_without_default_company,
			),
			self.assertRaises(frappe.ValidationError),
		):
			doc.validate()

	def test_insert_can_preserve_default_when_not_duplicate(self):
		"""Test inserting a default format does not clear is_default unless it is a copy."""
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Insert Default",
				"crispy_format_type": "DocType",
				"doc_type": "Language",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"is_default": 1,
			}
		)
		doc.insert()

		self.assertTrue(doc.is_default)

		doc.delete()

	def test_duplicate_insert_clears_default(self):
		"""Test copied formats do not inherit default status."""
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Duplicate Default",
				"crispy_format_type": "DocType",
				"doc_type": "Language",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"is_default": 1,
			}
		)
		doc.flags.from_copy = True
		doc.insert()

		self.assertFalse(doc.is_default)

		doc.delete()

	def test_set_default_format(self):
		"""Test setting a format as default clears other defaults"""
		# Create first format
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Default 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format1.insert()
		self._set_default(format1.name)
		format1.reload()
		self.assertTrue(format1.is_default)

		# Create second format and set as default
		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Default 2",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()
		self._set_default(format2.name)

		# Reload first format and verify it's no longer default
		format1.reload()
		format2.reload()
		self.assertFalse(format1.is_default)
		self.assertTrue(format2.is_default)

		# Clean up
		format1.delete()
		format2.delete()

	def test_default_format_is_scoped_by_company(self):
		"""Test same target can have separate defaults per company."""
		company_a = self._ensure_company("Test Format Company A", "TFCA")
		company_b = self._ensure_company("Test Format Company B", "TFCB")
		format_a = self._new_format("Test Format Company A Default", company=company_a)
		format_b = self._new_format("Test Format Company B Default", company=company_b)
		format_a.insert()
		format_b.insert()

		self._set_default(format_a.name)
		self._set_default(format_b.name)

		format_a.reload()
		format_b.reload()
		self.assertTrue(format_a.is_default)
		self.assertTrue(format_b.is_default)

	def test_default_format_is_scoped_by_format_type_and_target(self):
		"""Test report defaults do not clear DocType defaults for the same company."""
		generic_report_type = frappe.db.get_value("Crispy Generic Report", {}, "name")
		if not generic_report_type:
			self.skipTest("No Crispy Generic Report records available")

		company = self._ensure_company("Test Format Target Company", "TFTC")
		doctype_format = self._new_format("Test Format Target DocType Default", company=company)
		report_format = self._new_format(
			"Test Format Target Report Default",
			company=company,
			crispy_format_type="Report",
			doc_type=None,
			is_generic=1,
			generic_report_type=generic_report_type,
		)
		doctype_format.insert()
		report_format.insert()

		self._set_default(doctype_format.name)
		self._set_default(report_format.name)

		doctype_format.reload()
		report_format.reload()
		self.assertTrue(doctype_format.is_default)
		self.assertTrue(report_format.is_default)

	def test_custom_report_default_only_clears_overlapping_report_target(self):
		"""Test custom report defaults compete only when linked report rows overlap."""
		reports = frappe.get_all("Report", pluck="name", limit=2, order_by="name asc")
		if len(reports) < 2:
			self.skipTest("At least two Report records are required")

		company = self._ensure_company("Test Format Report Company", "TFRC")
		first = self._new_format(
			"Test Format Report Default 1",
			company=company,
			crispy_format_type="Report",
			doc_type=None,
			is_generic=0,
		)
		first.append("report", {"report": reports[0]})
		second = self._new_format(
			"Test Format Report Default 2",
			company=company,
			crispy_format_type="Report",
			doc_type=None,
			is_generic=0,
		)
		second.append("report", {"report": reports[0]})
		third = self._new_format(
			"Test Format Report Default 3",
			company=company,
			crispy_format_type="Report",
			doc_type=None,
			is_generic=0,
		)
		third.append("report", {"report": reports[1]})
		first.insert()
		second.insert()
		third.insert()

		self._set_default(first.name)
		self._set_default(second.name)
		self._set_default(third.name)

		first.reload()
		second.reload()
		third.reload()
		self.assertFalse(first.is_default)
		self.assertTrue(second.is_default)
		self.assertTrue(third.is_default)

	def test_get_current_default(self):
		"""Test getting the current default format for a DocType"""
		# Create default format
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Current Default",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format1.insert()
		self._set_default(format1.name)

		# Create another format for same DocType
		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Not Default",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()

		# Get current default
		current_default = format2.get_current_default()
		self.assertEqual(current_default, "Test Format Current Default")

		# Clean up
		format1.delete()
		format2.delete()

	def test_set_default_via_document(self):
		"""Test setting default via document save"""

		# Create format
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format Make Default",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		doc.insert()
		self.assertFalse(doc.is_default)

		# Set as administrator to bypass permissions
		frappe.set_user("Administrator")

		# Set default via document save
		self._set_default("Test Format Make Default")

		# Verify it's now default
		doc.reload()
		self.assertTrue(doc.is_default)

		# Clean up
		doc.delete()

	def test_layout_json_validation(self):
		"""Test that valid JSON is required for layout_json"""
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format JSON Valid",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps(
					{
						"sections": [
							{
								"label": "Header",
								"columns": [{"label": "Col 1", "fields": []}],
							}
						]
					}
				),
			}
		)
		doc.insert()

		# Verify JSON can be parsed
		layout = json.loads(doc.layout_json)
		self.assertIn("sections", layout)
		self.assertEqual(len(layout["sections"]), 1)

		# Clean up
		doc.delete()

	def test_multiple_doctypes_defaults(self):
		"""Test that different DocTypes can each have their own default"""
		# Create default for Sales Invoice
		format_si = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format SI Default",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_si.insert()
		self._set_default(format_si.name)

		# Create default for Purchase Invoice
		format_pi = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Format PI Default",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_pi.insert()
		self._set_default(format_pi.name)

		# Both should remain as defaults for their respective DocTypes
		format_si.reload()
		format_pi.reload()
		self.assertTrue(format_si.is_default)
		self.assertTrue(format_pi.is_default)

		# Clean up
		format_si.delete()
		format_pi.delete()
