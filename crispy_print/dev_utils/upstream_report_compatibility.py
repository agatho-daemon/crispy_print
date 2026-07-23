"""Capture and compare stable structural facts from an upstream report result.

Run through Bench after preparing representative data:

    bench --site SITE execute \
      crispy_print.dev_utils.upstream_report_compatibility.capture \
      --kwargs '{"report":"General Ledger","filters":{"company":"Example"}}'
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from crispy_print.report_renderers import get_upstream_versions, infer_report_renderer

SEMANTIC_ROW_KEYS = {
	"indent",
	"parent_account",
	"parent_section",
	"is_group",
	"is_total",
	"is_bold",
	"warn_if_negative",
}
TOTAL_KEYS = {"add_total_row", "skip_total_row", "total_row"}


def _column_contract(column: Any, index: int) -> dict[str, Any]:
	if isinstance(column, str):
		parts = column.split(":")
		return {
			"fieldname": parts[0] or f"column_{index}",
			"label": parts[0],
			"fieldtype": parts[1] if len(parts) > 1 else "",
		}
	if not isinstance(column, dict):
		return {"fieldname": f"column_{index}", "label": "", "fieldtype": ""}
	return {
		"fieldname": str(column.get("fieldname") or f"column_{index}"),
		"label": str(column.get("label") or ""),
		"fieldtype": str(column.get("fieldtype") or ""),
	}


def build_snapshot(report: str, report_data: dict, filters: dict | None = None) -> dict[str, Any]:
	columns = [
		_column_contract(column, index) for index, column in enumerate(report_data.get("columns") or [])
	]
	rows = report_data.get("result") or []
	semantic_keys = sorted(
		{key for row in rows if isinstance(row, dict) for key in SEMANTIC_ROW_KEYS if key in row}
	)
	total_flags = {key: report_data.get(key) for key in sorted(TOTAL_KEYS) if key in report_data}
	contract = {
		"report": report,
		"renderer": infer_report_renderer(report),
		"versions": get_upstream_versions(),
		"filters": sorted(str(key) for key in (filters or {})),
		"columns": columns,
		"semantic_row_keys": semantic_keys,
		"total_flags": total_flags,
		"chart_type": str((report_data.get("chart") or {}).get("type") or ""),
	}
	encoded = json.dumps(contract, sort_keys=True, separators=(",", ":"), default=str).encode()
	contract["fingerprint"] = hashlib.sha256(encoded).hexdigest()
	return contract


def compare_snapshots(expected: dict, current: dict) -> dict[str, Any]:
	def names(snapshot: dict, key: str) -> set[str]:
		if key == "columns":
			return {
				str(column.get("fieldname"))
				for column in snapshot.get("columns") or []
				if isinstance(column, dict)
			}
		return {str(value) for value in snapshot.get(key) or []}

	differences = []
	for key in ("filters", "columns", "semantic_row_keys"):
		before = names(expected, key)
		after = names(current, key)
		if before != after:
			differences.append(
				{
					"dimension": key,
					"removed": sorted(before - after),
					"added": sorted(after - before),
				}
			)
	for key in ("total_flags", "chart_type", "renderer"):
		if expected.get(key) != current.get(key):
			differences.append({"dimension": key, "expected": expected.get(key), "current": current.get(key)})
	return {
		"status": "review_required" if differences else "compatible",
		"expected_fingerprint": expected.get("fingerprint"),
		"current_fingerprint": current.get("fingerprint"),
		"differences": differences,
	}


def capture(report: str, filters: dict | str | None = None) -> dict[str, Any]:
	"""Execute a report and return a non-row-data structural review snapshot."""
	from crispy_print.api.v1.reports import _get_report_data

	if isinstance(filters, str):
		filters = json.loads(filters)
	filters = filters if isinstance(filters, dict) else {}
	return build_snapshot(report, _get_report_data(report, filters), filters)
