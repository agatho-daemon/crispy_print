"""Deterministic RTL browser-test seed data.

Run only on a disposable development/test site:
`bench --site <site> execute crispy_print.dev_utils.rtl_e2e.seed`
"""

from __future__ import annotations

import json

import frappe

FORMAT_NAME = "Crispy RTL E2E Arabic"
PERSIAN_FORMAT_NAME = "Crispy RTL E2E Persian"
ENGLISH_FORMAT_NAME = "Crispy RTL E2E English"
MULTIPAGE_FORMAT_NAME = "Crispy RTL E2E Multipage"
REPORT_FORMAT_NAME = "Crispy RTL E2E Report"
TEST_USER = "crispy-rtl-e2e@local.test"
RTL_FOOTER = (
	"#let footer_block = align(end + horizon)[\n"
	"  #set text(size: 8pt, dir: ltr)\n"
	'  #context counter(page).display("1 of 1", both: true)\n'
	"]"
)

LABELS = {
	"ar": {
		"section": "فاتورة تجريبية",
		"customer": "العميل",
		"date": "التاريخ",
		"document": "رقم المستند",
		"total": "الإجمالي",
		"items": "البنود",
		"item_code": "رمز الصنف",
		"description": "الوصف",
		"quantity": "الكمية",
		"amount": "المبلغ",
	},
	"fa": {
		"section": "فاکتور آزمایشی",
		"customer": "مشتری",
		"date": "تاریخ",
		"document": "شناسه سند",
		"total": "جمع کل",
		"items": "اقلام",
		"item_code": "کد کالا",
		"description": "شرح",
		"quantity": "مقدار",
		"amount": "مبلغ",
	},
	"en": {
		"section": "Test Invoice",
		"customer": "Customer",
		"date": "Date",
		"document": "Document ID",
		"total": "Grand Total",
		"items": "Items",
		"item_code": "Item Code",
		"description": "Description",
		"quantity": "Quantity",
		"amount": "Amount",
	},
}


def _section(language: str, index: int = 0, include_items: bool = True) -> dict:
	labels = LABELS[language]
	fields = [
		{
			"id": f"customer-name-{index}",
			"fieldname": "customer_name",
			"fieldtype": "Data",
			"label": labels["customer"],
			"align": "start",
		},
		{
			"id": f"posting-date-{index}",
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"label": labels["date"],
			"align": "end",
		},
		{
			"id": f"document-id-{index}",
			"fieldname": "name",
			"fieldtype": "Data",
			"label": labels["document"],
			"align": "end",
		},
		{
			"id": f"grand-total-{index}",
			"fieldname": "grand_total",
			"fieldtype": "Currency",
			"label": labels["total"],
			"align": "end",
		},
	]
	if include_items:
		fields.append(
			{
				"id": f"items-{index}",
				"fieldname": "items",
				"fieldtype": "Table",
				"label": labels["items"],
				"table_order": "logical",
				"table_columns": [
					{
						"fieldname": "item_code",
						"fieldtype": "Link",
						"label": labels["item_code"],
						"align": "start",
					},
					{
						"fieldname": "description",
						"fieldtype": "Text",
						"label": labels["description"],
						"align": "start",
					},
					{
						"fieldname": "qty",
						"fieldtype": "Float",
						"label": labels["quantity"],
						"align": "end",
					},
					{
						"fieldname": "amount",
						"fieldtype": "Currency",
						"label": labels["amount"],
						"align": "end",
					},
				],
			}
		)
	return {
		"id": f"rtl-e2e-main-{language}-{index}",
		"label": labels["section"] if index == 0 else f"{labels['section']} {index + 1}",
		"columns": [
			{
				"id": f"rtl-e2e-column-{language}-{index}",
				"label": "",
				"fields": fields,
			}
		],
	}


def _layout(language: str, repeat_sections: int = 1) -> dict:
	return {
		"schema_version": 4,
		"sections": [_section(language, index, include_items=index == 0) for index in range(repeat_sections)],
	}


def _presentation(language: str) -> dict:
	return {
		"language": language,
		"page": {
			"size": "A4",
			"orientation": "portrait",
			"margins": {"top": 20, "bottom": 20, "left": 18, "right": 18},
		},
		"qr": {
			"enabled": True,
			"sourceMode": "basic",
			"fields": ["name", "customer_name", "grand_total"],
			"symbology": "QR Code",
			"size": 18,
			"anchor": "end",
			"dx": 0,
			"dy": 0,
		},
	}


def _upsert_format(name: str, values: dict):
	if frappe.db.exists("Crispy Format", name):
		doc = frappe.get_doc("Crispy Format", name)
		doc.update(values)
		doc.save()
		return doc
	doc = frappe.get_doc({"doctype": "Crispy Format", "name": name, **values})
	doc.insert()
	return doc


def _doc_format_values(invoice, language: str, *, repeat_sections: int = 1) -> dict:
	return {
		"crispy_format_type": "DocType",
		"doc_type": "Sales Invoice",
		"company": invoice.company,
		"module": "Crispy Print",
		"raw_typst": 0,
		"default_print_language": language.split("-", 1)[0],
		"doc_footer": RTL_FOOTER,
		"layout_json": json.dumps(
			_layout(language.split("-", 1)[0], repeat_sections=repeat_sections),
			ensure_ascii=False,
		),
		"presentation_settings": json.dumps(_presentation(language), ensure_ascii=False),
	}


def _report_format_values(company: str) -> dict:
	return {
		"crispy_format_type": "Report",
		"company": company,
		"module": "Crispy Print",
		"raw_typst": 0,
		"report_scope": "Selected Reports",
		"report_renderer": "general_ledger",
		"report": [{"report": "General Ledger", "disabled": 0}],
		"default_print_language": "ar",
		"layout_json": json.dumps({"schema_version": 4, "sections": []}),
		"presentation_settings": json.dumps(_presentation("ar-KW"), ensure_ascii=False),
	}


def _ensure_test_user(password: str):
	if frappe.db.exists("User", TEST_USER):
		user = frappe.get_doc("User", TEST_USER)
	else:
		user = frappe.get_doc(
			{
				"doctype": "User",
				"email": TEST_USER,
				"first_name": "Crispy RTL",
				"last_name": "E2E",
				"enabled": 1,
				"user_type": "System User",
				"send_welcome_email": 0,
			}
		)
		user.insert(ignore_permissions=True)
	user.enabled = 1
	user.new_password = password
	user.save(ignore_permissions=True)
	required_roles = {"System Manager", "Accounts User", "Accounts Manager", "Sales User", "Sales Manager"}
	missing_roles = sorted(required_roles - set(frappe.get_roles(TEST_USER)))
	if missing_roles:
		user.add_roles(*missing_roles)
	return user


def disable_test_user() -> dict:
	"""Disable the opt-in disposable-site browser user."""
	frappe.only_for("System Manager")
	if frappe.db.exists("User", TEST_USER):
		frappe.db.set_value("User", TEST_USER, "enabled", 0)
		frappe.db.commit()
	return {"user": TEST_USER, "enabled": False}


def seed(publish: int | bool = 0, test_user_password: str | None = None) -> dict:
	"""Create/update the named test format and report usable source records."""
	frappe.only_for("System Manager")
	invoice = frappe.db.get_value(
		"Sales Invoice",
		{"docstatus": ["<", 2]},
		["name", "company"],
		as_dict=True,
	)
	if not invoice:
		frappe.throw("Create at least one draft or submitted Sales Invoice before seeding RTL E2E data.")

	formats = {
		"arabic": _upsert_format(FORMAT_NAME, _doc_format_values(invoice, "ar-KW")),
		"persian": _upsert_format(PERSIAN_FORMAT_NAME, _doc_format_values(invoice, "fa-IR")),
		"english": _upsert_format(ENGLISH_FORMAT_NAME, _doc_format_values(invoice, "en")),
		"multipage": _upsert_format(
			MULTIPAGE_FORMAT_NAME,
			_doc_format_values(invoice, "ar-KW", repeat_sections=12),
		),
		"report": _upsert_format(REPORT_FORMAT_NAME, _report_format_values(invoice.company)),
	}

	# Keep the original fixture name usable, but never retain its old bilingual labels.
	_upsert_format("Crispy RTL E2E", _doc_format_values(invoice, "ar-KW"))

	active_template = frappe.db.get_value(
		"Crispy Template",
		{"source_crispy_format": FORMAT_NAME, "status": "Approved", "is_active": 1},
		"name",
	)
	if publish and not active_template:
		from crispy_print.crispy_print.doctype.crispy_template.crispy_template import (
			publish_crispy_template,
		)

		# This can supersede another active template for the same company/DocType.
		# It is deliberately opt-in and suitable only for disposable acceptance sites.
		active_template = publish_crispy_template(
			FORMAT_NAME,
			make_active=True,
			notes="Deterministic RTL E2E fixture; disposable test sites only.",
		)["name"]

	test_user = _ensure_test_user(test_user_password) if test_user_password else None
	frappe.db.commit()
	return {
		"format": formats["arabic"].name,
		"formats": {key: value.name for key, value in formats.items()},
		"template": active_template,
		"publish_requested": bool(publish),
		"doctype": "Sales Invoice",
		"docname": invoice.name,
		"company": invoice.company,
		"test_user": test_user.name if test_user else None,
	}
