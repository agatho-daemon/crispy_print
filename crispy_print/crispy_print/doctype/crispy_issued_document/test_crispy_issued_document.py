# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.issued_documents import (
	cancel_issued_document,
	record_issued_document_integrity_check,
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
		self.assertNotIn("canonical_payload_json", result)
		self.assertNotIn("source_docname", result)

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

	def _new_issued_document(self):
		return frappe.get_doc(
			{
				"doctype": "Crispy Issued Document",
				"source_doctype": "DocType",
				"source_docname": "DocType",
				"crispy_format": self.format_name,
			}
		)

	def _ensure_format(self):
		name = "CID Test Format"
		if frappe.db.exists("Crispy Format", name):
			frappe.db.set_value("Crispy Format", name, "company", self.company)
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"company": self.company,
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
