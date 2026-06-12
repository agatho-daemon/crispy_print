frappe.listview_settings["Crispy Template"] = {
	add_fields: ["status", "is_active"],
	filters: [
		["status", "=", "Approved"],
		["is_active", "=", 1],
	],
	onload(listview) {
		listview.page.clear_primary_action();
	},
	refresh(listview) {
		listview.page.clear_primary_action();
	},
};
