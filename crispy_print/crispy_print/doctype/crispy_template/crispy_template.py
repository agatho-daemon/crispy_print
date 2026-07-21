# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from typing import Any

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from crispy_print.api.v1._common import parse_version
from crispy_print.api.v1.company_context import (
	extract_presentation_settings_company,
	extract_source_company,
)
from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	resolve_effective_presentation_settings,
)
from crispy_print.crispy_print.doctype.crispy_typst_block.crispy_typst_block import (
	resolve_layout_json_typst_blocks,
)
from crispy_print.json_utils import loads_dict_or_empty
from crispy_print.render_contract import (
	TEMPLATE_IMMUTABLE_AFTER_INSERT_FIELDS,
	TEMPLATE_SNAPSHOT_FIELD_MAP,
	TEMPLATE_SNAPSHOT_HASH_FIELDS_V1,
	TEMPLATE_SNAPSHOT_HASH_FIELDS_V2,
)
from crispy_print.template_resolution import (
	TemplateRenderContext,
	is_effective_template_row,
	resolve_active_template_for_context,
	template_resolution_payload,
	template_target_filters,
	validate_resolved_template_target,
)
from crispy_print.template_resolution import (
	get_latest_active_template as get_latest_active_template_for_context,
)

ZEBRA_VERSION = "0.1.0"
ALLOWED_STATUSES = {"Draft", "Approved", "Retired", "Superseded"}
ALLOWED_VERSION_BUMPS = {"minor", "major"}
ALLOWED_SNAPSHOT_HASH_VERSIONS = {"v1", "v2"}
ALLOWED_STATUS_TRANSITIONS = {
	"Draft": {"Draft", "Approved", "Retired"},
	"Approved": {"Approved", "Retired", "Superseded"},
	"Retired": {"Retired"},
	"Superseded": {"Superseded"},
}
IMMUTABLE_AFTER_INSERT_FIELDS = TEMPLATE_IMMUTABLE_AFTER_INSERT_FIELDS
SNAPSHOT_HASH_FIELDS_V1 = TEMPLATE_SNAPSHOT_HASH_FIELDS_V1
SNAPSHOT_HASH_FIELDS_V2 = TEMPLATE_SNAPSHOT_HASH_FIELDS_V2
SNAPSHOT_HASH_FIELDS = SNAPSHOT_HASH_FIELDS_V1


class CrispyTemplate(Document):
	def autoname(self) -> None:
		self.set_source_snapshot()
		self.set_version()
		self.name = build_template_id(
			self.template_name,
			self.company,
			self.version,
		)
		self.template_name = self.name

	def before_insert(self) -> None:
		self.set_source_snapshot()
		self.set_version()
		if self.name:
			self.template_name = self.name
		self.set_snapshot_hash()

	def on_trash(self) -> None:
		if frappe.flags.allow_crispy_template_delete:
			return
		frappe.throw(
			_(
				"Crispy Templates are immutable historical print snapshots and cannot be deleted. "
				"Retire or supersede the template instead."
			),
			frappe.PermissionError,
		)

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
		if self.is_new():
			self.snapshot_hash_version = "v2"
		elif not self.snapshot_hash_version:
			self.snapshot_hash_version = "v1"
		if self.snapshot_hash_version not in ALLOWED_SNAPSHOT_HASH_VERSIONS:
			frappe.throw(_("Invalid snapshot hash version: {0}").format(self.snapshot_hash_version))
		if self.is_new():
			self.zebra_version = self.zebra_version or ZEBRA_VERSION
			self.barcode_symbology = self.barcode_symbology or self.get_barcode_symbology()

	def set_source_snapshot(self) -> None:
		if not self.source_crispy_format:
			return

		source = frappe.get_doc("Crispy Format", self.source_crispy_format)
		source.check_permission("read")

		for format_field, template_field in TEMPLATE_SNAPSHOT_FIELD_MAP:
			self.set(template_field, _snapshot_value_from_source(source, format_field, template_field, self))
		self.typst_version = self.typst_version or get_typst_version()
		self.zebra_version = self.zebra_version or ZEBRA_VERSION
		self.source_branding_profile = self.source_branding_profile or _get_source_branding_profile(
			self.presentation_settings_json,
		)
		self.barcode_symbology = self.barcode_symbology or self.get_barcode_symbology()

	def get_barcode_symbology(self) -> str:
		settings = loads_dict_or_empty(self.presentation_settings_json)
		qr_settings = settings.get("qr") if isinstance(settings, dict) else {}
		if not isinstance(qr_settings, dict):
			return "QR Code"
		value = (
			qr_settings.get("symbology")
			or qr_settings.get("code_symbology")
			or qr_settings.get("code_format")
			or "QR Code"
		)
		return _normalize_barcode_symbology(value)

	def set_version(self) -> None:
		if self.version:
			return
		self.version = self.get_next_version()

	def get_next_version(self, bump: str | None = None) -> str:
		bump = self.get_version_bump(bump)
		latest_major = 0
		latest_minor = -1
		filters = {
			"source_crispy_format": self.source_crispy_format,
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
		payload = {field: self.get(field) for field in self.get_snapshot_hash_fields()}
		encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
		return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

	def get_snapshot_hash_fields(self) -> tuple[str, ...]:
		if (self.snapshot_hash_version or "v1") == "v2":
			return SNAPSHOT_HASH_FIELDS_V2
		return SNAPSHOT_HASH_FIELDS_V1

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
			"source_crispy_format": self.source_crispy_format,
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
			if (
				fieldname == "snapshot_hash_version"
				and not previous.get(fieldname)
				and self.get(fieldname) == "v1"
			):
				continue
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
	company: str | None = None,
) -> dict:
	if not source_crispy_format:
		frappe.throw(_("Source Crispy Format is required."))
	source = frappe.get_doc("Crispy Format", source_crispy_format)
	source.check_permission("read")
	source.check_permission("write")
	_validate_publish_source_company(source)
	_validate_expected_source_company(source, company)

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
	doc.insert(ignore_permissions=True)

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
		"snapshot_hash": doc.snapshot_hash,
		"snapshot_hash_version": doc.snapshot_hash_version,
		"typst_version": doc.typst_version,
		"zebra_version": doc.zebra_version,
		"barcode_symbology": doc.barcode_symbology,
	}


def get_publish_preview(
	source_crispy_format: str,
	version_bump: str = "minor",
	company: str | None = None,
) -> dict:
	if not source_crispy_format:
		frappe.throw(_("Source Crispy Format is required."))
	source = frappe.get_doc("Crispy Format", source_crispy_format)
	source.check_permission("read")
	_validate_publish_source_company(source)
	_validate_expected_source_company(source, company)

	template = frappe.new_doc("Crispy Template")
	template.template_name = get_template_key_for_format(source)
	template.source_crispy_format = source.name
	template.company = _get_source_company(source)
	template.set_source_snapshot()
	next_version = template.get_next_version(version_bump)

	current_version = _get_latest_version(
		template.source_crispy_format,
		template.company,
		template.crispy_format_type,
		template.source_doctype,
		template.source_report,
		template.source_contract,
	)
	template_id = build_template_id(template.template_name, template.company, next_version)
	return {
		"template_name": template_id,
		"template_id": template_id,
		"company": template.company,
		"company_abbr": get_company_abbr(template.company),
		"source_branding_profile": template.source_branding_profile,
		"snapshot_hash_version": template.snapshot_hash_version,
		"zebra_version": template.zebra_version,
		"barcode_symbology": template.barcode_symbology,
		"current_version": current_version,
		"next_version": next_version,
		"version_bump": template.get_version_bump(version_bump),
	}


def _validate_expected_source_company(source, company: str | None = None) -> None:
	expected_company = _clean(company)
	if expected_company and _clean(_get_source_company(source)) != expected_company:
		frappe.throw(_("Source Crispy Format does not belong to company {0}.").format(company))


def _validate_publish_source_company(source) -> None:
	if not _clean(_get_source_company(source)):
		frappe.throw(_("Source Crispy Format company is required to publish a Crispy Template."))


def resolve_active_crispy_template(
	source_doctype: str | None = None,
	source_docname: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
	template_name: str | None = None,
	template: str | None = None,
) -> dict:
	return resolve_active_template_for_context(
		TemplateRenderContext(
			source_doctype=source_doctype,
			source_docname=source_docname,
			source_report=source_report,
			source_contract=source_contract,
			company=company,
			template=template,
			template_name=template_name,
		)
	)


def _template_target_filters(
	source_doctype: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	template_name: str | None = None,
) -> dict:
	return template_target_filters(
		TemplateRenderContext(
			source_doctype=source_doctype,
			source_report=source_report,
			source_contract=source_contract,
			template_name=template_name,
		),
		include_template_name=True,
	)


def _get_latest_active_template(
	filters: dict,
	expected_company: str | None = None,
) -> CrispyTemplate | None:
	return get_latest_active_template_for_context(filters, expected_company=expected_company)


def _is_effective_now(row: dict, now) -> bool:
	return is_effective_template_row(row, now=now)


def _validate_resolved_template_target(
	doc: CrispyTemplate,
	source_doctype: str | None = None,
	source_report: str | None = None,
	source_contract: str | None = None,
	company: str | None = None,
) -> None:
	return validate_resolved_template_target(
		doc,
		TemplateRenderContext(
			source_doctype=source_doctype,
			source_report=source_report,
			source_contract=source_contract,
		),
		company=company,
	)


def _template_resolution_payload(
	doc: CrispyTemplate,
	effective_company: str | None,
	resolution_reason: str,
) -> dict:
	return template_resolution_payload(doc, effective_company, resolution_reason)


def build_template_id(template_name: str, company: str | None, version: str) -> str:
	scope = get_company_abbr(company) or "global"
	return f"{_slug_part(template_name)}-{_slug_part(scope)}-v{_slug_version(version)}"


def get_template_key_for_format(source: Document) -> str:
	return _clean(source.get("name"))


def get_company_abbr(company: str | None) -> str:
	if not company:
		return ""
	return _clean(frappe.db.get_value("Company", company, "abbr")) or _clean(company)


def get_typst_version() -> str:
	try:
		from crispy_print.api.v1.compile import get_cached_typst_version

		return get_cached_typst_version()
	except Exception:
		return ""


def _snapshot_value_from_source(
	source: Document,
	format_field: str,
	template_field: str,
	template: CrispyTemplate,
) -> Any:
	if template_field == "source_report":
		return _get_source_report(source)
	if template_field == "company":
		if template.company is not None:
			return template.company
		return _get_source_company(source)
	if template_field == "pdf_standard":
		return source.get(format_field) or template.pdf_standard or "PDF/A-2u"
	if template_field == "raw_typst":
		return 1 if source.get("raw_typst") else 0
	if template_field in {
		"compact_item_print",
		"print_uom_after_quantity",
		"print_taxes_with_zero_amount",
	}:
		return 1 if source.get(format_field) else 0
	if template_field == "presentation_settings_json":
		presentation_settings = resolve_effective_presentation_settings(
			loads_dict_or_empty(source.get(format_field)),
			company=template.company,
		)
		return json.dumps(
			presentation_settings,
			sort_keys=True,
			separators=(",", ":"),
			default=str,
		)
	if template_field == "layout_json":
		layout_json = source.get(format_field) or ""
		if layout_json and template.source_doctype:
			return resolve_layout_json_typst_blocks(
				layout_json,
				template.source_doctype,
				company=template.company,
			)
		return layout_json
	if template_field in {"doc_header", "doc_footer", "typst_preamble", "typst_code"}:
		return source.get(format_field) or ""
	return source.get(format_field)


def _get_source_company(source: Document) -> str | None:
	return extract_source_company(source)


def _get_presentation_settings_company(presentation_settings_json: str | None) -> str | None:
	return extract_presentation_settings_company(presentation_settings_json)


def _get_source_branding_profile(presentation_settings_json: str | None) -> str | None:
	settings = loads_dict_or_empty(presentation_settings_json)
	branding = settings.get("branding") or {}
	if settings.get("source") == "branding_profile":
		return _clean(branding.get("profile")) or None
	return None


def _get_latest_version(
	source_crispy_format: str,
	company: str | None,
	crispy_format_type: str | None,
	source_doctype: str | None,
	source_report: str | None,
	source_contract: str | None,
) -> str | None:
	filters = {
		"source_crispy_format": source_crispy_format,
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
			"source_crispy_format": template.source_crispy_format,
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


def _slug_part(value: Any) -> str:
	slug = re.sub(r"[^a-z0-9]+", "_", _clean(value).lower()).strip("_")
	return slug or "template"


def _slug_version(value: Any) -> str:
	slug = re.sub(r"[^a-z0-9.]+", "_", _clean(value).lower()).strip("_.")
	return slug or "0.0"


def _normalize_barcode_symbology(value: Any) -> str:
	raw = _clean(value).lower()
	if raw in {"datamatrix", "data matrix", "data_matrix"}:
		return "DataMatrix"
	return "QR Code"


def _parse_version(value: Any) -> tuple[int, int]:
	return parse_version(value)


def _get_source_report(source: Document) -> str | None:
	report_value = source.get("report")
	if isinstance(report_value, str):
		return report_value or None
	if isinstance(report_value, list):
		for row in report_value:
			if row.get("report") and not row.get("disabled"):
				return row.get("report")
	return None
