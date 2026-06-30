// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Typst Block", {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__("Open Builder"), () => {
			frappe.set_route("ctb-builder", frm.doc.name);
		});
	},
});
