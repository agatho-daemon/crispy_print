# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

ENVIRONMENTS = {"Sandbox", "Production"}
SUBMISSION_TYPES = {
	"Initial",
	"Amendment",
	"Cancellation",
	"Credit Note",
	"Debit Note",
	"Validation",
	"Sandbox Validation",
	"Other",
}
SUBMISSION_STATUSES = {
	"Draft",
	"Pending",
	"Submitted",
	"Accepted",
	"Rejected",
	"Failed",
	"Cancelled",
	"Superseded",
}


class CrispyIssuedDocumentRegulatorySubmission(Document):
	def validate(self):
		self.environment = self.environment or "Sandbox"
		self.submission_status = self.submission_status or "Draft"
		self._validate_select_value("environment", self.environment, ENVIRONMENTS, required=True)
		self._validate_select_value(
			"submission_type",
			self.submission_type,
			SUBMISSION_TYPES,
			required=True,
		)
		self._validate_select_value(
			"submission_status",
			self.submission_status,
			SUBMISSION_STATUSES,
			required=True,
		)

	def _validate_select_value(
		self,
		fieldname: str,
		value: str | None,
		allowed: set[str],
		required: bool = False,
	) -> None:
		if required and not value:
			frappe.throw(_("{0} is required.").format(frappe.unscrub(fieldname)))
		if value and value not in allowed:
			frappe.throw(
				_("Invalid {0}: {1}").format(frappe.unscrub(fieldname), value),
			)
