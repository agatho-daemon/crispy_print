# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crispy_print.json_utils import (
	cint_or_default,
	parse_json_list_or_object,
	parse_json_object,
)


class CrispyDocumentCodeRule(Document):
	"""Scaffolding for future document-code rule resolution.

	This child table is intentionally limited to validation/defaulting today.
	The actual runtime resolver that selects and applies these rules has not been
	implemented yet; that future resolver should sit above the live regulatory
	profile and fiscal credential helpers.
	"""

	def validate(self) -> None:
		self.set_defaults()
		self.validate_condition_fields()
		self.validate_json_overrides()
		self.validate_priority()

	def set_defaults(self) -> None:
		self.condition_type = self.condition_type or "Always"
		self.priority = cint_or_default(self.priority, 100)

	def validate_condition_fields(self) -> None:
		if self.condition_type == "Always":
			self.condition_json = None
			self.condition_expression = None
			return

		if self.condition_type == "Filter JSON":
			if not self.condition_json:
				frappe.throw(_("Condition JSON is required when Condition Type is Filter JSON."))
			self.condition_expression = None
			parse_json_object(self.condition_json, _("Condition JSON"))
			return

		if self.condition_type in {"Python Expression", "Custom Method"}:
			if not (self.condition_expression or "").strip():
				frappe.throw(
					_("Condition Expression / Method is required when Condition Type is {0}.").format(
						self.condition_type
					)
				)
			self.condition_json = None

	def validate_json_overrides(self) -> None:
		if self.selected_fields_json_override:
			parse_json_list_or_object(self.selected_fields_json_override, _("Selected Fields JSON Override"))
		if self.field_mapping_json_override:
			parse_json_object(self.field_mapping_json_override, _("Field Mapping JSON Override"))
		if self.encoder_settings_json_override:
			parse_json_object(self.encoder_settings_json_override, _("Encoder Settings JSON Override"))
		if self.presentation_override_json:
			parse_json_object(self.presentation_override_json, _("Presentation Override JSON"))

	def validate_priority(self) -> None:
		if cint_or_default(self.priority, 100) < 0:
			frappe.throw(_("Priority must be zero or greater."))
