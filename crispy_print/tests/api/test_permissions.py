import json
from pathlib import Path
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.install import ensure_designer_role
from crispy_print.permissions import (
	DESIGNER_ROLE,
	company_permission_query_condition,
	ensure_company_access,
	get_allowed_company_names,
	has_company_access,
	is_crispy_print_manager,
)

APP_ROOT = Path(__file__).resolve().parents[3]


class TestCompanyPermissionPolicy(FrappeTestCase):
	def test_designer_role_setup_is_idempotent(self):
		ensure_designer_role()
		ensure_designer_role()

		self.assertTrue(frappe.db.exists("Role", DESIGNER_ROLE))
		self.assertEqual(frappe.db.get_value("Role", DESIGNER_ROLE, "desk_access"), 1)

	def test_designer_is_not_manager_bypass(self):
		with mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[DESIGNER_ROLE]):
			self.assertFalse(is_crispy_print_manager("designer@example.com"))

	def test_designer_with_company_permissions_is_company_scoped(self):
		with (
			mock.patch("crispy_print.permissions.frappe.get_roles", return_value=[DESIGNER_ROLE]),
			mock.patch(
				"crispy_print.permissions.get_user_permissions",
				return_value={"Company": [frappe._dict(doc="Designer Company", applicable_for=None)]},
			),
		):
			condition = company_permission_query_condition(
				user="designer@example.com",
				doctype="Crispy Format",
			)

		self.assertIn("`tabCrispy Format`.`company` in", condition)
		self.assertIn(frappe.db.escape("Designer Company", percent=False), condition)

	def test_designer_authoring_permissions_are_declared(self):
		for doctype in (
			"Crispy Format",
			"Crispy Branding Profile",
			"Crispy Typst Block",
			"Crispy Document Code Profile",
		):
			permission = _doctype_permission(doctype, DESIGNER_ROLE)
			for ptype in ("create", "read", "write", "report", "export", "print", "select"):
				self.assertEqual(permission.get(ptype), 1, f"{doctype}.{ptype}")

	def test_designer_template_permissions_are_read_only(self):
		permission = _doctype_permission("Crispy Template", DESIGNER_ROLE)

		for ptype in ("read", "report", "export", "print", "select"):
			self.assertEqual(permission.get(ptype), 1, ptype)
		for ptype in ("create", "write", "delete"):
			self.assertFalse(permission.get(ptype), ptype)

	def test_designer_does_not_receive_manager_only_doctype_permissions(self):
		for doctype in (
			"Crispy Print Settings",
			"Crispy Fiscal Credential",
			"Crispy Issued Document",
		):
			self.assertEqual(_doctype_permission(doctype, DESIGNER_ROLE), {})

	def test_designer_has_builder_page_access(self):
		for page in ("crispy_format_builder", "ctb_builder"):
			roles = _page_roles(page)
			self.assertIn(DESIGNER_ROLE, roles)

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


def _doctype_permission(doctype: str, role: str) -> dict:
	payload = _load_json(_doctype_json_path(doctype))
	for permission in payload.get("permissions") or []:
		if permission.get("role") == role:
			return permission
	return {}


def _page_roles(page: str) -> set[str]:
	payload = _load_json(APP_ROOT / "crispy_print" / "crispy_print" / "page" / page / f"{page}.json")
	return {row.get("role") for row in payload.get("roles") or []}


def _doctype_json_path(doctype: str) -> Path:
	folder = doctype.lower().replace(" ", "_")
	return APP_ROOT / "crispy_print" / "crispy_print" / "doctype" / folder / f"{folder}.json"


def _load_json(path: Path) -> dict:
	return json.loads(path.read_text(encoding="utf-8"))
