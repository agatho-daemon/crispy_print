# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTemplateParityHarness(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_compare_template_signals_reports_missing_filter_keys(self):
		from crispy_print.api.v1.parity import compare_template_signals

		legacy = """
		{% if (filters.show_future_payments) { %}{% } %}
		{% if (filters.party) { %}{% } %}
		"""
		typst = """
		#if data.show_future_payments [
		  #text[Future]
		]
		"""

		out = compare_template_signals(legacy, typst)
		self.assertIn("party", out["summary"]["missing_filter_keys"])
		self.assertIn("show_future_payments", out["typst"]["filter_keys"])
		self.assertGreaterEqual(out["summary"]["legacy_filter_count"], 2)

	def test_run_report_template_parity_check_uses_report_source_and_returns_summary(self):
		from crispy_print.api.v1.parity import run_report_template_parity_check

		with TemporaryDirectory() as tmpdir:
			template_path = Path(tmpdir) / "accounts_receivable.html"
			template_path.write_text(
				"{% if (filters.show_sales_person) { %}x{% } %}",
				encoding="utf-8",
			)

			with (
				mock.patch(
					"crispy_print.api.v1.parity._resolve_report_html_path",
					return_value=template_path,
				),
				mock.patch(
					"crispy_print.api.v1.reports.get_report_typst_source",
					return_value="#if data.show_sales_person [#text[ok]]",
				),
				mock.patch(
					"crispy_print.api.v1.parity._report_template_allowed_roots",
					return_value=[Path(tmpdir).resolve()],
				),
			):
				out = run_report_template_parity_check("Accounts Receivable", "Accounts Report")

		self.assertEqual(out["report"], "Accounts Receivable")
		self.assertEqual(out["format_name"], "Accounts Report")
		self.assertEqual(out["summary"]["missing_filter_keys"], [])
		self.assertEqual(out["summary"]["filter_coverage_percent"], 100.0)

	def test_legacy_include_templates_are_inlined(self):
		from crispy_print.api.v1.parity import _read_legacy_template_source

		with TemporaryDirectory() as tmpdir:
			base = Path(tmpdir) / "base.html"
			shared = Path(tmpdir) / "shared.html"
			shared.write_text("{% if (filters.party) { %}Party{% } %}", encoding="utf-8")
			base.write_text('{% include "shared.html" %}', encoding="utf-8")
			source = _read_legacy_template_source(base)

		self.assertIn("filters.party", source)

	def test_explicit_legacy_template_path_must_stay_inside_allowed_roots(self):
		from crispy_print.api.v1.parity import _resolve_report_html_path

		with TemporaryDirectory() as tmpdir:
			rogue = Path(tmpdir) / "rogue.html"
			rogue.write_text("x", encoding="utf-8")
			with mock.patch(
				"crispy_print.api.v1.parity._report_template_allowed_roots",
				return_value=[Path(tmpdir).resolve() / "allowed"],
			):
				with self.assertRaises(frappe.ValidationError):
					_resolve_report_html_path("Accounts Receivable", str(rogue))

	def test_extracts_expected_accounts_receivable_signals_from_legacy_template(self):
		from crispy_print.api.v1.parity import extract_legacy_template_signals

		try:
			erpnext_path = Path(frappe.get_app_path("erpnext"))
		except Exception:
			self.skipTest("erpnext app path is not available in this environment")
			return

		template_path = (
			erpnext_path / "accounts" / "report" / "accounts_receivable" / "accounts_receivable.html"
		)
		if not template_path.exists():
			self.skipTest("accounts_receivable legacy template is not available in this environment")

		source = template_path.read_text(encoding="utf-8")
		signals = extract_legacy_template_signals(source)

		self.assertIn("show_future_payments", signals["filter_keys"])
		self.assertIn("show_sales_person", signals["filter_keys"])
		self.assertIn("credit_limit", signals["filter_keys"])
		self.assertIn("party", signals["filter_keys"])

	def test_extracts_financial_statements_filters_from_legacy_template(self):
		from crispy_print.api.v1.parity import extract_legacy_template_signals

		legacy = """
		{% if 'cost_center' in filters %}{% endif %}
		{% if (filters.from_date) { %}{% } %}
		{%= filters.company %}
		{%= filters.fiscal_year %}
		{%= filters.presentation_currency || erpnext.get_currency(filters.company) %}
		{%= frappe.datetime.str_to_user(filters.to_date) %}
		"""

		signals = extract_legacy_template_signals(legacy)
		for key in (
			"cost_center",
			"company",
			"fiscal_year",
			"presentation_currency",
			"from_date",
			"to_date",
		):
			self.assertIn(key, signals["filter_keys"])

	def test_financial_statements_typst_signal_parity_coverage(self):
		from crispy_print.api.v1.parity import compare_template_signals

		legacy = """
		{% if 'cost_center' in filters %}{% endif %}
		{% if (filters.from_date) { %}{% } %}
		{%= filters.company %}
		{%= filters.fiscal_year %}
		{%= filters.presentation_currency || erpnext.get_currency(filters.company) %}
		{%= frappe.datetime.str_to_user(filters.to_date) %}
		"""

		typst = """
		#let company = getFilterValue("company")
		#let costCenter = getFilterValue("cost_center")
		#let fiscalYear = getFilterValue("fiscal_year")
		#let presentationCurrency = getFilterValue("presentation_currency")
		#let fromDate = getFilterValue("from_date")
		#let toDate = getFilterValue("to_date")
		#if fromDate != "" and toDate != "" [#text[#fromDate - #toDate]]
		"""

		out = compare_template_signals(legacy, typst)
		self.assertEqual(out["summary"]["missing_filter_keys"], [])
