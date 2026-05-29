// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy QR Regulatory Profile", {
	refresh(frm) {
		frm.set_intro(
			__(
				"This regulatory profile provides encoder defaults for document-code generation and can be reused across multiple companies."
			),
			"blue"
		);
		if (!frm.is_new()) {
			frm.add_custom_button(__("Fiscal Credentials"), () => {
				frappe.set_route("List", "Crispy Fiscal Credential", {
					regulatory_profile: frm.doc.name,
				});
			});
			frm.add_custom_button(__("Document Code Profiles"), () => {
				frappe.set_route("List", "Crispy Document Code Profile", {
					regulatory_profile: frm.doc.name,
				});
			});
		}
	},

	standard(frm) {
		if (!frm.doc.encoder_key || frm.doc.encoder_key === "custom") {
			frm.set_value("encoder_key", make_encoder_key(frm.doc.standard));
		}
	},
});

function make_encoder_key(standard) {
	if (!standard || standard === "Custom") {
		return "custom";
	}
	return standard
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, "_")
		.replace(/^_+|_+$/g, "");
}
