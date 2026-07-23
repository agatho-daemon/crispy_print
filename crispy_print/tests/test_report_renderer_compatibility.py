from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import mock

from frappe.tests.utils import FrappeTestCase

from crispy_print.report_renderers import (
	RENDERER_BY_KEY,
	audit_report_registry,
	get_compatibility_review,
	get_source_fingerprint,
)


class TestReportRendererCompatibility(FrappeTestCase):
	def test_composite_fingerprint_changes_when_any_reviewed_source_changes(self):
		renderer = RENDERER_BY_KEY["general_ledger"]
		with TemporaryDirectory() as temp:
			root = Path(temp)
			for source in renderer.source_paths:
				path = root / source
				path.parent.mkdir(parents=True, exist_ok=True)
				path.write_text(f"fixture:{source}", encoding="utf-8")
			with mock.patch(
				"crispy_print.report_renderers.frappe.get_app_path",
				return_value=str(root / "erpnext"),
			):
				before = get_source_fingerprint(renderer.key)
				(root / renderer.source_paths[-1]).write_text("changed", encoding="utf-8")
				after = get_source_fingerprint(renderer.key)

		self.assertEqual(before["status"], "current")
		self.assertEqual(len(before["files"]), len(renderer.source_paths))
		self.assertNotEqual(before["fingerprint"], after["fingerprint"])

	def test_registry_audit_detects_missing_renamed_disabled_and_custom_reports(self):
		with mock.patch(
			"crispy_print.report_renderers.frappe.get_all",
			side_effect=[
				[
					{
						"name": "General Ledger",
						"disabled": 1,
						"is_standard": "No",
						"module": "Custom Accounts",
						"report_type": "Script Report",
						"reference_report": None,
						"ref_doctype": "GL Entry",
					}
				],
				[
					{
						"name": "Renamed Trial Balance",
						"reference_report": "Trial Balance",
						"is_standard": "No",
						"module": "Custom Accounts",
						"report_type": "Script Report",
					}
				],
			],
		):
			result = audit_report_registry(["General Ledger", "Trial Balance", "Missing Report"])

		codes = {issue["code"] for issue in result["issues"]}
		self.assertEqual(result["status"], "review_required")
		self.assertIn("report_disabled", codes)
		self.assertIn("custom_report_override", codes)
		self.assertIn("report_renamed", codes)
		self.assertIn("report_missing", codes)

	def test_compatibility_review_records_versions_and_unsupported_major(self):
		with (
			mock.patch(
				"crispy_print.report_renderers.get_app_version",
				side_effect=lambda app: "18.0.0" if app == "frappe" else "17.2.1",
			),
			mock.patch(
				"crispy_print.report_renderers.audit_report_registry",
				return_value={"status": "current", "reports": [], "issues": []},
			),
		):
			review = get_compatibility_review(RENDERER_BY_KEY["general_ledger"])

		self.assertEqual(review["status"], "review_required")
		self.assertFalse(review["versions"]["frappe"]["supported_major"])
		self.assertTrue(review["versions"]["erpnext"]["supported_major"])
		self.assertEqual(review["issues"][0]["code"], "unsupported_upstream_major")
		self.assertGreaterEqual(len(review["checklist"]), 5)

	def test_acknowledgement_requires_write_and_records_current_fingerprint(self):
		from crispy_print.api.v1 import acknowledge_report_renderer_compatibility

		doc = SimpleNamespace(
			crispy_format_type="Report",
			report_renderer="general_ledger",
			check_permission=mock.Mock(),
			db_set=mock.Mock(),
		)
		with (
			mock.patch("crispy_print.api.v1.frappe.get_doc", return_value=doc),
			mock.patch(
				"crispy_print.api.v1._get_source_fingerprint",
				return_value={"fingerprint": "accepted"},
			),
			mock.patch(
				"crispy_print.api.v1._get_renderer_metadata",
				return_value={"source": {"status": "current"}},
			),
		):
			result = acknowledge_report_renderer_compatibility("GL Format")

		doc.check_permission.assert_called_once_with("write")
		doc.db_set.assert_called_once_with("report_source_fingerprint", "accepted", update_modified=True)
		self.assertEqual(result["source"]["status"], "current")
