"""Deterministic RTL browser-test seed data.

Run only on a disposable development/test site:
`bench --site <site> execute crispy_print.dev_utils.rtl_e2e.seed`
"""

from __future__ import annotations

import json

import frappe

FORMAT_NAME = "Crispy RTL E2E"


def _layout() -> dict:
	return {
		"sections": [
			{
				"id": "rtl-e2e-main",
				"label": "فاتورة تجريبية / فاکتور آزمایشی",
				"columns": [
					{
						"id": "rtl-e2e-column",
						"label": "",
						"fields": [
							{
								"id": "customer-name",
								"fieldname": "customer_name",
								"fieldtype": "Data",
								"label": "العميل / مشتری",
								"align": "start",
							},
							{
								"id": "posting-date",
								"fieldname": "posting_date",
								"fieldtype": "Date",
								"label": "التاريخ / تاریخ",
								"align": "end",
							},
							{
								"id": "document-id",
								"fieldname": "name",
								"fieldtype": "Data",
								"label": "رقم المستند / شناسه",
								"align": "end",
							},
							{
								"id": "grand-total",
								"fieldname": "grand_total",
								"fieldtype": "Currency",
								"label": "الإجمالي / جمع",
								"align": "end",
							},
							{
								"id": "items",
								"fieldname": "items",
								"fieldtype": "Table",
								"label": "البنود / اقلام",
								"table_order": "logical",
								"table_columns": [
									{
										"fieldname": "item_code",
										"fieldtype": "Link",
										"label": "رمز الصنف",
										"align": "start",
									},
									{
										"fieldname": "description",
										"fieldtype": "Text",
										"label": "الوصف",
										"align": "start",
									},
									{
										"fieldname": "qty",
										"fieldtype": "Float",
										"label": "الكمية",
										"align": "end",
									},
									{
										"fieldname": "amount",
										"fieldtype": "Currency",
										"label": "المبلغ",
										"align": "end",
									},
								],
							},
						],
					}
				],
			}
		]
	}


def seed() -> dict:
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

	values = {
		"crispy_format_type": "DocType",
		"doc_type": "Sales Invoice",
		"company": invoice.company,
		"module": "Crispy Print",
		"raw_typst": 0,
		"default_print_language": "ar",
		"layout_json": json.dumps(_layout(), ensure_ascii=False),
		"presentation_settings": json.dumps(
			{
				"language": "ar-KW",
				"page": {
					"size": "A4",
					"orientation": "portrait",
					"margins": {"top": 20, "bottom": 20, "left": 18, "right": 18},
				},
			},
			ensure_ascii=False,
		),
	}
	if frappe.db.exists("Crispy Format", FORMAT_NAME):
		doc = frappe.get_doc("Crispy Format", FORMAT_NAME)
		doc.update(values)
		doc.save()
	else:
		doc = frappe.get_doc({"doctype": "Crispy Format", "name": FORMAT_NAME, **values})
		doc.insert()
	frappe.db.commit()
	return {
		"format": doc.name,
		"doctype": "Sales Invoice",
		"docname": invoice.name,
		"company": invoice.company,
	}
