from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class CrispyReportOutputAudit(Document):
	def before_insert(self) -> None:
		self.generated_by = self.generated_by or frappe.session.user
		self.generated_at = self.generated_at or now_datetime()

	def validate(self) -> None:
		if self.action not in {"Download", "Print"}:
			frappe.throw(_("Report output action must be Download or Print."))
		if not self.is_new():
			frappe.throw(_("Report output audit records are immutable."))

	def on_trash(self) -> None:
		if frappe.flags.allow_crispy_report_output_audit_delete:
			return
		frappe.throw(
			_("Report output audit records cannot be deleted."),
			frappe.PermissionError,
		)
