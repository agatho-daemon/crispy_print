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

	def _delete_test_blocks(self):
		names = frappe.get_all(
			"Crispy Typst Block",
			filters={"block_key": ["like", "cp_test_typst_block%"]},
			pluck="name",
		)
		for name in names:
			frappe.delete_doc("Crispy Typst Block", name, force=True, ignore_permissions=True)
