# Copyright (c) 2025, Agathodaemon and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from crispy_print.api.v1.company_context import resolve_effective_company
from crispy_print.defaults import enforce_single_default
from crispy_print.report_renderers import (
	get_source_fingerprint,
	infer_renderer_for_reports,
	validate_renderer_reports,
)


class CrispyFormat(Document):
	def _set_default_company_if_missing(self) -> None:
		# Report formats may intentionally be global and participate in the
		# company/global resolution chain.
		if self.company or self.crispy_format_type == "Report":
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
		"""Names are supplied by designers or deterministic setup/migration code."""

	def before_insert(self):
		"""Clear is_default when duplicating a format"""
		if self.is_default and self._is_duplicate_insert():
			self.is_default = 0

		# Set default template for new Report formats
		if self.crispy_format_type == "Report" and not self.typst_code:
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
		if not self.company and self.crispy_format_type != "Report":
			frappe.throw(_("Company is required for Crispy Format. Set a Default Company first."))

		# Validate Report mode fields
		if self.crispy_format_type == "Report":
			linked_reports = self._get_linked_reports()
			report_names = [row.get("report") for row in linked_reports]
			self.report_scope = self.report_scope or "Selected Reports"

			if self.report_scope == "All Compatible Reports":
				if linked_reports:
					frappe.throw(_("All-compatible report formats cannot link selected reports."))
				self.report_renderer = self.report_renderer or "generic_report"
			elif self.report_scope == "Selected Reports":
				if not linked_reports:
					frappe.throw(_("At least one linked report is required for selected-report formats."))
				self.report_renderer = self.report_renderer or infer_renderer_for_reports(report_names)
				if not validate_renderer_reports(self.report_renderer, report_names):
					frappe.throw(
						_(
							"Selected reports are incompatible with renderer {0}. Use the custom renderer to combine report families."
						).format(frappe.bold(self.report_renderer))
					)
			else:
				frappe.throw(_("Report Coverage must be All Compatible Reports or Selected Reports."))

			if not self.report_renderer:
				frappe.throw(_("Report Renderer is required."))
			fingerprint = get_source_fingerprint(self.report_renderer).get("fingerprint")
			if fingerprint and not self.report_source_fingerprint:
				self.report_source_fingerprint = fingerprint

			# Report mode source of truth: is_advanced drives raw_typst.
			self.raw_typst = 1 if self.is_advanced else 0

		# Validate DocType mode
		elif self.crispy_format_type == "DocType":
			if not self.doc_type:
				frappe.throw(_("DocType is required"))

			# DocType formats should not have report fields
			self.report_scope = None
			self.report_renderer = None
			self.report_source_fingerprint = None
			self.set("report", [])
			self.is_advanced = 0

		# Validate Contract mode
		elif self.crispy_format_type == "Contract":
			if not self.contract:
				frappe.throw(_("Contract is required"))

			# Contract formats should not have report fields
			self.report_scope = None
			self.report_renderer = None
			self.report_source_fingerprint = None
			self.set("report", [])
			self.is_advanced = 0

		# Clear other defaults when this format is set as default
		if self.is_default:
			cleared_defaults = self.clear_other_defaults()

			if cleared_defaults:
				message = f"Replaced {frappe.bold(cleared_defaults[0])} as default for {frappe.bold(self._get_default_scope_label())}"

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
		return enforce_single_default(
			"Crispy Format",
			self.name,
			self._get_default_scope_keys(),
			competing_names=self._get_scoped_default_names(),
		)

	def _get_default_scope_keys(self) -> list[str]:
		company = self._clean_scope_value(self.company)
		format_type = self._clean_scope_value(self.crispy_format_type)
		if self.crispy_format_type == "DocType":
			return [f"{company}|{format_type}|doctype|{self._clean_scope_value(self.doc_type)}"]
		if self.crispy_format_type == "Contract":
			return [f"{company}|{format_type}|contract|{self._clean_scope_value(self.contract)}"]
		if self.crispy_format_type == "Report" and self.report_scope == "All Compatible Reports":
			return [f"{company}|{format_type}|renderer|{self._clean_scope_value(self.report_renderer)}"]
		if self.crispy_format_type == "Report":
			report_names = sorted(
				{row.get("report") for row in self._get_linked_reports() if row.get("report")}
			)
			return [f"{company}|{format_type}|custom-report|{report}" for report in report_names]
		return [f"{company}|{format_type}|unknown|{self.name}"]

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
				"report_scope",
				"report_renderer",
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
		if self.report_scope == "All Compatible Reports":
			return [
				row.name
				for row in rows
				if row.get("report_scope") == "All Compatible Reports"
				and row.get("report_renderer") == self.report_renderer
			]

		report_names = {row.get("report") for row in self._get_linked_reports()}
		if not report_names:
			return []

		default_names = []
		candidate_names = [row.name for row in rows if row.get("report_scope") == "Selected Reports"]
		report_rows = []
		if candidate_names:
			report_rows = frappe.get_all(
				"Crispy Format Reports",
				filters={
					"parent": ["in", candidate_names],
					"parenttype": "Crispy Format",
					"disabled": 0,
				},
				fields=["parent", "report"],
			)
		reports_by_parent: dict[str, set[str]] = {}
		for report_row in report_rows:
			parent = report_row.get("parent")
			report = report_row.get("report")
			if parent and report:
				reports_by_parent.setdefault(parent, set()).add(report)

		for row in rows:
			if row.get("report_scope") != "Selected Reports":
				continue
			candidate_reports = reports_by_parent.get(row.name, set())
			if report_names.intersection(candidate_reports):
				default_names.append(row.name)
		return default_names

	def _get_default_scope_label(self) -> str:
		if self.crispy_format_type == "DocType":
			return self.doc_type or self.crispy_format_type
		if self.crispy_format_type == "Contract":
			return self.contract or self.crispy_format_type
		if self.crispy_format_type == "Report" and self.report_scope == "All Compatible Reports":
			return self.report_renderer or self.crispy_format_type
		if self.crispy_format_type == "Report":
			reports = [row.get("report") for row in self._get_linked_reports()]
			return ", ".join(reports) or self.crispy_format_type
		return self.crispy_format_type or _("Crispy Format")

	def _clean_scope_value(self, value) -> str:
		return (value or "").strip()
