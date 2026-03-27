# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

from unittest import mock

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
		self.assertEqual(row["cells"][0]["raw_value"], "ITEM-001")
		self.assertEqual(row["cells"][1]["value"], "2.00")
		self.assertEqual(row["cells"][1]["raw_value"], 2)
		self.assertEqual(row["item_code_raw"], "ITEM-001")
		self.assertEqual(row["qty_raw"], 2)

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

	def test_prepare_typst_report_data_includes_filter_map_and_context_flags(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [{"label": "Party", "fieldname": "party", "fieldtype": "Data", "col_index": 0}],
			"result": [["CUST-0001"]],
			"message": "Accounts Receivable",
		}
		filters = {
			"show_future_payments": 1,
			"show_sales_person": "true",
			"party": "Customer A",
		}

		out = _prepare_typst_report_data("Accounts Receivable", report_data, filters=filters)

		self.assertEqual(out["filters_map"]["show_future_payments"], "1")
		self.assertEqual(out["filters_map"]["show_sales_person"], "true")
		self.assertEqual(out["filters_map"]["party"], "Customer A")
		self.assertEqual(out["report_name"], "Accounts Receivable")
		self.assertEqual(out["report_key"], "accounts_receivable")
		self.assertTrue(out["report_context"]["is_accounts_receivable"])
		self.assertFalse(out["report_context"]["is_accounts_payable"])
		self.assertTrue(out["report_context"]["show_future_payments"])
		self.assertTrue(out["report_context"]["show_sales_person"])
		self.assertTrue(out["report_context"]["has_party_filter"])

	def test_prepare_typst_report_data_preserves_indent_for_tree_rows(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Account", "fieldname": "account_name", "fieldtype": "Data", "col_index": 0},
				{"label": "2025", "fieldname": "year_2025", "fieldtype": "Currency", "col_index": 1},
			],
			"result": [
				{"account_name": "Total Asset", "year_2025": 1000, "indent": 0, "is_bold": 1},
				{"account_name": "Cash", "year_2025": 250, "indent": 2},
			],
			"message": "Balance Sheet",
		}

		out = _prepare_typst_report_data("Balance Sheet", report_data)

		self.assertEqual(out["rows"][0]["indent"], 0)
		self.assertEqual(out["rows"][1]["indent"], 2)
		self.assertTrue(out["rows"][0]["is_bold"])
		self.assertFalse(out["rows"][1]["is_bold"])
		self.assertEqual(out["rows"][0]["cells"][0]["value"], "Total Asset")
		self.assertTrue(out["rows"][1]["cells"][0]["value"].startswith("\u00a0" * 8))

	def test_prepare_typst_report_data_preserves_parent_metadata_without_visible_columns(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Account", "fieldname": "account_name", "fieldtype": "Data", "col_index": 0},
				{"label": "2025", "fieldname": "year_2025", "fieldtype": "Currency", "col_index": 1},
			],
			"result": [
				{
					"account_name": "11000 - Current Assets",
					"year_2025": 1000,
					"parent_account": "10000 - Application of Funds",
					"parent_section": "Assets",
				}
			],
			"message": "Balance Sheet",
		}

		out = _prepare_typst_report_data("Balance Sheet", report_data)
		row = out["rows"][0]

		self.assertIn("parent_account", row)
		self.assertIn("parent_section", row)
		self.assertEqual(row["parent_account"], "10000 - Application of Funds")
		self.assertEqual(row["parent_section"], "Assets")

	def test_prepare_typst_report_data_preserves_warn_if_negative_for_top_level_rows(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Account", "fieldname": "account_name", "fieldtype": "Data", "col_index": 0},
				{"label": "2026", "fieldname": "year_2026", "fieldtype": "Currency", "col_index": 1},
			],
			"result": [
				{
					"account_name": "Total Liability",
					"year_2026": -601378.465,
					"warn_if_negative": 1,
				}
			],
			"message": "Balance Sheet",
		}

		out = _prepare_typst_report_data("Balance Sheet", report_data)
		row = out["rows"][0]

		self.assertTrue(row["warn_if_negative"])
		self.assertEqual(row["year_2026_raw"], -601378.465)

	def test_prepare_typst_report_data_formats_report_summary_like_report_view(self):
		import frappe

		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Account", "fieldname": "account_name", "fieldtype": "Data", "col_index": 0}
			],
			"result": [{"account_name": "Total Asset"}],
			"message": "Balance Sheet",
			"report_summary": [
				{
					"label": "Total Asset",
					"value": 3246546.895,
					"datatype": "Currency",
					"currency": "KWD",
					"indicator": "Green",
				},
				{
					"label": "Total Equity",
					"value": 0,
					"datatype": "Currency",
					"currency": "KWD",
					"color": "Blue",
				},
			],
		}

		out = _prepare_typst_report_data("Balance Sheet", report_data)
		expected_currency_value = frappe.format(
			3246546.895, {"fieldtype": "Currency", "options": "currency"}, currency="KWD"
		)

		self.assertEqual(out["report_summary"][0]["color_class"], "green")
		self.assertEqual(out["report_summary"][1]["color_class"], "blue")
		self.assertEqual(out["report_summary"][0]["formatted_value"], str(expected_currency_value))

	def test_prepare_typst_report_data_normalizes_separator_summary_items(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Account", "fieldname": "account_name", "fieldtype": "Data", "col_index": 0}
			],
			"result": [{"account_name": "Net Profit"}],
			"message": "Profit and Loss Statement",
			"report_summary": [
				{"value": 100, "label": "Income", "datatype": "Currency", "currency": "KWD"},
				{"type": "separator", "value": "-"},
			],
		}

		out = _prepare_typst_report_data("Profit and Loss Statement", report_data)

		self.assertEqual(out["report_summary"][1]["type"], "separator")
		self.assertEqual(out["report_summary"][1]["label"], "")
		self.assertEqual(out["report_summary"][1]["value"], "-")

	def test_prepare_typst_report_data_enriches_bank_reconciliation_party_display(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "col_index": 0},
				{
					"label": "Payment Document Type",
					"fieldname": "payment_document",
					"fieldtype": "Data",
					"col_index": 1,
				},
				{
					"label": "Payment Document",
					"fieldname": "payment_entry",
					"fieldtype": "Dynamic Link",
					"col_index": 2,
				},
				{
					"label": "Against Account",
					"fieldname": "against_account",
					"fieldtype": "Link",
					"col_index": 3,
				},
			],
			"result": [
				{
					"posting_date": "2023-01-07",
					"payment_document": "Payment Entry",
					"payment_entry": "ACC-PAY-0001",
					"against_account": "CUST-23-006",
				}
			],
			"message": "Bank Reconciliation Statement",
		}

		with mock.patch(
			"crispy_print.api.v1.reports.frappe.get_all",
			return_value=[
				{"name": "ACC-PAY-0001", "party": "CUST-23-006", "party_name": "Manaf Ameen Hasan Hasan"}
			],
		):
			out = _prepare_typst_report_data("Bank Reconciliation Statement", report_data)

		row = out["rows"][0]
		self.assertEqual(row["against_account_raw"], "CUST-23-006")
		self.assertEqual(row["against_account"], "Manaf Ameen Hasan Hasan")
		self.assertEqual(row["against_account_display"], "Manaf Ameen Hasan Hasan")
		against_cell = next(cell for cell in row["cells"] if cell["fieldname"] == "against_account")
		self.assertEqual(against_cell["value"], "Manaf Ameen Hasan Hasan")

	def test_prepare_typst_report_data_formats_currency_with_report_currency_precision(self):
		import frappe

		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{
					"label": "Debit",
					"fieldname": "debit",
					"fieldtype": "Currency",
					"options": "account_currency",
					"col_index": 0,
				},
				{"label": "Currency", "fieldname": "account_currency", "fieldtype": "Link", "col_index": 1},
			],
			"result": [{"debit": 718.28, "account_currency": "KWD"}],
			"message": "Bank Reconciliation Statement",
		}

		out = _prepare_typst_report_data("Bank Reconciliation Statement", report_data)
		expected = frappe.format(
			718.28,
			{"fieldtype": "Currency", "options": "account_currency"},
			currency="KWD",
			translated=False,
		)

		self.assertEqual(out["rows"][0]["debit"], str(expected))
		self.assertEqual(out["rows"][0]["debit_currency_display"], "KWD")
		self.assertEqual(out["rows"][0]["debit_amount_display"], str(expected).removeprefix("KWD "))

	def test_prepare_typst_report_data_hides_bank_reconciliation_summary_rows_when_totals_disabled(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		report_data = {
			"columns": [
				{"label": "Posting Date", "fieldname": "posting_date", "fieldtype": "Date", "col_index": 0},
				{
					"label": "Payment Document",
					"fieldname": "payment_entry",
					"fieldtype": "Data",
					"col_index": 1,
				},
				{
					"label": "Debit",
					"fieldname": "debit",
					"fieldtype": "Currency",
					"options": "account_currency",
					"col_index": 2,
				},
				{
					"label": "Credit",
					"fieldname": "credit",
					"fieldtype": "Currency",
					"options": "account_currency",
					"col_index": 3,
				},
				{"label": "Currency", "fieldname": "account_currency", "fieldtype": "Link", "col_index": 4},
			],
			"result": [
				{
					"posting_date": "2023-01-07",
					"payment_entry": "ACC-PAY-0001",
					"debit": 100,
					"credit": 0,
					"account_currency": "KWD",
				},
				{
					"payment_entry": "Bank Statement balance as per General Ledger",
					"debit": 100,
					"credit": 0,
					"account_currency": "KWD",
				},
				{},
				{
					"payment_entry": "Calculated Bank Statement balance",
					"debit": 100,
					"credit": 0,
					"account_currency": "KWD",
				},
			],
			"message": "Bank Reconciliation Statement",
		}

		out = _prepare_typst_report_data(
			"Bank Reconciliation Statement", report_data, include_total_row=False
		)

		self.assertEqual(len(out["rows"]), 1)
		self.assertEqual(out["rows"][0]["payment_entry"], "ACC-PAY-0001")
		self.assertFalse(out["show_totals"])

	def test_get_format_for_report_prefers_linked_custom_format(self):
		from crispy_print.api.v1.reports import _get_format_for_report

		with (
			mock.patch(
				"crispy_print.api.v1.reports.get_custom_report_formats",
				return_value=[{"name": "Linked Report Format"}],
			),
			mock.patch("crispy_print.api.v1.reports.frappe.db.get_value") as mock_get_value,
		):
			out = _get_format_for_report("Any Report")

		self.assertEqual(out, "Linked Report Format")
		mock_get_value.assert_not_called()

	def test_get_report_typst_source_skips_chart_when_include_chart_disabled(self):
		from types import SimpleNamespace

		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				return_value=SimpleNamespace(typst_code="#table()"),
			),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			out = get_report_typst_source(
				report="Any Report",
				format_name="Any Format",
				include_chart=0,
				chart_svg="<svg/>",
				preview_data={
					"title": "Any Report",
					"subtitle": "",
					"filters": [],
					"columns": [],
					"rows": [],
					"report_summary": [],
				},
			)

		self.assertEqual(out, "#typst")
		self.assertNotIn("chart_svg", captured_data)
