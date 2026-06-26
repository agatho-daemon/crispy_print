frappe.pages["crispy-print-preview"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({ parent: wrapper });
	frappe.pages["crispy-print-preview"].print_view = new frappe.ui.CrispyPrintView(wrapper);
};

frappe.pages["crispy-print-preview"].on_page_show = function () {
	const route = frappe.get_route();
	const doctype = route[1];
	const docname = route.slice(2, 3).join(""); // keep simple join for performance
	const format = route[3];
	const routeOptions = frappe.route_options || {};
	const isReportRoute = route[1] === "report";
	const routeReportName = isReportRoute ? route.slice(2).join("/") : null;

	const print_view = frappe.pages["crispy-print-preview"].print_view;
	if (!print_view) return;

	if (isReportRoute || routeOptions.source === "report") {
		print_view.show_report({
			report: routeReportName || routeOptions.report || null,
			source: "report",
			filters: routeOptions.filters || {},
			columns: routeOptions.columns || [],
			chartSvg: routeOptions.chartSvg || "",
		});
		frappe.route_options = null;
		return;
	}

	if (!doctype || !docname) {
		print_view.show_empty_state();
		return;
	}

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
		this.add_or_update_context_action_icon();
		this.setup_menu(format);

		if (!same_doc || !same_format) {
			this.render_preview(frm, format);
		}
	}

	show_empty_state() {
		this.current = {};
		this.vue_instance = null;
		this.page.set_title(__("Crispy Print Preview"));
		this.add_or_update_context_action_icon();
		this.setup_menu(null);
		this.status_el.text("");
		this.print_wrapper.find("#crispy-preview-root").empty();

		setTimeout(() => this.prompt_for_preview_context(), 0);
	}

	show_report(context) {
		const same_report = this.current.report === context.report;
		this.current = {
			report: context.report,
			source: context.source || "report",
			filters: context.filters || {},
			columns: context.columns || [],
			chartSvg: context.chartSvg || "",
		};

		const title = context.report ? `${context.report} Report Preview` : "Report Preview";
		this.page.set_title(__(title));
		this.add_or_update_context_action_icon();
		this.setup_menu(null);

		if (!same_report) {
			this.vue_instance = null;
			this.render_preview({ doctype: null, docname: null }, null, {
				source: context.source || "report",
				report: context.report || null,
				reportFilters: context.filters || {},
				reportColumns: context.columns || [],
				reportChartSvg: context.chartSvg || "",
			});
		}
	}

	render_preview(frm, format, extraProps = {}) {
		this.status_el.text(__("Loading preview..."));

		// Remove existing listener before adding new one
		if (this._remove_refresh_listener) {
			this._remove_refresh_listener();
			this._remove_refresh_listener = null;
		}

		load_crispy_preview_bundle(() => {
			// Mount Vue component if not already mounted
			if (!this.vue_instance) {
				this.vue_instance = window.mountCrispyPreview("#crispy-preview-root", {
					doctype: frm.doctype,
					docname: frm.docname,
					format,
					...extraProps,
				});
			}

			this.status_el.text(__("")); // clear after mount
		});
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
			icon: "es-line-download",
		});
		$download_pdf_btn &&
			$download_pdf_btn.attr &&
			$download_pdf_btn.attr("id", "typst-download");

		this.add_or_update_context_action_icon();
	}

	add_or_update_context_action_icon() {
		if (this._context_action_icon_btn && this._context_action_icon_btn.remove) {
			this._context_action_icon_btn.remove();
			this._context_action_icon_btn = null;
		}

		const isReportContext =
			this.current && this.current.source === "report" && this.current.report;
		const isDocumentContext = this.current && this.current.doctype && this.current.docname;
		if (!isReportContext && !isDocumentContext) return;

		const icon = isReportContext ? "es-line-reports" : "es-line-filetype";
		const tooltip = isReportContext ? __("Report") : __("Form");
		const onClick = isReportContext
			? () => this.go_to_report_view()
			: () => this.go_to_form_view();

		this._context_action_icon_btn = this.page.add_action_icon(icon, onClick, "", tooltip);
	}

	go_to_form_view() {
		if (this.current.doctype && this.current.docname) {
			frappe.set_route("Form", this.current.doctype, this.current.docname);
		}
	}

	go_to_report_view() {
		const reportName = this.current?.report;
		if (!reportName) return;
		const savedFilters = this.current?.filters || {};
		frappe.route_options = { ...savedFilters };
		frappe.set_route("query-report", reportName);
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

	prompt_for_preview_context() {
		if (this._preview_context_dialog?.display) return;

		const dialog = new frappe.ui.Dialog({
			title: __("Choose Print Preview Context"),
			fields: [
				{
					fieldname: "format_type",
					fieldtype: "Select",
					label: __("Document Type"),
					options: "\nDocType\nReport\nContract",
					reqd: 1,
					onchange: () => update_fields(),
				},
				{
					fieldname: "source_doctype",
					fieldtype: "Link",
					label: __("DocType"),
					options: "DocType",
					depends_on: "eval:doc.format_type == 'DocType'",
					reqd: 1,
				},
				{
					fieldname: "report_notice",
					fieldtype: "HTML",
					depends_on: "eval:doc.format_type == 'Report'",
					options: `
						<div class="text-muted" style="line-height: 1.55; padding: 4px 0 8px;">
							${__(
								"Report previews need a live report context, including filters, selected columns, and generated result data."
							)}
							<br>
							${__(
								"Open the report first, configure the view you want, then launch Crispy Print Preview from that report."
							)}
						</div>
					`,
				},
				{
					fieldname: "source_contract",
					fieldtype: "Data",
					label: __("Contract"),
					depends_on: "eval:doc.format_type == 'Contract'",
					description: __("Contract preview is not available yet."),
				},
				{
					fieldname: "source_document",
					fieldtype: "Dynamic Link",
					label: __("Document"),
					options: "source_doctype",
					depends_on: "eval:doc.format_type == 'DocType'",
					reqd: 1,
				},
				{
					fieldname: "format",
					fieldtype: "Link",
					label: __("Crispy Format"),
					options: "Crispy Format",
					depends_on: "eval:doc.format_type == 'DocType'",
				},
			],
			primary_action_label: __("Preview"),
			primary_action: (values) => {
				if (values.format_type === "DocType") {
					const route = [
						"crispy-print-preview",
						values.source_doctype,
						values.source_document,
					];
					if (values.format) route.push(values.format);
					dialog.hide();
					frappe.set_route(...route);
					return;
				}

				if (values.format_type === "Report") {
					frappe.msgprint({
						title: __("Open from a report"),
						message: __(
							"Report previews need filters, selected columns, and generated result data. Open the report first, configure the view you want, then launch Crispy Print Preview from that report."
						),
						indicator: "blue",
					});
					return;
				}

				frappe.msgprint(__("Contract preview is not available yet."));
			},
		});

		const update_fields = () => {
			const values = dialog.get_values(true) || {};
			const is_report = values.format_type === "Report";
			const is_contract = values.format_type === "Contract";
			dialog.set_primary_action_label(
				is_report ? __("How to Preview") : is_contract ? __("Coming Soon") : __("Preview")
			);
			dialog.fields_dict.source_contract.df.reqd = is_contract ? 1 : 0;
			dialog.refresh();
		};

		dialog.$wrapper.on("hidden.bs.modal", () => {
			this._preview_context_dialog = null;
		});
		this._preview_context_dialog = dialog;
		dialog.show();
		update_fields();
	}

	print_document() {
		if (!this.current.doctype && !this.current.report) {
			this.prompt_for_preview_context();
			return;
		}
		frappe.msgprint({
			title: __("Print"),
			message: __("Printing {0}...", [this.current.docname || this.current.report || ""]),
			primary_action: { label: __("Close"), action: () => {} },
		});
	}

	render_pdf() {
		if (!this.current.doctype && !this.current.report) {
			this.prompt_for_preview_context();
			return;
		}
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
		if (!this.current.doctype && !this.current.report) {
			this.prompt_for_preview_context();
			return;
		}
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
		if (!this.current.frm && !this.current.report) {
			this.show_empty_state();
			return;
		}
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

function load_crispy_preview_bundle(callback) {
	if (window.mountCrispyPreview) {
		callback();
		return;
	}
	frappe.require("crispy_preview.bundle.js", () => {
		if (!window.mountCrispyPreview) {
			console.error("[CrispyPrint] mountCrispyPreview not found. Bundle may not be loaded.");
			return;
		}
		callback();
	});
}
