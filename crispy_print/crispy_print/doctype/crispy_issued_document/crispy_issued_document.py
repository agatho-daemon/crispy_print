# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import secrets
import uuid

import frappe
from frappe import _
from frappe.model.document import Document

ISSUANCE_STATUSES = {"Draft", "Issued", "Failed", "Revoked", "Superseded"}
BUSINESS_STATUSES = {"Active", "Cancelled", "Revoked", "Superseded", "Expired"}
INTEGRITY_STATUSES = {"Pending", "Valid", "Tampered", "Corrupted", "Unknown"}


class CrispyIssuedDocument(Document):
	def before_insert(self):
		self._ensure_identity()

	def validate(self):
		self._ensure_identity()
		self._set_status_defaults()
		self._validate_statuses()
		self._sync_revocation_fields()
		self._validate_source_document()

	def before_trash(self):
		if self.issuance_status != "Draft":
			frappe.throw(_("Issued document records cannot be deleted after issuance starts."))

	def _ensure_identity(self):
		if not self.document_uuid:
			self.document_uuid = str(uuid.uuid4())
		if not self.verification_token:
			self.verification_token = secrets.token_urlsafe(32)

	def _set_status_defaults(self):
		self.issuance_status = self.issuance_status or "Draft"
		self.business_status = self.business_status or "Active"
		self.integrity_status = self.integrity_status or "Pending"

	def _validate_statuses(self):
		if self.issuance_status not in ISSUANCE_STATUSES:
			frappe.throw(_("Invalid issuance status: {0}").format(self.issuance_status))
		if self.business_status not in BUSINESS_STATUSES:
			frappe.throw(_("Invalid business status: {0}").format(self.business_status))
		if self.integrity_status not in INTEGRITY_STATUSES:
			frappe.throw(_("Invalid integrity status: {0}").format(self.integrity_status))

	def _sync_revocation_fields(self):
		if self.revoked and self.business_status == "Active":
			self.business_status = "Revoked"
		if self.business_status in {"Cancelled", "Revoked"}:
			self.revoked = 1

	def _validate_source_document(self):
		if not self.source_doctype or not self.source_docname:
			return
		if not frappe.db.exists(self.source_doctype, self.source_docname):
			frappe.throw(
				_("Source document {0} {1} does not exist.").format(
					self.source_doctype,
					self.source_docname,
				)
			)

	def as_verification_summary(self) -> dict:
		"""Return a minimal non-sensitive verification payload."""
		return {
			"name": self.name,
			"document_uuid": self.document_uuid,
			"issuance_status": self.issuance_status,
			"business_status": self.business_status,
			"integrity_status": self.integrity_status,
			"issued_at": self.issued_at,
			"revoked": bool(self.revoked),
			"revoked_at": self.revoked_at,
			"superseded_by": self.superseded_by,
			"amended_from": self.amended_from,
		}

	def get_artifacts_by_type(self, artifact_type: str) -> list:
		return [row for row in (self.artifacts or []) if row.artifact_type == artifact_type]

	def get_primary_artifact(self, artifact_type: str | None = None):
		rows = self.get_artifacts_by_type(artifact_type) if artifact_type else list(self.artifacts or [])
		for row in rows:
			if row.is_primary:
				return row
		return rows[0] if rows else None
