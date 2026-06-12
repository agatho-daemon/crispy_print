from __future__ import annotations

from typing import Any

import frappe
from frappe import _
from frappe.utils import getdate, now, nowdate

LETTER_HEAD_DOCTYPE = "Letter Head"

SECTION_FIELD = "custom_crispy_lifecycle_section"
COMPANY_FIELD = "custom_crispy_company"
VERSION_FIELD = "custom_crispy_version"
STATUS_FIELD = "custom_crispy_status"
EFFECTIVE_FROM_FIELD = "custom_crispy_effective_from"
EFFECTIVE_TO_FIELD = "custom_crispy_effective_to"
SUPERSEDED_BY_FIELD = "custom_crispy_superseded_by"
APPROVED_BY_FIELD = "custom_crispy_approved_by"
APPROVED_AT_FIELD = "custom_crispy_approved_at"

CUSTOM_FIELDNAMES = (
	SECTION_FIELD,
	COMPANY_FIELD,
	VERSION_FIELD,
	STATUS_FIELD,
	EFFECTIVE_FROM_FIELD,
	EFFECTIVE_TO_FIELD,
	SUPERSEDED_BY_FIELD,
	APPROVED_BY_FIELD,
	APPROVED_AT_FIELD,
)
POLICY_FIELDNAMES = (
	COMPANY_FIELD,
	VERSION_FIELD,
	STATUS_FIELD,
	EFFECTIVE_FROM_FIELD,
	EFFECTIVE_TO_FIELD,
	SUPERSEDED_BY_FIELD,
	APPROVED_BY_FIELD,
	APPROVED_AT_FIELD,
)


def letterhead_lifecycle_fields() -> dict[str, list[dict[str, Any]]]:
	return {
		LETTER_HEAD_DOCTYPE: [
			{
				"fieldname": SECTION_FIELD,
				"fieldtype": "Section Break",
				"label": "Letter Head Lifecycle",
				"collapsible": 1,
				"insert_after": "is_default",
			},
			{
				"fieldname": COMPANY_FIELD,
				"fieldtype": "Link",
				"label": "Company",
				"options": "Company",
				"insert_after": SECTION_FIELD,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"search_index": 1,
			},
			{
				"fieldname": VERSION_FIELD,
				"fieldtype": "Data",
				"label": "Version",
				"insert_after": COMPANY_FIELD,
			},
			{
				"fieldname": STATUS_FIELD,
				"fieldtype": "Select",
				"label": "Status",
				"options": "Draft\nActive\nRetired",
				"default": "Active",
				"insert_after": VERSION_FIELD,
				"in_list_view": 1,
				"in_standard_filter": 1,
				"search_index": 1,
			},
			{
				"fieldname": EFFECTIVE_FROM_FIELD,
				"fieldtype": "Date",
				"label": "Effective From",
				"insert_after": STATUS_FIELD,
				"in_standard_filter": 1,
			},
			{
				"fieldname": EFFECTIVE_TO_FIELD,
				"fieldtype": "Date",
				"label": "Effective To",
				"insert_after": EFFECTIVE_FROM_FIELD,
				"in_standard_filter": 1,
			},
			{
				"fieldname": SUPERSEDED_BY_FIELD,
				"fieldtype": "Link",
				"label": "Superseded By",
				"options": LETTER_HEAD_DOCTYPE,
				"insert_after": EFFECTIVE_TO_FIELD,
			},
			{
				"fieldname": APPROVED_BY_FIELD,
				"fieldtype": "Link",
				"label": "Approved By",
				"options": "User",
				"insert_after": SUPERSEDED_BY_FIELD,
				"read_only": 1,
			},
			{
				"fieldname": APPROVED_AT_FIELD,
				"fieldtype": "Datetime",
				"label": "Approved At",
				"insert_after": APPROVED_BY_FIELD,
				"read_only": 1,
			},
		]
	}


def has_letterhead_lifecycle_fields() -> bool:
	try:
		meta = frappe.get_meta(LETTER_HEAD_DOCTYPE)
	except Exception:
		return False
	return all(meta.get_field(fieldname) for fieldname in POLICY_FIELDNAMES)


def on_letterhead_validate(doc, method: str | None = None) -> None:
	if not has_letterhead_lifecycle_fields():
		return
	if not _has_crispy_lifecycle_values(doc):
		return
	_validate_effective_dates(doc)
	_validate_supersession(doc)
	_set_approval_metadata(doc)


def get_selectable_letterheads(company: str | None = None, include_current: str | None = None) -> list[str]:
	company = (company or "").strip()
	include_current = (include_current or "").strip()
	today = getdate(nowdate())
	rows = frappe.get_all(
		LETTER_HEAD_DOCTYPE,
		fields=[
			"name",
			"disabled",
			COMPANY_FIELD,
			STATUS_FIELD,
			EFFECTIVE_FROM_FIELD,
			EFFECTIVE_TO_FIELD,
			SUPERSEDED_BY_FIELD,
		],
		order_by="name asc",
	)
	rows = [row for row in rows if _is_selectable_letterhead(row, today, company=company or None)]
	default_letterhead = _get_company_default_letterhead(company) if company else None
	names = _sort_letterheads(rows, company=company or None)
	if default_letterhead and default_letterhead in names:
		names.remove(default_letterhead)
		names.insert(0, default_letterhead)
	if (
		include_current
		and include_current not in names
		and frappe.db.exists(LETTER_HEAD_DOCTYPE, include_current)
	):
		names.append(include_current)
	return names


def _has_crispy_lifecycle_values(doc) -> bool:
	return any(doc.get(fieldname) for fieldname in POLICY_FIELDNAMES)


def _validate_effective_dates(doc) -> None:
	effective_from = doc.get(EFFECTIVE_FROM_FIELD)
	effective_to = doc.get(EFFECTIVE_TO_FIELD)
	if effective_from and effective_to and getdate(effective_to) < getdate(effective_from):
		frappe.throw(_("Effective To cannot be earlier than Effective From."))


def _validate_supersession(doc) -> None:
	superseded_by = doc.get(SUPERSEDED_BY_FIELD)
	if superseded_by and superseded_by == doc.name:
		frappe.throw(_("A Letter Head cannot supersede itself."))


def _set_approval_metadata(doc) -> None:
	if doc.get(STATUS_FIELD) != "Active":
		return
	previous = doc.get_doc_before_save()
	previous_status = previous.get(STATUS_FIELD) if previous else ""
	if previous_status == "Active":
		return
	if not doc.get(APPROVED_BY_FIELD):
		doc.set(APPROVED_BY_FIELD, frappe.session.user)
	if not doc.get(APPROVED_AT_FIELD):
		doc.set(APPROVED_AT_FIELD, now())


def _is_selectable_letterhead(row, today, company: str | None = None) -> bool:
	if row.get("disabled"):
		return False
	if row.get(STATUS_FIELD) != "Active":
		return False
	row_company = (row.get(COMPANY_FIELD) or "").strip()
	if company and row_company and row_company != company:
		return False
	effective_from = row.get(EFFECTIVE_FROM_FIELD)
	if effective_from and getdate(effective_from) > today:
		return False
	effective_to = row.get(EFFECTIVE_TO_FIELD)
	if effective_to and getdate(effective_to) < today:
		return False
	if row.get(SUPERSEDED_BY_FIELD):
		return False
	return True


def _sort_letterheads(rows: list[Any], company: str | None = None) -> list[str]:
	def sort_key(row):
		row_company = (row.get(COMPANY_FIELD) or "").strip()
		company_rank = 0 if company and row_company == company else 1
		effective_from = row.get(EFFECTIVE_FROM_FIELD)
		effective_rank = -getdate(effective_from).toordinal() if effective_from else 0
		return (company_rank, effective_rank, row.get("name") or "")

	return [row.get("name") for row in sorted(rows, key=sort_key)]


def _get_company_default_letterhead(company: str) -> str | None:
	if not company or not frappe.db.exists("Company", company):
		return None
	try:
		meta = frappe.get_meta("Company")
	except Exception:
		return None
	if not meta.get_field("default_letter_head"):
		return None
	return frappe.db.get_value("Company", company, "default_letter_head") or None
