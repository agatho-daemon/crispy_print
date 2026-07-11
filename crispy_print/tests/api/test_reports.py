# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

from unittest import mock

from frappe.tests.utils import FrappeTestCase


class TestReportDataPrep(FrappeTestCase):
	"""Test report data shaping for Typst templates"""

	def test_renderer_registry_covers_initial_accounting_families(self):
		from crispy_print.report_renderers import infer_report_renderer

		self.assertEqual(infer_report_renderer("Accounts Receivable"), "receivable_payable")
		self.assertEqual(infer_report_renderer("Accounts Payable Summary"), "receivable_payable")
		self.assertEqual(infer_report_renderer("Balance Sheet"), "financial_statement")
		self.assertEqual(infer_report_renderer("General Ledger"), "general_ledger")
		self.assertEqual(infer_report_renderer("Bank Reconciliation Statement"), "bank_reconciliation")
		self.assertEqual(infer_report_renderer("Unknown Custom Report"), "generic_report")

	def test_report_payload_exposes_renderer_sections_and_row_roles(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		out = _prepare_typst_report_data(
			"Balance Sheet",
			{
				"columns": [{"fieldname": "account_name", "label": "Account", "fieldtype": "Data"}],
				"result": [{"account_name": "Assets", "indent": 0}, {}],
				"message": None,
			},
		)
		self.assertEqual(out["renderer"], "financial_statement")
		self.assertTrue(any(section["key"] == "table" for section in out["sections"]))
		self.assertEqual(out["rows"][0]["role"], "section")
		self.assertEqual(out["rows"][1]["role"], "spacer")

	def _fake_format_doc(self, **kwargs):
		from types import SimpleNamespace

		values = {
			"typst_code": "",
			"typst_preamble": "",
			"doc_header": "",
			"doc_footer": "",
			"filters": [],
		}
		values.update(kwargs)
		return SimpleNamespace(check_permission=mock.Mock(), **values)

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
		width_map = {
			col["fieldname"]: (col.get("width"), col.get("width_kind"), col.get("width_value"))
			for col in out["columns"]
		}

		self.assertEqual(width_map.get("item_code"), ("120pt", "pt", 120))
		self.assertEqual(width_map.get("qty"), ("80pt", "pt", 80))

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
		width_map = {
			col["fieldname"]: (col.get("width"), col.get("width_kind"), col.get("width_value"))
			for col in out["columns"]
		}

		self.assertEqual(width_map.get("item_code"), ("auto", "auto", None))
		self.assertEqual(width_map.get("qty"), ("auto", "auto", None))

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

	def test_get_report_data_enforces_internal_permission_and_rate_limits(self):
		from types import SimpleNamespace

		from crispy_print.api.v1.reports import _get_report_data

		with (
			mock.patch("crispy_print.api.v1.reports._ensure_report_read_permission") as mock_perm,
			mock.patch("crispy_print.api.v1.reports.enforce_rate_limit") as mock_limit,
			mock.patch(
				"crispy_print.api.v1.reports.frappe.desk",
				new=SimpleNamespace(
					query_report=SimpleNamespace(run=mock.Mock(return_value={"columns": [], "result": []}))
				),
			),
		):
			_get_report_data("General Ledger", {})

		mock_perm.assert_called_once_with("General Ledger")
		self.assertEqual(mock_limit.call_count, 2)
		mock_limit.assert_any_call("report_data", limit=20, window_seconds=60)
		mock_limit.assert_any_call("report_data:general_ledger", limit=10, window_seconds=60)

	def test_get_report_typst_source_returns_structured_truncation(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		format_doc = self._fake_format_doc(typst_code="#text[Hello]")
		report_data = {
			"columns": [{"label": "A", "fieldname": "a", "fieldtype": "Data", "col_index": 0}],
			"result": [["x"], ["y"]],
			"message": "Sample Report",
		}

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch("crispy_print.api.v1.reports._get_report_data", return_value=report_data) as get_data,
		):
			result = get_report_typst_source("Sample Report", "Any Format", limit=1)

		truncation = result["truncation"]
		self.assertTrue(truncation["is_truncated"])
		self.assertEqual(truncation["rows"]["original"], 2)
		self.assertEqual(truncation["rows"]["returned"], 1)
		self.assertEqual(truncation["rows"]["max"], 1)
		self.assertIn("columns", truncation)
		self.assertIn("cells_truncated_count", truncation)
		get_data.assert_called_once_with("Sample Report", {}, max_rows=1)

	def test_get_report_typst_source_rejects_oversized_live_payload(self):
		from crispy_print.api.v1.reports import MAX_REPORT_PAYLOAD_BYTES, get_report_typst_source

		format_doc = self._fake_format_doc(typst_code="#text[Hello]")
		oversized_payload = {
			"title": "Oversized",
			"subtitle": "",
			"columns": [],
			"rows": [{"value": "x" * MAX_REPORT_PAYLOAD_BYTES}],
			"report_summary": [],
		}

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch(
				"crispy_print.api.v1.reports._get_report_data",
				return_value={"columns": [], "result": [], "message": "Any Report"},
			),
			mock.patch(
				"crispy_print.api.v1.reports._prepare_typst_report_data",
				return_value=oversized_payload,
			),
		):
			with self.assertRaises(Exception):
				get_report_typst_source("Any Report", "Any Format")

	def test_generate_report_pdf_rejects_oversized_payload(self):
		from crispy_print.api.v1.reports import MAX_REPORT_PAYLOAD_BYTES, generate_report_pdf

		format_doc = self._fake_format_doc(typst_code="#text[Hello]", presentation_settings="{}")
		oversized_payload = {
			"title": "Oversized",
			"subtitle": "",
			"columns": [],
			"rows": [{"value": "x" * MAX_REPORT_PAYLOAD_BYTES}],
			"report_summary": [],
		}

		with (
			mock.patch("crispy_print.api.v1.reports._ensure_report_read_permission"),
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch(
				"crispy_print.api.v1.reports._get_report_data",
				return_value={"columns": [], "result": [], "message": "Any Report"},
			),
			mock.patch(
				"crispy_print.api.v1.reports._prepare_typst_report_data",
				return_value=oversized_payload,
			),
		):
			with self.assertRaises(Exception):
				generate_report_pdf("Any Report", format_name="Any Format")

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
			"crispy_print.api.v1.reports.frappe.get_list",
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
				"crispy_print.api.v1.formats.get_available_formats",
				return_value={
					"formats": [{"name": "Linked Report Format"}],
					"default_format": "Linked Report Format",
				},
			),
		):
			out = _get_format_for_report("Any Report")

		self.assertEqual(out, "Linked Report Format")

	def test_get_report_typst_source_skips_chart_when_include_chart_disabled(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				side_effect=[
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(typst_code="#table()"),
				],
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

		self.assertEqual(out["typst_source"], "#typst")
		self.assertFalse(out["truncation"]["is_truncated"])
		self.assertNotIn("chart_svg", captured_data)

	def test_get_report_typst_source_normalizes_preview_column_width_parts(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}
		preview_column = {"label": "Item", "fieldname": "item_code", "width": "2fr"}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				side_effect=[
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(typst_code="#table()"),
				],
			),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			get_report_typst_source(
				report="Any Report",
				format_name="Any Format",
				preview_data={
					"title": "Any Report",
					"subtitle": "",
					"filters": [],
					"columns": [preview_column, {"label": "Qty", "fieldname": "qty", "width": 80}],
					"rows": [],
					"report_summary": [],
				},
			)

		self.assertEqual(captured_data["columns"][0]["width"], "2fr")
		self.assertEqual(captured_data["columns"][0]["width_kind"], "fr")
		self.assertEqual(captured_data["columns"][0]["width_value"], 2)
		self.assertEqual(captured_data["columns"][1]["width"], "80pt")
		self.assertEqual(captured_data["columns"][1]["width_kind"], "pt")
		self.assertEqual(captured_data["columns"][1]["width_value"], 80)
		self.assertNotIn("width_kind", preview_column)

	def test_get_report_typst_source_normalizes_image_fields_and_returns_asset_files(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				return_value=self._fake_format_doc(typst_code="= Test\n#image(data.logo_image)"),
			),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			out = get_report_typst_source(
				report="Any Report",
				format_name="Any Format",
				preview_data={
					"title": "Any Report",
					"subtitle": "",
					"filters": [],
					"columns": [],
					"rows": [{"logo_image": "/private/files/brand/logo.svg"}],
					"report_summary": [],
				},
			)

		self.assertEqual(out["typst_source"], "#typst")
		self.assertEqual(out["asset_files"], ["/private/files/brand/logo.svg"])
		self.assertEqual(captured_data["rows"][0]["logo_image"], "logo.svg")

	def test_get_report_typst_source_accepts_presentation_settings(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured = {}

		def fake_build_typst_document(**kwargs):
			captured.update(kwargs)
			return "#typst"

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				return_value=self._fake_format_doc(typst_code="= Test"),
			),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			get_report_typst_source(
				report="Any Report",
				format_name="Any Format",
				presentation_settings={
					"page": {"size": "A5", "orientation": "portrait", "margins": {"left": 8}},
					"branding": {
						"mode": "letterhead",
						"letterhead": "LH-1",
						"letterhead_image": "/files/lh.png",
						"logo": {"image": "/files/logo.png"},
					},
					"report": {"chart_enabled": False},
				},
				preview_data={
					"title": "Any Report",
					"subtitle": "",
					"filters": [],
					"columns": [],
					"rows": [],
					"report_summary": [],
				},
			)

		data = captured["data_dict"]
		self.assertEqual(data["presentation_settings"]["page"]["size"], "A5")
		self.assertEqual(data["presentation_settings"]["branding"]["mode"], "letterhead")
		self.assertEqual(data["presentation_settings"]["page"]["orientation"], "portrait")
		self.assertIn("#set page(", captured["presentation_settings_block"])

	def test_get_report_typst_source_does_not_collect_chart_placeholder_as_asset(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				side_effect=[
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(typst_code="#table()"),
				],
			),
			mock.patch("crispy_print.api.v1.reports._build_typst_document", return_value="#typst"),
		):
			out = get_report_typst_source(
				report="Any Report",
				format_name="Any Format",
				include_chart=1,
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

		self.assertEqual(out["asset_files"], [])

	def test_get_report_data_caps_rows(self):
		from types import SimpleNamespace

		from crispy_print.api.v1.reports import _get_report_data

		with (
			mock.patch("crispy_print.api.v1.reports._ensure_report_read_permission"),
			mock.patch("crispy_print.api.v1.reports.enforce_rate_limit"),
			mock.patch(
				"crispy_print.api.v1.reports.frappe.desk",
				new=SimpleNamespace(
					query_report=SimpleNamespace(
						run=mock.Mock(
							return_value={
								"columns": [{"label": "Name", "fieldname": "name"}],
								"result": [[1], [2], [3], [4]],
							}
						)
					)
				),
			),
		):
			out = _get_report_data("Any Report", {}, max_rows=2)

		self.assertEqual(len(out["result"]), 2)
		self.assertTrue(out["result_truncated"])
		self.assertEqual(out["original_row_count"], 4)
		self.assertEqual(out["returned_row_count"], 2)
		self.assertEqual(out["max_rows"], 2)

	def test_prepare_typst_report_data_reports_column_and_cell_truncation(self):
		from crispy_print.api.v1 import reports
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		columns = [
			{"label": f"Col {idx}", "fieldname": f"col_{idx}", "fieldtype": "Data", "col_index": idx}
			for idx in range(reports.MAX_REPORT_COLUMNS + 1)
		]
		row = {f"col_{idx}": "x" for idx in range(reports.MAX_REPORT_COLUMNS + 1)}
		row["col_0"] = "x" * (reports.MAX_REPORT_CELL_BYTES + 10)

		out = _prepare_typst_report_data(
			"Wide Report",
			{
				"columns": columns,
				"result": [row],
				"message": "Wide Report",
			},
		)

		self.assertEqual(len(out["columns"]), reports.MAX_REPORT_COLUMNS)
		self.assertTrue(out["truncation"]["columns_truncated"])
		self.assertEqual(out["truncation"]["original_column_count"], reports.MAX_REPORT_COLUMNS + 1)
		self.assertGreaterEqual(out["truncation"]["cells_truncated_count"], 1)
		self.assertIn("col_0", out["truncation"]["truncated_fieldnames"])

	def test_get_report_typst_source_returns_truncation_metadata(self):
		from crispy_print.api.v1 import reports
		from crispy_print.api.v1.reports import get_report_typst_source

		columns = [
			{"label": f"Col {idx}", "fieldname": f"col_{idx}", "fieldtype": "Data", "col_index": idx}
			for idx in range(reports.MAX_REPORT_COLUMNS + 1)
		]
		row = {f"col_{idx}": "ok" for idx in range(reports.MAX_REPORT_COLUMNS + 1)}
		row["col_0"] = "x" * (reports.MAX_REPORT_CELL_BYTES + 10)

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				side_effect=[
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(filters=[]),
					self._fake_format_doc(typst_code="#table()"),
				],
			),
			mock.patch("crispy_print.api.v1.reports._build_typst_document", return_value="#typst"),
			mock.patch(
				"crispy_print.api.v1.reports._get_report_data",
				return_value={
					"columns": columns,
					"result": [row],
					"message": "Wide Report",
				},
			),
		):
			out = get_report_typst_source(
				report="Wide Report",
				format_name="Any Format",
				limit=50,
			)

		self.assertTrue(out["truncation"]["is_truncated"])
		self.assertTrue(out["truncation"]["columns"]["truncated"])
		self.assertEqual(out["truncation"]["columns"]["original"], len(columns))
		self.assertEqual(out["truncation"]["columns"]["returned"], reports.MAX_REPORT_COLUMNS)
		self.assertGreaterEqual(out["truncation"]["cells_truncated_count"], 1)

	def test_payment_entry_enrichment_uses_permission_aware_get_list(self):
		from crispy_print.api.v1.reports import _enrich_report_rows_for_typst

		rows = [
			{
				"payment_document_raw": "Payment Entry",
				"payment_entry_raw": "PE-0001",
				"against_account": "Original",
				"cells": [{"fieldname": "against_account", "value": "Original"}],
			}
		]

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_list",
				return_value=[{"name": "PE-0001", "party": "CUST-0001", "party_name": "Customer One"}],
			) as mock_get_list,
			mock.patch("crispy_print.api.v1.reports.frappe.get_all") as mock_get_all,
		):
			out = _enrich_report_rows_for_typst("Bank Reconciliation Statement", rows)

		mock_get_list.assert_called_once()
		mock_get_all.assert_not_called()
		self.assertEqual(out[0]["against_account"], "Customer One")
		self.assertEqual(out[0]["cells"][0]["value"], "Customer One")

	def test_get_report_typst_source_requires_write_for_code_override(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		format_doc = self._fake_format_doc(typst_code="#table()")
		format_doc.check_permission.side_effect = (
			lambda perm: (_ for _ in ()).throw(Exception("no write")) if perm == "write" else None
		)

		with mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc):
			with self.assertRaises(Exception):
				get_report_typst_source(
					report="Any Report",
					format_name="Any Format",
					typst_code_override="#text[override]",
					preview_data={
						"title": "Any Report",
						"subtitle": "",
						"filters": [],
						"columns": [],
						"rows": [],
						"report_summary": [],
					},
				)

	def test_fill_default_report_filters_checks_report_permission(self):
		from crispy_print.api.v1.reports import _fill_default_report_filters

		report_doc = self._fake_format_doc(filters=[])
		report_doc.check_permission.side_effect = Exception("no read")

		with mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=report_doc):
			with self.assertRaises(Exception):
				_fill_default_report_filters("Hidden Report", {})
