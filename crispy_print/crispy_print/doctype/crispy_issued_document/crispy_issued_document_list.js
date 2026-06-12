frappe.listview_settings["Crispy Issued Document"] = {
	onload(listview) {
		listview.page.clear_primary_action();
	},
	refresh(listview) {
		listview.page.clear_primary_action();
	},
};
