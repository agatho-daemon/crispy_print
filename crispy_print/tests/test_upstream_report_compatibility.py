from frappe.tests.utils import FrappeTestCase

from crispy_print.dev_utils.upstream_report_compatibility import (
	build_snapshot,
	compare_snapshots,
)


class TestUpstreamReportCompatibility(FrappeTestCase):
	def test_snapshot_captures_columns_filters_totals_grouping_and_chart(self):
		snapshot = build_snapshot(
			"General Ledger",
			{
				"columns": [
					{"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Date"},
					{"fieldname": "debit", "label": "Debit", "fieldtype": "Currency"},
				],
				"result": [{"posting_date": "2026-01-01", "debit": 10, "is_total": 1, "indent": 0}],
				"skip_total_row": 1,
				"chart": {"type": "bar"},
			},
			{"company": "Acme", "from_date": "2026-01-01"},
		)

		self.assertEqual(snapshot["filters"], ["company", "from_date"])
		self.assertEqual([column["fieldname"] for column in snapshot["columns"]], ["posting_date", "debit"])
		self.assertEqual(snapshot["semantic_row_keys"], ["indent", "is_total"])
		self.assertEqual(snapshot["total_flags"], {"skip_total_row": 1})
		self.assertEqual(snapshot["chart_type"], "bar")
		self.assertEqual(len(snapshot["fingerprint"]), 64)

	def test_snapshot_comparison_identifies_structural_drift(self):
		base = {
			"renderer": "general_ledger",
			"filters": ["company", "from_date"],
			"columns": [{"fieldname": "debit"}, {"fieldname": "credit"}],
			"semantic_row_keys": ["indent"],
			"total_flags": {"skip_total_row": 1},
			"chart_type": "",
			"fingerprint": "old",
		}
		current = {
			**base,
			"filters": ["company", "posting_date"],
			"columns": [{"fieldname": "debit"}, {"fieldname": "balance"}],
			"semantic_row_keys": [],
			"total_flags": {"skip_total_row": 0},
			"fingerprint": "new",
		}
		result = compare_snapshots(base, current)

		self.assertEqual(result["status"], "review_required")
		dimensions = {item["dimension"] for item in result["differences"]}
		self.assertEqual(dimensions, {"filters", "columns", "semantic_row_keys", "total_flags"})
