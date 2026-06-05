# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import secrets
import uuid

import frappe
from frappe import _
from frappe.model.document import Document

from crispy_print.api.v1.company_context import resolve_effective_company

ISSUANCE_STATUSES = {"Draft", "Issued", "Failed", "Revoked", "Superseded"}
BUSINESS_STATUSES = {"Active", "Cancelled", "Revoked", "Superseded", "Expired"}
INTEGRITY_STATUSES = {"Pending", "Valid", "Tampered", "Corrupted", "Unknown"}


class CrispyIssuedDocument(Document):
	def before_insert(self):
		self._ensure_identity()

	def validate(self):
		self._ensure_identity()
		self._set_company_if_missing()
		self._validate_company()
		self._validate_backend_controlled_changes()
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

	def _set_company_if_missing(self):
		if self.is_new():
			self.company = self._resolve_company()
			return

		if not self.company:
			self.company = self._resolve_company()

	def _validate_company(self):
		if not self.company:
			frappe.throw(_("Company is required for Crispy Issued Document."))

		resolved_company = self._resolve_company()
		if not self.is_new() and resolved_company and resolved_company != self.company:
			frappe.throw(
				_("Company must match the source document or Crispy Format company: {0}").format(
					frappe.bold(resolved_company)
				)
			)

	def _resolve_company(self) -> str | None:
		return resolve_effective_company(
			source_doctype=self.source_doctype,
			source_docname=self.source_docname,
			explicit_company=self._resolve_template_company() or self._resolve_format_company(),
		)

	def _resolve_source_company(self) -> str | None:
		if not self.source_doctype or not self.source_docname:
			return None

		for fieldname in ("company", "company_name"):
			df = frappe.get_meta(self.source_doctype).get_field(fieldname)
			if not df or df.fieldtype != "Link" or df.options != "Company":
				continue

			return frappe.db.get_value(self.source_doctype, self.source_docname, fieldname)

		return None

	def _resolve_format_company(self) -> str | None:
		if not self.crispy_format:
			return None
		return frappe.db.get_value("Crispy Format", self.crispy_format, "company")

	def _resolve_template_company(self) -> str | None:
		if not self.crispy_template:
			return None
		return frappe.db.get_value("Crispy Template", self.crispy_template, "company")

	def _validate_backend_controlled_changes(self):
		if self.is_new() or self.flags.allow_cid_state_transition:
			return

		previous = self.get_doc_before_save()
		if not previous:
			return

		controlled_fields = {
			"company",
			"source_doctype",
			"source_docname",
			"crispy_format",
			"crispy_template",
			"crispy_template_version",
			"document_uuid",
			"verification_token",
			"issued_at",
			"revoked",
			"revoked_at",
			"superseded_by",
			"amended_from",
			"canonical_payload_json",
			"canonical_payload_hash",
			"typst_source",
			"typst_version",
			"issuance_status",
			"business_status",
			"integrity_status",
			"verification_url",
		}
		for fieldname in controlled_fields:
			if self.get(fieldname) != previous.get(fieldname):
				frappe.throw(
					_(
						"Crispy Issued Document field {0} is backend-controlled. Use an action instead."
					).format(frappe.bold(frappe.unscrub(fieldname)))
				)

		for table_field in ("artifacts", "trust_events", "regulatory_submissions"):
			if self.has_value_changed(table_field):
				frappe.throw(
					_(
						"Crispy Issued Document table {0} is backend-controlled. Use an action instead."
					).format(frappe.bold(frappe.unscrub(table_field)))
				)

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
		template_metadata = self._get_template_metadata()
		return {
			"name": self.name,
			"document_uuid": self.document_uuid,
			"company": self.company,
			"source_crispy_format": self.crispy_format or template_metadata.get("source_crispy_format"),
			"crispy_template": self.crispy_template,
			"crispy_template_name": template_metadata.get("template_name"),
			"crispy_template_version": self.crispy_template_version,
			"source_target_identity": self._get_source_target_identity(template_metadata),
			"issuance_status": self.issuance_status,
			"business_status": self.business_status,
			"integrity_status": self.integrity_status,
			"issued_at": self.issued_at,
			"revoked": bool(self.revoked),
			"revoked_at": self.revoked_at,
			"superseded_by": self.superseded_by,
			"amended_from": self.amended_from,
		}

	def _get_template_metadata(self) -> dict:
		if not self.crispy_template:
			return {}
		values = frappe.db.get_value(
			"Crispy Template",
			self.crispy_template,
			[
				"template_name",
				"source_crispy_format",
				"crispy_format_type",
				"source_doctype",
				"source_report",
				"source_contract",
			],
			as_dict=True,
		)
		return dict(values or {})

	def _get_source_target_identity(self, template_metadata: dict | None = None) -> dict:
		template_metadata = template_metadata or {}
		if template_metadata:
			return {
				"crispy_format_type": template_metadata.get("crispy_format_type"),
				"source_doctype": template_metadata.get("source_doctype"),
				"source_report": template_metadata.get("source_report"),
				"source_contract": template_metadata.get("source_contract"),
			}
		if self.crispy_format:
			values = frappe.db.get_value(
				"Crispy Format",
				self.crispy_format,
				["crispy_format_type", "doc_type", "contract"],
				as_dict=True,
			)
			if values:
				return {
					"crispy_format_type": values.get("crispy_format_type"),
					"source_doctype": values.get("doc_type"),
					"source_report": None,
					"source_contract": values.get("contract"),
				}
		return {
			"crispy_format_type": None,
			"source_doctype": self.source_doctype,
			"source_report": None,
			"source_contract": None,
		}

	def get_artifacts_by_type(self, artifact_type: str) -> list:
		return [row for row in (self.artifacts or []) if row.artifact_type == artifact_type]

	def get_primary_artifact(self, artifact_type: str | None = None):
		rows = self.get_artifacts_by_type(artifact_type) if artifact_type else list(self.artifacts or [])
		for row in rows:
			if row.is_primary:
				return row
		return rows[0] if rows else None

	def append_trust_event(self, event_type: str, validation_message: str | None = None, **values):
		row = self.append(
			"trust_events",
			{
				"event_type": event_type,
				"validation_message": validation_message,
				**values,
			},
		)
		return row

	def save_backend_transition(self):
		self.flags.allow_cid_state_transition = True
		self.save(ignore_permissions=True)
