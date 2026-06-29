"""Smoke-test the backend QR field registry on a live Frappe site.

Usage:
    bench --site fdev.local execute crispy_print.dev_utils.qr_registry_smoke.run
"""

from __future__ import annotations

from typing import Any

import frappe

from crispy_print.api.v1.document_codes import generate_document_code


def run() -> dict[str, Any]:
	frappe.set_user("Administrator")
	result: dict[str, Any] = {}

	try:
		company = _ensure_company()
		result["company"] = company
		result["valid_profile"] = _insert_valid_company_profile(company)
		result["generated_code"] = generate_document_code(
			doctype="Company",
			name=company,
			code_purpose="Other",
			environment="Production",
			profile_name=result["valid_profile"],
		)
		result["invalid_field_rejected"] = _invalid_company_field_is_rejected(company)
		result["authority_required_fields_accepted"] = _authority_required_fields_are_accepted(company)
		result["authority_field_rejected"] = _authority_restricted_field_is_rejected(company)
		return result
	finally:
		frappe.db.rollback()


def _ensure_company() -> str:
	company = "QR Registry Smoke Company"
	if frappe.db.exists("Company", company):
		return company

	frappe.get_doc(
		{
			"doctype": "Company",
			"company_name": company,
			"abbr": "QRSMK",
			"default_currency": "KWD",
		}
	).insert(ignore_permissions=True)
	return company


def _insert_valid_company_profile(company: str) -> str:
	profile_name = f"QR Registry Smoke Valid {frappe.generate_hash(length=8)}"
	doc = _new_document_code_profile(
		company=company,
		profile_name=profile_name,
		code_purpose="Other",
		regulatory_profile=None,
		content_source="Selected Fields",
		selected_fields=[
			{"source_doctype": "Company", "field_key": "company_name", "output_key": "company"},
			{"source_doctype": "Company", "field_key": "abbr", "output_key": "code"},
		],
	)
	doc.append(
		"document_rules",
		{
			"document_type": "Company",
			"document_role": "Other",
			"condition_type": "Always",
			"priority": 100,
		},
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _invalid_company_field_is_rejected(company: str) -> bool:
	doc = _new_document_code_profile(
		company=company,
		profile_name=f"QR Registry Smoke Invalid {frappe.generate_hash(length=8)}",
		code_purpose="Other",
		regulatory_profile=None,
		content_source="Selected Fields",
		selected_fields=[
			{"source_doctype": "Company", "field_key": "owner.password"},
		],
	)
	doc.append(
		"document_rules",
		{
			"document_type": "Company",
			"document_role": "Other",
			"condition_type": "Always",
			"priority": 100,
		},
	)
	return _insert_raises_validation_error(doc)


def _authority_restricted_field_is_rejected(company: str) -> bool:
	regulatory_profile = _insert_zatca_profile()
	doc = _new_document_code_profile(
		company=company,
		profile_name=f"QR Registry Smoke Authority {frappe.generate_hash(length=8)}",
		code_purpose="Regulatory",
		regulatory_profile=regulatory_profile,
		content_source="Selected Fields",
		selected_fields=[
			{"source_doctype": "Sales Invoice", "field_key": "company"},
			{"source_doctype": "Sales Invoice", "field_key": "rounded_total"},
		],
	)
	doc.append(
		"document_rules",
		{
			"document_type": "Sales Invoice",
			"document_role": "Invoice",
			"condition_type": "Always",
			"priority": 100,
		},
	)
	return _insert_raises_validation_error(doc)


def _authority_required_fields_are_accepted(company: str) -> bool:
	regulatory_profile = _insert_zatca_profile()
	doc = _new_document_code_profile(
		company=company,
		profile_name=f"QR Registry Smoke ZATCA Required {frappe.generate_hash(length=8)}",
		code_purpose="Regulatory",
		regulatory_profile=regulatory_profile,
		content_source="Selected Fields",
		selected_fields=[
			{"source_doctype": "Sales Invoice", "field_key": "company"},
			{"source_doctype": "Sales Invoice", "field_key": "posting_date"},
			{"source_doctype": "Sales Invoice", "field_key": "posting_time"},
			{"source_doctype": "Sales Invoice", "field_key": "grand_total"},
			{"source_doctype": "Sales Invoice", "field_key": "total_taxes_and_charges"},
		],
	)
	doc.append(
		"document_rules",
		{
			"document_type": "Sales Invoice",
			"document_role": "Invoice",
			"condition_type": "Always",
			"priority": 100,
		},
	)
	doc.insert(ignore_permissions=True)
	return bool(doc.name)


def _new_document_code_profile(**values: Any) -> Any:
	base = {
		"doctype": "Crispy Document Code Profile",
		"enabled": 1,
		"environment": "Production",
		"code_format": "QR Code",
		"code_symbology": "QR Code",
		"payload_format": "JSON",
		"output_encoding": "Plain Text",
		"error_correction": "Medium",
		"encoder_key": "custom",
		"priority": 100,
	}
	base.update(values)
	return frappe.get_doc(base)


def _insert_zatca_profile() -> str:
	profile_name = f"QR Registry Smoke ZATCA {frappe.generate_hash(length=8)}"
	doc = frappe.get_doc(
		{
			"doctype": "Crispy QR Regulatory Profile",
			"profile_name": profile_name,
			"enabled": 1,
			"authority_code": "ZATCA",
			"standard": "ZATCA TLV",
			"payload_format": "JSON",
			"code_symbology": "QR Code",
			"output_encoding": "Plain Text",
			"error_correction": "Medium",
			"encoder_key": "custom",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _insert_raises_validation_error(doc: Any) -> bool:
	try:
		doc.insert(ignore_permissions=True)
	except frappe.ValidationError:
		return True
	return False
