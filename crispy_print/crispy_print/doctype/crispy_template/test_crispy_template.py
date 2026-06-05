# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	get_publish_preview,
	publish_crispy_template,
	resolve_active_crispy_template,
)


class TestCrispyTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company = frappe.db.get_value("Company", {}, "name")
		if not self.company:
			self.skipTest("No Company records available")
		self._delete_test_records()

	def tearDown(self):
		self._delete_test_records()
		frappe.db.rollback()

	def test_insert_derives_source_snapshot_hash_and_first_version(self):
		source = self._insert_format("CT Test Source 1")

		template = self._insert_template(
			template_name="CT Test Template",
			source_crispy_format=source.name,
			company=self.company,
		)

		self.assertEqual(template.version, "1.0")
		self.assertEqual(
			template.name,
			f"CT Test Template - {self._company_abbr(self.company)} - v1.0",
		)
		self.assertEqual(template.crispy_format_type, "DocType")
		self.assertEqual(template.source_doctype, "Sales Invoice")
		self.assertEqual(template.company, self.company)
		self.assertEqual(template.layout_json, source.layout_json)
		self.assertEqual(
			json.loads(template.presentation_settings_json or "{}"),
			json.loads(source.presentation_settings or "{}"),
		)
		self.assertEqual(template.doc_header, source.doc_header)
		self.assertEqual(template.doc_footer, source.doc_footer)
		self.assertEqual(template.typst_preamble, source.typst_preamble)
		self.assertEqual(template.typst_code, source.typst_code)
		self.assertEqual(template.snapshot_hash, template.compute_snapshot_hash())

	def test_insert_increments_version_for_same_template_scope(self):
		source = self._insert_format("CT Test Source 2")

		first = self._insert_template(
			template_name="CT Test Versioned Template",
			source_crispy_format=source.name,
			company=self.company,
		)
		second = self._insert_template(
			template_name="CT Test Versioned Template",
			source_crispy_format=source.name,
			company=self.company,
		)

		self.assertEqual(first.version, "1.0")
		self.assertEqual(second.version, "1.1")
		self.assertEqual(
			second.name,
			f"CT Test Versioned Template - {self._company_abbr(self.company)} - v1.1",
		)

	def test_major_version_bump_resets_minor_version(self):
		source = self._insert_format("CT Test Source Major")

		first = self._insert_template(
			template_name="CT Test Major Versioned Template",
			source_crispy_format=source.name,
			company=self.company,
		)
		second = self._insert_template(
			template_name="CT Test Major Versioned Template",
			source_crispy_format=source.name,
			company=self.company,
			version_bump="major",
		)

		self.assertEqual(first.version, "1.0")
		self.assertEqual(second.version, "2.0")

	def test_publish_preview_returns_generated_template_id(self):
		source = self._insert_format("CT Test Source Preview")

		preview = get_publish_preview(source.name, version_bump="minor")

		self.assertEqual(preview["template_name"], source.name)
		self.assertEqual(preview["next_version"], "1.0")
		self.assertEqual(
			preview["template_id"],
			f"{source.name} - {self._company_abbr(self.company)} - v1.0",
		)

	def test_publish_preview_rejects_mismatched_explicit_company(self):
		other_company = self._get_other_company()
		if not other_company:
			self.skipTest("Another Company record is required")
		source = self._insert_format("CT Test Source Preview Company")

		with self.assertRaises(frappe.ValidationError):
			get_publish_preview(source.name, version_bump="minor", company=other_company)

	def test_publish_supersedes_previous_active_template(self):
		source = self._insert_format("CT Test Source Publish")

		first = publish_crispy_template(source.name, version_bump="minor", make_active=True)
		second = publish_crispy_template(source.name, version_bump="minor", make_active=True)
		first_doc = frappe.get_doc("Crispy Template", first["name"])
		second_doc = frappe.get_doc("Crispy Template", second["name"])

		self.assertEqual(first["version"], "1.0")
		self.assertEqual(second["version"], "1.1")
		self.assertEqual(first_doc.status, "Superseded")
		self.assertEqual(first_doc.superseded_by, second_doc.name)
		self.assertEqual(first_doc.is_active, 0)
		self.assertEqual(second_doc.status, "Approved")
		self.assertEqual(second_doc.is_active, 1)

	def test_publish_requires_source_format_company(self):
		source = self._insert_format("CT Test Source No Company")
		frappe.db.set_value("Crispy Format", source.name, "company", "", update_modified=False)

		with self.assertRaises(frappe.ValidationError):
			get_publish_preview(source.name, version_bump="minor")

	def test_publish_rejects_mismatched_branding_profile_company(self):
		other_company = self._get_other_company()
		if not other_company:
			self.skipTest("Another Company record is required")
		profile = frappe.get_doc(
			{
				"doctype": "Crispy Branding Profile",
				"profile_name": "CT Test Other Company Profile",
				"company": other_company,
			}
		)
		profile.insert(ignore_permissions=True)
		source = self._insert_format("CT Test Source Branding Mismatch")
		source.presentation_settings = json.dumps(
			{
				"source": "branding_profile",
				"branding": {
					"profile": profile.name,
					"company": self.company,
					"logo": {"company": self.company},
				},
			}
		)
		source.save(ignore_permissions=True)

		with self.assertRaises(frappe.ValidationError):
			publish_crispy_template(source.name, version_bump="minor", make_active=True)

	def test_publish_hydrates_company_scoped_typst_block_snapshot(self):
		block_key = "ct_test_publish_block"
		global_block = frappe.get_doc(
			{
				"doctype": "Crispy Typst Block",
				"block_name": "CT Test Publish Global Block",
				"block_key": block_key,
				"enabled": 1,
				"typst_code": "#text[global]",
			}
		)
		global_block.append("applicable_documents", {"document_type": "Sales Invoice"})
		global_block.insert(ignore_permissions=True)
		company_block = frappe.get_doc(
			{
				"doctype": "Crispy Typst Block",
				"block_name": "CT Test Publish Company Block",
				"block_key": block_key,
				"company": self.company,
				"enabled": 1,
				"typst_code": "#text[company]",
			}
		)
		company_block.append("applicable_documents", {"document_type": "Sales Invoice"})
		company_block.insert(ignore_permissions=True)
		source = self._insert_format("CT Test Source CTB Snapshot")
		source.layout_json = json.dumps(
			{
				"sections": [
					{
						"columns": [
							{
								"fields": [
									{
										"fieldtype": "Crispy Typst Block",
										"fieldname": "_ctb",
										"crispy_typst_block": block_key,
									}
								]
							}
						]
					}
				]
			}
		)
		source.save(ignore_permissions=True)

		result = publish_crispy_template(source.name, version_bump="minor", make_active=True)
		template = frappe.get_doc("Crispy Template", result["name"])
		layout = json.loads(template.layout_json)
		field = layout["sections"][0]["columns"][0]["fields"][0]

		self.assertEqual(field["crispy_typst_block_code"], "#text[company]")
		self.assertEqual(field["crispy_typst_block_name"], "CT Test Publish Company Block")

	def test_publish_freezes_source_snapshot_fields(self):
		source = self._insert_format("CT Test Source Frozen Snapshot")
		result = publish_crispy_template(source.name, version_bump="minor", make_active=True)
		template = frappe.get_doc("Crispy Template", result["name"])
		original_layout = template.layout_json
		original_settings = template.presentation_settings_json
		original_typst_code = template.typst_code

		source.layout_json = json.dumps({"sections": [{"label": "Changed", "columns": []}]})
		source.presentation_settings = json.dumps({"page": {"size": "Letter"}})
		source.typst_code = "#text[changed]"
		source.save(ignore_permissions=True)
		template.reload()

		self.assertEqual(template.layout_json, original_layout)
		self.assertEqual(template.presentation_settings_json, original_settings)
		self.assertEqual(template.typst_code, original_typst_code)

	def test_rejects_duplicate_active_template_scope(self):
		source = self._insert_format("CT Test Source Active Unique")
		self._insert_template(
			template_name="CT Test Active Unique",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)

		self.assertRaises(
			frappe.ValidationError,
			self._insert_template,
			template_name="CT Test Active Unique",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)

	def test_resolver_prefers_explicit_template(self):
		source = self._insert_format("CT Test Source Explicit")
		first = self._insert_template(
			template_name="CT Test Explicit",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)
		second = self._insert_template(
			template_name="CT Test Explicit Other",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)

		resolved = resolve_active_crispy_template(
			source_doctype="Sales Invoice",
			company=self.company,
			template=second.name,
		)

		self.assertEqual(resolved["name"], second.name)
		self.assertEqual(resolved["resolution_reason"], "explicit")
		self.assertNotEqual(resolved["name"], first.name)

	def test_resolver_prefers_company_template_over_global(self):
		source = self._insert_format("CT Test Source Company Resolve")
		self._insert_template(
			template_name="CT Test Company Resolve",
			source_crispy_format=source.name,
			company="",
			status="Approved",
			is_active=1,
		)
		company_template = self._insert_template(
			template_name="CT Test Company Resolve",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)

		resolved = resolve_active_crispy_template(
			source_doctype="Sales Invoice",
			company=self.company,
			template_name="CT Test Company Resolve",
		)

		self.assertEqual(resolved["name"], company_template.name)
		self.assertEqual(resolved["resolution_reason"], "company")

	def test_resolver_uses_global_fallback(self):
		source = self._insert_format("CT Test Source Global Resolve")
		global_template = self._insert_template(
			template_name="CT Test Global Resolve",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)
		frappe.db.set_value("Crispy Template", global_template.name, "company", "")

		resolved = resolve_active_crispy_template(
			source_doctype="Sales Invoice",
			company=self.company,
			template_name="CT Test Global Resolve",
		)

		self.assertEqual(resolved["name"], global_template.name)
		self.assertEqual(resolved["resolution_reason"], "global")

	def test_resolver_raises_for_missing_active_template(self):
		self.assertRaises(
			frappe.ValidationError,
			resolve_active_crispy_template,
			source_doctype="Sales Invoice",
			company=self.company,
			template_name="CT Test Missing Active",
		)

	def test_rejects_company_mismatch_with_source_format(self):
		other_company = self._get_other_company()
		if not other_company:
			self.skipTest("Need at least two Company records")
		source = self._insert_format("CT Test Source 3", company=self.company)

		doc = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": "CT Test Company Mismatch",
				"company": other_company,
				"source_crispy_format": source.name,
			}
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_approved_insert_sets_approval_metadata(self):
		source = self._insert_format("CT Test Source 4")

		template = self._insert_template(
			template_name="CT Test Approved Template",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
		)

		self.assertEqual(template.status, "Approved")
		self.assertEqual(template.approved_by, "Administrator")
		self.assertTrue(template.approved_at)

	def test_rejects_mutating_frozen_snapshot_after_insert(self):
		source = self._insert_format("CT Test Source 5")
		template = self._insert_template(
			template_name="CT Test Immutable Template",
			source_crispy_format=source.name,
			company=self.company,
		)

		template.typst_code = "#text[changed]"

		self.assertRaises(frappe.ValidationError, template.save)

	def _insert_template(self, version_bump: str | None = None, **values):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				**values,
			}
		)
		if version_bump:
			doc.flags.template_version_bump = version_bump
		doc.insert(ignore_permissions=True)
		return doc

	def _insert_format(self, name: str, company: str | None = None):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"company": company or self.company,
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"page": {"size": "A4"}}),
				"doc_header": "#let header_block = [Header]",
				"doc_footer": "#let footer_block = [Footer]",
				"typst_preamble": "#set text(size: 10pt)",
				"typst_code": "#doc.name",
				"pdf_standard": "PDF/A-3u",
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def _get_other_company(self) -> str | None:
		return frappe.db.get_value("Company", {"name": ["!=", self.company]}, "name")

	def _company_abbr(self, company: str) -> str:
		return frappe.db.get_value("Company", company, "abbr") or company

	def _delete_test_records(self):
		frappe.db.delete("Crispy Template", {"template_name": ["like", "CT Test%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "CT Test Source%"]})
		frappe.db.delete("Crispy Typst Block", {"block_key": ["like", "ct_test_%"]})
		frappe.db.delete("Crispy Branding Profile", {"profile_name": ["like", "CT Test%"]})
