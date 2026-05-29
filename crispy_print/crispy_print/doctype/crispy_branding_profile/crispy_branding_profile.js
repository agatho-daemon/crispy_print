// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Branding Profile", {
	refresh(frm) {
		set_branding_field_state(frm);
		add_profile_actions(frm);
	},

	code_only(frm) {
		set_branding_field_state(frm);
	},

	branding_mode(frm) {
		set_branding_field_state(frm);
	},

	branding_logo_source(frm) {
		set_branding_field_state(frm);
	},

	branding_letterhead_source(frm) {
		set_branding_field_state(frm);
	},
});

function add_profile_actions(frm) {
	if (frm.is_new()) return;

	frm.add_custom_button(__("Builder Preview"), () => {
		frappe.set_route("cbp-builder", frm.doc.name);
	});
}

function set_branding_field_state(frm) {
	if (frm.doc.code_only) {
		frm.toggle_reqd("custom_typst_code", true);
		return;
	}

	frm.toggle_reqd("custom_typst_code", false);

	const usesLogo = ["Logo Only", "Logo + Letterhead"].includes(frm.doc.branding_mode);
	const usesLetterhead = ["Letterhead Only", "Logo + Letterhead"].includes(
		frm.doc.branding_mode
	);

	if (!usesLogo) {
		frm.set_value("branding_logo_upload", "");
	}
	if (!usesLetterhead) {
		frm.set_value("frappe_company_letterhead", "");
		frm.set_value("branding_letterhead_upload", "");
	}
	if (usesLogo && frm.doc.branding_logo_source === "Company logo") {
		frm.set_value("branding_logo_upload", "");
	}
	if (usesLetterhead && frm.doc.branding_letterhead_source === "Use System Letterhead") {
		frm.set_value("branding_letterhead_upload", "");
	}
	if (usesLetterhead && frm.doc.branding_letterhead_source === "Upload Letterhead") {
		frm.set_value("frappe_company_letterhead", "");
	}

	frm.toggle_reqd("branding_logo_width_mm", usesLogo);
	frm.toggle_reqd("branding_logo_offset_x_mm", usesLogo);
	frm.toggle_reqd("branding_logo_offset_y_mm", usesLogo);
	frm.toggle_reqd(
		"branding_logo_upload",
		usesLogo && frm.doc.branding_logo_source === "Upload image"
	);
	frm.toggle_reqd(
		"frappe_company_letterhead",
		usesLetterhead && frm.doc.branding_letterhead_source === "Use System Letterhead"
	);
	frm.toggle_reqd(
		"branding_letterhead_upload",
		usesLetterhead && frm.doc.branding_letterhead_source === "Upload Letterhead"
	);
}
