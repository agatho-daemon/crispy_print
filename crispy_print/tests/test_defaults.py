from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.defaults import build_default_lock_key, enforce_single_default


class TestDefaultHelpers(FrappeTestCase):
	def test_default_lock_key_is_stable_and_scoped(self):
		first = build_default_lock_key("Crispy Format", "Company A|DocType|Sales Invoice")
		second = build_default_lock_key("Crispy Format", "Company A|DocType|Sales Invoice")
		other = build_default_lock_key("Crispy Format", "Company B|DocType|Sales Invoice")

		self.assertEqual(first, second)
		self.assertNotEqual(first, other)
		self.assertTrue(first.startswith("crispy_print:default:Crispy Format:"))

	def test_lock_failure_raises_validation_error(self):
		with (
			mock.patch.object(frappe.db, "db_type", "mariadb"),
			mock.patch.object(frappe.db, "sql", return_value=((0,),)),
		):
			with self.assertRaises(frappe.ValidationError):
				enforce_single_default(
					"Crispy Format",
					"Current Format",
					"Company A|DocType|Sales Invoice",
					competing_names=["Other Format"],
					timeout_seconds=0,
				)

	def test_competing_defaults_are_cleared_in_one_operation(self):
		with (
			mock.patch("crispy_print.defaults.acquire_default_locks") as acquire_locks,
			mock.patch.object(frappe.db, "set_value") as set_value,
		):
			out = enforce_single_default(
				"Crispy Format",
				"Current Format",
				"Company A|DocType|Sales Invoice",
				competing_names=["Other Format", "Current Format", "Other Format"],
			)

		self.assertEqual(out, ["Other Format"])
		acquire_locks.assert_called_once()
		set_value.assert_called_once_with(
			"Crispy Format",
			{"name": ["in", ["Other Format"]]},
			"is_default",
			0,
			update_modified=False,
		)

	def test_non_competing_defaults_are_not_touched(self):
		with (
			mock.patch("crispy_print.defaults.acquire_default_locks") as acquire_locks,
			mock.patch.object(frappe.db, "set_value") as set_value,
		):
			out = enforce_single_default(
				"Crispy Format",
				"Current Format",
				"Company A|DocType|Sales Invoice",
				competing_names=["Current Format"],
			)

		self.assertEqual(out, [])
		acquire_locks.assert_called_once()
		set_value.assert_not_called()

	def test_filter_based_clearing_excludes_current_record(self):
		with (
			mock.patch("crispy_print.defaults.acquire_default_locks"),
			mock.patch.object(
				frappe, "get_all", return_value=["Current Profile", "Other Profile"]
			) as get_all,
			mock.patch.object(frappe.db, "set_value") as set_value,
		):
			out = enforce_single_default(
				"Crispy Branding Profile",
				"Current Profile",
				"Company A|default-branding-profile",
				filters={"company": "Company A", "is_default": 1},
			)

		self.assertEqual(out, ["Other Profile"])
		get_all.assert_called_once_with(
			"Crispy Branding Profile",
			filters={"company": "Company A", "is_default": 1},
			pluck="name",
			order_by="name asc",
		)
		set_value.assert_called_once_with(
			"Crispy Branding Profile",
			{"name": ["in", ["Other Profile"]]},
			"is_default",
			0,
			update_modified=False,
		)
