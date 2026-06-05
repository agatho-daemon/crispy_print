# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import hashlib
import json
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	resolve_effective_presentation_settings,
)
from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	resolve_layout_json_typst_blocks,
)

ALLOWED_STATUSES = {"Draft", "Approved", "Retired", "Superseded"}
ALLOWED_VERSION_BUMPS = {"minor", "major"}
ALLOWED_STATUS_TRANSITIONS = {
	"Draft": {"Draft", "Approved", "Retired"},
	"Approved": {"Approved", "Retired", "Superseded"},
	"Retired": {"Retired"},
	"Superseded": {"Superseded"},
}
IMMUTABLE_AFTER_INSERT_FIELDS = {
	"template_name",
	"company",
	"version",
	"source_crispy_format",
	"source_branding_profile",
	"crispy_format_type",
	"source_doctype",
	"source_report",
	"source_contract",
	"pdf_standard",
	"raw_typst",
	"typst_version",
	"layout_json",
	"presentation_settings_json",
	"doc_header",
	"doc_footer",
	"typst_preamble",
	"typst_code",
	"snapshot_hash",
	"approved_by",
	"approved_at",
	"retired_by",
	"retired_at",
}
SNAPSHOT_HASH_FIELDS = (
	"template_name",
	"company",
	"version",
	"source_crispy_format",
	"source_branding_profile",
	"crispy_format_type",
	"source_doctype",
	"source_report",
	"source_contract",
	"pdf_standard",
	"raw_typst",
	"typst_version",
	"layout_json",
	"presentation_settings_json",
	"doc_header",
	"doc_footer",
	"typst_preamble",
	"typst_code",
)


class CrispyTemplate(Document):
	def autoname(self) -> None:
		self.set_source_snapshot()
		self.set_version()
		self.name = build_template_id(
			self.template_name,
			self.company,
			self.version,
		)

	def before_insert(self) -> None:
		self.set_source_snapshot()
		self.set_version()
		self.set_snapshot_hash()

	def validate(self) -> None:
		self.set_defaults()
		if self.is_new():
			self.set_source_snapshot()
		if self.is_new() and not self.version:
			self.set_version()
		self.validate_status()
		self.validate_effective_dates()
		self.validate_company_scope()
		self.validate_source_target()
		self.validate_render_snapshot()
		self.validate_json_fields()
		self.validate_unique_active_scope()
		self.set_snapshot_hash()
		self.validate_snapshot_hash()
		self.validate_status_transition()
		self.validate_immutable_fields()
		self.sync_status_metadata()

	def set_defaults(self) -> None:
		self.status = self.status or "Draft"
		self.pdf_standard = self.pdf_standard or "PDF/A-2u"

	def set_source_snapshot(self) -> None:
		if not self.source_crispy_format:
			return

		source = frappe.get_doc("Crispy Format", self.source_crispy_format)
		source.check_permission("read")

		self.crispy_format_type = source.get("crispy_format_type")
		self.source_doctype = source.get("doc_type")
		self.source_report = _get_source_report(source)
		self.source_contract = source.get("contract")
		self.pdf_standard = source.get("pdf_standard") or self.pdf_standard or "PDF/A-2u"
		self.raw_typst = 1 if source.get("raw_typst") or source.get("is_advanced") else 0
		if self.company is None:
			self.company = source.get("company") or _get_presentation_settings_company(
				source.get("presentation_settings"),
			)
		presentation_settings = resolve_effective_presentation_settings(
			_parse_json(source.get("presentation_settings")),
			company=self.company,
		)
		self.presentation_settings_json = json.dumps(
			presentation_settings,
			sort_keys=True,
			separators=(",", ":"),
			default=str,
		)
		self.layout_json = source.get("layout_json") or ""
		if self.layout_json and self.source_doctype:
			self.layout_json = resolve_layout_json_typst_blocks(
				self.layout_json,
				self.source_doctype,
				company=self.company,
			)
		self.doc_header = source.get("doc_header") or ""
		self.doc_footer = source.get("doc_footer") or ""
		self.typst_preamble = source.get("typst_preamble") or ""
		self.typst_code = source.get("typst_code") or ""
		self.source_branding_profile = self.source_branding_profile or _get_source_branding_profile(
			self.presentation_settings_json,
		)

	def set_version(self) -> None:
		if self.version:
			return
		self.version = self.get_next_version()

	def get_next_version(self, bump: str | None = None) -> str:
		bump = self.get_version_bump(bump)
		latest_major = 0
		latest_minor = -1
		filters = {
			"template_name": self.template_name,
			"crispy_format_type": self.crispy_format_type,
			"source_doctype": self.source_doctype,
			"source_report": self.source_report,
			"source_contract": self.source_contract,
			"name": ["!=", self.name or ""],
		}
		rows = frappe.get_all(
			"Crispy Template",
			filters={key: value for key, value in filters.items() if value not in (None, "")},
			fields=["name", "company", "version"],
		)
		company = _clean(self.company)
		for row in rows:
			if _clean(row.get("company")) != company:
				continue
			major, minor = _parse_version(row.get("version"))
			if (major, minor) > (latest_major, latest_minor):
				latest_major, latest_minor = major, minor

		if latest_minor < 0:
			return "1.0"
		if bump == "major":
			return f"{latest_major + 1}.0"
		return f"{latest_major}.{latest_minor + 1}"

	def get_version_bump(self, bump: str | None = None) -> str:
		value = (bump or self.flags.get("template_version_bump") or "minor").strip().lower()
		if value not in ALLOWED_VERSION_BUMPS:
			frappe.throw(_("Invalid template version bump: {0}").format(value))
		return value

	def set_snapshot_hash(self) -> None:
		self.snapshot_hash = self.compute_snapshot_hash()

	def compute_snapshot_hash(self) -> str:
		payload = {field: self.get(field) for field in SNAPSHOT_HASH_FIELDS}
		encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
		return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

	def validate_snapshot_hash(self) -> None:
		if not self.snapshot_hash:
			frappe.throw(_("Snapshot Hash is required."))
		if self.snapshot_hash != self.compute_snapshot_hash():
			frappe.throw(_("Snapshot Hash does not match the frozen template snapshot."))

	def validate_status(self) -> None:
		if self.status not in ALLOWED_STATUSES:
			frappe.throw(_("Invalid Crispy Template status: {0}").format(self.status))
		if self.status == "Superseded":
			if not self.superseded_by:
				frappe.throw(_("Superseded By is required when status is Superseded."))
			if self.superseded_by == self.name:
				frappe.throw(_("A Crispy Template cannot supersede itself."))

	def validate_effective_dates(self) -> None:
		if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
			frappe.throw(_("Effective From cannot be after Effective To."))

	def validate_company_scope(self) -> None:
		if self.source_crispy_format and self.company:
			source_company = frappe.db.get_value("Crispy Format", self.source_crispy_format, "company")
			if source_company and source_company != self.company:
				frappe.throw(_("Crispy Template company must match the source Crispy Format company."))

		if self.source_branding_profile and self.company:
			branding_company = frappe.db.get_value(
				"Crispy Branding Profile",
				self.source_branding_profile,
				"company",
			)
			if branding_company and branding_company != self.company:
				frappe.throw(_("Crispy Template company must match the source Branding Profile company."))

	def validate_source_target(self) -> None:
		if self.crispy_format_type == "DocType" and not self.source_doctype:
			frappe.throw(_("Source DocType is required for DocType templates."))
		if self.crispy_format_type == "Report" and not self.source_report:
			frappe.throw(_("Source Report is required for Report templates."))
		if self.crispy_format_type == "Contract" and not self.source_contract:
			frappe.throw(_("Source Contract is required for Contract templates."))

	def validate_render_snapshot(self) -> None:
		if self.raw_typst:
			if not (self.typst_code or "").strip():
				frappe.throw(_("Typst Code is required for raw Typst templates."))
			return

		if not (self.layout_json or "").strip():
			frappe.throw(_("Layout JSON is required for visual templates."))

	def validate_json_fields(self) -> None:
		for fieldname in ("layout_json", "presentation_settings_json"):
			value = self.get(fieldname)
			if not value:
				continue
			try:
				json.loads(value)
			except json.JSONDecodeError:
				frappe.throw(_("{0} must contain valid JSON.").format(frappe.unscrub(fieldname)))

	def validate_unique_active_scope(self) -> None:
		if not self.is_active or self.status != "Approved" or self.flags.skip_active_template_uniqueness:
			return

		filters = {
			"template_name": self.template_name,
			"crispy_format_type": self.crispy_format_type,
			"source_doctype": self.source_doctype,
			"source_report": self.source_report,
			"source_contract": self.source_contract,
			"status": "Approved",
			"is_active": 1,
			"name": ["!=", self.name or ""],
		}
		rows = frappe.get_all(
			"Crispy Template",
			filters={key: value for key, value in filters.items() if value not in (None, "")},
			fields=["name", "company"],
		)
		expected_company = _clean(self.company)
		existing = next(
			(row.get("name") for row in rows if _clean(row.get("company")) == expected_company),
			None,
		)
		if existing:
			frappe.throw(
				_("An active Crispy Template already exists for this template scope: {0}.").format(
					frappe.bold(existing)
				)
			)

	def validate_status_transition(self) -> None:
		if self.is_new():
			return
		previous = self.get_doc_before_save()
		if not previous:
			return

		old_status = previous.get("status") or "Draft"
		new_status = self.status or "Draft"
		if new_status not in ALLOWED_STATUS_TRANSITIONS.get(old_status, {old_status}):
			frappe.throw(
				_("Cannot change Crispy Template status from {0} to {1}.").format(
					old_status,
					new_status,
				)
			)

	def validate_immutable_fields(self) -> None:
		if self.is_new() or self.flags.allow_template_state_transition:
			return
		previous = self.get_doc_before_save()
		if not previous:
			return

		for fieldname in IMMUTABLE_AFTER_INSERT_FIELDS:
			if self.get(fieldname) != previous.get(fieldname):
				frappe.throw(
					_("Crispy Template field {0} is immutable after creation.").format(
						frappe.bold(frappe.unscrub(fieldname))
					)
				)

	def sync_status_metadata(self) -> None:
		now = now_datetime()
		user = frappe.session.user

		if self.status == "Approved" and not self.approved_at:
			self.approved_by = user
			self.approved_at = now
		if self.status == "Retired" and not self.retired_at:
			self.retired_by = user
			self.retired_at = now
			self.effective_to = self.effective_to or now
		if self.status == "Superseded":
			self.effective_to = self.effective_to or now


def publish_crispy_template(
	source_crispy_format: str,
	version_bump: str = "minor",
	make_active: bool = True,
	effective_from: str | None = None,
	notes: str | None = None,
) -> dict:
	if not source_crispy_format:
		frappe.throw(_("Source Crispy Format is required."))
	source = frappe.get_doc("Crispy Format", source_crispy_format)
	source.check_permission("read")

	doc = frappe.get_doc(
		{
			"doctype": "Crispy Template",
			"template_name": get_template_key_for_format(source),
			"source_crispy_format": source.name,
			"company": _get_source_company(source),
			"status": "Approved",
			"is_active": 1 if make_active else 0,
			"effective_from": effective_from or now_datetime(),
			"notes": notes or "",
		}
	)
	doc.flags.template_version_bump = version_bump
	doc.flags.skip_active_template_uniqueness = bool(make_active)
	doc.insert()

	if make_active:
		_supersede_previous_active_templates(doc)

	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"company": doc.company,
		"company_abbr": get_company_abbr(doc.company),
		"version": doc.version,
		"status": doc.status,
		"is_active": bool(doc.is_active),
		"source_branding_profile": doc.source_branding_profile,
	}


def get_publish_preview(source_crispy_format: str, version_bump: str = "minor") -> dict:
	if not source_crispy_format:
		frappe.throw(_("Source Crispy Format is required."))
	source = frappe.get_doc("Crispy Format", source_crispy_format)
	source.check_permission("read")

	template = frappe.new_doc("Crispy Template")
	template.template_name = get_template_key_for_format(source)
	template.source_crispy_format = source.name
	template.company = _get_source_company(source)
	template.set_source_snapshot()
	next_version = template.get_next_version(version_bump)

	current_version = _get_latest_version(
		template.template_name,
		template.company,
		template.crispy_format_type,
		template.source_doctype,
		template.source_report,
		template.source_contract,
	)
	return {
		"template_name": template.template_name,
		"template_id": build_template_id(template.template_name, template.company, next_version),
		"company": template.company,
		"company_abbr": get_company_abbr(template.company),
		"source_branding_profile": template.source_branding_profile,
		"current_version": current_version,
		"next_version": next_version,
		"version_bump": template.get_version_bump(version_bump),
	}


def resolve_active_crispy_template(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
	template_name: str | None = None,
	template: str | None = None,
) -> dict:
	from crispy_print.api.v1.company_context import resolve_effective_company

	effective_company = resolve_effective_company(
		source_doctype=source_doctype,
		source_docname=source_docname,
		explicit_company=company,
		allow_global_fallback=False,
	)
	if template:
		doc = frappe.get_doc("Crispy Template", template)
		doc.check_permission("read")
		_validate_resolved_template_target(
			doc,
			source_doctype=source_doctype,
			source_report=source_report,
			source_contract=source_contract,
			company=effective_company,
		)
		return _template_resolution_payload(doc, effective_company, "explicit")

	target_filters = _template_target_filters(
		source_doctype=source_doctype,
		source_report=source_report,
		source_contract=source_contract,
		template_name=template_name,
	)
	if not target_filters.get("crispy_format_type"):
		frappe.throw(_("Template target is required."))

	base_filters = {
		**target_filters,
		"status": "Approved",
		"is_active": 1,
	}

	if effective_company:
		doc = _get_latest_active_template({**base_filters, "company": effective_company})
		if doc:
			return _template_resolution_payload(doc, effective_company, "company")

	doc = _get_latest_active_template(base_filters, expected_company="")
	if doc:
		return _template_resolution_payload(doc, effective_company, "global")

	frappe.throw(_("No active Crispy Template found for this document context."))


def _template_target_filters(
	source_doctype: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	template_name: str | None = None,
) -> dict:
	filters = {}
	if source_doctype:
		filters.update({"crispy_format_type": "DocType", "source_doctype": source_doctype})
	elif source_report:
		filters.update({"crispy_format_type": "Report", "source_report": source_report})
	elif source_contract:
		filters.update({"crispy_format_type": "Contract", "source_contract": source_contract})
	if template_name:
		filters["template_name"] = template_name
	return filters


def _get_latest_active_template(
	filters: dict,
	expected_company: str | None = None,
) -> CrispyTemplate | None:
	rows = frappe.get_all(
		"Crispy Template",
		filters={key: value for key, value in filters.items() if value not in (None, "")},
		fields=["name", "company", "version", "effective_from", "effective_to"],
	)
	if expected_company is not None:
		rows = [row for row in rows if _clean(row.get("company")) == _clean(expected_company)]
	now = now_datetime()
	rows = [row for row in rows if _is_effective_now(row, now)]
	if not rows:
		return None
	rows.sort(key=lambda row: str(row.get("name") or ""))
	rows.sort(key=lambda row: _parse_version(row.get("version")), reverse=True)
	rows.sort(key=lambda row: str(row.get("effective_from") or ""), reverse=True)
	return frappe.get_doc("Crispy Template", rows[0].get("name"))


def _is_effective_now(row: dict, now) -> bool:
	if row.get("effective_from") and row.get("effective_from") > now:
		return False
	if row.get("effective_to") and row.get("effective_to") < now:
		return False
	return True


def _validate_resolved_template_target(
	doc: CrispyTemplate,
	source_doctype: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
) -> None:
	if doc.status != "Approved" or not doc.is_active:
		frappe.throw(_("Selected Crispy Template is not an active approved template."))
	if source_doctype and doc.source_doctype != source_doctype:
		frappe.throw(_("Selected Crispy Template does not match the source DocType."))
	if source_report and doc.source_report != source_report:
		frappe.throw(_("Selected Crispy Template does not match the source Report."))
	if source_contract and doc.source_contract != source_contract:
		frappe.throw(_("Selected Crispy Template does not match the source Contract."))
	if doc.company and company and doc.company != company:
		frappe.throw(_("Selected Crispy Template does not belong to company {0}.").format(company))


def _template_resolution_payload(
	doc: CrispyTemplate,
	effective_company: str | None,
	resolution_reason: str,
) -> dict:
	return {
		"name": doc.name,
		"template_name": doc.template_name,
		"template_id": build_template_id(doc.template_name, doc.company, doc.version),
		"company": doc.company,
		"company_abbr": get_company_abbr(doc.company),
		"effective_company": effective_company,
		"scope": "Company" if doc.company else "Global",
		"version": doc.version,
		"resolution_reason": resolution_reason,
		"source_crispy_format": doc.source_crispy_format,
		"source_branding_profile": doc.source_branding_profile,
		"crispy_format_type": doc.crispy_format_type,
		"source_doctype": doc.source_doctype,
		"source_report": doc.source_report,
		"source_contract": doc.source_contract,
		"pdf_standard": doc.pdf_standard,
		"raw_typst": bool(doc.raw_typst),
		"layout_json": doc.layout_json,
		"presentation_settings": doc.presentation_settings_json,
		"doc_header": doc.doc_header,
		"doc_footer": doc.doc_footer,
		"typst_preamble": doc.typst_preamble,
		"typst_code": doc.typst_code,
		"snapshot_hash": doc.snapshot_hash,
	}


def build_template_id(template_name: str, company: str | None, version: str) -> str:
	scope = get_company_abbr(company) or "Global"
	return f"{_clean(template_name)} - {scope} - v{_clean(version)}"


def get_template_key_for_format(source: Document) -> str:
	return _clean(source.get("name"))


def get_company_abbr(company: str | None) -> str:
	if not company:
		return ""
	return _clean(frappe.db.get_value("Company", company, "abbr")) or _clean(company)


def _get_source_company(source: Document) -> str | None:
	return source.get("company") or _get_presentation_settings_company(source.get("presentation_settings"))


def _get_presentation_settings_company(presentation_settings_json: str | None) -> str | None:
	settings = _parse_json(presentation_settings_json)
	branding = settings.get("branding") or {}
	logo = branding.get("logo") or {}
	return _clean(branding.get("company") or logo.get("company")) or None


def _get_source_branding_profile(presentation_settings_json: str | None) -> str | None:
	settings = _parse_json(presentation_settings_json)
	branding = settings.get("branding") or {}
	if settings.get("source") == "branding_profile":
		return _clean(branding.get("profile")) or None
	return None


def _parse_json(value: str | None) -> dict:
	if not value:
		return {}
	try:
		parsed = json.loads(value)
	except (TypeError, json.JSONDecodeError):
		return {}
	return parsed if isinstance(parsed, dict) else {}


def _get_latest_version(
	template_name: str,
	company: str | None,
	crispy_format_type: str | None,
	source_doctype: str | None,
	source_report: str | None,
	source_contract: str | None,
) -> str | None:
	filters = {
		"template_name": template_name,
		"company": company,
		"crispy_format_type": crispy_format_type,
		"source_doctype": source_doctype,
		"source_report": source_report,
		"source_contract": source_contract,
	}
	rows = frappe.get_all(
		"Crispy Template",
		filters={key: value for key, value in filters.items() if value not in (None, "")},
		fields=["company", "version"],
	)
	expected_company = _clean(company)
	latest: tuple[int, int] | None = None
	latest_value = None
	for row in rows:
		if _clean(row.get("company")) != expected_company:
			continue
		version = row.get("version")
		parsed = _parse_version(version)
		if latest is None or parsed > latest:
			latest = parsed
			latest_value = version
	return latest_value


def _supersede_previous_active_templates(template: CrispyTemplate) -> None:
	rows = frappe.get_all(
		"Crispy Template",
		filters={
			"template_name": template.template_name,
			"crispy_format_type": template.crispy_format_type,
			"source_doctype": template.source_doctype,
			"source_report": template.source_report,
			"source_contract": template.source_contract,
			"is_active": 1,
			"name": ["!=", template.name],
		},
		fields=["name", "company"],
	)
	expected_company = _clean(template.company)
	for row in rows:
		if _clean(row.get("company")) != expected_company:
			continue
		previous = frappe.get_doc("Crispy Template", row.get("name"))
		previous.flags.allow_template_state_transition = True
		previous.status = "Superseded"
		previous.superseded_by = template.name
		previous.is_active = 0
		previous.save(ignore_permissions=True)


def _clean(value: Any) -> str:
	return str(value or "").strip()


def _parse_version(value: Any) -> tuple[int, int]:
	major_raw, _, minor_raw = str(value or "0.0").partition(".")
	try:
		major = int(major_raw)
	except (TypeError, ValueError):
		major = 0
	try:
		minor = int(minor_raw or 0)
	except (TypeError, ValueError):
		minor = 0
	return major, minor


def _get_source_report(source: Document) -> str | None:
	report_value = source.get("report")
	if isinstance(report_value, str):
		return report_value or None
	if isinstance(report_value, list):
		for row in report_value:
			if row.get("report") and not row.get("disabled"):
				return row.get("report")
	return None
