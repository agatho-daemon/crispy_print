# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

CBP_CODE_ONLY_TEMPLATE_PATH = ("public", "js", "templates", "cbp_code_only_template.json")


def get_cbp_code_only_template() -> str:
	path = frappe.get_app_path("crispy_print", *CBP_CODE_ONLY_TEMPLATE_PATH)
	with open(path) as template_file:
		return json.load(template_file)["template"]


CBP_CODE_ONLY_TEMPLATE = get_cbp_code_only_template()
DEFAULT_BRANDING_PROFILE_NAME_PREFIX = "Default Branding Profile - "


def _build_default_branding_profile_name(company_doc) -> str:
	abbr = (company_doc.get("abbr") or "").strip()
	if not abbr:
		frappe.throw(_("Company abbreviation is required to provision the default Branding Profile."))
	return f"{DEFAULT_BRANDING_PROFILE_NAME_PREFIX}{abbr}"


def _get_default_branding_profile_values(company_doc) -> dict:
	return {
		"doctype": "Crispy Branding Profile",
		"profile_name": _build_default_branding_profile_name(company_doc),
		"company": company_doc.name,
		"is_default": 1,
	}


def ensure_default_branding_profile(company: str) -> "CrispyBrandingProfile":
	company_name = (company or "").strip()
	if not company_name:
		frappe.throw(_("Company is required to provision the default Branding Profile."))

	existing_default = frappe.db.get_value(
		"Crispy Branding Profile",
		{"company": company_name, "is_default": 1},
		"name",
	)
	if existing_default:
		return frappe.get_doc("Crispy Branding Profile", existing_default)

	company_doc = frappe.get_doc("Company", company_name)
	values = _get_default_branding_profile_values(company_doc)
	existing_named_profile = frappe.db.get_value(
		"Crispy Branding Profile",
		{"company": company_name, "profile_name": values["profile_name"]},
		"name",
	)
	if existing_named_profile:
		doc = frappe.get_doc("Crispy Branding Profile", existing_named_profile)
		doc.db_set("is_default", 1, update_modified=False)
		doc.reload()
		return doc

	doc = frappe.get_doc(values)
	doc.insert(ignore_permissions=True)
	return doc


def ensure_default_branding_profiles_for_all_companies() -> list[str]:
	companies = frappe.get_all("Company", pluck="name", order_by="name asc")
	created_or_verified: list[str] = []
	for company in companies:
		doc = ensure_default_branding_profile(company)
		created_or_verified.append(doc.name)
	return created_or_verified


def on_company_after_insert(doc, method=None) -> None:
	ensure_default_branding_profile(doc.name)


class CrispyBrandingProfile(Document):
	def validate(self) -> None:
		self.set_defaults()
		self.validate_code_only()
		# TODO(CBP code-only): Code-only mode is parked before shipping. Keep normal
		# profile validation active so hidden stale fields cannot bypass integrity
		# checks. When code-only is finalized, uncomment the early return below and
		# document which basic-mode fields remain irrelevant in that mode.
		# if flt(self.get("code_only")):
		# 	return
		self.validate_branding_assets()
		self.validate_numeric_settings()

	def on_update(self) -> None:
		self.clear_other_company_defaults()

	def set_defaults(self) -> None:
		defaults = {
			"page_size": "A4",
			"orientation": "portrait",
			"margin_top_mm": 20,
			"margin_bottom_mm": 20,
			"margin_right_mm": 20,
			"margin_left_mm": 20,
			"section_label_font_family": "Arial",
			"section_label_font_size_pt": 14,
			"section_label_font_style": "Normal",
			"section_label_font_weight": "Bold",
			"section_label_font_color": "#000000",
			"field_label_font_family": "Arial",
			"field_label_font_size_pt": 8,
			"field_label_font_style": "Normal",
			"field_label_font_weight": "Semibold",
			"field_label_font_color": "#64748B",
			"field_value_font_family": "Arial",
			"field_value_font_size_pt": 10,
			"field_value_font_style": "Normal",
			"field_value_font_weight": "Regular",
			"field_value_font_color": "#000000",
			"table_cell_inset_top_pt": 5,
			"table_cell_inset_right_pt": 5,
			"table_cell_inset_bottom_pt": 5,
			"table_cell_inset_left_pt": 5,
			"table_border_stroke_width_pt": 0.5,
			"table_border_color": "#E2E8F0",
			"table_header_background_color": "#F1F5F9",
			"table_stripe_color": "#F8FAFC",
			"table_header_font_family": "Arial",
			"table_header_font_size_pt": 9,
			"table_header_font_style": "Normal",
			"table_header_font_weight": "Semibold",
			"table_header_font_color": "#000000",
			"table_body_font_family": "Arial",
			"table_body_font_size_pt": 9,
			"table_body_font_style": "Normal",
			"table_body_font_weight": "Regular",
			"table_body_font_color": "#000000",
			"branding_mode": "None",
			"branding_logo_source": "Company logo",
			"branding_logo_width_mm": 20,
			"branding_logo_offset_x_mm": 0,
			"branding_logo_offset_y_mm": 0,
			"branding_letterhead_source": "Use System Letterhead",
			"qr_code_size_mm": 20,
			"qr_dx_mm": 0,
			"qr_dy_mm": 0,
			"qr_source_mode": "Basic QR",
			"qr_symbology": "QR Code",
			"qr_error_correction": "Medium",
			"qr_quiet_zone": 1,
			"qr_module_size_pt": 3,
			"custom_typst_code": CBP_CODE_ONLY_TEMPLATE,
		}
		for fieldname, value in defaults.items():
			if self.get(fieldname) in (None, ""):
				self.set(fieldname, value)

		if self.is_legacy_code_only_template(self.get("custom_typst_code")):
			self.set("custom_typst_code", CBP_CODE_ONLY_TEMPLATE)

	def is_legacy_code_only_template(self, code: str | None) -> bool:
		code = code or ""
		return (
			"CBP code-only template for the dummy e-invoice preview" in code
			or "CBP dummy e-invoice data available in code-only preview" in code
			or (
				"#let specimen = (" in code
				and "Rendered table header sample" in code
				and "Alternating row specimen" in code
			)
		)

	def validate_code_only(self) -> None:
		if flt(self.get("code_only")) and not (self.get("custom_typst_code") or "").strip():
			frappe.throw(_("Typst Code is required when Code Only is enabled."))

	def validate_branding_assets(self) -> None:
		if self.uses_logo():
			if flt(self.branding_logo_width_mm) <= 0:
				frappe.throw(_("Logo width must be greater than zero."))

			if self.branding_logo_source == "Upload image" and not self.branding_logo_upload:
				frappe.throw(_("Upload logo is required when Logo source is Upload image."))

		if self.uses_letterhead():
			if self.branding_letterhead_source == "Upload Letterhead" and not self.branding_letterhead_upload:
				frappe.throw(_("Upload letterhead is required when Letterhead source is Upload Letterhead."))

			if (
				self.branding_letterhead_source == "Use System Letterhead"
				and not self.frappe_company_letterhead
			):
				frappe.throw(
					_("Company letterhead is required when Letterhead source is Use System Letterhead.")
				)

	def validate_numeric_settings(self) -> None:
		positive_values = {
			"section_label_font_size_pt": _("Section label font size"),
			"field_label_font_size_pt": _("Field label font size"),
			"field_value_font_size_pt": _("Field value font size"),
			"table_header_font_size_pt": _("Table header font size"),
			"table_body_font_size_pt": _("Table body font size"),
		}
		for fieldname, label in positive_values.items():
			if flt(self.get(fieldname)) <= 0:
				frappe.throw(_("{0} must be greater than zero.").format(label))

		non_negative_values = {
			"margin_top_mm": _("Top margin"),
			"margin_bottom_mm": _("Bottom margin"),
			"margin_right_mm": _("Right margin"),
			"margin_left_mm": _("Left margin"),
			"table_cell_inset_top_pt": _("Table cell top inset"),
			"table_cell_inset_right_pt": _("Table cell right inset"),
			"table_cell_inset_bottom_pt": _("Table cell bottom inset"),
			"table_cell_inset_left_pt": _("Table cell left inset"),
			"table_border_stroke_width_pt": _("Table border stroke thickness"),
			"branding_logo_offset_x_mm": _("Logo X position"),
			"branding_logo_offset_y_mm": _("Logo Y position"),
			"qr_dx_mm": _("QR Code X position"),
		}
		for fieldname, label in non_negative_values.items():
			if flt(self.get(fieldname)) < 0:
				frappe.throw(_("{0} cannot be negative.").format(label))

		if flt(self.enable_qr_code) and flt(self.qr_code_size_mm) <= 0:
			frappe.throw(_("QR Code size must be greater than zero."))

	def clear_other_company_defaults(self) -> None:
		if not flt(self.is_default) or not self.company:
			return

		frappe.db.set_value(
			"Crispy Branding Profile",
			{
				"company": self.company,
				"is_default": 1,
				"name": ["!=", self.name],
			},
			"is_default",
			0,
		)

	def uses_logo(self) -> bool:
		return self.branding_mode in {"Logo Only", "Logo + Letterhead"}

	def uses_letterhead(self) -> bool:
		return self.branding_mode in {"Letterhead Only", "Logo + Letterhead"}

	def to_presentation_settings(self) -> dict:
		"""Return the normalized presentation payload used by the builder."""
		settings = {
			"codeOnly": bool(flt(self.get("code_only"))),
			"typstCode": self.get("custom_typst_code") or "",
			"page": {
				"size": self.page_size,
				"orientation": self.orientation,
				"margins": {
					"top": flt(self.margin_top_mm),
					"bottom": flt(self.margin_bottom_mm),
					"left": flt(self.margin_left_mm),
					"right": flt(self.margin_right_mm),
				},
			},
			"branding": {
				"mode": self.get_presentation_settings_branding_mode(),
				"letterhead": self.get_letterhead_name(),
				"letterhead_image": self.get_letterhead_image(),
				"logo": {
					"company": self.company if self.branding_logo_source == "Company logo" else "",
					"image": self.get_logo_image(),
					"size": flt(self.branding_logo_width_mm),
					"dx": flt(self.branding_logo_offset_x_mm),
					"dy": flt(self.branding_logo_offset_y_mm),
				},
			},
			"typography": {
				"sectionLabel": self.get_typography_style("section_label"),
				"fieldLabel": self.get_typography_style("field_label"),
				"fieldValue": self.get_typography_style("field_value"),
			},
			"table": {
				"inset": {
					"top": flt(self.table_cell_inset_top_pt),
					"right": flt(self.table_cell_inset_right_pt),
					"bottom": flt(self.table_cell_inset_bottom_pt),
					"left": flt(self.table_cell_inset_left_pt),
				},
				"stroke": {
					"width": flt(self.table_border_stroke_width_pt),
					"color": self.table_border_color or "#E2E8F0",
				},
				"header": {
					"backgroundColor": self.table_header_background_color or "#F1F5F9",
				},
				"stripe": {
					"enabled": bool(flt(self.table_row_striping)),
					"color": self.table_stripe_color or "#F8FAFC",
				},
				"typography": {
					"header": self.get_typography_style("table_header"),
					"body": self.get_typography_style("table_body"),
				},
			},
			"qr": {
				"enabled": bool(flt(self.enable_qr_code)),
				"size": flt(self.qr_code_size_mm),
				"dx": flt(self.qr_dx_mm),
				"dy": flt(self.qr_dy_mm),
				"fields": [],
				"sourceMode": self.get_qr_source_mode(),
				"symbology": self.qr_symbology or "QR Code",
				"errorCorrection": self.qr_error_correction or "Medium",
				"quietZone": flt(self.qr_quiet_zone),
				"moduleSize": flt(self.qr_module_size_pt),
				"datamatrixEncodation": self.get_datamatrix_encodation(),
				"datamatrixSymbols": self.get_datamatrix_symbols(),
			},
		}
		return settings

	def get_qr_source_mode(self) -> str:
		return {
			"Basic QR": "basic",
			"Document Code Profile": "document_code_profile",
		}.get(self.qr_source_mode or "Basic QR", "basic")

	def get_datamatrix_encodation(self) -> str:
		return {
			"ASCII": "ascii",
			"C40": "c40",
			"Text": "text",
			"X12": "x12",
			"EDIFACT": "edifact",
			"Base256": "base256",
		}.get(self.datamatrix_encodation or "", "")

	def get_datamatrix_symbols(self) -> str:
		return {
			"Square": "",
			"Rectangular": "rect",
			"DMRE": "rect-ext",
		}.get(self.datamatrix_symbols or "", "")

	def get_presentation_settings_branding_mode(self) -> str:
		return {
			"None": "none",
			"Logo Only": "logo",
			"Letterhead Only": "letterhead",
			"Logo + Letterhead": "logo_letterhead",
		}.get(self.branding_mode or "None", "none")

	def get_letterhead_name(self) -> str:
		if self.branding_letterhead_source == "Use System Letterhead":
			return self.frappe_company_letterhead or ""
		return ""

	def get_letterhead_image(self) -> str:
		if self.branding_letterhead_source == "Upload Letterhead":
			return self.branding_letterhead_upload or ""
		return ""

	def get_logo_image(self) -> str:
		if not self.uses_logo():
			return ""
		if self.branding_logo_source == "Upload image":
			return self.branding_logo_upload or ""
		if self.branding_logo_source == "Company logo" and self.company:
			return frappe.db.get_value("Company", self.company, "company_logo") or ""
		return ""

	def get_typography_style(self, prefix: str) -> dict:
		return {
			"fontFamily": self.get(f"{prefix}_font_family") or "Inter",
			"fontSize": f"{flt(self.get(f'{prefix}_font_size_pt'))}pt",
			"fontStyle": (self.get(f"{prefix}_font_style") or "Normal").lower(),
			"fontWeight": (self.get(f"{prefix}_font_weight") or "Regular").lower(),
			"color": self.get(f"{prefix}_font_color") or "#000000",
		}


def get_branding_profile(name: str) -> CrispyBrandingProfile:
	if not name:
		frappe.throw(_("Branding Profile is required."))

	if not frappe.db.exists("Crispy Branding Profile", name):
		frappe.throw(_("Crispy Branding Profile {0} was not found.").format(frappe.bold(name)))

	return frappe.get_doc("Crispy Branding Profile", name)


def get_branding_profiles(company: str | None = None) -> list[dict]:
	filters = {}
	if company:
		filters["company"] = company

	return frappe.get_all(
		"Crispy Branding Profile",
		filters=filters,
		fields=["name", "profile_name", "company", "is_default", "branding_mode", "modified"],
		order_by="is_default desc, profile_name asc",
	)


def get_branding_profile_presentation_settings(name: str) -> dict:
	return get_branding_profile(name).to_presentation_settings()


def resolve_effective_presentation_settings(
	presentation_settings: dict | None,
	company: str | None = None,
) -> dict:
	"""Resolve selected Crispy Branding Profile into effective presentation settings."""
	settings = dict(presentation_settings or {})
	branding = dict(settings.get("branding") or {})
	profile_name = (branding.get("profile") or "").strip()

	if settings.get("source") != "branding_profile" or not profile_name:
		return settings

	profile = get_branding_profile(profile_name)
	if company and profile.company and profile.company != company:
		frappe.throw(
			_("Branding Profile {0} does not belong to company {1}.").format(
				frappe.bold(profile_name),
				frappe.bold(company),
			)
		)

	profile_settings = profile.to_presentation_settings()
	profile_branding = dict(profile_settings.get("branding") or {})
	profile_branding["profile"] = profile_name

	effective = {
		**profile_settings,
		"source": "branding_profile",
		"branding": profile_branding,
	}

	if settings.get("language"):
		effective["language"] = settings.get("language")
	if settings.get("report"):
		effective["report"] = settings.get("report")

	return effective
