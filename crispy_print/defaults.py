from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

import frappe


def enforce_single_default(
	doctype: str,
	current_name: str,
	*,
	competing_names: Callable[[], Iterable[str]] | None = None,
	filters: dict[str, Any] | None = None,
) -> list[str]:
	"""Serialize default changes using a row that exists even when there are no defaults."""
	if not frappe.db.get_value("DocType", doctype, "name", for_update=True):
		raise frappe.DoesNotExistError(doctype)

	if filters is not None:
		names = frappe.db.get_values(
			doctype, filters, "name", for_update=True, pluck=True, order_by="name asc"
		)
	else:
		names = competing_names() if competing_names else []

	names = sorted({name for name in names if name and name != current_name})
	if names:
		frappe.db.set_value(
			doctype,
			{"name": ["in", names]},
			"is_default",
			0,
			update_modified=False,
		)
	return names
