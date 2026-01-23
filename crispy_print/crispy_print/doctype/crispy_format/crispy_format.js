// Copyright (c) 2025, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Format", {
	refresh(frm) {
		// Open Builder button - routes to builder with appropriate mode
		frm.add_custom_button(__("Open Builder"), function () {
			const required_field_by_type = {
				DocType: "doc_type",
				Report: "report",
				Contract: "contract",
			};

			// Generic templates don't require a specific report
			if (frm.doc.crispy_format_type === "Report" && frm.doc.is_generic) {
				if (!frm.doc.generic_report_type) {
					frappe.msgprint(__("Please select Generic Report Type first"));
					return;
				}
			} else {
				const required_field = required_field_by_type[frm.doc.crispy_format_type];

				if (required_field && !frm.doc[required_field]) {
					frappe.msgprint(
						__("Please select {0} first", [
							frappe.meta.get_label("Crispy Format", required_field, frm.doc.name) ||
								required_field,
						])
					);
					return;
				}
			}

			// Navigate to builder page
			frappe.set_route("crispy-format-builder", frm.doc.name);
		});

		// Set as Default button
		if (!frm.is_new() && !frm.doc.is_default) {
			frm.add_custom_button(__("Set as Default"), () => {
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
									frm.reload_doc();
									frappe.show_alert({
										message: r.message.message || __("Set as default"),
										indicator: "green",
									});
								} else {
									frappe.msgprint({
										title: __("Error"),
										message:
											r.message?.error || __("Failed to set as default"),
										indicator: "red",
									});
								}
							},
						});
					}
				);
			});
		}

		if (frm.doc.is_default) {
			frm.dashboard.set_headline(__("Default format for {0}", [frm.doc.doc_type]), "green");
		}

		// Show alert for generic templates
		if (frm.doc.crispy_format_type === "Report" && frm.doc.is_generic) {
			frm.dashboard.set_headline(
				__("Generic template for {0} reports", [frm.doc.generic_report_type]),
				"blue"
			);
		}
	},

	is_generic(frm) {
		if (frm.doc.crispy_format_type !== "Report") return;

		if (frm.doc.is_generic) {
			// Auto-enable raw_typst for generic templates
			frm.set_value("raw_typst", 1);

			// Clear report field (generic templates don't have specific reports)
			if (frm.doc.report) {
				frm.set_value("report", null);
			}

			frappe.show_alert(
				{
					message: __(
						"Raw Typst enabled. You can manually edit Typst code for this template."
					),
					indicator: "blue",
				},
				5
			);
		} else {
			// Clear generic_report_type when switching to custom report
			if (frm.doc.generic_report_type) {
				frm.set_value("generic_report_type", null);
			}

			// Clear raw_typst (it was auto-enabled for generic templates)
			if (frm.doc.raw_typst) {
				frm.set_value("raw_typst", 0);
			}
		}
	},

	raw_typst(frm) {
		// Prevent unchecking raw_typst for generic templates
		if (frm.doc.crispy_format_type === "Report" && frm.doc.is_generic && !frm.doc.raw_typst) {
			frappe.show_alert(
				{
					message: __("Generic templates must use Raw Typst mode"),
					indicator: "orange",
				},
				3
			);
			frm.set_value("raw_typst", 1);
		}
	},
});
