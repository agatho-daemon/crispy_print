from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import frappe
from frappe import _

from .formats import (
	EXPORT_SCHEMA_VERSION,
	_insert_format_duplicate_for_company,
	_validate_import_payload,
)

JSONDict = dict[str, Any]


def list_sample_formats() -> list[JSONDict]:
	"""Return valid file-based sample format catalog entries."""
	samples: list[JSONDict] = []
	for path in _sample_format_dir().glob("*.json"):
		try:
			samples.append(_catalog_card(_load_sample_file(path), path))
		except Exception:
			frappe.log_error(
				title="Crispy Print Sample Format Catalog",
				message=f"Skipping invalid sample format file: {path.name}",
			)
	samples.sort(key=lambda row: (str(row.get("target_type") or ""), str(row.get("title") or "")))
	return samples


def get_sample_format(sample_id: str) -> JSONDict:
	"""Return one validated sample format payload."""
	path = _sample_path(sample_id)
	if not path.exists():
		frappe.throw(_("Sample format {0} was not found.").format(sample_id))
	return _load_sample_file(path)


def create_format_from_sample(
	sample_id: str,
	company: str,
	name: str | None = None,
	set_default: int | bool = 0,
) -> JSONDict:
	"""Create a real company-scoped Crispy Format from a file-based sample."""
	sample = get_sample_format(sample_id)
	format_data = _validate_import_payload(sample)
	format_data["company"] = None
	format_data["is_default"] = 0

	doc, warnings = _insert_format_duplicate_for_company(
		format_data,
		target_company=company,
		source_name=str(format_data.get("name") or sample_id),
		set_default=set_default,
		name=name,
		name_strategy="copy",
	)

	return {
		"success": True,
		"name": doc.name,
		"sample_id": sample_id,
		"company": doc.get("company"),
		"is_default": 1 if doc.get("is_default") else 0,
		"warnings": warnings,
	}


def _sample_format_dir() -> Path:
	return Path(frappe.get_app_path("crispy_print")) / "examples" / "formats"


def _sample_path(sample_id: str) -> Path:
	clean = str(sample_id or "").strip()
	if not clean or "/" in clean or "\\" in clean or clean in {".", ".."}:
		frappe.throw(_("Invalid sample format id."))
	path = (_sample_format_dir() / f"{clean}.json").resolve()
	base = _sample_format_dir().resolve()
	if base not in path.parents:
		frappe.throw(_("Invalid sample format id."))
	return path


def _load_sample_file(path: Path) -> JSONDict:
	try:
		payload = json.loads(path.read_text(encoding="utf-8"))
	except json.JSONDecodeError:
		frappe.throw(_("Sample format {0} contains invalid JSON.").format(path.name))

	if not isinstance(payload, dict):
		frappe.throw(_("Sample format {0} must be a JSON object.").format(path.name))
	if payload.get("schema_version") != EXPORT_SCHEMA_VERSION:
		frappe.throw(_("Sample format {0} has an unsupported schema version.").format(path.name))

	format_data = _validate_import_payload(payload)
	sample = payload.get("sample")
	if not isinstance(sample, dict):
		frappe.throw(_("Sample format {0} is missing catalog metadata.").format(path.name))
	if str(sample.get("id") or "").strip() != path.stem:
		frappe.throw(_("Sample format id must match its filename."))

	_validate_company_neutral_payload(payload, format_data, payload.get("format") or {})
	return payload


def _catalog_card(payload: JSONDict, path: Path) -> JSONDict:
	sample = payload.get("sample") or {}
	format_data = payload.get("format") or {}
	return {
		"id": sample.get("id") or path.stem,
		"title": sample.get("title") or format_data.get("name") or path.stem,
		"description": sample.get("description") or "",
		"target_type": sample.get("target_type") or format_data.get("crispy_format_type") or "",
		"doc_type": sample.get("doc_type") or format_data.get("doc_type") or "",
		"report_kind": sample.get("report_kind") or format_data.get("report_renderer") or "",
		"tags": sample.get("tags") if isinstance(sample.get("tags"), list) else [],
		"recommended_use": sample.get("recommended_use") or "",
		"format_name": format_data.get("name") or "",
	}


def _validate_company_neutral_payload(
	payload: JSONDict, format_data: JSONDict, raw_format_data: JSONDict
) -> None:
	if format_data.get("company"):
		frappe.throw(_("Sample formats must not include a company."))
	if raw_format_data.get("is_default"):
		frappe.throw(_("Sample formats must not be marked as default."))

	metadata = payload.get("metadata")
	if isinstance(metadata, dict) and metadata.get("company"):
		frappe.throw(_("Sample formats must not include company metadata."))

	for value in _walk_values(payload):
		if not isinstance(value, str):
			continue
		clean = value.strip()
		if "/private/" in clean or clean.startswith("private/files/"):
			frappe.throw(_("Sample formats must not reference private files."))


def _walk_values(value: Any):
	if isinstance(value, dict):
		for child in value.values():
			yield from _walk_values(child)
	elif isinstance(value, list):
		for child in value:
			yield from _walk_values(child)
	else:
		yield value
