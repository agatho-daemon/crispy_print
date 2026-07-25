# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import json
from unittest import mock

import frappe
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

	def test_report_page_shell_repeats_furniture_and_numbers_pages(self):
		from crispy_print.api.v1.reports import _build_report_presentation_settings_block

		source = _build_report_presentation_settings_block(
			{
				"page": {
					"size": "A4",
					"orientation": "landscape",
					"margins": {"top": 15, "bottom": 15, "left": 12, "right": 12},
				},
				"branding": {"mode": "none"},
			},
			None,
			None,
		)

		self.assertIn("flipped: true", source)
		self.assertIn("header: header_block", source)
		self.assertIn("footer: context", source)
		self.assertIn("footer_block", source)
		self.assertIn('counter(page).display("1 / 1", both: true)', source)

	def test_report_localization_sets_rtl_locale_and_localizes_dates(self):
		from crispy_print.api.v1.reports import _localize_report_typst_data

		data = {
			"columns": [
				{
					"fieldname": "posting_date",
					"label": "Posting Date",
					"fieldtype": "Date",
				},
				{"fieldname": "amount", "label": "Amount", "fieldtype": "Currency"},
			],
			"rows": [
				{
					"cells": [
						{
							"fieldname": "posting_date",
							"label": "Posting Date",
							"raw_value": "2026-07-23",
							"value": "2026-07-23",
							"is_numeric": False,
						},
						{
							"fieldname": "amount",
							"label": "Amount",
							"raw_value": -12.375,
							"value": "KWD -12.375",
							"is_numeric": True,
						},
					]
				}
			],
		}

		out = _localize_report_typst_data(data, "ar-KW")

		self.assertEqual(
			out["locale"],
			{"language": "ar-KW", "direction": "rtl", "numbering_system": "latn"},
		)
		self.assertTrue(out["rows"][0]["cells"][0]["value"])
		self.assertEqual(out["rows"][0]["cells"][1]["value"], "KWD -12.375")
		self.assertTrue(out["columns"][0]["is_ltr"])
		self.assertTrue(out["rows"][0]["cells"][1]["is_ltr"])

	def test_report_snapshot_is_user_and_tab_bound_and_cache_only(self):
		from crispy_print.api.v1.reports import (
			REPORT_PREVIEW_SNAPSHOT_TTL_SECONDS,
			_store_report_preview_snapshot,
		)

		data = {"filters_map": {"company": "Acme"}, "rows": [{"secret": "private"}]}
		with (
			mock.patch("crispy_print.api.v1.reports.frappe.generate_hash", return_value="snap-1"),
			mock.patch("crispy_print.api.v1.reports.frappe.cache.set_value") as set_value,
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc") as get_doc,
			mock.patch("crispy_print.api.v1.reports.frappe.log_error") as log_error,
		):
			result = _store_report_preview_snapshot("General Ledger", data, "tab-a")

		self.assertEqual(result, "snap-1")
		key, payload = set_value.call_args.args
		self.assertEqual(key, "crispy_report_preview:snap-1")
		self.assertEqual(payload["owner"], frappe.session.user)
		self.assertEqual(payload["preview_tab_id"], "tab-a")
		self.assertEqual(payload["company"], "Acme")
		self.assertEqual(payload["data"], data)
		self.assertTrue(set_value.call_args.kwargs["user"])
		self.assertEqual(
			set_value.call_args.kwargs["expires_in_sec"],
			REPORT_PREVIEW_SNAPSHOT_TTL_SECONDS,
		)
		get_doc.assert_not_called()
		log_error.assert_not_called()

	def test_expired_or_logged_out_report_snapshot_requires_fresh_preview(self):
		from crispy_print.api.v1.reports import _load_report_preview_snapshot

		with mock.patch("crispy_print.api.v1.reports.frappe.cache.get_value", return_value=None):
			with self.assertRaisesRegex(Exception, "Run Preview again"):
				_load_report_preview_snapshot("General Ledger", "expired", "tab-a")

	def test_report_snapshot_cannot_be_exchanged_across_users_or_tabs(self):
		from crispy_print.api.v1.reports import _load_report_preview_snapshot

		base_payload = {
			"report": "General Ledger",
			"owner": frappe.session.user,
			"preview_tab_id": "tab-a",
			"data": {"rows": []},
		}
		attempts = [
			({**base_payload, "owner": "another@example.com"}, "tab-a"),
			(base_payload, "tab-b"),
		]
		for payload, tab_id in attempts:
			with self.subTest(payload=payload, tab_id=tab_id):
				with mock.patch("crispy_print.api.v1.reports.frappe.cache.get_value", return_value=payload):
					with self.assertRaisesRegex(Exception, "Run Preview again"):
						_load_report_preview_snapshot("General Ledger", "snap-1", tab_id)

	def test_report_snapshot_rechecks_permissions_before_reuse(self):
		from crispy_print.api.v1.reports import _load_report_preview_snapshot

		payload = {
			"report": "General Ledger",
			"owner": frappe.session.user,
			"preview_tab_id": "tab-a",
			"company": "Acme",
			"data": {"rows": []},
		}
		with (
			mock.patch("crispy_print.api.v1.reports.frappe.cache.get_value", return_value=payload),
			mock.patch(
				"crispy_print.api.v1.reports._ensure_report_read_permission",
				side_effect=frappe.PermissionError,
			),
		):
			with self.assertRaisesRegex(frappe.PermissionError, "Run Preview again"):
				_load_report_preview_snapshot("General Ledger", "snap-1", "tab-a")

	def test_report_snapshot_rechecks_company_user_permission(self):
		from crispy_print.api.v1.reports import _load_report_preview_snapshot

		payload = {
			"report": "General Ledger",
			"owner": frappe.session.user,
			"preview_tab_id": "tab-a",
			"company": "Acme",
			"data": {"rows": []},
		}
		with (
			mock.patch("crispy_print.api.v1.reports.frappe.cache.get_value", return_value=payload),
			mock.patch("crispy_print.api.v1.reports._ensure_report_read_permission"),
			mock.patch(
				"crispy_print.api.v1.reports.ensure_company_access",
				side_effect=frappe.PermissionError,
			) as ensure_company,
		):
			with self.assertRaisesRegex(frappe.PermissionError, "Run Preview again"):
				_load_report_preview_snapshot("General Ledger", "snap-1", "tab-a")

		ensure_company.assert_called_once_with("Acme", doctype="Report")

	def test_compile_report_preview_compiles_pdf_and_preserves_metadata(self):
		from crispy_print.api.v1.reports import compile_report_preview

		source_payload = {
			"typst_source": "= Report",
			"truncation": {"is_truncated": False},
			"asset_files": ["logo.svg"],
			"chart_spec": {"kind": "bar"},
			"chart_render": {"engine": "lilaq", "status": "ready"},
			"chart_svg": None,
			"_generated_data_files": {"crispy-report-data.json": b"{}"},
		}
		with (
			mock.patch(
				"crispy_print.api.v1.reports.get_report_typst_source",
				return_value=source_payload,
			),
			mock.patch(
				"crispy_print.api.v1.reports.compile_typst",
				return_value={"success": True, "format": "pdf", "pdf_data": "JVBERg=="},
			) as compile_mock,
		):
			result = compile_report_preview("Sample Report", preview_snapshot_id="snapshot")

		self.assertEqual(result["format"], "pdf")
		self.assertEqual(result["chart_spec"], {"kind": "bar"})
		compile_mock.assert_called_once_with(
			"= Report",
			output_format="pdf",
			pdf_standard=None,
			asset_files=["logo.svg"],
			chart_svg=None,
			_trusted_data_files={"crispy-report-data.json": b"{}"},
		)

	def test_report_download_audit_records_hashes_without_filter_values_or_cid(self):
		from types import SimpleNamespace

		from crispy_print.api.v1.reports import _record_report_output_audit

		format_doc = SimpleNamespace(
			name="GL Format",
			crispy_format_type="Report",
			report_renderer="general_ledger",
			report_source_fingerprint="source-hash",
			pdf_standard="PDF/A-2u",
			company="Acme",
			check_permission=mock.Mock(),
		)
		activity = SimpleNamespace(name="activity-1", insert=mock.Mock())
		captured = {}

		def fake_get_doc(*args):
			if args == ("Crispy Format", "GL Format"):
				return format_doc
			captured.update(args[0])
			return activity

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", side_effect=fake_get_doc),
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_all",
				return_value=[
					{
						"name": "gl-format-acme-v1_0",
						"version": "1.0",
						"snapshot_hash": "template-hash",
						"company": "Acme",
					}
				],
			),
		):
			result = _record_report_output_audit(
				report="General Ledger",
				format_name="GL Format",
				filters={"company": "Secret Company"},
				output_action="download",
				result={"pdf_data": "JVBERg==", "page_count": 2},
				source_payload={"truncation": {"rows": {"returned": 25}}},
				pdf_standard=None,
			)

		format_doc.check_permission.assert_called_once_with("read")
		activity.insert.assert_called_once_with(ignore_permissions=True)
		self.assertEqual(captured["doctype"], "Crispy Report Output Audit")
		self.assertNotIn("Secret Company", json.dumps(captured))
		self.assertNotIn("Crispy Issued Document", json.dumps(captured))
		self.assertEqual(result["template_snapshot_hash"], "template-hash")
		self.assertEqual(result["page_count"], 2)

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

	def test_get_report_typst_source_returns_complete_result_by_default(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		format_doc = self._fake_format_doc(typst_code="#text[Hello]")
		report_data = {
			"columns": [{"label": "A", "fieldname": "a", "fieldtype": "Data", "col_index": 0}],
			"result": [["x"], ["y"], ["z"]],
			"message": "Sample Report",
		}

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch("crispy_print.api.v1.reports._get_report_data", return_value=report_data) as get_data,
		):
			result = get_report_typst_source("Sample Report", "Any Format")

		self.assertFalse(result["truncation"]["is_truncated"])
		self.assertEqual(result["truncation"]["rows"]["returned"], 3)
		get_data.assert_called_once_with("Sample Report", {}, max_rows=None)

	def test_get_report_typst_source_forces_saved_format_company_into_report_filters(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		format_doc = self._fake_format_doc(
			typst_code="#text[Hello]",
			company="Format Company",
		)
		report_data = {
			"columns": [],
			"result": [],
			"message": "Sample Report",
		}

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch("crispy_print.api.v1.reports._get_report_data", return_value=report_data) as get_data,
		):
			get_report_typst_source(
				"Sample Report",
				"Any Format",
				filters={"company": "Wrong Company"},
			)

		get_data.assert_called_once_with(
			"Sample Report",
			{"company": "Format Company"},
			max_rows=None,
		)

	def test_get_sample_report_data_stores_complete_server_snapshot(self):
		from crispy_print.api.v1.reports import get_sample_report_data

		report_data = {
			"columns": [{"label": "A", "fieldname": "a", "fieldtype": "Data", "col_index": 0}],
			"result": [["x"], ["y"], ["z"]],
			"message": "Sample Report",
		}

		with (
			mock.patch("crispy_print.api.v1.reports._fill_default_report_filters", return_value={}),
			mock.patch("crispy_print.api.v1.reports._get_report_data", return_value=report_data) as get_data,
			mock.patch(
				"crispy_print.api.v1.reports._store_report_preview_snapshot",
				return_value="snapshot-1",
			) as store_snapshot,
		):
			result = get_sample_report_data("Sample Report", store_snapshot=1, preview_tab_id="tab-a")

		self.assertEqual(result["preview_snapshot_id"], "snapshot-1")
		self.assertNotIn("rows", result)
		self.assertEqual(result["total_rows"], 3)
		get_data.assert_called_once_with("Sample Report", {}, max_rows=None)
		self.assertEqual(len(store_snapshot.call_args.args[1]["rows"]), 3)
		self.assertEqual(store_snapshot.call_args.args[2], "tab-a")

	def test_report_source_can_externalize_complete_data_as_json(self):
		from crispy_print.api.v1.reports import REPORT_DATA_FILENAME, get_report_typst_source

		captured = {}

		def fake_build_typst_document(**kwargs):
			captured.update(kwargs)
			return f'#let data = json("{REPORT_DATA_FILENAME}")'

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.has_permission", return_value=True),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			result = get_report_typst_source(
				report="Sample Report",
				format_company="Format Company",
				typst_code_override="#text[Hello]",
				preview_data={
					"title": "Sample Report",
					"columns": [{"fieldname": "a", "label": "A"}],
					"rows": [{"a": "complete value"}],
					"report_summary": [],
				},
				_externalize_data=True,
			)

		self.assertIsNone(captured["data_dict"])
		self.assertEqual(captured["data_file"], REPORT_DATA_FILENAME)
		data = json.loads(result["_generated_data_files"][REPORT_DATA_FILENAME])
		self.assertEqual(data["rows"][0]["a"], "complete value")

	def test_get_report_typst_source_uses_transient_format_company_as_render_context(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.has_permission", return_value=True),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			get_report_typst_source(
				report="Sample Report",
				format_company="Format Company",
				filters={"company": "Wrong Company"},
				typst_code_override="#text[Hello]",
				presentation_settings={
					"source": "custom",
					"branding": {"company": "Wrong Company"},
				},
				preview_data={
					"title": "Sample Report",
					"columns": [],
					"rows": [],
					"report_summary": [],
				},
			)

		self.assertEqual(
			captured_data["presentation_settings"]["branding"]["company"],
			"Format Company",
		)

	def test_project_report_preview_data_reuses_rows_for_selected_builder_columns(self):
		from crispy_print.api.v1.reports import _project_report_preview_data

		snapshot = {
			"columns": [
				{"fieldname": "item", "label": "Item", "width": "auto"},
				{"fieldname": "qty", "label": "Qty", "width": "auto"},
				{"fieldname": "amount", "label": "Amount", "width": "auto"},
			],
			"rows": [
				{
					"item": "ITEM-1",
					"qty": "2",
					"amount": "10.00",
					"cells": [
						{"fieldname": "item", "value": "ITEM-1"},
						{"fieldname": "qty", "value": "2"},
						{"fieldname": "amount", "value": "10.00"},
					],
				}
			],
			"filters": [{"label": "company", "value": "ACME"}],
			"report_summary": [{"label": "Total", "value": "10.00"}],
		}

		projected = _project_report_preview_data(
			snapshot,
			[
				{"fieldname": "amount", "width": "2fr"},
				{"fieldname": "item", "width": "1fr"},
			],
			include_filters=False,
			include_summary=False,
			include_total_row=True,
		)

		self.assertEqual([column["fieldname"] for column in projected["columns"]], ["amount", "item"])
		self.assertEqual([cell["fieldname"] for cell in projected["rows"][0]["cells"]], ["amount", "item"])
		self.assertEqual(projected["columns"][0]["width"], "2fr")
		self.assertEqual(projected["filters"], [])
		self.assertEqual(projected["report_summary"], [])
		self.assertEqual(len(snapshot["columns"]), 3)
		self.assertEqual(len(snapshot["rows"][0]["cells"]), 3)

	def test_builder_recompile_with_preview_data_does_not_execute_report(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}
		format_doc = self._fake_format_doc(typst_code="#text[Hello]", company="Format Company")
		preview_data = {
			"title": "Sample Report",
			"columns": [
				{"fieldname": "item", "label": "Item", "width": "auto"},
				{"fieldname": "qty", "label": "Qty", "width": "auto"},
			],
			"rows": [
				{
					"cells": [
						{"fieldname": "item", "value": "ITEM-1"},
						{"fieldname": "qty", "value": "2"},
					]
				}
			],
			"report_summary": [],
		}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch("crispy_print.api.v1.reports._get_report_data") as get_data,
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			get_report_typst_source(
				report="Sample Report",
				format_name="Any Format",
				preview_data=preview_data,
				column_config=[{"fieldname": "qty", "width": "1fr"}],
			)

		get_data.assert_not_called()
		self.assertEqual([column["fieldname"] for column in captured_data["columns"]], ["qty"])
		self.assertEqual([cell["fieldname"] for cell in captured_data["rows"][0]["cells"]], ["qty"])

	def test_builder_recompile_with_server_snapshot_does_not_execute_report(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		format_doc = self._fake_format_doc(typst_code="#text[Hello]", company="Format Company")
		preview_data = {
			"title": "Sample Report",
			"columns": [{"fieldname": "item", "label": "Item", "width": "auto"}],
			"rows": [{"cells": [{"fieldname": "item", "value": "ITEM-1"}]}],
			"report_summary": [],
		}

		with (
			mock.patch("crispy_print.api.v1.reports.frappe.get_doc", return_value=format_doc),
			mock.patch(
				"crispy_print.api.v1.reports._load_report_preview_snapshot",
				return_value=preview_data,
			) as load_snapshot,
			mock.patch("crispy_print.api.v1.reports._get_report_data") as get_data,
		):
			get_report_typst_source(
				report="Sample Report",
				format_name="Any Format",
				preview_snapshot_id="snapshot-1",
			)

		load_snapshot.assert_called_once_with("Sample Report", "snapshot-1", None)
		get_data.assert_not_called()

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

	def test_get_report_typst_source_rejects_basic_format_without_generated_source(self):
		from frappe.exceptions import ValidationError

		from crispy_print.api.v1.reports import get_report_typst_source

		with mock.patch(
			"crispy_print.api.v1.reports.frappe.get_doc",
			return_value=self._fake_format_doc(typst_code="", raw_typst=0),
		):
			with self.assertRaisesRegex(ValidationError, "no generated Typst code"):
				get_report_typst_source(
					report="Any Report",
					format_name="Any Format",
					preview_data={
						"title": "Any Report",
						"subtitle": "",
						"filters": [],
						"columns": [],
						"rows": [],
						"report_summary": [],
					},
				)

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
					self._fake_format_doc(filters=[], typst_code="#table()"),
					self._fake_format_doc(filters=[], typst_code="#table()"),
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
					self._fake_format_doc(filters=[], typst_code="#table()"),
					self._fake_format_doc(filters=[], typst_code="#table()"),
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
					self._fake_format_doc(filters=[], typst_code="#table()"),
					self._fake_format_doc(filters=[], typst_code="#table()"),
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

	def test_native_lilaq_source_never_receives_browser_svg_even_in_advanced_mode(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		captured_data = {}

		def fake_build_typst_document(**kwargs):
			captured_data.update(kwargs.get("data_dict") or {})
			return "#typst"

		with (
			mock.patch(
				"crispy_print.api.v1.reports.frappe.get_doc",
				return_value=self._fake_format_doc(typst_code="= Advanced", raw_typst=1),
			),
			mock.patch(
				"crispy_print.api.v1.reports._build_typst_document",
				side_effect=fake_build_typst_document,
			),
		):
			out = get_report_typst_source(
				report="Any Report",
				format_name="Any Format",
				include_chart=1,
				chart_svg='<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L1 1"/></svg>',
				preview_data={
					"title": "Any Report",
					"subtitle": "",
					"filters": [],
					"columns": [],
					"rows": [],
					"report_summary": [],
					"chart": {
						"type": "line",
						"data": {
							"labels": ["A", "B"],
							"datasets": [{"name": "Series", "values": [1, 2]}],
						},
					},
				},
			)

		self.assertEqual(out["chart_render"]["engine"], "lilaq")
		self.assertEqual(out["chart_render"]["reason"], "native_lilaq")
		self.assertNotIn("chart_svg", captured_data)
		self.assertIsNone(out["chart_svg"])

	def test_get_report_data_honors_explicit_optional_row_limit(self):
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

	def test_prepare_typst_report_data_preserves_wide_columns_and_long_cells(self):
		from crispy_print.api.v1.reports import _prepare_typst_report_data

		columns = [
			{"label": f"Col {idx}", "fieldname": f"col_{idx}", "fieldtype": "Data", "col_index": idx}
			for idx in range(125)
		]
		long_value = "x" * 5000
		row = {f"col_{idx}": "x" for idx in range(125)}
		row["col_0"] = long_value

		out = _prepare_typst_report_data(
			"Wide Report",
			{
				"columns": columns,
				"result": [row],
				"message": "Wide Report",
			},
		)

		self.assertEqual(len(out["columns"]), 125)
		self.assertFalse(out["truncation"]["columns_truncated"])
		self.assertEqual(out["rows"][0]["col_0"], long_value)
		self.assertEqual(out["truncation"]["cells_truncated_count"], 0)

	def test_get_report_typst_source_does_not_report_crispy_output_truncation(self):
		from crispy_print.api.v1.reports import get_report_typst_source

		columns = [
			{"label": f"Col {idx}", "fieldname": f"col_{idx}", "fieldtype": "Data", "col_index": idx}
			for idx in range(125)
		]
		row = {f"col_{idx}": "ok" for idx in range(125)}
		row["col_0"] = "x" * 5000

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
			)

		self.assertFalse(out["truncation"]["is_truncated"])
		self.assertFalse(out["truncation"]["columns"]["truncated"])
		self.assertEqual(out["truncation"]["columns"]["original"], len(columns))
		self.assertEqual(out["truncation"]["columns"]["returned"], len(columns))
		self.assertEqual(out["truncation"]["cells_truncated_count"], 0)

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
