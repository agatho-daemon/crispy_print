import frappe


def capture_defaults(doctypes: list[str]) -> dict[str, list[str]]:
	saved: dict[str, list[str]] = {}
	for dt in doctypes:
		names = frappe.get_all(
			"Crispy Format",
			filters={"doc_type": dt, "is_default": 1},
			pluck="name",
		)
		saved[dt] = names or []
	return saved


def clear_defaults(doctypes: list[str]):
	if not doctypes:
		return
	frappe.db.sql(
		"update `tabCrispy Format` set is_default = 0 where doc_type in %s",
		(tuple(doctypes),),
	)


def restore_defaults(saved: dict[str, list[str]]):
	for names in (saved or {}).values():
		for name in names:
			frappe.db.set_value("Crispy Format", name, "is_default", 1)
