import frappe
from frappe.tests.utils import FrappeTestCase


class TestCrispyReportOutputAudit(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.flags.allow_crispy_report_output_audit_delete = True
		frappe.db.delete("Crispy Report Output Audit", {"crispy_format": "Test Report Audit Format"})
		frappe.db.delete("Crispy Format", {"name": "Test Report Audit Format"})
		frappe.flags.allow_crispy_report_output_audit_delete = False

	def tearDown(self):
		frappe.flags.allow_crispy_report_output_audit_delete = True
		frappe.db.delete("Crispy Report Output Audit", {"crispy_format": "Test Report Audit Format"})
		frappe.db.delete("Crispy Format", {"name": "Test Report Audit Format"})
		frappe.flags.allow_crispy_report_output_audit_delete = False

	def _insert_format(self):
		report = frappe.db.get_value("Report", {}, "name")
		if not report:
			self.skipTest("A Report record is required")
		return frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test Report Audit Format",
				"crispy_format_type": "Report",
				"report_scope": "Selected Reports",
				"report_renderer": "custom",
				"report": [{"report": report}],
				"module": "Crispy Print",
			}
		).insert(ignore_permissions=True)

	def test_audit_is_metadata_only_immutable_and_delete_protected(self):
		format_doc = self._insert_format()
		audit = frappe.get_doc(
			{
				"doctype": "Crispy Report Output Audit",
				"report": format_doc.report[0].report,
				"action": "Download",
				"crispy_format": format_doc.name,
				"renderer": format_doc.report_renderer,
				"filters_hash": "a" * 64,
				"pdf_sha256": "b" * 64,
				"page_count": 2,
				"row_count": 10,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(audit.generated_by, "Administrator")
		self.assertTrue(audit.generated_at)
		self.assertFalse(hasattr(audit, "report_rows"))
		self.assertFalse(hasattr(audit, "pdf_data"))

		audit.page_count = 3
		with self.assertRaisesRegex(Exception, "immutable"):
			audit.save(ignore_permissions=True)
		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc("Crispy Report Output Audit", audit.name, ignore_permissions=True)
