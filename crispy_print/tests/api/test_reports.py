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
