from __future__ import annotations

import frappe
from frappe.model.rename_doc import rename_doc
from frappe.tests.utils import FrappeTestCase

from crispy_print.crispy_print.doctype.crispy_template.crispy_template import build_template_id
from crispy_print.patches.post_model_sync.canonicalize_crispy_template_ids import execute


class TestCanonicalizeCrispyTemplateIdsPatch(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.company = self._ensure_company()
		self._delete_test_records()

	def tearDown(self):
		self._delete_test_records()
		frappe.db.rollback()

	def test_renames_legacy_template_and_updates_template_name(self):
		source = self._insert_format("Patch Migration Source")
		template = self._insert_template("Patch Migration Legacy Template", source.name)
		legacy_name = "patch_migration_legacy_template"
		canonical_id = build_template_id(source.name, self.company, template.version)
		self._rename_template(template.name, legacy_name)

		execute()
		execute()

		self.assertFalse(frappe.db.exists("Crispy Template", legacy_name))
		self.assertTrue(frappe.db.exists("Crispy Template", canonical_id))
		self.assertEqual(
			frappe.db.get_value("Crispy Template", canonical_id, "template_name"),
			canonical_id,
		)

	def test_renaming_preserves_existing_issued_document_link(self):
		source = self._insert_format("Patch Migration Linked Source")
		template = self._insert_template("Patch Migration Linked Template", source.name)
		legacy_name = "patch_migration_linked_template"
		canonical_id = build_template_id(source.name, self.company, template.version)
		self._rename_template(template.name, legacy_name)
		issued = self._insert_issued_document(source.name, legacy_name, template.version)

		execute()

		self.assertEqual(
			frappe.db.get_value("Crispy Issued Document", issued.name, "crispy_template"),
			canonical_id,
		)

	def test_collision_fails_without_overwriting_target(self):
		source = self._insert_format("Patch Migration Collision Source")
		template = self._insert_template("Patch Migration Collision Legacy", source.name)
		legacy_name = "patch_migration_collision_legacy"
		canonical_id = build_template_id(source.name, self.company, template.version)
		self._rename_template(template.name, legacy_name)
		collision = self._insert_template(
			"Patch Migration Collision Target",
			source.name,
			status="Draft",
			is_active=0,
		)
		self._rename_template(collision.name, canonical_id)
		frappe.db.set_value(
			"Crispy Template", canonical_id, "version", template.version, update_modified=False
		)

		with self.assertRaises(frappe.ValidationError) as context:
			execute()

		message = str(context.exception)
		self.assertIn(legacy_name, message)
		self.assertIn(canonical_id, message)
		self.assertIn("database backup", message)
		self.assertTrue(frappe.db.exists("Crispy Template", legacy_name))
		self.assertTrue(frappe.db.exists("Crispy Template", canonical_id))
		self.assertEqual(
			frappe.db.get_value("Crispy Template", canonical_id, "source_crispy_format"),
			source.name,
		)

	def _insert_template(
		self,
		template_name: str,
		source_format: str,
		*,
		status: str = "Approved",
		is_active: int = 1,
	):
		template = frappe.get_doc(
			{
				"doctype": "Crispy Template",
				"template_name": template_name,
				"source_crispy_format": source_format,
				"company": self.company,
				"status": status,
				"is_active": is_active,
			}
		)
		template.insert(ignore_permissions=True)
		return template

	def _insert_format(self, name: str):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": name,
				"company": self.company,
				"crispy_format_type": "DocType",
				"doc_type": "DocType",
				"module": "Crispy Print",
				"layout_json": '{"sections":[]}',
			}
		)
		doc.insert(ignore_permissions=True)
		return doc

	def _insert_issued_document(self, source_format: str, template_name: str, template_version: str):
		doc = frappe.get_doc(
			{
				"doctype": "Crispy Issued Document",
				"source_doctype": "DocType",
				"source_docname": "DocType",
				"crispy_format": source_format,
				"crispy_template": template_name,
				"crispy_template_version": template_version,
			}
		)
		doc.flags.allow_cid_backend_insert = True
		doc.insert(ignore_permissions=True)
		return doc

	def _rename_template(self, source: str, target: str) -> None:
		rename_doc(
			"Crispy Template",
			source,
			target,
			force=True,
			ignore_permissions=True,
		)
		frappe.db.set_value("Crispy Template", target, "template_name", source, update_modified=False)

	def _ensure_company(self) -> str:
		name = "Patch Migration Company"
		if not frappe.db.exists("Company", name):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": name,
					"abbr": "PMIG",
					"default_currency": "KWD",
				}
			).insert(ignore_permissions=True)
		return name

	def _delete_test_records(self) -> None:
		frappe.db.delete("Crispy Issued Document", {"crispy_format": ["like", "Patch Migration%"]})
		frappe.db.delete("Crispy Template", {"source_crispy_format": ["like", "Patch Migration%"]})
		frappe.db.delete("Crispy Template", {"name": ["like", "patch_migration_%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Patch Migration%"]})
