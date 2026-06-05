from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	resolve_active_crispy_template,
)

from .security import ensure_crispy_print_manager_permission, ensure_doctype_read_permission

DOCTYPE = "Crispy Issued Document"
JSONDict = dict[str, Any]


def get_issued_document(name: str) -> JSONDict:
	ensure_doctype_read_permission(DOCTYPE)
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	return doc.as_dict()


def get_issued_document_by_token(verification_token: str) -> JSONDict:
	ensure_doctype_read_permission(DOCTYPE)
	name = _get_name_for_token(verification_token)
	if not name:
		frappe.throw(_("Issued document not found."), frappe.DoesNotExistError)
	return get_issued_document(name)


def verify_issued_document_token(verification_token: str) -> JSONDict:
	"""Return a minimal verification summary for an opaque token.

	This is intentionally not a public/guest endpoint yet. It gives the future
	verification layer a stable internal shape without exposing live ERP data.
	"""
	ensure_doctype_read_permission(DOCTYPE)
	name = _get_name_for_token(verification_token)
	if not name:
		return {
			"exists": False,
			"verification_status": "Not Found",
		}

	doc = frappe.get_doc(DOCTYPE, name)
	status = "Valid"
	if doc.revoked or doc.business_status in {"Cancelled", "Revoked"}:
		status = "Revoked"
	elif doc.business_status == "Superseded" or doc.superseded_by:
		status = "Superseded"
	elif doc.integrity_status in {"Tampered", "Corrupted"}:
		status = doc.integrity_status
	elif doc.integrity_status not in {"Valid", "Pending"}:
		status = "Unknown"

	return {
		"exists": True,
		"verification_status": status,
		**doc.as_verification_summary(),
	}


def create_issued_document_snapshot(
	source_doctype: str,
	source_docname: str,
	crispy_format: str | None = None,
	crispy_template: str | None = None,
) -> JSONDict:
	"""Create an additive draft issued-document registry entry.

	This records the resolved frozen template/version while keeping the legacy
	Crispy Format link for compatibility. Artifact rendering/signing remains a
	later step.
	"""
	ensure_crispy_print_manager_permission()

	source_doc = frappe.get_doc(source_doctype, source_docname)
	source_doc.check_permission("read")
	resolved_template = resolve_active_crispy_template(
		source_doctype=source_doctype,
		source_docname=source_docname,
		template=crispy_template,
	)
	if crispy_format:
		frappe.get_doc("Crispy Format", crispy_format).check_permission("read")
	else:
		crispy_format = resolved_template.get("source_crispy_format")

	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"source_doctype": source_doctype,
			"source_docname": source_docname,
			"company": resolved_template.get("effective_company") or resolved_template.get("company"),
			"crispy_format": crispy_format,
			"crispy_template": resolved_template.get("name"),
			"crispy_template_version": resolved_template.get("version"),
			"canonical_payload_json": frappe.as_json(
				{
					"source_doctype": source_doctype,
					"source_docname": source_docname,
					"company": resolved_template.get("effective_company") or resolved_template.get("company"),
					"crispy_template": resolved_template.get("name"),
					"crispy_template_version": resolved_template.get("version"),
				}
			),
			"typst_source": "",
			"typst_version": resolved_template.get("version"),
			"issuance_status": "Draft",
			"business_status": "Active",
			"integrity_status": "Pending",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.as_verification_summary()


def revoke_issued_document(name: str, reason: str | None = None) -> JSONDict:
	ensure_crispy_print_manager_permission()
	doc = _get_transition_doc(name)

	if doc.revoked or doc.business_status == "Revoked":
		frappe.throw(_("Issued document is already revoked."))
	if doc.business_status in {"Cancelled", "Superseded"}:
		frappe.throw(_("Cannot revoke an issued document with status {0}.").format(doc.business_status))

	doc.revoked = 1
	doc.revoked_at = now_datetime()
	doc.business_status = "Revoked"
	doc.issuance_status = "Revoked"
	doc.append_trust_event(
		"Revocation Check",
		validation_status="Revoked",
		validation_message=reason or _("Issued document revoked."),
	)
	doc.save_backend_transition()
	return doc.as_verification_summary()


def cancel_issued_document(name: str, reason: str | None = None) -> JSONDict:
	ensure_crispy_print_manager_permission()
	doc = _get_transition_doc(name)

	if doc.business_status in {"Cancelled", "Revoked"}:
		frappe.throw(_("Issued document is already {0}.").format(doc.business_status.lower()))
	if doc.business_status == "Superseded":
		frappe.throw(_("Cannot cancel a superseded issued document."))

	doc.revoked = 1
	doc.revoked_at = now_datetime()
	doc.business_status = "Cancelled"
	doc.issuance_status = "Revoked"
	doc.append_trust_event(
		"Other",
		validation_status="Valid",
		validation_message=reason or _("Issued document cancelled."),
	)
	doc.save_backend_transition()
	return doc.as_verification_summary()


def supersede_issued_document(
	name: str,
	superseded_by: str,
	reason: str | None = None,
) -> JSONDict:
	ensure_crispy_print_manager_permission()
	doc = _get_transition_doc(name)
	replacement = (superseded_by or "").strip()

	if not replacement:
		frappe.throw(_("Superseding issued document is required."))
	if replacement == name:
		frappe.throw(_("Issued document cannot supersede itself."))
	if not frappe.db.exists(DOCTYPE, replacement):
		frappe.throw(_("Superseding issued document {0} was not found.").format(frappe.bold(replacement)))
	if doc.business_status in {"Cancelled", "Revoked"}:
		frappe.throw(_("Cannot supersede an issued document with status {0}.").format(doc.business_status))

	doc.superseded_by = replacement
	doc.business_status = "Superseded"
	doc.issuance_status = "Superseded"
	doc.append_trust_event(
		"Other",
		validation_status="Valid",
		validation_message=reason or _("Issued document superseded by {0}.").format(replacement),
	)
	doc.save_backend_transition()
	return doc.as_verification_summary()


def record_issued_document_integrity_check(
	name: str,
	integrity_status: str,
	message: str | None = None,
) -> JSONDict:
	ensure_crispy_print_manager_permission()
	doc = _get_transition_doc(name)
	status = (integrity_status or "").strip()

	if status not in {"Pending", "Valid", "Tampered", "Corrupted", "Unknown"}:
		frappe.throw(_("Invalid integrity status: {0}").format(status))

	doc.integrity_status = status
	doc.append_trust_event(
		"Validation",
		validation_status=_trust_validation_status_for_integrity(status),
		validation_message=message or _("Integrity status set to {0}.").format(status),
	)
	doc.save_backend_transition()
	return doc.as_verification_summary()


def add_issued_document_trust_event(name: str, event: dict | None = None, **values) -> JSONDict:
	ensure_crispy_print_manager_permission()
	doc = _get_transition_doc(name)
	payload = {**(event or {}), **values}
	event_type = payload.pop("event_type", None)

	if not event_type:
		frappe.throw(_("Trust event type is required."))

	doc.append_trust_event(event_type, **payload)
	doc.save_backend_transition()
	return doc.as_dict()


def _get_name_for_token(verification_token: str) -> str | None:
	token = (verification_token or "").strip()
	if not token:
		frappe.throw(_("Verification token is required."))
	return frappe.db.get_value(DOCTYPE, {"verification_token": token}, "name")


def _get_transition_doc(name: str):
	docname = (name or "").strip()
	if not docname:
		frappe.throw(_("Issued document is required."))
	doc = frappe.get_doc(DOCTYPE, docname)
	doc.check_permission("write")
	return doc


def _trust_validation_status_for_integrity(integrity_status: str) -> str:
	if integrity_status == "Valid":
		return "Valid"
	if integrity_status in {"Tampered", "Corrupted"}:
		return "Invalid"
	if integrity_status == "Pending":
		return "Pending"
	return "Unknown"
