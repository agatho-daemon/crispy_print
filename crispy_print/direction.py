from __future__ import annotations

from typing import Literal, TypedDict

RTL_LANGUAGE_PREFIXES = frozenset({"ar", "fa", "he", "ur"})
LTR_FIELD_TYPES = frozenset(
	{"Int", "Float", "Currency", "Percent", "Date", "Datetime", "Time", "Duration", "Barcode"}
)
LTR_FIELDNAME_PARTS = frozenset(
	{
		"uuid",
		"hash",
		"code",
		"sku",
		"tax",
		"vat",
		"iban",
		"swift",
		"bic",
		"phone",
		"mobile",
		"email",
		"url",
		"website",
		"barcode",
		"qr",
		"reference",
		"serial",
		"batch",
	}
)


class LanguageDirection(TypedDict):
	language: str
	language_code: str
	region: str
	direction: Literal["ltr", "rtl"]


def normalize_language(language: str | None, fallback: str = "en") -> str:
	value = str(language or fallback).strip().replace("_", "-")
	return value or fallback


def get_language_direction(language: str | None, fallback: str = "en") -> LanguageDirection:
	normalized = normalize_language(language, fallback)
	parts = normalized.split("-", 1)
	language_code = parts[0].lower()
	region = parts[1].upper() if len(parts) > 1 else ""
	return {
		"language": f"{language_code}-{region}" if region else language_code,
		"language_code": language_code,
		"region": region,
		"direction": "rtl" if language_code in RTL_LANGUAGE_PREFIXES else "ltr",
	}


def is_ltr_field(fieldtype: str | None = None, fieldname: str | None = None) -> bool:
	if str(fieldtype or "") in LTR_FIELD_TYPES:
		return True
	normalized_fieldname = str(fieldname or "").strip().lower().replace("-", "_")
	if normalized_fieldname in {"name", "id"}:
		return True
	parts = {part for part in normalized_fieldname.split("_") if part}
	return bool(parts & LTR_FIELDNAME_PARTS)
