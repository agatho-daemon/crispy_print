# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_datetime


class CrispyFiscalCredential(Document):
	def validate(self) -> None:
		self.validate_validity_window()
		self.validate_unique_enabled_credential()

	def validate_validity_window(self) -> None:
		if not self.valid_from or not self.valid_until:
			return

		if get_datetime(self.valid_until) <= get_datetime(self.valid_from):
			frappe.throw(_("Valid Until must be after Valid From."))

	def validate_unique_enabled_credential(self) -> None:
		if not self.enabled:
			return

		duplicate = frappe.db.exists(
			"Crispy Fiscal Credential",
			{
				"enabled": 1,
				"company": self.company,
				"regulatory_profile": self.regulatory_profile,
				"authority_code": self.authority_code,
				"environment": self.environment,
				"name": ["!=", self.name],
			},
		)
		if duplicate:
			frappe.throw(
				_(
					"An enabled fiscal credential already exists for this company, regulatory profile, authority code, and environment: {0}"
				).format(frappe.bold(duplicate))
			)
