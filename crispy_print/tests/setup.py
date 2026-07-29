import frappe


def before_tests() -> None:
	"""Prepare the ERPNext baseline required by Crispy's clean-site test suite."""
	if not frappe.db.exists("Warehouse Type", "Transit"):
		from erpnext.setup.setup_wizard.operations.install_fixtures import install

		install(country="United States")

	from erpnext.setup import utils as erpnext_test_utils

	prepare_erpnext_tests = getattr(erpnext_test_utils, "before_tests", None)
	if prepare_erpnext_tests:
		prepare_erpnext_tests()
	elif not frappe.db.exists("Company", {"abbr": "CPT"}):
		frappe.get_doc(
			{
				"doctype": "Company",
				"company_name": "Crispy Print Test Company",
				"abbr": "CPT",
				"default_currency": "USD",
				"country": "United States",
			}
		).insert(ignore_permissions=True)
	_ensure_default_company()


def _ensure_default_company() -> None:
	if frappe.db.get_single_value("Global Defaults", "default_company"):
		return

	company = frappe.get_all("Company", pluck="name", order_by="creation asc", limit=1)
	if not company:
		frappe.throw("ERPNext test setup did not create a Company.")

	company_name = company[0]
	frappe.db.set_single_value("Global Defaults", "default_company", company_name)
	frappe.db.set_default("company", company_name)
	frappe.db.commit()
