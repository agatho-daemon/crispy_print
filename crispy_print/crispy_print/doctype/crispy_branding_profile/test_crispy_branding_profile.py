# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	_build_default_branding_profile_name,
	ensure_default_branding_profile,
	ensure_default_branding_profiles_for_all_companies,
	get_branding_profile_presentation_settings,
	get_branding_profiles,
	on_company_after_insert,
	resolve_effective_presentation_settings,
)
from crispy_print.install import after_install
from crispy_print.patches.post_model_sync.backfill_default_branding_profiles import (
	execute as backfill_default_branding_profiles,
)


class TestCrispyBrandingProfile(FrappeTestCase):
	def setUp(self):
		self.company = self._ensure_company()

	def tearDown(self):
		frappe.db.rollback()

	def test_exports_normalized_presentation_settings(self):
		doc = self._insert_profile(
			branding_mode="Logo Only",
			branding_logo_source="Upload image",
			branding_logo_upload="/files/cbp-logo.png",
			margin_top_mm=11,
			margin_bottom_mm=12,
			margin_left_mm=13,
			margin_right_mm=14,
			section_label_font_family="Inter 18pt",
			section_label_font_size_pt=15,
			section_label_font_weight="Extrabold",
			enable_qr_code=1,
			qr_code_size_mm=22,
			qr_dx_mm=3,
			qr_dy_mm=4,
		)

		settings = doc.to_presentation_settings()

		self.assertEqual(settings["page"]["size"], "A4")
		self.assertEqual(settings["branding"]["mode"], "logo")
		self.assertEqual(settings["page"]["margins"]["top"], 11)
		self.assertEqual(settings["page"]["margins"]["right"], 14)
		self.assertEqual(settings["branding"]["logo"]["image"], "/files/cbp-logo.png")
		self.assertEqual(settings["typography"]["sectionLabel"]["fontFamily"], "Inter 18pt")
		self.assertEqual(settings["typography"]["sectionLabel"]["fontSize"], "15.0pt")
		self.assertEqual(settings["typography"]["sectionLabel"]["fontWeight"], "extrabold")
		self.assertTrue(settings["qr"]["enabled"])
		self.assertEqual(settings["qr"]["dy"], 4)
		self.assertEqual(settings["qr"]["sourceMode"], "basic")

	def test_rejects_negative_position_coordinates(self):
		doc = self._new_profile(
			branding_mode="Logo Only",
			branding_logo_source="Upload image",
			branding_logo_upload="/files/cbp-logo.png",
			branding_logo_offset_x_mm=-1,
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

		doc = self._new_profile(enable_qr_code=1, qr_dx_mm=-1)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_allows_negative_qr_y_position(self):
		doc = self._insert_profile(enable_qr_code=1, qr_dy_mm=-5)

		settings = doc.to_presentation_settings()

		self.assertEqual(settings["qr"]["dy"], -5)

	def test_minimal_profile_insert_sets_presentation_defaults(self):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Branding Profile",
				"profile_name": "CBP Test Minimal",
				"company": self.company,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(doc.page_size, "A4")
		self.assertEqual(doc.branding_mode, "None")
		self.assertEqual(doc.table_header_font_size_pt, 9)
		self.assertEqual(doc.qr_code_size_mm, 20)
		self.assertIn(
			"CBP code-only template for the Branding Profile Specimen preview", doc.custom_typst_code
		)
		self.assertIn("Use System Letterhead", doc.custom_typst_code)

	def test_code_only_requires_typst_code(self):
		doc = self._new_profile(code_only=1, custom_typst_code="   ")

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_code_only_exports_typst_code(self):
		doc = self._insert_profile(
			profile_name="CBP Test Code Only",
			code_only=1,
			custom_typst_code="#text[Power user profile]",
		)

		settings = doc.to_presentation_settings()

		self.assertTrue(settings["codeOnly"])
		self.assertEqual(settings["typstCode"], "#text[Power user profile]")

	def test_code_only_does_not_bypass_basic_validation_while_frozen(self):
		doc = self._new_profile(
			code_only=1,
			custom_typst_code="#text[Power user profile]",
			section_label_font_size_pt=0,
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_preserves_logo_and_letterhead_mode_in_payload(self):
		doc = self._insert_profile(
			profile_name="CBP Test Combo",
			branding_mode="Logo + Letterhead",
			branding_logo_source="Upload image",
			branding_logo_upload="/files/cbp-logo.png",
			branding_letterhead_source="Upload Letterhead",
			branding_letterhead_upload="/files/cbp-letterhead.png",
		)

		settings = get_branding_profile_presentation_settings(doc.name)

		self.assertEqual(settings["branding"]["mode"], "logo_letterhead")
		self.assertEqual(settings["branding"]["letterhead_image"], "/files/cbp-letterhead.png")
		self.assertEqual(settings["branding"]["logo"]["image"], "/files/cbp-logo.png")

	def test_resolves_effective_presentation_settings_from_selected_profile(self):
		doc = self._insert_profile(
			profile_name="CBP Test Effective",
			branding_mode="Logo Only",
			branding_logo_source="Upload image",
			branding_logo_upload="/files/cbp-effective-logo.png",
			margin_top_mm=9,
		)

		settings = resolve_effective_presentation_settings(
			{
				"source": "branding_profile",
				"language": "ar",
				"branding": {"profile": doc.name, "mode": "none"},
				"report": {"mode": "basic"},
			}
		)

		self.assertEqual(settings["source"], "branding_profile")
		self.assertEqual(settings["branding"]["profile"], doc.name)
		self.assertEqual(settings["branding"]["mode"], "logo")
		self.assertEqual(settings["branding"]["logo"]["image"], "/files/cbp-effective-logo.png")
		self.assertEqual(settings["page"]["margins"]["top"], 9)
		self.assertEqual(settings["language"], "ar")
		self.assertEqual(settings["report"]["mode"], "basic")

	def test_exports_document_code_profile_qr_mode(self):
		doc = self._insert_profile(
			profile_name="CBP Test QR Source",
			enable_qr_code=1,
			qr_source_mode="Document Code Profile",
		)

		settings = doc.to_presentation_settings()

		self.assertEqual(settings["qr"]["sourceMode"], "document_code_profile")

	def test_rejects_missing_uploaded_logo(self):
		doc = self._new_profile(
			branding_mode="Logo Only",
			branding_logo_source="Upload image",
			branding_logo_upload="",
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_rejects_missing_system_letterhead(self):
		doc = self._new_profile(
			branding_mode="Letterhead Only",
			branding_letterhead_source="Use System Letterhead",
			frappe_company_letterhead="",
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_keeps_one_default_per_company(self):
		first = self._insert_profile(profile_name="CBP Test Default 1", is_default=1)
		second = self._insert_profile(profile_name="CBP Test Default 2", is_default=1)

		self.assertEqual(frappe.db.get_value("Crispy Branding Profile", second.name, "is_default"), 1)
		self.assertEqual(frappe.db.get_value("Crispy Branding Profile", first.name, "is_default"), 0)

	def test_lists_profiles_for_company(self):
		doc = self._insert_profile(profile_name="CBP Test Listed")

		rows = get_branding_profiles(company=self.company)

		self.assertIn(doc.name, {row["name"] for row in rows})

	def test_builds_default_profile_name_from_company_abbr(self):
		company_doc = frappe.get_doc("Company", self.company)
		self.assertEqual(
			_build_default_branding_profile_name(company_doc),
			"Default Branding Profile - CBPT",
		)

	def test_ensure_default_branding_profile_creates_company_default(self):
		doc = ensure_default_branding_profile(self.company)

		self.assertEqual(doc.company, self.company)
		self.assertEqual(doc.profile_name, "Default Branding Profile - CBPT")
		self.assertEqual(int(doc.is_default), 1)

	def test_ensure_default_branding_profile_is_idempotent(self):
		first = ensure_default_branding_profile(self.company)
		second = ensure_default_branding_profile(self.company)

		self.assertEqual(first.name, second.name)
		self.assertEqual(
			frappe.db.count("Crispy Branding Profile", {"company": self.company, "is_default": 1}),
			1,
		)

	def test_ensure_default_branding_profile_promotes_existing_conventional_profile(self):
		doc = ensure_default_branding_profile(self.company)
		doc.db_set("is_default", 0, update_modified=False)
		doc.reload()

		out = ensure_default_branding_profile(self.company)

		self.assertEqual(out.name, doc.name)
		self.assertEqual(int(frappe.db.get_value("Crispy Branding Profile", doc.name, "is_default")), 1)
		self.assertEqual(
			frappe.db.count("Crispy Branding Profile", {"company": self.company}),
			1,
		)

	def test_ensure_default_branding_profiles_for_all_companies_backfills_existing_companies(self):
		second_company = self._ensure_company(name="CBP Test Company 2", abbr="CBP2")

		created = ensure_default_branding_profiles_for_all_companies()

		self.assertIn(
			frappe.db.get_value(
				"Crispy Branding Profile", {"company": self.company, "is_default": 1}, "name"
			),
			created,
		)
		self.assertIn(
			frappe.db.get_value(
				"Crispy Branding Profile", {"company": second_company, "is_default": 1}, "name"
			),
			created,
		)

	def test_company_after_insert_provisions_default_branding_profile(self):
		company_name = self._ensure_company(name="CBP Hook Company", abbr="CBPH", create_only=True)
		company_doc = frappe.get_doc("Company", company_name)

		on_company_after_insert(company_doc)

		self.assertTrue(
			frappe.db.exists(
				"Crispy Branding Profile",
				{"company": company_name, "profile_name": "Default Branding Profile - CBPH", "is_default": 1},
			)
		)

	def test_after_install_provisions_defaults_for_all_existing_companies(self):
		second_company = self._ensure_company(name="CBP Install Company", abbr="CBPI")

		after_install()

		self.assertTrue(
			frappe.db.exists(
				"Crispy Branding Profile",
				{"company": self.company, "profile_name": "Default Branding Profile - CBPT", "is_default": 1},
			)
		)
		self.assertTrue(
			frappe.db.exists(
				"Crispy Branding Profile",
				{
					"company": second_company,
					"profile_name": "Default Branding Profile - CBPI",
					"is_default": 1,
				},
			)
		)

	def test_backfill_patch_provisions_defaults_for_all_existing_companies(self):
		second_company = self._ensure_company(name="CBP Patch Company", abbr="CBPP")

		backfill_default_branding_profiles()

		self.assertTrue(
			frappe.db.exists(
				"Crispy Branding Profile",
				{"company": self.company, "profile_name": "Default Branding Profile - CBPT", "is_default": 1},
			)
		)
		self.assertTrue(
			frappe.db.exists(
				"Crispy Branding Profile",
				{
					"company": second_company,
					"profile_name": "Default Branding Profile - CBPP",
					"is_default": 1,
				},
			)
		)

	def _ensure_company(self, name="CBP Test Company", abbr="CBPT", create_only=False):
		company = name
		if not create_only:
			existing = frappe.get_all("Company", filters={"abbr": abbr}, pluck="name", limit=1)
			if existing:
				return existing[0]

		if not frappe.db.exists("Company", company):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": company,
					"abbr": abbr,
					"default_currency": "KWD",
				}
			).insert(ignore_permissions=True)
		return company

	def _new_profile(self, **overrides):
		values = {
			"doctype": "Crispy Branding Profile",
			"profile_name": "CBP Test Profile",
			"company": self.company,
			"is_default": 0,
			"code_only": 0,
			"custom_typst_code": "",
			"page_size": "A4",
			"orientation": "portrait",
			"margin_top_mm": 20,
			"margin_bottom_mm": 20,
			"margin_left_mm": 20,
			"margin_right_mm": 20,
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
			"table_row_striping": 0,
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
			"enable_qr_code": 0,
			"qr_code_size_mm": 20,
			"qr_dx_mm": 0,
			"qr_dy_mm": 0,
		}
		values.update(overrides)
		return frappe.get_doc(values)

	def _insert_profile(self, **overrides):
		doc = self._new_profile(**overrides)
		doc.insert(ignore_permissions=True)
		return doc
