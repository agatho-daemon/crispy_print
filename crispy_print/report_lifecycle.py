"""Report-format lifecycle policy shared by publishing and resolution."""

from __future__ import annotations

import re
from typing import Any

import frappe
from frappe import _

from crispy_print.report_renderers import get_source_fingerprint

REPORT_BASIC_GENERATOR_VERSION = 4
_GENERATOR_PATTERN = re.compile(r"CRISPY_REPORT_BASIC_GENERATOR:(\d+)")


def get_report_generator_version(typst_code: str | None) -> int | None:
	match = _GENERATOR_PATTERN.search(str(typst_code or ""))
	return int(match.group(1)) if match else None


def validate_report_format_for_publish(source) -> None:
	"""Require a single reviewed report target and a current Basic generator."""
	if source.get("crispy_format_type") != "Report":
		return
	rows = [row for row in (source.get("report") or []) if row.get("report") and not row.get("disabled")]
	if source.get("report_scope") != "Selected Reports" or len(rows) != 1:
		frappe.throw(
			_(
				"Published Report templates must target exactly one selected Report. "
				"Use separate formats when reports need separate frozen histories."
			)
		)
	if not source.get("raw_typst") and str(source.get("typst_code") or "").strip():
		version = get_report_generator_version(source.get("typst_code"))
		if version != REPORT_BASIC_GENERATOR_VERSION:
			frappe.throw(
				_(
					"This Basic report format uses generator version {0}; version {1} is required. "
					"Open it in the Report Format Builder, save it, and publish again."
				).format(version or _("unknown"), REPORT_BASIC_GENERATOR_VERSION)
			)
	current = get_source_fingerprint(source.get("report_renderer")).get("fingerprint")
	accepted = str(source.get("report_source_fingerprint") or "")
	if current and accepted != current:
		frappe.throw(
			_(
				"The upstream report renderer changed after this format was reviewed. "
				"Complete the compatibility review and acknowledge the current fingerprint before publishing."
			)
		)


def report_format_resolution_rank(
	row: dict[str, Any],
	*,
	report_renderer: str,
	company: str | None,
) -> tuple[int, int, str]:
	"""Deterministic selected-report/company/renderer/global precedence."""
	row_company = str(row.get("company") or "").strip()
	exact_company = bool(company and row_company == str(company).strip())
	global_company = not row_company
	exact_target = row.get("report_scope") == "Selected Reports"
	exact_renderer = row.get("report_renderer") == report_renderer

	if exact_target and exact_company:
		bucket = 0
	elif exact_target and global_company:
		bucket = 1
	elif exact_renderer and exact_company:
		bucket = 2
	elif exact_renderer and global_company:
		bucket = 3
	elif exact_company:
		bucket = 4
	else:
		bucket = 5
	return bucket, 0 if row.get("is_default") else 1, str(row.get("name") or "")
