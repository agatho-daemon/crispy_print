# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.issued_documents import verify_issued_document_token


class TestCrispyIssuedDocument(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
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

	def test_verify_issued_document_token_returns_minimal_status(self):
		doc = self._new_issued_document()
		doc.integrity_status = "Valid"
		doc.insert(ignore_permissions=True)

		result = verify_issued_document_token(doc.verification_token)

		self.assertTrue(result["exists"])
		self.assertEqual(result["verification_status"], "Valid")
		self.assertEqual(result["document_uuid"], doc.document_uuid)
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
			return name
		frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"crispy_format_type": "DocType",
				"doc_type": "DocType",
				"module": "Crispy Print",
				"layout_json": '{"sections":[]}',
			}
		).insert(ignore_permissions=True)
		return name
