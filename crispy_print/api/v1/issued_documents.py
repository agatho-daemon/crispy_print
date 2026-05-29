from __future__ import annotations

from typing import Any

import frappe
from frappe import _

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
	crispy_format: str,
) -> JSONDict:
	"""Reserve the issuance API shape without implementing rendering/signing yet."""
	ensure_crispy_print_manager_permission()

	source_doc = frappe.get_doc(source_doctype, source_docname)
	source_doc.check_permission("read")
	frappe.get_doc("Crispy Format", crispy_format).check_permission("read")

	frappe.throw(
		_("Crispy Issued Document snapshot creation is scaffolded but not implemented yet."),
		NotImplementedError,
	)


def _get_name_for_token(verification_token: str) -> str | None:
	token = (verification_token or "").strip()
	if not token:
		frappe.throw(_("Verification token is required."))
	return frappe.db.get_value(DOCTYPE, {"verification_token": token}, "name")
