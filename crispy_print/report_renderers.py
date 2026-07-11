from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frappe


@dataclass(frozen=True)
class ReportRenderer:
	key: str
	label: str
	reports: tuple[str, ...]
	sections: tuple[dict[str, Any], ...]
	source_app: str | None = None
	source_path: str | None = None


def _section(key: str, label: str, *, optional: bool = True, movable: bool = True) -> dict[str, Any]:
	return {"key": key, "label": label, "optional": optional, "movable": movable, "visible": True}


RENDERERS: tuple[ReportRenderer, ...] = (
	ReportRenderer(
		"receivable_payable",
		"Receivables and Payables",
		(
			"Accounts Receivable",
			"Accounts Payable",
			"Accounts Receivable Summary",
			"Accounts Payable Summary",
		),
		(
			_section("heading", "Report Heading", optional=False, movable=False),
			_section("party_identity", "Party and Tax Identity"),
			_section("aging_context", "Aging Context"),
			_section("commercial_terms", "Payment Terms and Credit Limit"),
			_section("future_payments", "Future Payments Summary"),
			_section("report_summary", "Report Summary"),
			_section("chart", "Chart"),
			_section("table", "Aging Table", optional=False, movable=False),
			_section("footer", "Footer"),
		),
		"erpnext",
		"erpnext/accounts/report/accounts_receivable/accounts_receivable.html",
	),
	ReportRenderer(
		"financial_statement",
		"Financial Statements",
		(
			"Balance Sheet",
			"Profit and Loss Statement",
			"Cash Flow",
			"Trial Balance",
			"Gross and Net Profit Report",
			"Profitability Analysis",
		),
		(
			_section("heading", "Statement Heading", optional=False, movable=False),
			_section("fiscal_context", "Fiscal and Currency Context"),
			_section("message", "Statement Notices"),
			_section("report_summary", "Report Summary"),
			_section("chart", "Chart"),
			_section("table", "Financial Statement", optional=False, movable=False),
			_section("footer", "Footer"),
		),
		"erpnext",
		"erpnext/accounts/report/financial_statements.html",
	),
	ReportRenderer(
		"general_ledger",
		"General Ledger",
		("General Ledger",),
		(
			_section("heading", "Statement Heading", optional=False, movable=False),
			_section("party_identity", "Party, Account and Tax Identity"),
			_section("period", "Statement Period"),
			_section("filters", "Additional Filters"),
			_section("table", "Ledger Movements", optional=False, movable=False),
			_section("footer", "Footer"),
		),
		"erpnext",
		"erpnext/accounts/report/general_ledger/general_ledger.html",
	),
	ReportRenderer(
		"bank_reconciliation",
		"Bank Reconciliation",
		("Bank Reconciliation Statement",),
		(
			_section("heading", "Reconciliation Heading", optional=False, movable=False),
			_section("account_context", "Bank Account Context"),
			_section("table", "Reconciliation Movements", optional=False, movable=False),
			_section("reconciliation_totals", "Reconciliation Calculation", optional=False),
			_section("footer", "Footer"),
		),
		"erpnext",
		"erpnext/accounts/report/bank_reconciliation_statement/bank_reconciliation_statement.html",
	),
	ReportRenderer(
		"generic_report",
		"Generic Report",
		(),
		(
			_section("heading", "Report Heading", optional=False, movable=False),
			_section("filters", "Filters"),
			_section("report_summary", "Report Summary"),
			_section("chart", "Chart"),
			_section("table", "Report Table", optional=False, movable=False),
			_section("footer", "Footer"),
		),
		"frappe",
		"frappe/public/js/frappe/views/reports/print_grid.html",
	),
	ReportRenderer("custom", "Custom", (), (), None, None),
)

RENDERER_BY_KEY = {renderer.key: renderer for renderer in RENDERERS}
REPORT_TO_RENDERER = {report: renderer.key for renderer in RENDERERS for report in renderer.reports}


def infer_report_renderer(report: str | None) -> str:
	return REPORT_TO_RENDERER.get((report or "").strip(), "generic_report")


def infer_renderer_for_reports(reports: list[str]) -> str:
	keys = {infer_report_renderer(report) for report in reports if report}
	return keys.pop() if len(keys) == 1 else ("generic_report" if not keys else "custom")


def validate_renderer_reports(renderer: str, reports: list[str]) -> bool:
	if renderer == "custom":
		return True
	return all(infer_report_renderer(report) == renderer for report in reports)


def _source_file(renderer: ReportRenderer) -> Path | None:
	if not renderer.source_app or not renderer.source_path:
		return None
	try:
		app_root = Path(frappe.get_app_path(renderer.source_app)).parent
		return app_root.joinpath(*Path(renderer.source_path).parts)
	except Exception:
		return None


def get_source_fingerprint(renderer_key: str) -> dict[str, Any]:
	renderer = RENDERER_BY_KEY.get(renderer_key)
	if not renderer:
		return {"status": "source_unavailable", "fingerprint": None, "path": None}
	path = _source_file(renderer)
	if not path or not path.is_file():
		return {"status": "source_unavailable", "fingerprint": None, "path": renderer.source_path}
	return {
		"status": "current",
		"fingerprint": hashlib.sha256(path.read_bytes()).hexdigest(),
		"path": renderer.source_path,
	}


def get_renderer_metadata(renderer_key: str, expected_fingerprint: str | None = None) -> dict[str, Any]:
	renderer = RENDERER_BY_KEY.get(renderer_key) or RENDERER_BY_KEY["generic_report"]
	source = get_source_fingerprint(renderer.key)
	if expected_fingerprint and source.get("fingerprint") and expected_fingerprint != source["fingerprint"]:
		source["status"] = "review_required"
	return {
		"key": renderer.key,
		"label": renderer.label,
		"reports": list(renderer.reports),
		"sections": [dict(section) for section in renderer.sections],
		"source": source,
	}


def list_renderer_metadata() -> list[dict[str, Any]]:
	return [get_renderer_metadata(renderer.key) for renderer in RENDERERS]
