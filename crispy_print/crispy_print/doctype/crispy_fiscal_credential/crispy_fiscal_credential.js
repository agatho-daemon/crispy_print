// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Fiscal Credential", {
	refresh(frm) {
		frm.set_intro(
			__(
				"This credential is used by the backend document-code generator when a matching profile requires signing or regulated encoding."
			),
			"blue"
		);
		show_validity_warnings(frm);
		if (!frm.is_new()) {
			frm.add_custom_button(__("Document Code Profiles"), () => {
				frappe.set_route("List", "Crispy Document Code Profile", {
					fiscal_credential: frm.doc.name,
				});
			});
			if (frm.doc.regulatory_profile) {
				frm.add_custom_button(__("Regulatory Profile"), () => {
					frappe.set_route(
						"Form",
						"Crispy QR Regulatory Profile",
						frm.doc.regulatory_profile
					);
				});
			}
		}
	},

	regulatory_profile(frm) {
		if (!frm.doc.regulatory_profile) {
			return;
		}

		frappe.db
			.get_value("Crispy QR Regulatory Profile", frm.doc.regulatory_profile, [
				"authority_code",
				"country",
			])
			.then((response) => {
				const values = response.message || {};
				if (!frm.doc.authority_code && values.authority_code) {
					frm.set_value("authority_code", values.authority_code);
				}
				if (!frm.doc.country && values.country) {
					frm.set_value("country", values.country);
				}
			});
	},
});

function show_validity_warnings(frm) {
	if (!frm.doc.valid_until) {
		return;
	}

	const now = frappe.datetime.now_datetime();
	if (frm.doc.valid_until < now) {
		frm.dashboard.set_headline_alert(__("This fiscal credential is expired."), "orange");
		return;
	}

	const expiry_date = frappe.datetime.str_to_obj(frm.doc.valid_until);
	const threshold = frappe.datetime.add_days(frappe.datetime.now_date(), 30);
	if (expiry_date <= frappe.datetime.str_to_obj(threshold)) {
		frm.dashboard.set_headline_alert(
			__("This fiscal credential expires within 30 days."),
			"yellow"
		);
	}
}
