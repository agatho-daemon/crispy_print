from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.permissions import (
	company_permission_query_condition,
	ensure_company_access,
	get_allowed_company_names,
	has_company_access,
)


class TestCompanyPermissionPolicy(FrappeTestCase):
	def test_manager_has_unrestricted_query_condition(self):
		with mock.patch("crispy_print.permissions.frappe.get_roles", return_value=["Crispy Print Manager"]):
			condition = company_permission_query_condition(
				user="manager@example.com",
				doctype="Crispy Format",
			)

		self.assertEqual(condition, "")

	def test_user_without_company_permissions_is_unrestricted_for_backward_compatibility(self):
		with (
			mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[]),
			mock.patch("crispy_print.permissions.get_user_permissions", return_value={}),
		):
			self.assertIsNone(get_allowed_company_names(user="user@example.com", doctype="Crispy Format"))
			self.assertEqual(
				company_permission_query_condition(
					user="user@example.com",
					doctype="Crispy Format",
				),
				"",
			)

	def test_company_permissions_filter_company_scoped_doctype_and_allow_global_fallback(self):
		with (
			mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[]),
			mock.patch(
				"crispy_print.permissions.get_user_permissions",
				return_value={
					"Company": [
						frappe._dict(doc="Allowed Company", applicable_for=None),
						frappe._dict(doc="Other Company", applicable_for="Sales Invoice"),
					]
				},
			),
		):
			condition = company_permission_query_condition(
				user="user@example.com",
				doctype="Crispy Format",
			)

		self.assertIn("`tabCrispy Format`.`company` in", condition)
		self.assertIn(frappe.db.escape("Allowed Company", percent=False), condition)
		self.assertNotIn("Other Company", condition)
		self.assertIn("ifnull(`tabCrispy Format`.`company`, '')=''", condition)

	def test_company_permissions_filter_strict_company_doctype_without_global_fallback(self):
		with (
			mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[]),
			mock.patch(
				"crispy_print.permissions.get_user_permissions",
				return_value={"Company": [frappe._dict(doc="Allowed Company", applicable_for=None)]},
			),
		):
			condition = company_permission_query_condition(
				user="user@example.com",
				doctype="Crispy Branding Profile",
			)

		self.assertIn("`tabCrispy Branding Profile`.`company` in", condition)
		self.assertNotIn("ifnull(", condition)

	def test_company_permission_applicable_to_other_doctype_does_not_restrict_crispy_doctype(self):
		with (
			mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[]),
			mock.patch(
				"crispy_print.permissions.get_user_permissions",
				return_value={
					"Company": [frappe._dict(doc="Allowed Company", applicable_for="Sales Invoice")]
				},
			),
		):
			self.assertIsNone(get_allowed_company_names(user="user@example.com", doctype="Crispy Format"))
			self.assertEqual(
				company_permission_query_condition(
					user="user@example.com",
					doctype="Crispy Format",
				),
				"",
			)

	def test_has_company_access_uses_allowed_company_values(self):
		with (
			mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[]),
			mock.patch(
				"crispy_print.permissions.get_user_permissions",
				return_value={"Company": [frappe._dict(doc="Allowed Company", applicable_for=None)]},
			),
		):
			self.assertTrue(
				has_company_access(
					"Allowed Company",
					user="user@example.com",
					doctype="Crispy Format",
				)
			)
			self.assertFalse(
				has_company_access(
					"Blocked Company",
					user="user@example.com",
					doctype="Crispy Format",
				)
			)
			self.assertRaises(
				frappe.PermissionError,
				ensure_company_access,
				"Blocked Company",
				user="user@example.com",
				doctype="Crispy Format",
			)
