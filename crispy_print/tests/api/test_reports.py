# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

from frappe.tests.utils import FrappeTestCase


class TestReportDataPrep(FrappeTestCase):
	"""Test report data shaping for Typst templates"""

	def test_prepare_typst_report_data_cells_and_defaults(self):
		"""Rows should include cells and default flags used by generic templates."""
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Item", "fieldname": "item_code", "fieldtype": "Data", "col_index": 0},
				{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "col_index": 1},
			],
			"result": [["ITEM-001", 2]],
			"message": "Sample Report",
			"chart": {},
		}

		out = _prepare_typst_report_data("Sample Report", report_data)

		self.assertEqual(out.get("title"), "Sample Report")
		self.assertIn("subtitle", out)
		self.assertEqual(out.get("subtitle"), "")
		self.assertTrue(out.get("rows"))

		row = out["rows"][0]
		self.assertIn("cells", row)
		self.assertEqual(len(row["cells"]), 2)
		self.assertIn("is_bold", row)
		self.assertIs(row["is_bold"], False)
		self.assertEqual(row["cells"][0]["value"], "ITEM-001")
		self.assertEqual(row["cells"][1]["value"], "2.00")

	def test_prepare_typst_report_data_normalizes_column_widths(self):
		"""Unitless widths should be normalized so Typst table columns compile."""
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Item", "fieldname": "item_code", "fieldtype": "Data", "col_index": 0},
				{"label": "Qty", "fieldname": "qty", "fieldtype": "Float", "col_index": 1},
			],
			"result": [["ITEM-001", 2]],
			"message": "Sample Report",
		}
		column_filter = [
			{"fieldname": "item_code", "width": 120},
			{"fieldname": "qty", "width": "80"},
		]

		out = _prepare_typst_report_data("Sample Report", report_data, column_filter=column_filter)
		width_map = {col["fieldname"]: col.get("width") for col in out["columns"]}

		self.assertEqual(width_map.get("item_code"), "120pt")
		self.assertEqual(width_map.get("qty"), "80pt")

	def test_prepare_typst_report_data_defaults_widths_to_auto(self):
		"""Backend should ignore report metadata widths unless column_filter provides one."""
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{
					"label": "Item",
					"fieldname": "item_code",
					"fieldtype": "Data",
					"width": 150,
					"col_index": 0,
				},
				{
					"label": "Qty",
					"fieldname": "qty",
					"fieldtype": "Float",
					"width": "90pt",
					"col_index": 1,
				},
			],
			"result": [["ITEM-001", 2]],
			"message": "Sample Report",
		}

		out = _prepare_typst_report_data("Sample Report", report_data, column_filter=None)
		width_map = {col["fieldname"]: col.get("width") for col in out["columns"]}

		self.assertEqual(width_map.get("item_code"), "auto")
		self.assertEqual(width_map.get("qty"), "auto")
