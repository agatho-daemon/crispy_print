# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1 import get_applicable_typst_blocks as get_applicable_typst_blocks_api
from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	get_applicable_typst_blocks,
	get_typst_block,
	resolve_layout_typst_blocks,
)


class TestCrispyTypstBlock(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self._delete_test_blocks()

	def tearDown(self):
		self._delete_test_blocks()
		frappe.db.rollback()

	def test_rejects_invalid_block_key(self):
		doc = self._new_block(block_key="Invalid Key")

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_autoname_uses_block_key_and_version(self):
		doc = self._insert_block(
			block_key="cp_test_typst_block_doc_name",
			block_name="CP Test Invoice Header!",
		)

		self.assertEqual(doc.name, "cp_test_typst_block_doc_name-v1.0")

	def test_defaults_block_key_from_block_name(self):
		doc = self._insert_block(
			block_key="",
			block_name="CP Test Invoice Header!",
		)

		self.assertEqual(doc.block_key, "cp_test_invoice_header")
		self.assertEqual(doc.name, "cp_test_invoice_header-v1.0")

	def test_defaults_version_to_1_0(self):
		doc = self._insert_block(
			block_key="cp_test_typst_block_default_version",
			version="",
		)

		self.assertEqual(doc.version, "1.0")
		self.assertEqual(doc.name, "cp_test_typst_block_default_version-v1.0")

	def test_accepts_version_with_leading_v(self):
		doc = self._insert_block(
			block_key="cp_test_typst_block_leading_v_version",
			version="v1.2",
		)

		self.assertEqual(doc.version, "1.2")
		self.assertEqual(doc.name, "cp_test_typst_block_leading_v_version-v1.2")

	def test_normalizes_zero_patch_version(self):
		doc = self._insert_block(
			block_key="cp_test_typst_block_zero_patch_version",
			version="1.0.0",
		)

		self.assertEqual(doc.version, "1.0")
		self.assertEqual(doc.name, "cp_test_typst_block_zero_patch_version-v1.0")

	def test_rejects_invalid_version(self):
		doc = self._new_block(
			block_key="cp_test_typst_block_invalid_version",
			version="1.0.1",
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_autoname_adds_numeric_suffix_for_duplicate_id(self):
		company = self._ensure_company()
		first = self._insert_block(
			block_key="cp_test_typst_block_duplicate_id",
			block_name="CP Test Global Shared Header",
		)
		second = self._insert_block(
			block_key="cp_test_typst_block_duplicate_id",
			block_name="CP Test Company Shared Header",
			company=company,
		)

		self.assertEqual(first.name, "cp_test_typst_block_duplicate_id-v1.0")
		self.assertEqual(second.name, "cp_test_typst_block_duplicate_id-v1.0-2")

	def test_rejects_duplicate_applicable_documents(self):
		doc = self._new_block(
			block_key="cp_test_typst_block_duplicate_docs",
			applicable_documents=["Sales Invoice", "Sales Invoice"],
		)

		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_empty_applicable_documents_applies_globally(self):
		doc = self._insert_block(block_key="cp_test_typst_block_global")

		self.assertTrue(doc.applies_to_doctype("Sales Invoice"))
		self.assertTrue(doc.applies_to_doctype("Purchase Order"))
		self.assertEqual(doc.get_applicable_document_types(), [])

	def test_specific_document_type_restricts_applicability(self):
		doc = self._insert_block(
			block_key="cp_test_typst_block_sales_invoice",
			applicable_documents=["Sales Invoice"],
		)

		self.assertTrue(doc.applies_to_doctype("Sales Invoice"))
		self.assertFalse(doc.applies_to_doctype("Purchase Invoice"))
		self.assertEqual(doc.get_applicable_document_types(), ["Sales Invoice"])

	def test_get_typst_block_looks_up_by_reference_key(self):
		doc = self._insert_block(block_key="cp_test_typst_block_lookup")

		result = get_typst_block("cp_test_typst_block_lookup")

		self.assertEqual(result.name, doc.name)
		self.assertEqual(result.block_key, "cp_test_typst_block_lookup")

	def test_get_applicable_typst_blocks_returns_global_and_matching_blocks(self):
		global_block = self._insert_block(block_key="cp_test_typst_block_query_global")
		matching_block = self._insert_block(
			block_key="cp_test_typst_block_query_matching",
			applicable_documents=["Sales Invoice"],
		)
		non_matching_block = self._insert_block(
			block_key="cp_test_typst_block_query_non_matching",
			applicable_documents=["Purchase Invoice"],
		)
		disabled_block = self._insert_block(
			block_key="cp_test_typst_block_query_disabled",
			enabled=0,
		)

		rows = get_applicable_typst_blocks("Sales Invoice")
		block_keys = {row["block_key"] for row in rows}

		self.assertIn(global_block.block_key, block_keys)
		self.assertIn(matching_block.block_key, block_keys)
		self.assertNotIn(non_matching_block.block_key, block_keys)
		self.assertNotIn(disabled_block.block_key, block_keys)

	def test_get_applicable_typst_blocks_can_include_disabled_blocks(self):
		disabled_block = self._insert_block(
			block_key="cp_test_typst_block_include_disabled",
			enabled=0,
		)

		rows = get_applicable_typst_blocks("Sales Invoice", enabled_only=False)
		block_keys = {row["block_key"] for row in rows}

		self.assertIn(disabled_block.block_key, block_keys)

	def test_company_scoped_blocks_override_global_blocks(self):
		company = self._ensure_company()
		global_block = self._insert_block(
			block_key="cp_test_typst_block_company_override",
			block_name="CP Test Global Override Block",
			typst_code="#text[global]",
		)
		company_block = self._insert_block(
			block_key="cp_test_typst_block_company_override",
			block_name="CP Test Company Override Block",
			company=company,
			typst_code="#text[company]",
		)

		global_rows = get_applicable_typst_blocks("Sales Invoice")
		company_rows = get_applicable_typst_blocks("Sales Invoice", company=company)
		global_by_key = {row["block_key"]: row for row in global_rows}
		company_by_key = {row["block_key"]: row for row in company_rows}

		self.assertEqual(global_by_key[global_block.block_key]["name"], global_block.name)
		self.assertEqual(company_by_key[company_block.block_key]["name"], company_block.name)
		self.assertEqual(company_by_key[company_block.block_key]["company"], company)

	def test_get_typst_block_prefers_company_specific_block(self):
		company = self._ensure_company(name="CTB Lookup Company", abbr="CTBL")
		global_block = self._insert_block(
			block_key="cp_test_typst_block_company_lookup",
			block_name="CP Test Global Lookup Block",
		)
		company_block = self._insert_block(
			block_key="cp_test_typst_block_company_lookup",
			block_name="CP Test Company Lookup Block",
			company=company,
		)

		self.assertEqual(get_typst_block(global_block.block_key).name, global_block.name)
		self.assertEqual(get_typst_block(company_block.block_key, company=company).name, company_block.name)

	def test_resolve_layout_typst_blocks_uses_company_override(self):
		company = self._ensure_company(name="CTB Resolve Company", abbr="CTBR")
		self._insert_block(
			block_key="cp_test_typst_block_company_resolve",
			block_name="CP Test Global Resolve Block",
			typst_code="#text[global]",
		)
		self._insert_block(
			block_key="cp_test_typst_block_company_resolve",
			block_name="CP Test Company Resolve Block",
			company=company,
			typst_code="#text[company]",
		)
		layout = {
			"sections": [
				{
					"columns": [
						{
							"fields": [
								{
									"fieldtype": "Crispy Typst Block",
									"crispy_typst_block": "cp_test_typst_block_company_resolve",
								}
							]
						}
					]
				}
			]
		}

		resolved = resolve_layout_typst_blocks(layout, "Sales Invoice", company=company)
		field = resolved["sections"][0]["columns"][0]["fields"][0]

		self.assertEqual(field["crispy_typst_block_name"], "CP Test Company Resolve Block")
		self.assertEqual(field["crispy_typst_block_code"], "#text[company]")

	def test_api_returns_applicable_enabled_blocks_with_code(self):
		global_block = self._insert_block(block_key="cp_test_typst_block_api_global")
		matching_block = self._insert_block(
			block_key="cp_test_typst_block_api_matching",
			applicable_documents=["Sales Invoice"],
		)
		self._insert_block(
			block_key="cp_test_typst_block_api_non_matching",
			applicable_documents=["Purchase Invoice"],
		)
		self._insert_block(
			block_key="cp_test_typst_block_api_disabled",
			enabled=0,
		)

		rows = get_applicable_typst_blocks_api("Sales Invoice")
		by_key = {row["block_key"]: row for row in rows}

		self.assertIn(global_block.block_key, by_key)
		self.assertIn(matching_block.block_key, by_key)
		self.assertNotIn("cp_test_typst_block_api_non_matching", by_key)
		self.assertNotIn("cp_test_typst_block_api_disabled", by_key)
		self.assertEqual(by_key[global_block.block_key]["typst_code"], global_block.typst_code)

	def test_api_filters_blocks_by_query(self):
		self._insert_block(
			block_key="cp_test_typst_block_api_query_match",
			block_name="CP Test Special Header",
		)
		self._insert_block(
			block_key="cp_test_typst_block_api_query_other",
			block_name="CP Test Other Block",
		)

		rows = get_applicable_typst_blocks_api("Sales Invoice", query="special")
		block_keys = {row["block_key"] for row in rows}

		self.assertIn("cp_test_typst_block_api_query_match", block_keys)
		self.assertNotIn("cp_test_typst_block_api_query_other", block_keys)

	def test_api_requires_read_permission(self):
		self._insert_block(block_key="cp_test_typst_block_api_permission")

		frappe.set_user("Guest")
		try:
			self.assertRaises(frappe.PermissionError, get_applicable_typst_blocks_api, "Sales Invoice")
		finally:
			frappe.set_user("Administrator")

	def test_resolve_layout_typst_blocks_hydrates_applicable_references(self):
		self._insert_block(
			block_key="cp_test_typst_block_resolve",
			block_name="CP Test Resolve Block",
			typst_code="#text[#doc.customer_name]",
			applicable_documents=["Sales Invoice"],
		)
		layout = {
			"sections": [
				{
					"columns": [
						{
							"fields": [
								{
									"fieldtype": "Crispy Typst Block",
									"fieldname": "_crispy_typst_block",
									"crispy_typst_block": "cp_test_typst_block_resolve",
								}
							]
						}
					]
				}
			]
		}

		resolved = resolve_layout_typst_blocks(layout, "Sales Invoice")
		field = resolved["sections"][0]["columns"][0]["fields"][0]

		self.assertEqual(field["crispy_typst_block_name"], "CP Test Resolve Block")
		self.assertEqual(field["crispy_typst_block_code"], "#text[#doc.customer_name]")
		self.assertNotIn("crispy_typst_block_code", layout["sections"][0]["columns"][0]["fields"][0])

	def test_resolve_layout_typst_blocks_clears_unavailable_references(self):
		self._insert_block(
			block_key="cp_test_typst_block_purchase_only",
			applicable_documents=["Purchase Invoice"],
		)
		self._insert_block(
			block_key="cp_test_typst_block_disabled_resolve",
			enabled=0,
		)
		layout = {
			"sections": [
				{
					"columns": [
						{
							"fields": [
								{
									"fieldtype": "Crispy Typst Block",
									"crispy_typst_block": "cp_test_typst_block_purchase_only",
									"crispy_typst_block_name": "Stale Name",
									"crispy_typst_block_code": "#text[stale]",
								},
								{
									"fieldtype": "Crispy Typst Block",
									"crispy_typst_block": "cp_test_typst_block_disabled_resolve",
									"crispy_typst_block_name": "Disabled Name",
									"crispy_typst_block_code": "#text[disabled]",
								},
								{
									"fieldtype": "Crispy Typst Block",
									"crispy_typst_block": "cp_test_typst_block_missing",
									"crispy_typst_block_name": "Missing Name",
									"crispy_typst_block_code": "#text[missing]",
								},
							]
						}
					]
				}
			]
		}

		resolved = resolve_layout_typst_blocks(layout, "Sales Invoice")
		fields = resolved["sections"][0]["columns"][0]["fields"]

		for field in fields:
			self.assertNotIn("crispy_typst_block_name", field)
			self.assertNotIn("crispy_typst_block_code", field)

	def _new_block(self, **overrides):
		block_key = overrides.pop("block_key", "cp_test_typst_block")
		applicable_documents = overrides.pop("applicable_documents", [])
		values = {
			"doctype": "Crispy Typst Block",
			"block_name": f"CP Test Typst Block {block_key}",
			"company": "",
			"block_key": block_key,
			"enabled": 1,
			"category": "Utility",
			"description": "Test Typst block",
			"typst_code": "#let test-block() = []",
		}
		values.update(overrides)

		doc = frappe.get_doc(values)
		for document_type in applicable_documents:
			doc.append("applicable_documents", {"document_type": document_type})

		return doc

	def _insert_block(self, **overrides):
		doc = self._new_block(**overrides)
		doc.insert(ignore_permissions=True)
		return doc

	def _ensure_company(self, name="CTB Test Company", abbr="CTBT"):
		existing = frappe.get_all("Company", filters={"abbr": abbr}, pluck="name", limit=1)
		if existing:
			return existing[0]

		if not frappe.db.exists("Company", name):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": name,
					"abbr": abbr,
					"default_currency": "KWD",
					"country": "Kuwait",
				}
			).insert(ignore_permissions=True)
		return name

	def _delete_test_blocks(self):
		names = frappe.get_all(
			"Crispy Typst Block",
			filters={"block_key": ["like", "cp_test_typst_block%"]},
			pluck="name",
		)
		for name in names:
			frappe.delete_doc("Crispy Typst Block", name, force=True, ignore_permissions=True)
