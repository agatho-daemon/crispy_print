# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

ARTIFACT_TYPES = {
	"Archival PDF",
	"PDF/A",
	"Rendered SVG",
	"XML Payload",
	"JSON Payload",
	"Signature",
	"Certificate",
	"Authority Receipt",
	"Other",
}


class CrispyIssuedDocumentArtifact(Document):
	def validate(self):
		self.hash_algorithm = self.hash_algorithm or "SHA-256"
		if self.artifact_type and self.artifact_type not in ARTIFACT_TYPES:
			frappe.throw(_("Invalid issued document artifact type: {0}").format(self.artifact_type))
		if self.page_number is not None and cint(self.page_number) < 0:
			frappe.throw(_("Artifact page number cannot be negative."))
