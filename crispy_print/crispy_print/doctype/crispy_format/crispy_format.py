# Copyright (c) 2025, Agathodaemon and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crispy_print.api.v1.company_context import resolve_effective_company


class CrispyFormat(Document):
	def _set_default_company_if_missing(self) -> None:
		if self.company:
			return

		self.company = resolve_effective_company(allow_global_fallback=True)

	def _invalidate_doctype_formats_cache(self):
		from crispy_print.api.v1.formats import invalidate_crispy_formats_cache_for_doctype

		invalidate_crispy_formats_cache_for_doctype(self.doc_type)

		previous = self.get_doc_before_save()
		if previous and previous.doc_type != self.doc_type:
			invalidate_crispy_formats_cache_for_doctype(previous.doc_type)

	def _get_linked_reports(self) -> list:
		"""Return non-disabled linked report rows from report child table."""
		rows = self.get("report") or []
		return [row for row in rows if row.get("report") and not row.get("disabled")]

	def autoname(self):
		"""Auto-generate name for generic templates"""
		if self.crispy_format_type == "Report" and self.is_generic and self.generic_report_type:
			# Format: "Generic Report - Grid", "Generic Report - Tree", etc.
			self.name = f"Generic Report - {self.generic_report_type}"

	def before_insert(self):
		"""Clear is_default when duplicating a format"""
		if self.is_default and self._is_duplicate_insert():
			self.is_default = 0

		# Set default template for new Report formats
		if self.crispy_format_type == "Report" and self.is_generic and not self.typst_code:
			self._set_default_report_template()

	def _is_duplicate_insert(self) -> bool:
		"""Return true when caller explicitly marks this insert as a copied document."""
		return bool(
			self.flags.get("from_copy")
			or self.flags.get("copied_from")
			or self.get("_copied_from")
			or self.get("__copied_from")
		)

	def _set_default_report_template(self):
		"""Load default Typst template for Report mode"""
		from pathlib import Path

		app_path = frappe.get_app_path("crispy_print")
		template_path = Path(app_path).parent / "REPORT_TEMPLATE_DEFAULT.typ"

		if template_path.exists():
			self.typst_code = template_path.read_text(encoding="utf-8")
		else:
			# Fallback inline template
			self.typst_code = """// Generic Report Template
// Available data: #data.title, #data.columns, #data.rows, #data.filters

#set page(
  paper: "a4",
  margin: (x: 1.5cm, y: 2cm),
  flipped: data.presentation_settings.page.orientation == "landscape",
  header: header_block,
  footer: footer_block,
)

#align(center)[
  #text(size: 16pt, weight: "bold")[#data.title]
  #v(0.3em)
  #text(size: 9pt, fill: rgb("#666"))[#data.subtitle]
]

#v(1em)

// Table
#let cp_column_width(col) = {
  if "width_kind" in col {
    if col.width_kind == "auto" { auto }
    else if col.width_kind == "fr" { col.width_value * 1fr }
    else if col.width_kind == "pt" { col.width_value * 1pt }
    else if col.width_kind == "em" { col.width_value * 1em }
    else if col.width_kind == "rem" { col.width_value * 1em }
    else if col.width_kind == "%" { col.width_value * 1% }
    else if col.width_kind == "cm" { col.width_value * 1cm }
    else if col.width_kind == "mm" { col.width_value * 1mm }
    else if col.width_kind == "in" { col.width_value * 1in }
    else { auto }
  } else { auto }
}

#table(
  columns: data.columns.map(cp_column_width),
  stroke: 0.5pt,
  inset: 8pt,
  align: (x, y) => if y == 0 { center } else if data.columns.at(x).is_numeric { right } else { left },

  // Header
  ..data.columns.map(col => text(weight: "bold")[#col.label]),

  // Rows
  ..data.rows.map(row => row.cells.map(cell => cell.value)).flatten()
)
"""

	def validate(self):
		"""Validate field combinations and keep report raw mode aligned with is_advanced."""
		self._set_default_company_if_missing()
		if not self.company:
			frappe.throw(_("Company is required for Crispy Format. Set a Default Company first."))

		# Validate Report mode fields
		if self.crispy_format_type == "Report":
			linked_reports = self._get_linked_reports()

			if self.is_generic:
				# Generic templates must have generic_report_type
				if not self.generic_report_type:
					frappe.throw(_("Generic Report Type is required for generic templates"))

				# Generic templates must not have specific linked reports
				if linked_reports:
					frappe.throw(_("Generic templates cannot be linked to a specific report"))

			else:
				# Custom report formats must have at least one linked report
				if not linked_reports:
					frappe.throw(_("At least one linked report is required for custom report formats"))

				# Custom formats must not have generic_report_type
				if self.generic_report_type:
					frappe.throw(_("Custom report formats cannot have a Generic Report Type"))

			# Report mode source of truth: is_advanced drives raw_typst.
			self.raw_typst = 1 if self.is_advanced else 0

		# Validate DocType mode
		elif self.crispy_format_type == "DocType":
			if not self.doc_type:
				frappe.throw(_("DocType is required"))

			# DocType formats should not have report fields
			if self.generic_report_type or self.is_generic:
				self.generic_report_type = None
				self.is_generic = 0
			self.set("report", [])
			self.is_advanced = 0

		# Validate Contract mode
		elif self.crispy_format_type == "Contract":
			if not self.contract:
				frappe.throw(_("Contract is required"))

			# Contract formats should not have report fields
			if self.generic_report_type or self.is_generic:
				self.generic_report_type = None
				self.is_generic = 0
			self.set("report", [])
			self.is_advanced = 0

		# Clear other defaults when this format is set as default
		if self.is_default:
			old_default = self.get_current_default()
			self.clear_other_defaults()

			if old_default:
				message = f"Replaced {frappe.bold(old_default)} as default for {frappe.bold(self._get_default_scope_label())}"

				frappe.msgprint(message, indicator="blue")

	def on_update(self):
		self._invalidate_doctype_formats_cache()

	def on_trash(self):
		self._invalidate_doctype_formats_cache()

	def get_current_default(self):
		"""Get the current default format name for this scoped target."""
		defaults = self._get_scoped_default_names()
		return defaults[0] if defaults else None

	def clear_other_defaults(self):
		"""Clear is_default on other formats for this scoped target."""
		for name in self._get_scoped_default_names():
			frappe.db.set_value("Crispy Format", name, "is_default", 0, update_modified=False)

	def _get_scoped_default_names(self) -> list[str]:
		company = self._clean_scope_value(self.company)
		rows = frappe.get_all(
			"Crispy Format",
			filters={
				"crispy_format_type": self.crispy_format_type,
				"name": ["!=", self.name],
				"is_default": 1,
			},
			fields=[
				"name",
				"company",
				"doc_type",
				"contract",
				"is_generic",
				"generic_report_type",
			],
			order_by="name asc",
		)
		rows = [row for row in rows if self._clean_scope_value(row.get("company")) == company]

		if self.crispy_format_type == "DocType":
			return [row.name for row in rows if row.get("doc_type") == self.doc_type]
		if self.crispy_format_type == "Contract":
			return [row.name for row in rows if row.get("contract") == self.contract]
		if self.crispy_format_type == "Report":
			return self._get_scoped_report_default_names(rows)
		return []

	def _get_scoped_report_default_names(self, rows: list[dict]) -> list[str]:
		if self.is_generic:
			return [
				row.name
				for row in rows
				if row.get("is_generic") and row.get("generic_report_type") == self.generic_report_type
			]

		report_names = {row.get("report") for row in self._get_linked_reports()}
		if not report_names:
			return []

		default_names = []
		for row in rows:
			if row.get("is_generic"):
				continue
			candidate_reports = set(
				frappe.get_all(
					"Crispy Format Reports",
					filters={
						"parent": row.name,
						"parenttype": "Crispy Format",
						"disabled": 0,
					},
					pluck="report",
				)
			)
			if report_names.intersection(candidate_reports):
				default_names.append(row.name)
		return default_names

	def _get_default_scope_label(self) -> str:
		if self.crispy_format_type == "DocType":
			return self.doc_type or self.crispy_format_type
		if self.crispy_format_type == "Contract":
			return self.contract or self.crispy_format_type
		if self.crispy_format_type == "Report" and self.is_generic:
			return self.generic_report_type or self.crispy_format_type
		if self.crispy_format_type == "Report":
			reports = [row.get("report") for row in self._get_linked_reports()]
			return ", ".join(reports) or self.crispy_format_type
		return self.crispy_format_type or _("Crispy Format")

	def _clean_scope_value(self, value) -> str:
		return (value or "").strip()
