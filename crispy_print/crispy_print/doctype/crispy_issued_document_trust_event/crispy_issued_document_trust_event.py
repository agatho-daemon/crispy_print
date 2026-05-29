# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document

EVENT_TYPES = {
	"Hash",
	"Signature",
	"Timestamp",
	"Certificate",
	"Validation",
	"Revocation Check",
	"Other",
}
SIGNATURE_FORMATS = {
	"PAdES",
	"XAdES",
	"CAdES/CMS",
	"Detached",
	"Embedded PDF",
	"Other",
}
VALIDATION_STATUSES = {
	"Pending",
	"Valid",
	"Invalid",
	"Expired",
	"Revoked",
	"Unknown",
	"Failed",
}


class CrispyIssuedDocumentTrustEvent(Document):
	def validate(self):
		self.digest_algorithm = self.digest_algorithm or "SHA-256"
		self.validation_status = self.validation_status or "Pending"
		self._validate_select_value("event_type", self.event_type, EVENT_TYPES, required=True)
		self._validate_select_value("signature_format", self.signature_format, SIGNATURE_FORMATS)
		self._validate_select_value("validation_status", self.validation_status, VALIDATION_STATUSES)

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
