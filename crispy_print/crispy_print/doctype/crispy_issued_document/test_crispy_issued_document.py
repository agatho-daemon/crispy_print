# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import hashlib

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.issued_documents import (
	cancel_issued_document,
	create_issued_document_snapshot,
	get_issued_document_audit_events,
	get_issued_documents,
	record_issued_document_integrity_check,
	render_issued_document_pdf,
	revoke_issued_document,
	supersede_issued_document,
	verify_issued_document_token,
)


class TestCrispyIssuedDocument(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company = self._ensure_company()
		self.format_name = self._ensure_format()

	def tearDown(self):
		frappe.db.rollback()

	def test_before_insert_generates_identity(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)

		self.assertTrue(doc.document_uuid)
		self.assertTrue(doc.verification_token)
		self.assertEqual(doc.issuance_status, "Draft")
		self.assertEqual(doc.business_status, "Active")
		self.assertEqual(doc.integrity_status, "Pending")
		self.assertEqual(doc.company, self.company)

	def test_manual_insert_is_blocked_without_backend_flag(self):
		doc = self._new_issued_document(allow_backend_insert=False)

		self.assertRaises(frappe.PermissionError, doc.insert, ignore_permissions=True)

	def test_derives_company_on_insert(self):
		other_company = self._ensure_company(name="CID Other Company", abbr="CIDO")
		doc = self._new_issued_document()
		doc.company = other_company

		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.company, self.company)

	def test_direct_status_edit_is_blocked_after_insert(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)
		doc.business_status = "Cancelled"

		self.assertRaises(frappe.ValidationError, doc.save)

	def test_revoke_action_updates_status_and_trust_event(self):
		doc = self._new_issued_document()
		doc.integrity_status = "Valid"
		doc.insert(ignore_permissions=True)

		result = revoke_issued_document(doc.name, reason="Duplicate issue")
		doc.reload()

		self.assertEqual(result["business_status"], "Revoked")
		self.assertEqual(doc.business_status, "Revoked")
		self.assertEqual(doc.issuance_status, "Revoked")
		self.assertTrue(doc.revoked)
		self.assertTrue(doc.revoked_at)
		self.assertEqual(doc.trust_events[-1].event_type, "Revocation Check")

	def test_cancel_action_updates_status_and_trust_event(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)

		cancel_issued_document(doc.name, reason="Customer cancelled")
		doc.reload()

		self.assertEqual(doc.business_status, "Cancelled")
		self.assertEqual(doc.issuance_status, "Revoked")
		self.assertTrue(doc.revoked)
		self.assertEqual(doc.trust_events[-1].event_type, "Other")

	def test_supersede_action_links_replacement(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)
		replacement = self._new_issued_document()
		replacement.insert(ignore_permissions=True)

		supersede_issued_document(doc.name, superseded_by=replacement.name, reason="Reissued")
		doc.reload()

		self.assertEqual(doc.business_status, "Superseded")
		self.assertEqual(doc.issuance_status, "Superseded")
		self.assertEqual(doc.superseded_by, replacement.name)

	def test_backend_transition_allows_source_company_drift(self):
		other_company = self._ensure_company(name="CID Drift Company", abbr="CIDD")
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Crispy Format", self.format_name, "company", other_company)

		revoke_issued_document(doc.name, reason="Source format company changed after issuance")
		doc.reload()

		self.assertEqual(doc.company, self.company)
		self.assertEqual(doc.business_status, "Revoked")
		self.assertEqual(doc.issuance_status, "Revoked")

	def test_normal_save_rejects_source_company_drift(self):
		other_company = self._ensure_company(name="CID Save Drift Company", abbr="CIDSD")
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Crispy Format", self.format_name, "company", other_company)
		doc.reload()

		with self.assertRaises(frappe.ValidationError):
			doc.save(ignore_permissions=True)

	def test_backend_transition_requires_frozen_company(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)
		frappe.db.set_value("Crispy Issued Document", doc.name, "company", "")
		doc.reload()
		doc.business_status = "Revoked"
		doc.issuance_status = "Revoked"

		with self.assertRaises(frappe.ValidationError):
			doc.save_backend_transition()

	def test_draft_issued_document_can_be_deleted_by_backend_path(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)

		frappe.delete_doc("Crispy Issued Document", doc.name, ignore_permissions=True)

		self.assertFalse(frappe.db.exists("Crispy Issued Document", doc.name))

	def test_non_draft_issued_document_cannot_be_deleted(self):
		doc = self._new_issued_document()
		doc.issuance_status = "Issued"
		doc.insert(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			frappe.delete_doc("Crispy Issued Document", doc.name, ignore_permissions=True)

		self.assertTrue(frappe.db.exists("Crispy Issued Document", doc.name))

	def test_integrity_check_action_updates_status_and_trust_event(self):
		doc = self._new_issued_document()
		doc.insert(ignore_permissions=True)

		record_issued_document_integrity_check(doc.name, integrity_status="Tampered", message="Hash mismatch")
		doc.reload()

		self.assertEqual(doc.integrity_status, "Tampered")
		self.assertEqual(doc.trust_events[-1].event_type, "Validation")
		self.assertEqual(doc.trust_events[-1].validation_status, "Invalid")

	def test_verify_issued_document_token_returns_minimal_status(self):
		doc = self._new_issued_document()
		doc.integrity_status = "Valid"
		doc.insert(ignore_permissions=True)

		result = verify_issued_document_token(doc.verification_token)

		self.assertTrue(result["exists"])
		self.assertEqual(result["verification_status"], "Valid")
		self.assertEqual(result["document_uuid"], doc.document_uuid)
		self.assertEqual(result["company"], self.company)
		self.assertEqual(result["source_crispy_format"], self.format_name)
		self.assertEqual(
			result["source_target_identity"],
			{
				"crispy_format_type": "DocType",
				"source_doctype": "DocType",
				"source_report": None,
				"source_contract": None,
			},
		)
		self.assertNotIn("canonical_payload_json", result)
		self.assertNotIn("source_docname", result)

	def test_verify_issued_document_token_returns_template_metadata(self):
		template = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": "CID Test Template",
				"source_crispy_format": self.format_name,
				"company": self.company,
				"status": "Approved",
				"is_active": 1,
			}
		)
		template.insert(ignore_permissions=True)
		doc = self._new_issued_document()
		doc.crispy_template = template.name
		doc.crispy_template_version = template.version
		doc.integrity_status = "Valid"
		doc.insert(ignore_permissions=True)

		result = verify_issued_document_token(doc.verification_token)

		self.assertEqual(result["verification_status"], "Valid")
		self.assertEqual(result["crispy_template"], template.name)
		self.assertEqual(result["crispy_template_name"], template.template_name)
		self.assertEqual(result["crispy_template_version"], template.version)
		self.assertEqual(result["source_crispy_format"], self.format_name)
		self.assertEqual(result["source_target_identity"]["crispy_format_type"], "DocType")
		self.assertEqual(result["source_target_identity"]["source_doctype"], "DocType")
		self.assertNotIn("source_docname", result)

	def test_create_snapshot_records_template_render_facts(self):
		template = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": "CID Test Snapshot Template",
				"source_crispy_format": self.format_name,
				"company": self.company,
				"status": "Approved",
				"is_active": 1,
			}
		)
		template.insert(ignore_permissions=True)

		final_typst_source = '#set document(title: "CID")\nRendered DocType value'
		result = create_issued_document_snapshot(
			"DocType",
			"DocType",
			crispy_template=template.name,
			typst_source=final_typst_source,
		)
		doc = frappe.get_doc("Crispy Issued Document", result["name"])

		self.assertEqual(doc.crispy_template, template.name)
		self.assertEqual(doc.crispy_template_version, template.version)
		self.assertEqual(doc.template_hash, template.snapshot_hash)
		self.assertEqual(doc.pdf_standard, template.pdf_standard)
		self.assertEqual(doc.zebra_version, template.zebra_version)
		self.assertEqual(doc.barcode_symbology, template.barcode_symbology)
		self.assertEqual(doc.typst_source, final_typst_source)
		self.assertEqual(
			doc.typst_source_hash,
			hashlib.sha256(final_typst_source.encode("utf-8")).hexdigest(),
		)
		self.assertEqual(doc.issuance_status, "Issued")
		self.assertEqual(doc.integrity_status, "Valid")
		self.assertTrue(doc.issued_at)
		self.assertTrue(doc.canonical_payload_hash)
		canonical_payload = frappe.parse_json(doc.canonical_payload_json)
		self.assertIn("render_payload_hashes", canonical_payload)
		self.assertIn("typst_code", canonical_payload["render_payload_hashes"])
		self.assertEqual(canonical_payload["typst_source_hash"], doc.typst_source_hash)
		self.assertEqual(doc.pdfa_validation_status, "Generated")
		self.assertIn("producer-asserted by Typst", doc.pdfa_validation_result)
		events = {row.event_type: row for row in doc.trust_events}
		self.assertEqual(events["Hash"].validation_status, "Valid")
		self.assertIn("Canonical payload", events["Hash"].validation_message)
		self.assertEqual(events["Other"].validation_status, "Valid")
		self.assertIn("Render contract", events["Other"].validation_message)
		self.assertEqual(events["Validation"].validation_status, "Valid")
		self.assertIn("producer-asserted by Typst", events["Validation"].validation_message)

	def test_create_snapshot_returns_existing_document_for_same_typst_hash(self):
		template = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": "CID Test Idempotent Template",
				"source_crispy_format": self.format_name,
				"company": self.company,
				"status": "Approved",
				"is_active": 1,
			}
		)
		template.insert(ignore_permissions=True)

		final_typst_source = "same generated typst"
		first = create_issued_document_snapshot(
			"DocType",
			"DocType",
			crispy_template=template.name,
			typst_source=final_typst_source,
		)
		second = create_issued_document_snapshot(
			"DocType",
			"DocType",
			crispy_template=template.name,
			typst_source=final_typst_source,
		)

		self.assertEqual(second["name"], first["name"])
		self.assertEqual(
			frappe.db.count(
				"Crispy Issued Document",
				{
					"source_doctype": "DocType",
					"source_docname": "DocType",
					"crispy_template": template.name,
					"typst_source_hash": first["typst_source_hash"],
				},
			),
			1,
		)

	def test_render_issued_document_pdf_uses_stored_typst_source_without_new_cid(self):
		template = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": "CID Test Render Template",
				"source_crispy_format": self.format_name,
				"company": self.company,
				"status": "Approved",
				"is_active": 1,
			}
		)
		template.insert(ignore_permissions=True)
		result = create_issued_document_snapshot(
			"DocType",
			"DocType",
			crispy_template=template.name,
			typst_source="#set page(width: 120pt, height: 80pt)\nCID reprint",
		)
		before_count = frappe.db.count("Crispy Issued Document")

		pdf = render_issued_document_pdf(result["name"])

		self.assertEqual(pdf["format"], "pdf")
		self.assertTrue(pdf["pdf_data"])
		self.assertEqual(pdf["name"], result["name"])
		self.assertEqual(pdf["filename"], f"{result['name']}.pdf")
		self.assertEqual(pdf["typst_source_hash"], result["typst_source_hash"])
		self.assertEqual(frappe.db.count("Crispy Issued Document"), before_count)

	def test_issued_document_lists_filter_by_company_without_source_docname(self):
		other_company = self._ensure_company(name="CID List Other Company", abbr="CIDLO")
		other_format = self._ensure_format("CID List Other Format", company=other_company)
		doc = self._new_issued_document()
		doc.integrity_status = "Valid"
		doc.insert(ignore_permissions=True)
		other = self._new_issued_document()
		other.crispy_format = other_format
		other.integrity_status = "Valid"
		other.flags.allow_cid_backend_insert = True
		other.insert(ignore_permissions=True)

		rows = get_issued_documents(company=self.company, integrity_status="Valid")

		self.assertTrue(any(row["name"] == doc.name for row in rows))
		self.assertFalse(any(row["name"] == other.name for row in rows))
		self.assertTrue(all("source_docname" not in row for row in rows))

	def test_issued_document_audit_events_filter_by_company(self):
		doc = self._new_issued_document()
		doc.append_trust_event("Hash", validation_status="Valid", validation_message="ok")
		doc.insert(ignore_permissions=True)

		rows = get_issued_document_audit_events(company=self.company)

		self.assertTrue(any(row["parent"] == doc.name and row["event_type"] == "Hash" for row in rows))

	def test_superseded_business_status_controls_verification_result(self):
		doc = self._new_issued_document()
		doc.business_status = "Superseded"
		doc.integrity_status = "Valid"
		doc.insert(ignore_permissions=True)

		result = verify_issued_document_token(doc.verification_token)

		self.assertEqual(result["verification_status"], "Superseded")

	def test_artifact_child_defaults_hash_algorithm(self):
		doc = self._new_issued_document()
		doc.append(
			"artifacts",
			{
				"artifact_type": "Archival PDF",
				"file": "/private/files/cid-test.pdf",
			},
		)
		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.artifacts[0].hash_algorithm, "SHA-256")

	def test_get_primary_artifact_returns_primary_row(self):
		doc = self._new_issued_document()
		doc.append(
			"artifacts",
			{
				"artifact_type": "Rendered SVG",
				"file": "/private/files/cid-preview.svg",
			},
		)
		doc.append(
			"artifacts",
			{
				"artifact_type": "Archival PDF",
				"file": "/private/files/cid-test.pdf",
				"is_primary": 1,
			},
		)
		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.get_primary_artifact().artifact_type, "Archival PDF")
		self.assertEqual(doc.get_primary_artifact("Rendered SVG").file, "/private/files/cid-preview.svg")

	def test_trust_event_defaults_validation_status(self):
		doc = self._new_issued_document()
		doc.append(
			"trust_events",
			{
				"event_type": "Timestamp",
				"timestamp_authority": "Example TSA",
			},
		)
		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.trust_events[0].digest_algorithm, "SHA-256")
		self.assertEqual(doc.trust_events[0].validation_status, "Pending")

	def test_regulatory_submission_defaults_status(self):
		doc = self._new_issued_document()
		doc.append(
			"regulatory_submissions",
			{
				"submission_type": "Sandbox Validation",
			},
		)
		doc.insert(ignore_permissions=True)

		self.assertEqual(doc.regulatory_submissions[0].environment, "Sandbox")
		self.assertEqual(doc.regulatory_submissions[0].submission_status, "Draft")

	def _new_issued_document(self, allow_backend_insert: bool = True):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Issued Document",
				"source_doctype": "DocType",
				"source_docname": "DocType",
				"crispy_format": self.format_name,
			}
		)
		if allow_backend_insert:
			doc.flags.allow_cid_backend_insert = True
		return doc

	def _ensure_format(self, name="CID Test Format", company: str | None = None):
		company = company or self.company
		if frappe.db.exists("Crispy Format", name):
			frappe.db.set_value("Crispy Format", name, "company", company)
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"company": company,
				"crispy_format_type": "DocType",
				"doc_type": "DocType",
				"module": "Crispy Print",
				"layout_json": '{"sections":[]}',
			}
		).insert(ignore_permissions=True)
		return name

	def _ensure_company(self, name="CID Test Company", abbr="CIDT"):
		existing = frappe.get_all("Company", filters={"abbr": abbr}, pluck="name", limit=1)
		if existing:
			return existing[0]

		if not frappe.db.exists("Company", name):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": name,
					"abbr": abbr,
					"default_currency": "KWD",
				}
			).insert(ignore_permissions=True)
		return name
