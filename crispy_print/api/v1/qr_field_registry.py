from __future__ import annotations

from typing import Any

from crispy_print.qr_registry import (
	get_business_field_set,
	get_qr_fields,
	get_qr_registry_metadata,
)

JSONDict = dict[str, Any]


def get_qr_field_registry_metadata() -> JSONDict:
	return get_qr_registry_metadata()


def get_qr_registry_fields(
	doctype: str,
	authority_code: str | None = None,
	include_business_fields: int | bool = 1,
) -> JSONDict:
	return get_qr_fields(
		doctype=doctype,
		authority_code=authority_code,
		include_business_fields=include_business_fields,
	)


def get_qr_business_field_set(key: str) -> JSONDict:
	return get_business_field_set(key)
