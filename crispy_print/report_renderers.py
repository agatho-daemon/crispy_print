from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import frappe
from frappe.utils import get_app_version

SUPPORTED_UPSTREAM_MAJORS = {15, 16, 17}


@dataclass(frozen=True)
class ReportRenderer:
	key: str
	label: str
	reports: tuple[str, ...]
	sections: tuple[dict[str, Any], ...]
	source_app: str | None = None
	source_paths: tuple[str, ...] = ()


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
		(
			"erpnext/accounts/report/accounts_receivable/accounts_receivable.html",
			"erpnext/accounts/report/accounts_receivable/accounts_receivable.js",
			"erpnext/accounts/report/accounts_receivable/accounts_receivable.json",
			"erpnext/accounts/report/accounts_receivable/accounts_receivable.py",
			"erpnext/accounts/report/accounts_receivable_summary/accounts_receivable_summary.py",
		),
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
		(
			"erpnext/accounts/report/financial_statements.html",
			"erpnext/accounts/report/financial_statements.py",
			"erpnext/accounts/report/balance_sheet/balance_sheet.js",
			"erpnext/accounts/report/balance_sheet/balance_sheet.py",
			"erpnext/accounts/report/profit_and_loss_statement/profit_and_loss_statement.py",
		),
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
		(
			"erpnext/accounts/report/general_ledger/general_ledger.html",
			"erpnext/accounts/report/general_ledger/general_ledger.js",
			"erpnext/accounts/report/general_ledger/general_ledger.json",
			"erpnext/accounts/report/general_ledger/general_ledger.py",
		),
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
		(
			"erpnext/accounts/report/bank_reconciliation_statement/bank_reconciliation_statement.html",
			"erpnext/accounts/report/bank_reconciliation_statement/bank_reconciliation_statement.js",
			"erpnext/accounts/report/bank_reconciliation_statement/bank_reconciliation_statement.json",
			"erpnext/accounts/report/bank_reconciliation_statement/bank_reconciliation_statement.py",
		),
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
		(
			"frappe/public/js/frappe/views/reports/print_grid.html",
			"frappe/public/js/frappe/views/reports/query_report.js",
			"frappe/desk/query_report.py",
		),
	),
	ReportRenderer("custom", "Custom", (), (), None, None),
)

RENDERER_BY_KEY = {renderer.key: renderer for renderer in RENDERERS}
REPORT_TO_RENDERER = {report: renderer.key for renderer in RENDERERS for report in renderer.reports}
RENDERER_PRESENTATION_DEFAULTS: dict[str, dict[str, Any]] = {
	"receivable_payable": {"page": {"orientation": "landscape"}},
	"financial_statement": {"page": {"orientation": "landscape"}},
	"general_ledger": {"page": {"orientation": "landscape"}},
	"bank_reconciliation": {"page": {"orientation": "landscape"}},
	"generic_report": {},
	"custom": {},
}


def infer_report_renderer(report: str | None) -> str:
	return REPORT_TO_RENDERER.get((report or "").strip(), "generic_report")


def infer_renderer_for_reports(reports: list[str]) -> str:
	keys = {infer_report_renderer(report) for report in reports if report}
	return keys.pop() if len(keys) == 1 else ("generic_report" if not keys else "custom")


def validate_renderer_reports(renderer: str, reports: list[str]) -> bool:
	if renderer == "custom":
		return True
	return all(infer_report_renderer(report) == renderer for report in reports)


def get_renderer_presentation_defaults(renderer_key: str | None) -> dict[str, Any]:
	"""Return structural defaults applied after the Branding Profile layer."""
	return dict(RENDERER_PRESENTATION_DEFAULTS.get(renderer_key or "generic_report", {}))


def _source_files(renderer: ReportRenderer) -> list[tuple[str, Path]]:
	if not renderer.source_app or not renderer.source_paths:
		return []
	try:
		app_root = Path(frappe.get_app_path(renderer.source_app)).parent
		return [(source, app_root.joinpath(*Path(source).parts)) for source in renderer.source_paths]
	except Exception:
		return []


def get_source_fingerprint(renderer_key: str) -> dict[str, Any]:
	renderer = RENDERER_BY_KEY.get(renderer_key)
	if not renderer:
		return {"status": "source_unavailable", "fingerprint": None, "paths": [], "files": []}
	source_files = _source_files(renderer)
	if not source_files or any(not path.is_file() for _, path in source_files):
		return {
			"status": "source_unavailable",
			"fingerprint": None,
			"paths": list(renderer.source_paths or ()),
			"files": [],
		}
	files = [
		{"path": source, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
		for source, path in source_files
	]
	manifest = json.dumps(files, sort_keys=True, separators=(",", ":")).encode()
	return {
		"status": "current",
		"fingerprint": hashlib.sha256(manifest).hexdigest(),
		"path": renderer.source_paths[0],
		"paths": list(renderer.source_paths),
		"files": files,
	}


def _major(version: str) -> int | None:
	try:
		return int(str(version).lstrip("v").split(".", 1)[0])
	except (TypeError, ValueError):
		return None


def get_upstream_versions() -> dict[str, dict[str, Any]]:
	result = {}
	for app in ("frappe", "erpnext"):
		version = get_app_version(app)
		major = _major(version)
		result[app] = {
			"version": version,
			"major": major,
			"supported_major": major in SUPPORTED_UPSTREAM_MAJORS,
		}
	return result


def audit_report_registry(report_names: list[str]) -> dict[str, Any]:
	"""Detect missing, disabled, renamed/customized, and overridden Report records."""
	names = sorted({str(name).strip() for name in report_names if str(name).strip()})
	if not names:
		return {"status": "not_applicable", "reports": [], "issues": []}
	rows = frappe.get_all(
		"Report",
		filters={"name": ["in", names]},
		fields=[
			"name",
			"disabled",
			"is_standard",
			"module",
			"report_type",
			"reference_report",
			"ref_doctype",
		],
	)
	by_name = {row.get("name"): row for row in rows}
	missing = [name for name in names if name not in by_name]
	renamed_rows = (
		frappe.get_all(
			"Report",
			filters={"reference_report": ["in", missing]},
			fields=["name", "reference_report", "is_standard", "module", "report_type"],
		)
		if missing
		else []
	)
	issues: list[dict[str, Any]] = []
	for name in missing:
		candidates = [row.get("name") for row in renamed_rows if row.get("reference_report") == name]
		issues.append(
			{
				"code": "report_renamed" if candidates else "report_missing",
				"report": name,
				"candidates": candidates,
			}
		)
	for name, row in by_name.items():
		if row.get("disabled"):
			issues.append({"code": "report_disabled", "report": name})
		if str(row.get("is_standard") or "").lower() != "yes" or row.get("reference_report"):
			issues.append(
				{
					"code": "custom_report_override",
					"report": name,
					"reference_report": row.get("reference_report"),
					"module": row.get("module"),
				}
			)
	return {
		"status": "review_required" if issues else "current",
		"reports": [dict(row) for row in rows],
		"issues": issues,
	}


def get_compatibility_review(renderer: ReportRenderer) -> dict[str, Any]:
	versions = get_upstream_versions()
	registry = audit_report_registry(list(renderer.reports))
	issues = list(registry["issues"])
	for app, details in versions.items():
		if not details["supported_major"]:
			issues.append(
				{
					"code": "unsupported_upstream_major",
					"app": app,
					"version": details["version"],
				}
			)
	return {
		"status": "review_required" if issues else "current",
		"versions": versions,
		"registry": registry,
		"issues": issues,
		"checklist": [
			"Confirm report names and Report records.",
			"Compare filters and returned columns with reviewed fixtures.",
			"Check totals, grouping, indentation, and empty-result behavior.",
			"Compile representative PDFs and inspect renderer-family semantics.",
			"Record the reviewed source fingerprint only after acceptance.",
		],
	}


def get_renderer_metadata(renderer_key: str, expected_fingerprint: str | None = None) -> dict[str, Any]:
	renderer = RENDERER_BY_KEY.get(renderer_key) or RENDERER_BY_KEY["generic_report"]
	source = get_source_fingerprint(renderer.key)
	if expected_fingerprint and source.get("fingerprint") and expected_fingerprint != source["fingerprint"]:
		source["status"] = "review_required"
	compatibility = get_compatibility_review(renderer)
	if source["status"] != "current":
		compatibility["status"] = "review_required"
		compatibility["issues"].insert(
			0,
			{
				"code": source["status"],
				"expected_fingerprint": expected_fingerprint,
				"current_fingerprint": source.get("fingerprint"),
			},
		)
	return {
		"key": renderer.key,
		"label": renderer.label,
		"reports": list(renderer.reports),
		"sections": [dict(section) for section in renderer.sections],
		"presentation_defaults": get_renderer_presentation_defaults(renderer.key),
		"source": source,
		"compatibility": compatibility,
	}


def list_renderer_metadata() -> list[dict[str, Any]]:
	return [get_renderer_metadata(renderer.key) for renderer in RENDERERS]
