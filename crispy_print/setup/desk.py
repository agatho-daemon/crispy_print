import frappe
from frappe import __version__ as frappe_version


def get_frappe_major() -> int:
	return int(frappe_version.lstrip("v").split(".", 1)[0])


def set_workspace_hidden(workspace: str, hidden: bool) -> None:
	if frappe.db.exists("Workspace", workspace):
		frappe.db.set_value(
			"Workspace",
			workspace,
			"is_hidden",
			1 if hidden else 0,
			update_modified=False,
		)


def setup_desk_compatibility() -> None:
	frappe_major = get_frappe_major()

	if frappe_major < 16:
		# v15 uses classic Workspace sidebar.
		set_workspace_hidden("Crispy", False)
		set_workspace_hidden("Crispy Studio", True)
		frappe.clear_cache()
