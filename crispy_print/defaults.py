from __future__ import annotations

import hashlib
import time
from collections.abc import Iterable
from typing import Any

import frappe
from frappe import _

DEFAULT_LOCK_TIMEOUT_SECONDS = 3


def enforce_single_default(
	doctype: str,
	current_name: str,
	scope_keys: str | Iterable[str],
	*,
	competing_names: Iterable[str] | None = None,
	filters: dict[str, Any] | None = None,
	timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> list[str]:
	"""Serialize and clear competing defaults for a defaultable DocType scope."""
	lock_keys = _normalize_scope_keys(doctype, scope_keys)
	acquire_default_locks(lock_keys, timeout_seconds=timeout_seconds)

	names = _normalize_names(competing_names)
	if filters is not None:
		names = frappe.get_all(doctype, filters=filters, pluck="name", order_by="name asc")

	names = [name for name in names if name and name != current_name]
	if not names:
		return []

	frappe.db.set_value(
		doctype,
		{"name": ["in", names]},
		"is_default",
		0,
		update_modified=False,
	)
	return names


def acquire_default_locks(
	scope_keys: str | Iterable[str],
	*,
	timeout_seconds: int = DEFAULT_LOCK_TIMEOUT_SECONDS,
) -> list[str]:
	lock_keys = _normalize_lock_keys(scope_keys)
	for lock_key in lock_keys:
		_acquire_default_lock(lock_key, timeout_seconds=timeout_seconds)
	return lock_keys


def build_default_lock_key(doctype: str, scope_key: str) -> str:
	raw = f"{doctype}:{scope_key}"
	digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
	return f"crispy_print:default:{doctype}:{digest}"


def _normalize_scope_keys(doctype: str, scope_keys: str | Iterable[str]) -> list[str]:
	return [build_default_lock_key(doctype, scope_key) for scope_key in _normalize_lock_keys(scope_keys)]


def _normalize_lock_keys(scope_keys: str | Iterable[str]) -> list[str]:
	if isinstance(scope_keys, str):
		values = [scope_keys]
	else:
		values = [str(value or "").strip() for value in scope_keys]
	values = sorted({value for value in values if value})
	if not values:
		frappe.throw(_("Default scope is required."))
	return values


def _normalize_names(names: Iterable[str] | None) -> list[str]:
	return sorted({str(name or "").strip() for name in names or [] if str(name or "").strip()})


def _acquire_default_lock(lock_key: str, *, timeout_seconds: int) -> None:
	if _is_default_lock_held(lock_key):
		return

	db_type = getattr(frappe.db, "db_type", "mariadb")
	if db_type == "postgres":
		_acquire_postgres_default_lock(lock_key, timeout_seconds=timeout_seconds)
		return
	_acquire_mariadb_default_lock(lock_key, timeout_seconds=timeout_seconds)


def _acquire_mariadb_default_lock(lock_key: str, *, timeout_seconds: int) -> None:
	result = frappe.db.sql("select get_lock(%s, %s)", (lock_key, timeout_seconds))[0][0]
	if int(result or 0) != 1:
		frappe.throw(
			_("Could not acquire default-setting lock for {0}. Please retry.").format(lock_key),
			frappe.ValidationError,
		)
	_mark_default_lock_held(lock_key)
	frappe.db.after_commit.add(lambda key=lock_key: _release_mariadb_default_lock(key))
	frappe.db.after_rollback.add(lambda key=lock_key: _release_mariadb_default_lock(key))


def _release_mariadb_default_lock(lock_key: str) -> None:
	try:
		frappe.db.sql("select release_lock(%s)", (lock_key,))
	finally:
		_get_held_default_locks().discard(lock_key)


def _acquire_postgres_default_lock(lock_key: str, *, timeout_seconds: int) -> None:
	lock_id = _postgres_lock_id(lock_key)
	deadline = time.monotonic() + max(timeout_seconds, 0)
	while True:
		result = frappe.db.sql("select pg_try_advisory_xact_lock(%s)", (lock_id,))[0][0]
		if result:
			_mark_default_lock_held(lock_key)
			return
		if time.monotonic() >= deadline:
			frappe.throw(
				_("Could not acquire default-setting lock for {0}. Please retry.").format(lock_key),
				frappe.ValidationError,
			)
		time.sleep(0.1)


def _postgres_lock_id(lock_key: str) -> int:
	raw = hashlib.sha256(lock_key.encode("utf-8")).digest()[:8]
	return int.from_bytes(raw, "big", signed=False) & 0x7FFFFFFFFFFFFFFF


def _get_held_default_locks() -> set[str]:
	if not hasattr(frappe.local, "crispy_default_locks"):
		frappe.local.crispy_default_locks = set()
	return frappe.local.crispy_default_locks


def _is_default_lock_held(lock_key: str) -> bool:
	return lock_key in _get_held_default_locks()


def _mark_default_lock_held(lock_key: str) -> None:
	_get_held_default_locks().add(lock_key)
