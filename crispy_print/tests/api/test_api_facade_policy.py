import ast
import inspect
from unittest import mock

import frappe
from frappe.tests.utils import FrappeTestCase

import crispy_print.api.v1 as api_v1
from crispy_print.api.v1.security import endpoint_policy


class TestEndpointPolicy(FrappeTestCase):
	def test_endpoint_policy_enforces_permission_and_rate_limit(self):
		calls = []

		@endpoint_policy(
			rate_key="test_policy",
			limit=7,
			window_seconds=30,
			permissions=(("Crispy Format", "read"),),
		)
		def sample():
			calls.append("called")
			return {"ok": True}

		with (
			mock.patch("crispy_print.api.v1.security.ensure_doctype_permission") as ensure_perm,
			mock.patch("crispy_print.api.v1.security.enforce_rate_limit") as enforce_limit,
		):
			result = sample()

		self.assertEqual(result, {"ok": True})
		self.assertEqual(calls, ["called"])
		ensure_perm.assert_called_once_with("Crispy Format", "read")
		enforce_limit.assert_called_once_with("test_policy", limit=7, window_seconds=30)
		self.assertEqual(sample.__crispy_endpoint_policy__["rate_key"], "test_policy")
		self.assertEqual(
			sample.__crispy_endpoint_policy__["permissions"],
			(("Crispy Format", "read"),),
		)

	def test_endpoint_policy_enforces_manager_permission(self):
		@endpoint_policy(manager_only=True)
		def sample():
			return {"ok": True}

		with mock.patch(
			"crispy_print.api.v1.security.ensure_crispy_print_manager_permission"
		) as ensure_manager:
			self.assertEqual(sample(), {"ok": True})

		ensure_manager.assert_called_once_with()


class TestApiFacadePolicy(FrappeTestCase):
	def test_all_whitelisted_facade_functions_declare_policy(self):
		missing = []
		for name in _whitelisted_function_names():
			fn = getattr(api_v1, name)
			if not hasattr(fn, "__crispy_endpoint_policy__"):
				missing.append(name)

		self.assertEqual(missing, [])

	def test_policy_metadata_has_rate_or_explicit_delegation(self):
		invalid = []
		for name in _whitelisted_function_names():
			policy = getattr(api_v1, name).__crispy_endpoint_policy__
			if policy.get("rate_key") or policy.get("delegated") or policy.get("exempt_reason"):
				continue
			invalid.append(name)

		self.assertEqual(invalid, [])

	def test_mutating_facade_functions_have_permission_policy_or_delegation(self):
		mutating = {
			"add_issued_document_trust_event",
			"cancel_issued_document",
			"check_import_conflicts",
			"create_format_from_sample",
			"create_issued_document_snapshot",
			"duplicate_crispy_format_for_company",
			"duplicate_crispy_template_for_company",
			"generate_document_code",
			"import_crispy_format",
			"publish_template_from_crispy_format",
			"record_issued_document_integrity_check",
			"revoke_issued_document",
			"run_report_template_parity_check",
			"supersede_issued_document",
		}
		invalid = []
		for name in mutating:
			policy = getattr(api_v1, name).__crispy_endpoint_policy__
			if policy.get("permissions") or policy.get("manager_only") or policy.get("delegated"):
				continue
			invalid.append(name)

		self.assertEqual(invalid, [])

	def test_formatted_doc_facade_applies_rate_limit_before_delegate(self):
		with (
			mock.patch("crispy_print.api.v1.security.enforce_rate_limit") as enforce_limit,
			mock.patch("crispy_print.api.v1._get_formatted_doc", return_value={"name": "SINV-1"}) as inner,
		):
			result = api_v1.get_formatted_doc("Sales Invoice", "SINV-1")

		self.assertEqual(result, {"name": "SINV-1"})
		enforce_limit.assert_called_once_with("get_formatted_doc", limit=60, window_seconds=60)
		inner.assert_called_once_with(
			"Sales Invoice",
			"SINV-1",
			qr_source_mode=None,
			fields=None,
			allow_document_code_preview=0,
		)

	def test_available_formats_facade_applies_read_permission_and_rate_limit(self):
		with (
			mock.patch("crispy_print.api.v1.security.ensure_doctype_permission") as ensure_perm,
			mock.patch("crispy_print.api.v1.security.enforce_rate_limit") as enforce_limit,
			mock.patch("crispy_print.api.v1._get_available_formats", return_value={}) as inner,
		):
			result = api_v1.get_available_formats("General Ledger", company="Test Company")

		self.assertEqual(result, {})
		ensure_perm.assert_called_once_with("Crispy Format", "read")
		enforce_limit.assert_called_once_with("get_available_formats", limit=120, window_seconds=60)
		inner.assert_called_once_with("General Ledger", company="Test Company")

	def test_branding_presentation_facade_applies_rate_limit(self):
		with (
			mock.patch("crispy_print.api.v1.security.enforce_rate_limit") as enforce_limit,
			mock.patch(
				"crispy_print.api.v1._get_branding_profile_presentation_settings",
				return_value={"page": {"size": "A4"}},
			) as inner,
		):
			result = api_v1.get_branding_profile_presentation_settings("Branding A")

		self.assertEqual(result, {"page": {"size": "A4"}})
		enforce_limit.assert_called_once_with(
			"get_branding_profile_presentation_settings",
			limit=120,
			window_seconds=60,
		)
		inner.assert_called_once_with("Branding A")

	def test_fiscal_credential_status_facade_applies_read_permission_and_rate_limit(self):
		with (
			mock.patch("crispy_print.api.v1.security.ensure_doctype_permission") as ensure_perm,
			mock.patch("crispy_print.api.v1.security.enforce_rate_limit") as enforce_limit,
			mock.patch("crispy_print.api.v1._get_fiscal_credential_status", return_value={}) as inner,
		):
			result = api_v1.get_fiscal_credential_status(
				"Test Company",
				"ZATCA",
				environment="Production",
				authority_code="KSA",
			)

		self.assertEqual(result, {})
		ensure_perm.assert_called_once_with("Crispy Fiscal Credential", "read")
		enforce_limit.assert_called_once_with(
			"get_fiscal_credential_status",
			limit=120,
			window_seconds=60,
		)
		inner.assert_called_once_with(
			company="Test Company",
			regulatory_profile="ZATCA",
			environment="Production",
			authority_code="KSA",
		)

	def test_template_resolution_facade_applies_rate_limit(self):
		with (
			mock.patch("crispy_print.api.v1.security.enforce_rate_limit") as enforce_limit,
			mock.patch(
				"crispy_print.api.v1._get_resolved_crispy_template_for_render",
				return_value={"name": "template"},
			) as inner,
		):
			result = api_v1.get_resolved_crispy_template_for_render(
				source_doctype="Sales Invoice",
				company="Test Company",
			)

		self.assertEqual(result, {"name": "template"})
		enforce_limit.assert_called_once_with(
			"get_resolved_crispy_template_for_render",
			limit=120,
			window_seconds=60,
		)
		inner.assert_called_once_with(
			source_doctype="Sales Invoice",
			source_docname=None,
			source_report=None,
			source_contract=None,
			company="Test Company",
			template=None,
			template_name=None,
		)


def _whitelisted_function_names() -> list[str]:
	source = inspect.getsource(api_v1)
	tree = ast.parse(source)
	names = []
	for node in tree.body:
		if not isinstance(node, ast.FunctionDef):
			continue
		if any(_is_frappe_whitelist(decorator) for decorator in node.decorator_list):
			names.append(node.name)
	return names


def _is_frappe_whitelist(node: ast.AST) -> bool:
	if not isinstance(node, ast.Call):
		return False
	func = node.func
	return (
		isinstance(func, ast.Attribute)
		and func.attr == "whitelist"
		and isinstance(func.value, ast.Name)
		and func.value.id == "frappe"
	)
