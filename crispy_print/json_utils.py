# Copyright (c) 2026, Agathodaemon and contributors
# For license information, please see license.txt

from __future__ import annotations

import json
from typing import Any

import frappe
from frappe import _


def parse_json_value(value: Any, label: str) -> Any:
	"""Parse a JSON string, raising a user-facing error on invalid JSON."""
	if isinstance(value, str):
		try:
			return json.loads(value)
		except json.JSONDecodeError:
			frappe.throw(_("{0} must contain valid JSON.").format(label))
	return value


def parse_json_object(value: Any, label: str) -> dict:
	parsed = parse_json_value(value, label)
	if not isinstance(parsed, dict):
		frappe.throw(_("{0} must be a JSON object.").format(label))
	return parsed


def parse_json_list_or_object(value: Any, label: str) -> list | dict:
	parsed = parse_json_value(value, label)
	if not isinstance(parsed, list | dict):
		frappe.throw(_("{0} must be a JSON array or object.").format(label))
	return parsed


def cint_or_default(value: Any, default: int) -> int:
	try:
		return int(value if value not in (None, "") else default)
	except (TypeError, ValueError):
		return default


def loads_dict_or_empty(value: Any) -> dict:
	"""Lenient parse: return a dict, or {} on any failure. Never raises."""
	if isinstance(value, dict):
		return value
	if not value:
		return {}
	try:
		parsed = json.loads(value)
	except (TypeError, json.JSONDecodeError):
		return {}
	return parsed if isinstance(parsed, dict) else {}
