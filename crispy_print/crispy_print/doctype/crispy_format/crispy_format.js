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
		// Show "Set as Default" button only if not already default
		if (!frm.is_new() && !frm.doc.is_default) {
			frm.add_custom_button(__("Set as Default"),
			() => {
				const format_label = frm.doc.name;

				frappe.confirm(
					__("Set {0} as the default Crispy Format for {1}?", [
						format_label,
						frm.doc.doc_type,
					]),
					() => {
						frappe.call({
							method: "crispy_print.crispy_print.doctype.crispy_format.crispy_format.make_default",
							args: { name: frm.doc.name },
							freeze: true,
							freeze_message: __("Setting as default..."),
							callback(r) {
								frappe.call({
									method: "crispy_print.api.get_default_doctypes",
									callback(r) {
										const doctypes = r.message || [];
										if (window.typstPrint?.registerButtonsFor) {
											window.typstPrint.registerButtonsFor(doctypes);
										}
									},
								});

								if (r.message?.success) {
									frm.reload_doc()
									frappe.show_alert({
										message: r.message.message || __("Set as default"),
										indicator: "green",
									})
								} else {
									frappe.msgprint({
										title: __("Error"),
										message: r.message?.error || __("Failed to set as default"),
										indicator: "red",
									})
								}
							},
						})
					}
				)
			})
		}

		if (frm.doc.is_default) {
			frm.dashboard.set_headline(
				__("Default format for {0}", [frm.doc.doc_type]),
				"green"
			)
		}
	},
});
