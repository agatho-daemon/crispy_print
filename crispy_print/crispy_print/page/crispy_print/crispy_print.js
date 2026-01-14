frappe.pages["crispy-print"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper });
	frappe.pages["crispy-print"].print_view = new frappe.ui.CrispyPrintView(wrapper);
};

frappe.pages["crispy-print"].on_page_show = function () {
	const route = frappe.get_route();
	const doctype = route[1];
	const docname = route.slice(2, 3).join(""); // keep simple join for performance
	const format = route[3];

	const print_view = frappe.pages["crispy-print"].print_view;
	if (!print_view || !doctype || !docname) return;

	// Let the Typst worker be the single source of truth for fetching the document (via API).
	// We only pass doctype/docname through; the worker will fetch and compile.
	const frm = { doctype, docname };
	print_view.show(frm, format);
};

frappe.ui.CrispyPrintView = class {
	constructor(wrapper) {
		this.wrapper = $(wrapper);
		this.page = wrapper.page;
		this.current = {};
		this.make();
	}

	make() {
		this.print_wrapper = this.page.main.empty().html(
			`<div class="print-preview-wrapper" style="padding: 0; background: transparent; border-radius: 6px; overflow: hidden;">
                <div id="crispy-preview-root"></div>
                <div class="text-muted small" id="crispy-preview-status"></div>
            </div>`
		);

		this.status_el = this.print_wrapper.find("#crispy-preview-status");
		this.setup_toolbar();

		// Hide Frappe's sidebar completely (settings are in CrispyPP.vue)
		this.page.sidebar.hide();
		this.wrapper.find(".page-head").removeClass("drop-shadow");
	}

	show(frm, format) {
		const same_doc =
			this.current.doctype === frm.doctype && this.current.docname === frm.docname;
		const same_format = this.current.format === format;

		this.current = { doctype: frm.doctype, docname: frm.docname, format, frm };

		this.page.set_title(__(frm.docname));
		this.setup_menu(format);

		if (!same_doc || !same_format) {
			this.render_preview(frm, format);
		}
	}

	render_preview(frm, format) {
		this.status_el.text(__("Loading preview..."));

		// Remove existing listener before adding new one
		if (this._remove_refresh_listener) {
			this._remove_refresh_listener();
			this._remove_refresh_listener = null;
		}

		// Mount Vue component if not already mounted
		if (!this.vue_instance) {
			this.vue_instance = window.mountCrispyPreview("#crispy-preview-root", {
				doctype: frm.doctype,
				docname: frm.docname,
				format,
			});
		}

		this.status_el.text(__("")); // clear after mount
	}

	// Optional: call this when tearing down the page to avoid lingering listeners
	destroy() {
		this.vue_instance = null;
	}

	setup_toolbar() {
		this.page.set_primary_action(__("Print"), () => this.print_document(), "printer");
		const $view_pdf_btn = this.page.add_button(__("PDF"), () => this.render_pdf(), {
			icon: "small-file",
		});
		$view_pdf_btn && $view_pdf_btn.attr && $view_pdf_btn.attr("id", "typst-view-pdf");

		const $download_pdf_btn = this.page.add_button(__("Download"), () => this.download_pdf(), {
			icon: "download",
		});
		$download_pdf_btn &&
			$download_pdf_btn.attr &&
			$download_pdf_btn.attr("id", "typst-download");

		this.page.add_action_icon(
			"es-line-filetype",
			() => this.go_to_form_view(),
			"",
			__("Form")
		);
	}

	go_to_form_view() {
		if (this.current.doctype && this.current.docname) {
			frappe.set_route("Form", this.current.doctype, this.current.docname);
		}
	}

	setup_menu(format) {
		this.page.clear_menu();
		this.page.add_menu_item(__("Print Settings"), () =>
			frappe.set_route("Form", "Print Settings")
		);
		if (format) {
			this.page.add_menu_item(__("Customize"), () =>
				frappe.set_route("crispy-format-builder", format)
			);
		}
	}

	print_document() {
		frappe.msgprint({
			title: __("Print"),
			message: __("Printing {0}...", [this.current.docname || ""]),
			primary_action: { label: __("Close"), action: () => {} },
		});
	}

	render_pdf() {
		frappe.show_alert({ message: __("Generating PDF..."), indicator: "blue" });

		// Call Vue component's PDF generation method
		if (this.vue_instance?.component?.generatePDF) {
			this.vue_instance.component.generatePDF();
		} else {
			frappe.show_alert({
				message: __("PDF generation not available"),
				indicator: "red",
			});
		}
	}

	download_pdf() {
		frappe.show_alert({ message: __("Generating PDF..."), indicator: "blue" });

		if (this.vue_instance?.component?.downloadPDF) {
			this.vue_instance.component.downloadPDF();
		} else if (this.vue_instance?.component?.generatePDF) {
			// Fallback to opening in new tab if download isn't available
			this.vue_instance.component.generatePDF();
		} else {
			frappe.show_alert({
				message: __("PDF generation not available"),
				indicator: "red",
			});
		}
	}

	refresh_preview() {
		// Trigger refresh via Vue component
		if (this.vue_instance?.component?.triggerRefresh) {
			this.vue_instance.component.triggerRefresh();
		} else {
			// Fallback: remount
			this.vue_instance = null;
			this.render_preview(this.current.frm, this.current.format);
		}
	}
};
