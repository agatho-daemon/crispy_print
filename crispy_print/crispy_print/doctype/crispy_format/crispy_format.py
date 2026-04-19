# Copyright (c) 2025, Agathodaemon and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.query_builder import DocType


class CrispyFormat(Document):
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
		# When duplicating via Frappe's "Duplicate" feature, is_default shouldn't carry over
		# Only one format can be default per DocType
		if self.is_default:
			self.is_default = 0

		# Set default template for new Report formats
		if self.crispy_format_type == "Report" and self.is_generic and not self.typst_code:
			self._set_default_report_template()

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
  flipped: data.page_settings.orientation == "landscape",
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
#table(
  columns: data.columns.map(col => {
    if col.width == "auto" { auto } else { eval(col.width) }
  }),
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
				message = f"Replaced {frappe.bold(old_default)} as default for {frappe.bold(self.doc_type)}"

				frappe.msgprint(message, indicator="blue")

	def on_update(self):
		self._invalidate_doctype_formats_cache()

	def on_trash(self):
		self._invalidate_doctype_formats_cache()

	def get_current_default(self):
		"""Get the current default format name for this DocType"""
		CrispyFormat = DocType("Crispy Format")

		result = (
			frappe.qb.from_(CrispyFormat)
			.select(CrispyFormat.name)
			.where(CrispyFormat.doc_type == self.doc_type)
			.where(CrispyFormat.name != self.name)
			.where(CrispyFormat.is_default == 1)
			.run(as_dict=True)
		)

		return result[0].name if result else None

	def clear_other_defaults(self):
		"""Clear is_default on other formats for this DocType"""
		# Get all other default formats for this DocType
		CrispyFormat = DocType("Crispy Format")

		other_defaults = (
			frappe.qb.from_(CrispyFormat)
			.select(CrispyFormat.name)
			.where(CrispyFormat.doc_type == self.doc_type)
			.where(CrispyFormat.name != self.name)
			.where(CrispyFormat.is_default == 1)
			.run(as_dict=True)
		)

		# Clear is_default using frappe.db.set_value for proper transaction handling
		for record in other_defaults:
			frappe.db.set_value("Crispy Format", record.name, "is_default", 0, update_modified=False)
