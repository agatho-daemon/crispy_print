# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import json
import re
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_to_date, now_datetime

from crispy_print.api.v1.templates import get_active_crispy_templates_for_render
from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
	get_publish_preview,
	publish_crispy_template,
	resolve_active_crispy_template,
)
from crispy_print.install import ensure_designer_role
from crispy_print.permissions import DESIGNER_ROLE
from crispy_print.template_resolution import (
	TemplateRenderContext,
	is_effective_template_row,
	template_target_filters,
	validate_template_render_context,
)


class TestCrispyTemplate(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company = frappe.db.get_value("Company", {}, "name")
		if not self.company:
			self.skipTest("No Company records available")
		self._delete_test_records()

	def tearDown(self):
		frappe.set_user("Administrator")
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
			self._template_id("CT Test Template", "1.0"),
		)
		self.assertEqual(template.template_name, template.name)
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
		self.assertEqual(template.snapshot_hash_version, "v2")
		self.assertEqual(template.zebra_version, "0.1.0")
		self.assertEqual(template.barcode_symbology, "QR Code")
		self.assertEqual(template.snapshot_hash, template.compute_snapshot_hash())

	def test_report_template_rejects_missing_generated_typst_code(self):
		source = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "CT Test Report Missing Typst",
				"company": self.company,
				"crispy_format_type": "Report",
				"module": "Crispy Print",
				"report_scope": "Selected Reports",
				"report_renderer": "general_ledger",
				"report": [{"report": "General Ledger"}],
				"layout_json": json.dumps({"sections": []}),
				"presentation_settings": json.dumps({"report": {"mode": "basic"}}),
				"raw_typst": 0,
				"typst_code": "",
			}
		).insert(ignore_permissions=True)

		with self.assertRaisesRegex(frappe.ValidationError, "Generated Typst Code is required"):
			publish_crispy_template(source.name)

	def test_legacy_v1_snapshot_hash_still_validates_after_v2_fields_exist(self):
		source = self._insert_format("CT Test Source Legacy Hash")
		template = self._insert_template(
			template_name="CT Test Legacy Hash",
			source_crispy_format=source.name,
			company=self.company,
		)
		v1_fields = template.snapshot_hash_version
		template.snapshot_hash_version = "v1"
		template.snapshot_hash = template.compute_snapshot_hash()
		template.flags.allow_template_state_transition = True
		template.save(ignore_permissions=True)
		v1_hash = template.snapshot_hash

		template.reload()
		template.notes = "legacy hash note"
		template.save(ignore_permissions=True)

		self.assertEqual(v1_fields, "v2")
		self.assertEqual(template.snapshot_hash_version, "v1")
		self.assertEqual(template.snapshot_hash, v1_hash)

	def test_v2_snapshot_hash_includes_render_facts(self):
		source = self._insert_format("CT Test Source V2 Hash")
		template = self._insert_template(
			template_name="CT Test V2 Hash",
			source_crispy_format=source.name,
			company=self.company,
		)
		original_hash = template.snapshot_hash

		template.flags.allow_template_state_transition = True
		template.zebra_version = "0.2.0"

		self.assertNotEqual(template.compute_snapshot_hash(), original_hash)

	def test_get_typst_version_uses_cached_compile_helper_and_preserves_empty_fallback(self):
		from crispy_print.crispy_print.doctype.crispy_template.crispy_template import get_typst_version

		with mock.patch(
			"crispy_print.api.v1.compile.get_cached_typst_version", return_value="typst 0.15.2"
		) as cached_version:
			self.assertEqual(get_typst_version(), "typst 0.15.2")

		cached_version.assert_called_once()

		with mock.patch(
			"crispy_print.api.v1.compile.get_cached_typst_version", side_effect=Exception("missing")
		):
			self.assertEqual(get_typst_version(), "")

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
			self._template_id("CT Test Versioned Template", "1.1"),
		)
		self.assertEqual(second.template_name, second.name)

	def test_template_cannot_be_deleted_through_document_api(self):
		source = self._insert_format("CT Test Source Delete Guard")
		template = self._insert_template(
			template_name="CT Test Delete Guard",
			source_crispy_format=source.name,
			company=self.company,
		)

		with self.assertRaises(frappe.PermissionError):
			frappe.delete_doc("Crispy Template", template.name, ignore_permissions=True)

		self.assertTrue(frappe.db.exists("Crispy Template", template.name))

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

		self.assertEqual(preview["next_version"], "1.0")
		self.assertEqual(preview["template_name"], self._template_id(source.name, "1.0"))
		self.assertEqual(preview["template_id"], self._template_id(source.name, "1.0"))

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

	def test_publish_preview_returns_read_only_template_history_and_next_hash(self):
		source = self._insert_format("CT Test Source History")
		first = publish_crispy_template(
			source.name,
			version_bump="minor",
			make_active=True,
			notes="Initial approval",
		)
		second = publish_crispy_template(
			source.name,
			version_bump="minor",
			make_active=True,
			notes="Updated approval",
		)

		preview = get_publish_preview(source.name, version_bump="minor")

		self.assertEqual(preview["next_version"], "1.2")
		self.assertEqual(len(preview["snapshot_hash"]), 64)
		self.assertEqual([row["name"] for row in preview["history"][:2]], [second["name"], first["name"]])
		self.assertEqual(preview["history"][0]["notes"], "Updated approval")
		self.assertEqual(preview["history"][0]["snapshot_hash"], second["snapshot_hash"])
		self.assertEqual(preview["history"][1]["is_active"], 0)

	def test_publish_freezes_exact_custom_qr_field_order(self):
		source = self._insert_format("CT Test Source Custom QR Freeze")
		original_fields = ["name", "posting_date", "customer_name", "grand_total"]
		source.presentation_settings = json.dumps(
			{
				"qr": {
					"enabled": True,
					"sourceMode": "custom",
					"fields": original_fields,
				}
			}
		)
		source.save(ignore_permissions=True)

		result = publish_crispy_template(source.name, version_bump="minor", make_active=True)
		template = frappe.get_doc("Crispy Template", result["name"])
		frozen_before = json.loads(template.presentation_settings_json)

		source.presentation_settings = json.dumps(
			{
				"qr": {
					"enabled": True,
					"sourceMode": "custom",
					"fields": ["grand_total", "name"],
				}
			}
		)
		source.save(ignore_permissions=True)
		template.reload()

		self.assertEqual(frozen_before["qr"]["fields"], original_fields)
		self.assertEqual(json.loads(template.presentation_settings_json)["qr"]["fields"], original_fields)

	def test_frozen_legacy_basic_template_keeps_legacy_snapshot(self):
		source = self._insert_format("CT Test Source Legacy Basic Frozen")
		# Existing editable formats reject this mode, so emulate a template
		# published before Custom Document QR replaced Basic QR.
		frappe.db.set_value(
			"Crispy Format",
			source.name,
			"presentation_settings",
			json.dumps(
				{
					"qr": {
						"enabled": True,
						"sourceMode": "basic",
						"fields": ["timestamp", "name"],
					}
				}
			),
			update_modified=False,
		)
		template = self._insert_template(
			template_name="CT Test Legacy Basic Frozen",
			source_crispy_format=source.name,
			company=self.company,
		)

		settings = json.loads(template.presentation_settings_json)
		self.assertEqual(settings["qr"]["sourceMode"], "basic")
		self.assertEqual(settings["qr"]["fields"], ["timestamp", "name"])

	def test_designer_can_publish_template_from_writable_format(self):
		ensure_designer_role()
		source = self._insert_format("CT Test Source Designer Publish")
		self._ensure_user("ct-test-designer@example.com", [DESIGNER_ROLE])
		frappe.set_user("ct-test-designer@example.com")

		result = publish_crispy_template(source.name, version_bump="minor", make_active=True)

		self.assertEqual(result["source_branding_profile"], None)
		self.assertEqual(result["company"], self.company)
		self.assertTrue(frappe.db.exists("Crispy Template", result["name"]))

	def test_non_designer_without_format_write_cannot_publish_template(self):
		source = self._insert_format("CT Test Source Designer Blocked")
		self._ensure_user("ct-test-viewer@example.com", ["Desk User"])
		frappe.set_user("ct-test-viewer@example.com")

		with self.assertRaises(frappe.PermissionError):
			publish_crispy_template(source.name, version_bump="minor", make_active=True)

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

	def test_duplicate_template_for_company_preserves_frozen_snapshot(self):
		from crispy_print.api.v1.templates import duplicate_crispy_template_for_company

		other_company = self._get_other_company()
		if not other_company:
			self.skipTest("Need at least two Company records")
		source = self._insert_format("CT Test Source Duplicate Snapshot")
		result = publish_crispy_template(source.name, version_bump="minor", make_active=True)
		template = frappe.get_doc("Crispy Template", result["name"])
		original_layout = template.layout_json
		original_settings = template.presentation_settings_json
		original_typst_code = template.typst_code

		source.layout_json = json.dumps({"sections": [{"label": "Changed", "columns": []}]})
		source.presentation_settings = json.dumps({"page": {"size": "Letter"}})
		source.typst_code = "#text[changed]"
		source.save(ignore_permissions=True)

		duplicate = duplicate_crispy_template_for_company(
			template.name,
			other_company,
			clone_mode="snapshot",
			make_active=0,
		)
		cloned_template = frappe.get_doc("Crispy Template", duplicate["template"]["name"])
		cloned_format = frappe.get_doc("Crispy Format", duplicate["cloned_format"])
		cloned_settings = json.loads(cloned_template.presentation_settings_json)
		cloned_format_settings = json.loads(cloned_format.presentation_settings)

		self.assertEqual(duplicate["clone_mode"], "snapshot")
		self.assertEqual(cloned_template.company, other_company)
		self.assertEqual(cloned_template.layout_json, original_layout)
		self.assertEqual(cloned_settings["page"], json.loads(original_settings)["page"])
		self.assertEqual(cloned_settings["branding"]["company"], other_company)
		self.assertEqual(cloned_template.typst_code, original_typst_code)
		self.assertEqual(cloned_format.company, other_company)
		self.assertEqual(cloned_format.layout_json, original_layout)
		self.assertEqual(cloned_format_settings["page"], json.loads(original_settings)["page"])
		self.assertEqual(cloned_format_settings["branding"]["company"], other_company)
		self.assertEqual(cloned_format.typst_code, original_typst_code)

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
		other_source = self._insert_format("CT Test Source Explicit Other")
		first = self._insert_template(
			template_name="CT Test Explicit",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)
		second = self._insert_template(
			template_name="CT Test Explicit Other",
			source_crispy_format=other_source.name,
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

	def test_template_render_context_requires_exactly_one_target(self):
		with self.assertRaises(frappe.ValidationError):
			validate_template_render_context(TemplateRenderContext())

		with self.assertRaises(frappe.ValidationError):
			validate_template_render_context(
				TemplateRenderContext(source_doctype="Sales Invoice", source_report="General Ledger")
			)

	def test_template_target_filters_are_shared_for_all_targets(self):
		self.assertEqual(
			template_target_filters(TemplateRenderContext(source_doctype="Sales Invoice")),
			{"crispy_format_type": "DocType", "source_doctype": "Sales Invoice"},
		)
		self.assertEqual(
			template_target_filters(TemplateRenderContext(source_report="General Ledger")),
			{"crispy_format_type": "Report", "source_report": "General Ledger"},
		)
		self.assertEqual(
			template_target_filters(TemplateRenderContext(source_contract="NDA")),
			{"crispy_format_type": "Contract", "source_contract": "NDA"},
		)

	def test_template_name_filter_is_opt_in_for_named_resolution(self):
		context = TemplateRenderContext(source_doctype="Sales Invoice", template_name="Template A")

		self.assertNotIn("template_name", template_target_filters(context))
		self.assertEqual(
			template_target_filters(context, include_template_name=True)["template_name"],
			"Template A",
		)

	def test_template_effective_date_helper_rejects_future_and_expired_rows(self):
		now = now_datetime()

		self.assertFalse(is_effective_template_row({"effective_from": add_to_date(now, days=1)}, now=now))
		self.assertFalse(is_effective_template_row({"effective_to": add_to_date(now, days=-1)}, now=now))
		self.assertTrue(
			is_effective_template_row(
				{
					"effective_from": add_to_date(now, days=-1),
					"effective_to": add_to_date(now, days=1),
				},
				now=now,
			)
		)

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
			template_name=company_template.name,
		)

		self.assertEqual(resolved["name"], company_template.name)
		self.assertEqual(resolved["resolution_reason"], "company")

	def test_active_template_list_and_resolver_share_company_precedence(self):
		source = self._insert_format("CT Test Source List Resolve Parity")
		global_template = self._insert_template(
			template_name="CT Test List Resolve Parity",
			source_crispy_format=source.name,
			company="",
			status="Approved",
			is_active=1,
		)
		company_template = self._insert_template(
			template_name="CT Test List Resolve Parity",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)

		rows = get_active_crispy_templates_for_render(
			source_doctype="Sales Invoice",
			company=self.company,
		)
		resolved = resolve_active_crispy_template(
			source_doctype="Sales Invoice",
			company=self.company,
			template_name=company_template.name,
		)
		test_rows = [row for row in rows if row["name"] in {company_template.name, global_template.name}]

		self.assertEqual([row["name"] for row in test_rows], [company_template.name, global_template.name])
		self.assertEqual(resolved["name"], company_template.name)

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
			template_name=global_template.name,
		)

		self.assertEqual(resolved["name"], global_template.name)
		self.assertEqual(resolved["resolution_reason"], "global")

	def test_resolver_returns_frozen_render_payload(self):
		source = self._insert_format("CT Test Source Frozen Payload")
		template = self._insert_template(
			template_name="CT Test Frozen Payload",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)

		frappe.db.set_value("Crispy Format", source.name, "typst_code", "#doc.changed")
		frappe.db.set_value(
			"Crispy Format",
			source.name,
			"presentation_settings",
			json.dumps({"page": {"size": "Letter"}}),
		)
		resolved = resolve_active_crispy_template(
			source_doctype="Sales Invoice",
			company=self.company,
			template=template.name,
		)
		payload = resolved["render_payload"]

		self.assertEqual(payload["crispy_template"], template.name)
		self.assertEqual(payload["crispy_template_version"], template.version)
		self.assertEqual(payload["template_hash"], template.snapshot_hash)
		self.assertEqual(payload["typst_code"], "#doc.name")
		self.assertEqual(json.loads(payload["presentation_settings"]), {"page": {"size": "A4"}})

	def test_resolver_raises_for_missing_active_template(self):
		self.assertRaises(
			frappe.ValidationError,
			resolve_active_crispy_template,
			source_doctype="Sales Invoice",
			company=self.company,
			template_name="CT Test Missing Active",
		)

	def test_explicit_template_validation_rejects_inactive_template(self):
		source = self._insert_format("CT Test Source Explicit Inactive")
		template = self._insert_template(
			template_name="CT Test Explicit Inactive",
			source_crispy_format=source.name,
			company=self.company,
			status="Approved",
			is_active=1,
		)
		frappe.db.set_value("Crispy Template", template.name, "is_active", 0, update_modified=False)

		self.assertRaises(
			frappe.ValidationError,
			resolve_active_crispy_template,
			source_doctype="Sales Invoice",
			company=self.company,
			template=template.name,
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

	def test_rejects_mutating_frozen_render_facts_after_insert(self):
		source = self._insert_format("CT Test Source Immutable Render Facts")
		template = self._insert_template(
			template_name="CT Test Immutable Render Facts",
			source_crispy_format=source.name,
			company=self.company,
		)

		template.zebra_version = "0.2.0"

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

	def _ensure_user(self, email: str, roles: list[str]) -> str:
		if frappe.db.exists("User", email):
			user = frappe.get_doc("User", email)
			user.enabled = 1
			existing_roles = {row.role for row in user.roles}
		else:
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": "CT Test",
					"last_name": "Designer",
					"send_welcome_email": 0,
					"enabled": 1,
				}
			)
			existing_roles = set()

		for role in roles:
			if role not in existing_roles:
				user.append("roles", {"role": role})
		user.save(ignore_permissions=True)
		return email

	def _company_abbr(self, company: str) -> str:
		return frappe.db.get_value("Company", company, "abbr") or company

	def _template_id(self, template_name: str, version: str, company: str | None = None) -> str:
		template_key = re.sub(r"[^a-z0-9]+", "_", template_name.lower()).strip("_")
		company_abbr = re.sub(
			r"[^a-z0-9]+",
			"_",
			self._company_abbr(company or self.company).lower(),
		).strip("_")
		return f"{template_key}-{company_abbr}-v{version}"

	def _delete_test_records(self):
		frappe.db.delete("Crispy Template", {"source_crispy_format": ["like", "CT Test Source%"]})
		frappe.db.delete("Crispy Template", {"name": ["like", "ct_test_%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "CT Test Source%"]})
		frappe.db.delete("Crispy Typst Block", {"block_key": ["like", "ct_test_%"]})
		frappe.db.delete("Crispy Branding Profile", {"profile_name": ["like", "CT Test%"]})
