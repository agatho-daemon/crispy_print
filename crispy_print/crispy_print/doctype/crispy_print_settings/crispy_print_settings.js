// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Print Settings", {
	refresh(frm) {
		refresh_font_paths(frm);
	},

	upload_font(frm) {
		const uploader = new frappe.ui.FileUploader({
			folder: "Home/Attachments",
			restrictions: {
				allowed_file_types: [".ttf", ".otf", ".ttc", ".woff", ".woff2"],
				max_file_size: 25 * 1024 * 1024,
			},
			on_success(file_doc) {
				frappe.call({
					method: "crispy_print.crispy_print.doctype.crispy_print_settings.crispy_print_settings.import_uploaded_font",
					args: {
						file_name: file_doc.name,
						file_url: file_doc.file_url,
					},
					freeze: true,
					freeze_message: __("Importing font..."),
					callback(r) {
						const message = r.message || {};
						if (message.font_search_paths) {
							frm.set_value("font_search_paths", message.font_search_paths);
						}
						frappe.show_alert({
							message: __("Font uploaded"),
							indicator: "green",
						});
						frm.reload_doc();
					},
				});
			},
		});
		if (uploader.dialog?.set_value) {
			uploader.dialog.set_value("is_private", 1);
		}
	},

	refresh_font_list(frm) {
		frappe.call({
			method: "crispy_print.crispy_print.doctype.crispy_print_settings.crispy_print_settings.refresh_font_list",
			freeze: true,
			freeze_message: __("Refreshing font list..."),
			callback(r) {
				const message = r.message || {};
				if (message.font_search_paths) {
					frm.set_value("font_search_paths", message.font_search_paths);
				}
				frappe.show_alert({
					message: __("Font list refreshed"),
					indicator: "green",
				});
			},
		});
	},
});

function refresh_font_paths(frm) {
	frappe.call({
		method: "crispy_print.crispy_print.doctype.crispy_print_settings.crispy_print_settings.refresh_font_list",
		callback(r) {
			const message = r.message || {};
			if (message.font_search_paths) {
				frm.set_value("font_search_paths", message.font_search_paths);
			}
		},
	});
}
