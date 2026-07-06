frappe.ui.form.register_print_engine("crispy_print", {
	async can_print({ doctype, name }) {
		if (!doctype || !name) {
			return false;
		}

		try {
			const response = await frappe.call({
				method: "crispy_print.api.v1.can_resolve_crispy_template_for_document",
				args: {
					source_doctype: doctype,
					source_docname: name,
				},
			});

			return Boolean(response.message);
		} catch (error) {
			console.warn("Crispy Print skipped: template eligibility check failed", error);
			return false;
		}
	},

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
