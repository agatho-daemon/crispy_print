# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document

REGULATORY_PROFILE_DOCTYPE = "Crispy QR Regulatory Profile"
FISCAL_CREDENTIAL_DOCTYPE = "Crispy Fiscal Credential"


class CrispyDocumentCodeProfile(Document):
	"""Scaffolding for future document-code orchestration.

	This DocType is intended to become the single entry point that resolves
	document-code behavior for a document/context, then delegates to the live
	regulatory profile and fiscal credential layers. Until that resolver exists,
	this controller only performs validation, normalization, and conservative
	default propagation from linked configuration.
	"""

	def validate(self) -> None:
		self.set_defaults()
		self.validate_linked_regulatory_profile()
		self.apply_regulatory_profile_defaults()
		self.apply_fallback_output_defaults()
		self.validate_required_fields()
		self.validate_json_fields()
		self.validate_dimensions()
		self.validate_fiscal_credential_link()
		self.normalize_child_rule_order()

	def set_defaults(self) -> None:
		self.environment = self.environment or "Sandbox"
		self.code_format = self.code_format or "QR Code"
		self.content_source = self.content_source or "Encoder"
		self.priority = _cint_or_default(self.priority, 100)

	def apply_fallback_output_defaults(self) -> None:
		self.code_symbology = self.code_symbology or self._default_symbology_for_code_format()
		self.payload_format = self.payload_format or "TLV"
		self.output_encoding = self.output_encoding or "Plain Text"
		if self.code_format == "QR Code":
			self.error_correction = self.error_correction or "Medium"

	def validate_linked_regulatory_profile(self) -> None:
		if self.code_purpose == "Regulatory" and not self.regulatory_profile:
			frappe.throw(_("Regulatory Profile is required when Code Purpose is Regulatory."))

	def apply_regulatory_profile_defaults(self) -> None:
		if not self.regulatory_profile or not frappe.db.exists(
			REGULATORY_PROFILE_DOCTYPE, self.regulatory_profile
		):
			return

		row = frappe.db.get_value(
			REGULATORY_PROFILE_DOCTYPE,
			self.regulatory_profile,
			[
				"payload_format",
				"output_encoding",
				"error_correction",
				"include_hash",
				"requires_online_verification",
				"verification_url_template",
				"encoder_key",
				"encoder_settings_json",
			],
			as_dict=True,
		)
		if not row:
			return

		if self._is_unset_or_meta_default("payload_format"):
			self.payload_format = row.payload_format
		if self._is_unset_or_meta_default("output_encoding"):
			self.output_encoding = row.output_encoding
		if self.code_format == "QR Code" and self._is_unset_or_meta_default("error_correction"):
			self.error_correction = row.error_correction
		if not self.include_hash and row.include_hash:
			self.include_hash = row.include_hash
		if not self.requires_verification_url and row.requires_online_verification:
			self.requires_verification_url = row.requires_online_verification
		if not (self.verification_url_template or "").strip() and row.verification_url_template:
			self.verification_url_template = row.verification_url_template
		if not (self.encoder_key or "").strip() and row.encoder_key:
			self.encoder_key = row.encoder_key
		if self._is_unset_or_meta_default("encoder_settings_json") and row.encoder_settings_json:
			self.encoder_settings_json = row.encoder_settings_json

	def validate_required_fields(self) -> None:
		if self.content_source == "Payload Template" and not (self.payload_template or "").strip():
			frappe.throw(_("Payload Template is required when Content Source is Payload Template."))
		if self.content_source == "Selected Fields" and not self.selected_fields_json:
			frappe.throw(_("Selected Fields JSON is required when Content Source is Selected Fields."))
		if self.content_source == "Verification URL" and not (self.verification_url_template or "").strip():
			frappe.throw(_("Verification URL Template is required when Content Source is Verification URL."))
		if self.requires_verification_url and not (self.verification_url_template or "").strip():
			frappe.throw(_("Verification URL Template is required when verification URLs are enabled."))
		if self.requires_signature and not self.fiscal_credential:
			frappe.throw(_("Fiscal Credential is required when signature support is enabled."))
		if self.requires_signature and not self.signature_method:
			frappe.throw(_("Signature Method is required when signature support is enabled."))
		if self.include_hash and not self.hash_method:
			frappe.throw(_("Hash Method is required when Include Hash is enabled."))
		if self.code_format in {"Text", "URL"}:
			self.code_symbology = None
			self.error_correction = None
		elif not self.code_symbology:
			self.code_symbology = self._default_symbology_for_code_format()

	def validate_json_fields(self) -> None:
		if self.selected_fields_json:
			_parse_json_list_or_object(self.selected_fields_json, _("Selected Fields JSON"))
		if self.field_mapping_json:
			_parse_json_object(self.field_mapping_json, _("Field Mapping JSON"))
		if self.encoder_settings_json:
			_parse_json_object(self.encoder_settings_json, _("Encoder Settings JSON"))

	def validate_dimensions(self) -> None:
		for fieldname, label in (("width_mm", _("Width (mm)")), ("height_mm", _("Height (mm)"))):
			value = self.get(fieldname)
			if value in (None, ""):
				continue
			try:
				numeric = float(value)
			except (TypeError, ValueError):
				frappe.throw(_("{0} must be a number.").format(label))
			if numeric <= 0:
				frappe.throw(_("{0} must be greater than zero.").format(label))

	def validate_fiscal_credential_link(self) -> None:
		if not self.fiscal_credential:
			return
		if not frappe.db.exists(FISCAL_CREDENTIAL_DOCTYPE, self.fiscal_credential):
			return

		credential = frappe.db.get_value(
			FISCAL_CREDENTIAL_DOCTYPE,
			self.fiscal_credential,
			["company", "regulatory_profile", "environment"],
			as_dict=True,
		)
		if not credential:
			return
		if credential.company and credential.company != self.company:
			frappe.throw(_("Fiscal Credential must belong to the same company as this profile."))
		if credential.environment and credential.environment != self.environment:
			frappe.throw(_("Fiscal Credential environment must match the Document Code Profile environment."))
		if (
			self.regulatory_profile
			and credential.regulatory_profile
			and credential.regulatory_profile != self.regulatory_profile
		):
			frappe.throw(
				_("Fiscal Credential regulatory profile must match the selected Regulatory Profile.")
			)

	def normalize_child_rule_order(self) -> None:
		rules = sorted(
			self.document_rules or [],
			key=lambda row: (_cint_or_default(row.priority, 100), row.idx or 0),
		)
		for index, row in enumerate(rules, start=1):
			row.idx = index
			row.priority = _cint_or_default(row.priority, 100)
		if rules:
			self.document_rules = rules

	def _default_symbology_for_code_format(self) -> str | None:
		return {
			"QR Code": "QR Code",
			"DataMatrix": "DataMatrix",
			"Barcode": "Code 128",
		}.get(self.code_format)

	def _is_unset_or_meta_default(self, fieldname: str) -> bool:
		value = self.get(fieldname)
		if value in (None, ""):
			return True
		field = self.meta.get_field(fieldname)
		if not field:
			return False
		default = field.default
		if default in (None, ""):
			return False
		return str(value) == str(default)


def _parse_json_value(value, label: str):
	if isinstance(value, str):
		try:
			return json.loads(value)
		except json.JSONDecodeError:
			frappe.throw(_("{0} must contain valid JSON.").format(label))
	return value


def _parse_json_object(value, label: str) -> dict:
	parsed = _parse_json_value(value, label)
	if not isinstance(parsed, dict):
		frappe.throw(_("{0} must be a JSON object.").format(label))
	return parsed


def _parse_json_list_or_object(value, label: str) -> list | dict:
	parsed = _parse_json_value(value, label)
	if not isinstance(parsed, list | dict):
		frappe.throw(_("{0} must be a JSON array or object.").format(label))
	return parsed


def _cint_or_default(value, default: int) -> int:
	try:
		return int(value if value not in (None, "") else default)
	except (TypeError, ValueError):
		return default
