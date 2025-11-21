// Copyright (c) 2025, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Format", {
	refresh(frm) {
		frm.add_custom_button(__("Edit Format"), function () {
		if (!frm.doc.doc_type) {
			frappe.msgprint(__("Please select DocType first"));
			return;
		}
		frappe.set_route("crispy-print-builder", frm.doc.name);
	});

	},
});
