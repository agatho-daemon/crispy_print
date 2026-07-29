from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.business_format_acceptance import CORE_V1_BUSINESS_FORMATS
from crispy_print.dev_utils import business_formats_e2e


class TestBusinessFormatE2ESeed(FrappeTestCase):
	def test_seed_uses_every_core_v1_sample_and_reports_missing_documents(self):
		created = []

		def fake_create(sample_id, company, name=None):
			created.append((sample_id, company, name))
			return {"name": name}

		with (
			patch("frappe.only_for"),
			patch("frappe.db.exists", return_value=False),
			patch("frappe.defaults.get_user_default", return_value="_Test Company"),
			patch.object(business_formats_e2e, "create_format_from_sample", side_effect=fake_create),
			patch.object(
				business_formats_e2e,
				"_latest",
				return_value={"available": False},
			),
			patch.object(
				business_formats_e2e,
				"_seed_pos_invoice",
				return_value={"available": False},
			),
			patch.object(
				business_formats_e2e,
				"_seed_cash_journal_entry",
				return_value={"available": False},
			),
			patch("frappe.db.commit"),
		):
			result = business_formats_e2e.seed()

		self.assertEqual(
			[sample_id for sample_id, _company, _name in created],
			[spec.sample_id for spec in CORE_V1_BUSINESS_FORMATS],
		)
		self.assertTrue(all(not row["available"] for row in result["documents"].values()))

	def test_cleanup_is_scoped_to_business_acceptance_formats(self):
		with (
			patch("frappe.only_for"),
			patch("frappe.delete_doc") as delete_doc,
			patch("frappe.db.commit"),
			patch(
				"frappe.get_all",
				side_effect=[
					["Crispy V1 E2E 01 payment-entry-voucher"],
					[],
					[],
					[],
				],
			) as get_all,
		):
			result = business_formats_e2e.cleanup()

		self.assertEqual(result["deleted_formats"], ["Crispy V1 E2E 01 payment-entry-voucher"])
		self.assertEqual(result["deleted_items"], [])
		self.assertEqual(get_all.call_args_list[0].kwargs["filters"]["name"][0], "like")
		delete_doc.assert_called_once()
