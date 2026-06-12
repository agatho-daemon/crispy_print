# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document


class CrispyQRRegulatoryProfile(Document):
	def validate(self) -> None:
		self.set_defaults()
		self.validate_online_verification()
		self.validate_encoder_settings_json()

	def set_defaults(self) -> None:
		self.standard = self.standard or "Custom"
		self.payload_format = self.payload_format or "TLV"
		self.code_symbology = self.code_symbology or "QR Code"
		self.output_encoding = self.output_encoding or "Base64"
		self.error_correction = self.error_correction or "Medium"
		self.quiet_zone = self.quiet_zone if self.quiet_zone not in (None, "") else 1
		self.module_size_pt = self.module_size_pt if self.module_size_pt not in (None, "") else 3
		self.encoder_key = (self.encoder_key or "custom").strip()

	def validate_online_verification(self) -> None:
		if self.requires_online_verification and not self.verification_url_template:
			frappe.throw(_("Verification URL Template is required when online verification is enabled."))

	def validate_encoder_settings_json(self) -> None:
		if not self.encoder_settings_json:
			return

		value = self.encoder_settings_json
		if isinstance(value, str):
			try:
				value = json.loads(value)
			except json.JSONDecodeError:
				frappe.throw(_("Settings JSON must contain valid JSON."))

		if not isinstance(value, dict):
			frappe.throw(_("Settings JSON must be a JSON object."))
