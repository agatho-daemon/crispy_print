from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.defaults import enforce_single_default


class TestDefaultHelpers(FrappeTestCase):
	def test_resolves_competing_defaults_after_locking(self):
		with (
			mock.patch.object(frappe.db, "get_value", return_value="Crispy Format") as lock,
			mock.patch.object(frappe.db, "set_value") as set_value,
		):

			def competing_names():
				lock.assert_called_once_with("DocType", "Crispy Format", "name", for_update=True)
				return ["Other Format", "Current Format", "Other Format"]

			out = enforce_single_default("Crispy Format", "Current Format", competing_names=competing_names)

		self.assertEqual(out, ["Other Format"])
		set_value.assert_called_once_with(
			"Crispy Format", {"name": ["in", ["Other Format"]]}, "is_default", 0, update_modified=False
		)

	def test_non_competing_defaults_are_not_touched(self):
		with (
			mock.patch.object(frappe.db, "get_value", return_value="Crispy Format"),
			mock.patch.object(frappe.db, "set_value") as set_value,
		):
			out = enforce_single_default(
				"Crispy Format", "Current Format", competing_names=lambda: ["Current Format"]
			)
		self.assertEqual(out, [])
		set_value.assert_not_called()

	def test_filter_based_clearing_uses_current_locked_rows(self):
		filters = {"company": "Company A", "is_default": 1}
		with (
			mock.patch.object(frappe.db, "get_value", return_value="Crispy Branding Profile"),
			mock.patch.object(
				frappe.db, "get_values", return_value=["Current Profile", "Other Profile"]
			) as get_values,
			mock.patch.object(frappe.db, "set_value") as set_value,
		):
			out = enforce_single_default("Crispy Branding Profile", "Current Profile", filters=filters)

		self.assertEqual(out, ["Other Profile"])
		get_values.assert_called_once_with(
			"Crispy Branding Profile", filters, "name", for_update=True, pluck=True, order_by="name asc"
		)
		set_value.assert_called_once_with(
			"Crispy Branding Profile",
			{"name": ["in", ["Other Profile"]]},
			"is_default",
			0,
			update_modified=False,
		)
