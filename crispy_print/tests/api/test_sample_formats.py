import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestSampleFormatCatalog(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Crispy Format", {"name": ["like", "Sample Sales Invoice Starter%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Sample Format%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Core V1 Sample%"]})
		frappe.db.commit()

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("Crispy Format", {"name": ["like", "Sample Sales Invoice Starter%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Sample Format%"]})
		frappe.db.delete("Crispy Format", {"name": ["like", "Test Core V1 Sample%"]})
		frappe.db.commit()

	def _ensure_company(self, name="Test Sample Format Company", abbr="TSFC"):
		if not frappe.db.exists("Company", name):
			frappe.get_doc(
				{
					"doctype": "Company",
					"company_name": name,
					"abbr": abbr,
					"default_currency": "USD",
					"country": "United States",
				}
			).insert(ignore_permissions=True)
		return name

	def test_hooks_do_not_ship_crispy_format_fixtures(self):
		from crispy_print import hooks

		self.assertFalse(getattr(hooks, "fixtures", None))

	def test_catalog_lists_valid_company_neutral_samples(self):
		from crispy_print.api.v1.sample_formats import get_sample_format, list_sample_formats

		samples = list_sample_formats()
		sample_ids = {row["id"] for row in samples}

		self.assertIn("sales-invoice-basic", sample_ids)
		self.assertIn("receipt-voucher-raw-typst", sample_ids)
		self.assertIn("payment-entry-voucher", sample_ids)
		self.assertIn("statement-of-account", sample_ids)
		self.assertIn("pos-invoice-thermal", sample_ids)
		for row in samples:
			payload = get_sample_format(row["id"])
			format_data = payload["format"]
			self.assertFalse(format_data.get("company"))
			self.assertFalse(format_data.get("is_default"))
			self.assertNotIn("/private/", json.dumps(payload))

		receipt = get_sample_format("receipt-voucher-raw-typst")["format"]
		self.assertEqual(receipt.get("doc_type"), "Payment Entry")
		self.assertEqual(receipt.get("raw_typst"), 1)
		self.assertIn("Receipt Voucher", receipt.get("typst_code") or "")

		core_card = next(row for row in samples if row["id"] == "payment-entry-voucher")
		self.assertEqual(core_card["release_scope"], "core-v1")
		self.assertEqual(core_card["variant"], "receive-or-pay")

	def test_catalog_skips_invalid_sample_files(self):
		from crispy_print.api.v1 import sample_formats

		with TemporaryDirectory() as tmpdir:
			base = Path(tmpdir)
			(base / "valid.json").write_text(
				json.dumps(
					{
						"schema_version": 1,
						"app": "crispy_print",
						"sample": {
							"id": "valid",
							"title": "Valid",
							"target_type": "DocType",
							"doc_type": "Sales Invoice",
						},
						"format": {
							"name": "Test Sample Format Valid",
							"crispy_format_type": "DocType",
							"doc_type": "Sales Invoice",
							"company": None,
							"layout_json": json.dumps({"sections": []}),
							"presentation_settings": json.dumps({"page": {"size": "a4"}}),
						},
					}
				),
				encoding="utf-8",
			)
			(base / "invalid.json").write_text("{invalid", encoding="utf-8")

			with patch.object(sample_formats, "_sample_format_dir", return_value=base):
				samples = sample_formats.list_sample_formats()

		self.assertEqual([row["id"] for row in samples], ["valid"])

	def test_create_format_from_sample_requires_create_permission(self):
		from crispy_print.api.v1.sample_formats import create_format_from_sample

		company = self._ensure_company()
		with patch("frappe.has_permission", return_value=False):
			self.assertRaises(
				frappe.ValidationError,
				create_format_from_sample,
				"sales-invoice-basic",
				company,
			)

	def test_create_format_from_sample_requires_valid_company(self):
		from crispy_print.api.v1.sample_formats import create_format_from_sample

		self.assertRaises(
			frappe.ValidationError,
			create_format_from_sample,
			"sales-invoice-basic",
			"Missing Sample Company",
		)

	def test_create_format_from_sample_creates_company_scoped_copy(self):
		from crispy_print.api.v1.sample_formats import create_format_from_sample

		company = self._ensure_company()
		result = create_format_from_sample(
			"sales-invoice-basic",
			company,
			name="Test Sample Format Invoice",
			set_default=0,
		)

		doc = frappe.get_doc("Crispy Format", result["name"])
		self.assertEqual(doc.company, company)
		self.assertEqual(doc.doc_type, "Sales Invoice")
		self.assertFalse(doc.is_default)

	def test_create_format_from_sample_uses_copy_name_on_collision(self):
		from crispy_print.api.v1.sample_formats import create_format_from_sample

		company = self._ensure_company()
		first = create_format_from_sample(
			"sales-invoice-basic",
			company,
			name="Test Sample Format Collision",
		)
		second = create_format_from_sample(
			"sales-invoice-basic",
			company,
			name="Test Sample Format Collision",
		)

		self.assertEqual(first["name"], "Test Sample Format Collision")
		self.assertNotEqual(second["name"], first["name"])
		self.assertTrue(second["name"].startswith("Test Sample Format Collision"))

	def test_every_core_v1_sample_creates_a_company_scoped_format(self):
		from crispy_print.api.v1.sample_formats import create_format_from_sample
		from crispy_print.business_format_acceptance import CORE_V1_BUSINESS_FORMATS

		company = self._ensure_company()
		for index, spec in enumerate(CORE_V1_BUSINESS_FORMATS, start=1):
			result = create_format_from_sample(
				spec.sample_id,
				company,
				name=f"Test Core V1 Sample {index}",
			)
			doc = frappe.get_doc("Crispy Format", result["name"])
			self.assertEqual(doc.company, company)
			self.assertEqual(doc.crispy_format_type, spec.target_type)
