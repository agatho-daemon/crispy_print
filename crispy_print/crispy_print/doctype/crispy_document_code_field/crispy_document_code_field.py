# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document

from crispy_print.qr_registry import get_qr_field_definition, validate_qr_field_selection

REGULATORY_PROFILE_DOCTYPE = "Crispy QR Regulatory Profile"
PROFILE_DOCTYPE = "Crispy Document Code Profile"


class CrispyDocumentCodeField(Document):
	def validate(self) -> None:
		self.validate_registry_key()
		self.apply_registry_metadata()

	def validate_registry_key(self) -> None:
		if not self.source_doctype:
			frappe.throw(_("Source DocType is required for selected QR fields."))
		if not self.field_key:
			frappe.throw(_("Field Key is required for selected QR fields."))

		validate_qr_field_selection(
			self.source_doctype,
			[self.field_key],
			authority_code=self._authority_code(),
		)

	def apply_registry_metadata(self) -> None:
		definition = get_qr_field_definition(self.source_doctype, self.field_key)
		self.label = definition.get("label")
		self.source_path = definition.get("path")
		self.source = definition.get("source")
		self.datatype = definition.get("datatype")
		self.purpose = definition.get("purpose")

	def _authority_code(self) -> str | None:
		parent = self._parent_doc()
		if not parent or parent.get("code_purpose") != "Regulatory":
			return None
		regulatory_profile = parent.get("regulatory_profile")
		if not regulatory_profile or not frappe.db.exists(REGULATORY_PROFILE_DOCTYPE, regulatory_profile):
			return None
		return frappe.db.get_value(REGULATORY_PROFILE_DOCTYPE, regulatory_profile, "authority_code")

	def _parent_doc(self) -> Any | None:
		if self.parenttype == PROFILE_DOCTYPE and self.parent:
			try:
				return frappe.get_doc(PROFILE_DOCTYPE, self.parent)
			except Exception:
				return None
		return getattr(self, "parent_doc", None)
