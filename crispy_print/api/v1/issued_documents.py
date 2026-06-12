from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	resolve_active_crispy_template,
)
from crispy_print.json_utils import loads_dict_or_empty

from .security import ensure_crispy_print_manager_permission, ensure_doctype_read_permission

DOCTYPE = "Crispy Issued Document"
JSONDict = dict[str, Any]


def get_issued_document(name: str) -> JSONDict:
	ensure_doctype_read_permission(DOCTYPE)
	doc = frappe.get_doc(DOCTYPE, name)
	doc.check_permission("read")
	return doc.as_dict()


def get_issued_documents(
	company: str | None = None,
	issuance_status: str | None = None,
	business_status: str | None = None,
	integrity_status: str | None = None,
	limit: int = 50,
) -> list[JSONDict]:
	ensure_doctype_read_permission(DOCTYPE)
	filters = _issued_document_filters(
		company=company,
		issuance_status=issuance_status,
		business_status=business_status,
		integrity_status=integrity_status,
	)
	rows = frappe.get_all(
		DOCTYPE,
		filters=filters,
		fields=[
			"name",
			"document_uuid",
			"company",
			"source_doctype",
			"crispy_format",
			"crispy_template",
			"crispy_template_version",
			"template_hash",
			"pdf_standard",
			"typst_version",
			"zebra_version",
			"barcode_symbology",
			"pdfa_validation_status",
			"issuance_status",
			"business_status",
			"integrity_status",
			"issued_at",
			"revoked",
			"revoked_at",
			"superseded_by",
			"amended_from",
			"modified",
		],
		order_by="modified desc",
		limit_page_length=max(1, min(int(limit or 50), 200)),
	)
	return [dict(row) for row in rows]


def get_issued_document_audit_events(
	company: str | None = None,
	issued_document: str | None = None,
	event_type: str | None = None,
	limit: int = 50,
) -> list[JSONDict]:
	ensure_doctype_read_permission(DOCTYPE)
	parents = _issued_document_names_for_audit(company=company, issued_document=issued_document)
	if not parents:
		return []
	filters: dict[str, Any] = {"parent": ["in", parents]}
	if event_type:
		filters["event_type"] = event_type
	rows = frappe.get_all(
		"Crispy Issued Document Trust Event",
		filters=filters,
		fields=[
			"parent",
			"idx",
			"event_type",
			"validation_status",
			"validation_message",
			"digest_algorithm",
			"timestamp_authority",
			"timestamp_token",
			"creation",
		],
		order_by="parent asc, idx asc",
		limit_page_length=max(1, min(int(limit or 50), 200)),
	)
	return [dict(row) for row in rows]


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

	render_payload = resolved_template.get("render_payload") or {}
	frozen_render_hashes = _get_frozen_render_hashes(render_payload)
	pdfa_conformance = _get_pdfa_conformance_record(resolved_template)
	canonical_payload = {
		"source_doctype": source_doctype,
		"source_docname": source_docname,
		"company": resolved_template.get("effective_company") or resolved_template.get("company"),
		"crispy_template": resolved_template.get("name"),
		"crispy_template_version": resolved_template.get("version"),
		"template_hash": resolved_template.get("snapshot_hash"),
		"pdf_standard": resolved_template.get("pdf_standard"),
		"typst_version": resolved_template.get("typst_version"),
		"zebra_version": resolved_template.get("zebra_version"),
		"barcode_symbology": resolved_template.get("barcode_symbology"),
		"render_payload_hashes": frozen_render_hashes,
	}
	canonical_payload_json = json.dumps(
		canonical_payload,
		sort_keys=True,
		separators=(",", ":"),
		default=str,
	)
	doc = frappe.get_doc(
		{
			"doctype": DOCTYPE,
			"source_doctype": source_doctype,
			"source_docname": source_docname,
			"company": resolved_template.get("effective_company") or resolved_template.get("company"),
			"crispy_format": crispy_format,
			"crispy_template": resolved_template.get("name"),
			"crispy_template_version": resolved_template.get("version"),
			"canonical_payload_json": canonical_payload_json,
			"canonical_payload_hash": hashlib.sha256(canonical_payload_json.encode("utf-8")).hexdigest(),
			"template_hash": resolved_template.get("snapshot_hash"),
			"typst_source": render_payload.get("typst_code") or resolved_template.get("typst_code") or "",
			"typst_version": resolved_template.get("typst_version"),
			"pdf_standard": resolved_template.get("pdf_standard"),
			"zebra_version": resolved_template.get("zebra_version"),
			"barcode_symbology": resolved_template.get("barcode_symbology"),
			"barcode_settings_json": _get_template_barcode_settings_json(resolved_template),
			"pdfa_validation_status": pdfa_conformance["status"],
			"pdfa_validation_result": pdfa_conformance["message"],
			"issuance_status": "Draft",
			"business_status": "Active",
			"integrity_status": "Pending",
		}
	)
	_append_snapshot_trust_events(doc, resolved_template)
	doc.flags.allow_cid_backend_insert = True
	doc.insert(ignore_permissions=True)
	return doc.as_verification_summary()


def _append_snapshot_trust_events(doc, resolved_template: JSONDict) -> None:
	doc.append_trust_event(
		"Hash",
		validation_status="Valid",
		validation_message=_("Canonical payload and frozen template hashes recorded."),
	)
	doc.append_trust_event(
		"Other",
		validation_status="Valid",
		validation_message=_("Render contract recorded: Typst {0}, Zebra {1}, barcode {2}.").format(
			resolved_template.get("typst_version") or _("unknown"),
			resolved_template.get("zebra_version") or _("not configured"),
			resolved_template.get("barcode_symbology") or _("QR Code"),
		),
	)
	doc.append_trust_event(
		"Validation",
		validation_status="Valid" if _is_pdfa_standard(resolved_template.get("pdf_standard")) else "Pending",
		validation_message=_get_pdfa_conformance_record(resolved_template)["message"],
	)


def _get_pdfa_conformance_record(resolved_template: JSONDict) -> JSONDict:
	pdf_standard = str(resolved_template.get("pdf_standard") or "").strip()
	typst_version = str(resolved_template.get("typst_version") or "").strip()
	if _is_pdfa_standard(pdf_standard):
		typst_label = typst_version or _("unknown")
		return {
			"status": "Generated",
			"message": _(
				"PDF/A conformance is producer-asserted by Typst {0} using pdf standard {1}."
			).format(typst_label, pdf_standard),
		}
	return {
		"status": "Skipped",
		"message": _("PDF/A conformance was not requested for pdf standard {0}.").format(
			pdf_standard or _("unspecified")
		),
	}


def _is_pdfa_standard(pdf_standard: Any) -> bool:
	standard = str(pdf_standard or "").strip().lower()
	return standard.startswith("pdf/a") or standard.startswith("a-")


def _get_template_barcode_settings_json(resolved_template: JSONDict) -> str:
	settings = loads_dict_or_empty(resolved_template.get("presentation_settings"))
	qr_settings = settings.get("qr") if isinstance(settings, dict) else {}
	if not isinstance(qr_settings, dict):
		qr_settings = {}
	payload = {
		"symbology": resolved_template.get("barcode_symbology") or qr_settings.get("symbology") or "QR Code",
		"qr": qr_settings,
	}
	return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _get_frozen_render_hashes(render_payload: JSONDict) -> JSONDict:
	return {
		fieldname: hashlib.sha256(str(render_payload.get(fieldname) or "").encode("utf-8")).hexdigest()
		for fieldname in (
			"layout_json",
			"presentation_settings",
			"doc_header",
			"doc_footer",
			"typst_preamble",
			"typst_code",
		)
	}


def _issued_document_filters(
	company: str | None = None,
	issuance_status: str | None = None,
	business_status: str | None = None,
	integrity_status: str | None = None,
) -> dict[str, Any]:
	filters: dict[str, Any] = {}
	if company:
		filters["company"] = company
	if issuance_status:
		filters["issuance_status"] = issuance_status
	if business_status:
		filters["business_status"] = business_status
	if integrity_status:
		filters["integrity_status"] = integrity_status
	return filters


def _issued_document_names_for_audit(
	company: str | None = None,
	issued_document: str | None = None,
) -> list[str]:
	if issued_document:
		if not frappe.db.exists(DOCTYPE, issued_document):
			return []
		if company and frappe.db.get_value(DOCTYPE, issued_document, "company") != company:
			return []
		return [issued_document]
	return frappe.get_all(
		DOCTYPE,
		filters=_issued_document_filters(company=company),
		pluck="name",
		limit_page_length=200,
	)


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
