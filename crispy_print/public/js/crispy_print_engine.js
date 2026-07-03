frappe.ui.form.register_print_engine("crispy_print", {
	open({ frm, doctype, name }) {
		frappe.route_options = {
			frm,
			doctype,
			name,
			docname: name,
			source: "print_doc",
			print_engine: "crispy_print",
		};

		frappe.set_route("crispy-print-preview", doctype, name);
	},
});
