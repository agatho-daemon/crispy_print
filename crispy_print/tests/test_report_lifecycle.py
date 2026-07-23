from unittest import mock

from frappe.tests.utils import FrappeTestCase

from crispy_print.report_lifecycle import (
	REPORT_BASIC_GENERATOR_VERSION,
	get_report_generator_version,
	report_format_resolution_rank,
	validate_report_format_for_publish,
)


class TestReportLifecycle(FrappeTestCase):
	def _source(self, **overrides):
		source = {
			"crispy_format_type": "Report",
			"report_scope": "Selected Reports",
			"report": [{"report": "General Ledger", "disabled": 0}],
			"report_renderer": "general_ledger",
			"report_source_fingerprint": "accepted",
			"raw_typst": 0,
			"typst_code": f"// CRISPY_REPORT_BASIC_GENERATOR:{REPORT_BASIC_GENERATOR_VERSION}",
		}
		source.update(overrides)
		return source

	def test_report_publish_requires_one_exact_target_and_current_generator(self):
		with mock.patch(
			"crispy_print.report_lifecycle.get_source_fingerprint",
			return_value={"fingerprint": "accepted"},
		):
			validate_report_format_for_publish(self._source())

			with self.assertRaisesRegex(Exception, "exactly one selected Report"):
				validate_report_format_for_publish(
					self._source(report_scope="All Compatible Reports", report=[])
				)
			with self.assertRaisesRegex(Exception, "generator version 3"):
				validate_report_format_for_publish(
					self._source(typst_code="// CRISPY_REPORT_BASIC_GENERATOR:3")
				)

	def test_report_publish_requires_acknowledged_renderer_fingerprint(self):
		with mock.patch(
			"crispy_print.report_lifecycle.get_source_fingerprint",
			return_value={"fingerprint": "current"},
		):
			with self.assertRaisesRegex(Exception, "changed after this format was reviewed"):
				validate_report_format_for_publish(self._source())

	def test_generator_signature_parser(self):
		self.assertEqual(
			get_report_generator_version("// CRISPY_REPORT_BASIC_GENERATOR:4"),
			4,
		)
		self.assertIsNone(get_report_generator_version("#table()"))

	def test_default_precedence_is_exact_company_then_global_then_renderer(self):
		rows = [
			{
				"name": "Renderer Company",
				"company": "Acme",
				"report_scope": "All Compatible Reports",
				"report_renderer": "general_ledger",
				"is_default": 1,
			},
			{
				"name": "Exact Global",
				"company": "",
				"report_scope": "Selected Reports",
				"report_renderer": "general_ledger",
				"is_default": 1,
			},
			{
				"name": "Exact Company",
				"company": "Acme",
				"report_scope": "Selected Reports",
				"report_renderer": "general_ledger",
				"is_default": 0,
			},
		]
		rows.sort(
			key=lambda row: report_format_resolution_rank(
				row, report_renderer="general_ledger", company="Acme"
			)
		)
		self.assertEqual(
			[row["name"] for row in rows],
			["Exact Company", "Exact Global", "Renderer Company"],
		)
