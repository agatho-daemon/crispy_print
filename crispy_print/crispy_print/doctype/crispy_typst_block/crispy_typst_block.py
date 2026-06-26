# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import copy
import json
import re

import frappe
from frappe import _
from frappe.model.document import Document

BLOCK_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")

PUBLIC_FIELDS = [
	"name",
	"block_name",
	"company",
	"block_key",
	"enabled",
	"category",
	"description",
	"typst_code",
	"version",
]

MAX_TYPST_BLOCK_ID_LENGTH = 140


def build_typst_block_id(block_name: str | None) -> str:
	base = slugify_typst_block_name(block_name)
	if not frappe.db.exists("Crispy Typst Block", base):
		return base

	suffix = 2
	while True:
		candidate_suffix = f"-{suffix}"
		candidate = f"{base[: MAX_TYPST_BLOCK_ID_LENGTH - len(candidate_suffix)]}{candidate_suffix}"
		if not frappe.db.exists("Crispy Typst Block", candidate):
			return candidate
		suffix += 1


def slugify_typst_block_name(block_name: str | None) -> str:
	slug = re.sub(r"[^a-z0-9]+", "-", (block_name or "").strip().lower()).strip("-")
	return (slug or "typst-block")[:MAX_TYPST_BLOCK_ID_LENGTH]


class CrispyTypstBlock(Document):
	def before_naming(self) -> None:
		self.normalize_block_key()

	def autoname(self) -> None:
		self.normalize_block_key()
		self.name = build_typst_block_id(self.get("block_name"))

	def validate(self) -> None:
		self.validate_block_key()
		self.validate_unique_block_key_for_company()
		self.validate_unique_applicable_documents()

	def normalize_block_key(self) -> None:
		self.block_key = (self.block_key or "").strip()

	def validate_block_key(self) -> None:
		self.normalize_block_key()

		if not self.block_key:
			frappe.throw(_("Reference Key is required."))

		if not BLOCK_KEY_PATTERN.match(self.block_key):
			frappe.throw(
				_(
					"Reference Key must start with a lowercase letter and contain only lowercase letters, numbers, and single underscores."
				)
			)

	def validate_unique_block_key_for_company(self) -> None:
		company = (self.company or "").strip()
		existing = frappe.get_all(
			"Crispy Typst Block",
			filters={"block_key": self.block_key, "name": ["!=", self.name or ""]},
			fields=["name", "company"],
		)
		if any((row.get("company") or "").strip() == company for row in existing):
			scope = company or _("global")
			frappe.throw(
				_("Reference Key {0} already exists for {1} scope.").format(
					frappe.bold(self.block_key),
					frappe.bold(scope),
				)
			)

	def validate_unique_applicable_documents(self) -> None:
		seen: set[str] = set()

		for row in self.applicable_documents or []:
			if not row.document_type:
				frappe.throw(_("Document Type is required in Applicable Documents."))

			if row.document_type in seen:
				frappe.throw(
					_("Document Type {0} is listed more than once in Applicable Documents.").format(
						frappe.bold(row.document_type)
					)
				)

			seen.add(row.document_type)

	def get_applicable_document_types(self) -> list[str]:
		return [row.document_type for row in self.applicable_documents or [] if row.document_type]

	def applies_to_doctype(self, doctype: str) -> bool:
		document_types = self.get_applicable_document_types()

		if not document_types:
			return True

		return doctype in document_types


def get_typst_block(
	block_key: str,
	enabled_only: bool = True,
	company: str | None = None,
) -> CrispyTypstBlock:
	filters = {"block_key": block_key}
	if enabled_only:
		filters["enabled"] = 1

	rows = [
		row
		for row in frappe.get_all(
			"Crispy Typst Block",
			filters=filters,
			fields=["name", "company"],
			order_by="modified desc",
		)
		if _row_matches_company_scope(row, company)
	]
	name = _select_company_scoped_row(rows, company).get("name") if rows else None
	if not name:
		frappe.throw(_("Crispy Typst Block {0} was not found.").format(frappe.bold(block_key)))

	return frappe.get_doc("Crispy Typst Block", name)


def get_applicable_typst_blocks(
	doctype: str,
	enabled_only: bool = True,
	category: str | None = None,
	company: str | None = None,
) -> list[dict]:
	filters: dict[str, object] = {}
	if enabled_only:
		filters["enabled"] = 1
	if category:
		filters["category"] = category

	rows = [
		row
		for row in frappe.get_all(
			"Crispy Typst Block",
			filters=filters,
			fields=PUBLIC_FIELDS,
			order_by="category asc, block_name asc",
		)
		if _row_matches_company_scope(row, company)
	]
	if not rows:
		return []

	names = [row["name"] for row in rows]
	child_doctype = "Crispy Typst Block Applicable Document"
	restricted_names = set(frappe.get_all(child_doctype, filters={"parent": ["in", names]}, pluck="parent"))
	matching_names = set(
		frappe.get_all(
			child_doctype,
			filters={"parent": ["in", names], "document_type": doctype},
			pluck="parent",
		)
	)

	applicable_rows = [
		row for row in rows if row["name"] not in restricted_names or row["name"] in matching_names
	]
	return _prefer_company_scoped_blocks(applicable_rows, company)


def resolve_layout_typst_blocks(
	layout: dict | list | None,
	doctype: str,
	company: str | None = None,
) -> dict | list | None:
	"""Hydrate Crispy Typst Block layout references with transient Typst code.

	The stored layout remains reference-only. This helper returns a deep copy with
	``crispy_typst_block_code`` and ``crispy_typst_block_name`` filled where a block
	is enabled and applicable to the current DocType.
	"""
	if layout is None:
		return None
	if not doctype:
		return copy.deepcopy(layout)

	resolved = copy.deepcopy(layout)
	fields = _get_typst_block_layout_fields(resolved)
	if not fields:
		return resolved

	blocks = get_applicable_typst_blocks(doctype, enabled_only=True, company=company)
	by_key = {block.get("block_key"): block for block in blocks}

	for field in fields:
		block_key = str(field.get("crispy_typst_block") or "").strip()
		if not block_key:
			_clear_transient_typst_block_fields(field)
			continue

		block = by_key.get(block_key)
		if not block:
			_clear_transient_typst_block_fields(field)
			continue

		field["crispy_typst_block_name"] = block.get("block_name") or ""
		field["crispy_typst_block_code"] = block.get("typst_code") or ""

	return resolved


def resolve_layout_json_typst_blocks(
	layout_json: str | None,
	doctype: str,
	company: str | None = None,
) -> str | None:
	"""Parse layout JSON and return JSON with CTB references hydrated for rendering."""
	if not layout_json:
		return layout_json

	layout = json.loads(layout_json)
	resolved = resolve_layout_typst_blocks(layout, doctype, company=company)
	return json.dumps(resolved)


def _row_matches_company_scope(row: dict, company: str | None) -> bool:
	row_company = (row.get("company") or "").strip()
	if not row_company:
		return True

	company = (company or "").strip()
	return bool(company and row_company == company)


def _select_company_scoped_row(rows: list[dict], company: str | None) -> dict:
	company = (company or "").strip()
	if company:
		for row in rows:
			if (row.get("company") or "") == company:
				return row
	return rows[0]


def _prefer_company_scoped_blocks(rows: list[dict], company: str | None) -> list[dict]:
	company = (company or "").strip()
	by_key: dict[str, dict] = {}

	for row in rows:
		block_key = row.get("block_key")
		if not block_key:
			continue

		current = by_key.get(block_key)
		if not current:
			by_key[block_key] = row
			continue

		if company and (row.get("company") or "") == company:
			by_key[block_key] = row

	return sorted(
		by_key.values(),
		key=lambda row: ((row.get("category") or ""), (row.get("block_name") or "")),
	)


def _get_typst_block_layout_fields(node) -> list[dict]:
	fields: list[dict] = []

	def visit(value) -> None:
		if isinstance(value, dict):
			if value.get("fieldtype") == "Crispy Typst Block":
				fields.append(value)
			for child in value.values():
				visit(child)
		elif isinstance(value, list):
			for child in value:
				visit(child)

	visit(node)
	return fields


def _clear_transient_typst_block_fields(field: dict) -> None:
	field.pop("crispy_typst_block_code", None)
	field.pop("crispy_typst_block_name", None)
