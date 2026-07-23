// Copyright (c) 2025, Agathodaemon and contributors
// For license information, please see license.txt

frappe.provide("crispy_print");

(() => {
	const getLogger = (scope = {}) => {
		const base = window?.CrispyPrintLogger;
		if (base && typeof base.child === "function") {
			return base.child(scope);
		}
		const noop = {
			debug: () => {},
			info: () => {},
			warn: () => {},
			error: () => {},
			child: () => noop,
			setLevel: () => {},
		};
		return noop;
	};
	const logger = getLogger({ module: "ReportButton" });
	// Avoid double-binding if assets are loaded twice in dev.
	if (window.__crispy_qr_patched__) return;
	window.__crispy_qr_patched__ = true;

	const BTN_MARK = "data-crispy-print-btn";

	crispy_print.add_print_button = function (report) {
		const qr = report || frappe.query_report;

		// Must exist and have a page to attach the button to
		if (!qr || !qr.report_name || !qr.page || typeof qr.page.add_inner_button !== "function") {
			return;
		}

		// Already added and still in DOM
		if (qr.page.btn_typst_print) {
			const btn = qr.page.btn_typst_print;
			const btnEl = btn && btn.length ? btn[0] : null;
			if (btnEl && document.contains(btnEl)) {
				if (btnEl.__crispy_report_instance__ === qr) return;
				btn.remove?.();
			}
			qr.page.btn_typst_print = null;
		}

		// Prevent duplicates even if page.btn_typst_print is lost
		if (qr.page && qr.page.inner_toolbar) {
			const existing = qr.page.inner_toolbar[0]?.querySelector?.(`button[${BTN_MARK}="1"]`);
			if (existing) return;
		}

		const btn_label = `<img src="/assets/crispy_print/icons/typst.svg"
			style="width:45px;height:45px;margin-top:2px;"
			alt="${__("Crispy Print")}"
			title="${__("Open Crispy Print Preview")}"/>`;

		qr.page.btn_typst_print = qr.page.add_inner_button(btn_label, () => {
			const filters = qr.get_filter_values ? qr.get_filter_values() : {};
			const columns = qr.columns || [];
			const chartSvgEl =
				document.querySelector(".chart-container svg") ||
				document.querySelector(".report-chart svg") ||
				document.querySelector("#chart svg");
			const chartSvg = chartSvgEl ? chartSvgEl.outerHTML : "";
			const safeFilters = JSON.parse(JSON.stringify(filters || {}));
			const safeColumns = JSON.parse(JSON.stringify(columns || []));
			const state = {
				report: qr.report_name,
				filters: safeFilters,
				columns: safeColumns,
				chartSvg,
			};
			try {
				if (typeof window !== "undefined") {
					window.sessionStorage.setItem(
						`crispy-print:report:${qr.report_name}`,
						JSON.stringify(state)
					);
				}
			} catch (error) {
				logger.warn("Failed to persist report state", error);
			}
			frappe.route_options = {
				source: "report",
				filters: safeFilters,
				columns: safeColumns,
				chartSvg,
			};
			frappe.set_route("crispy-print-preview", "report", qr.report_name);
		});

		const btnEl = qr.page.btn_typst_print && qr.page.btn_typst_print[0];
		if (btnEl) {
			btnEl.setAttribute(BTN_MARK, "1");
			btnEl.__crispy_report_instance__ = qr;
		}
	};

	function inQueryReportRoute() {
		const route = typeof frappe.get_route === "function" ? frappe.get_route() : null;
		return Array.isArray(route) && route[0] === "query-report";
	}

	function tryAddButton() {
		if (!inQueryReportRoute()) return;
		const qr = frappe.query_report;
		if (!qr || !qr.report_name) return;
		crispy_print.add_print_button(qr);
	}

	function tryAddButtonForReport(report) {
		if (!report || !report.report_name) return;
		crispy_print.add_print_button(report);
	}

	function withSpanYAxisMode(options) {
		if (!options || typeof options !== "object") return options;
		const chartType = String(options.type || "").toLowerCase();
		const axisTypes = new Set(["bar", "line", "scatter", "axis-mixed"]);
		if (!axisTypes.has(chartType)) return options;
		options.axisOptions = options.axisOptions || {};
		options.axisOptions.yAxisMode = "span";
		return options;
	}

	// Try on initial route load
	setTimeout(tryAddButton, 300);

	// Re-try when navigation happens
	$(document).on("page-change", tryAddButton);
	if (frappe.router && typeof frappe.router.on === "function") {
		frappe.router.on("change", tryAddButton);
	}

	// Monkey-patch refresh to re-attach button after report renders
	const QueryReport = frappe.views && frappe.views.QueryReport;
	const proto = QueryReport && QueryReport.prototype;
	if (proto && !proto.__crispy_refresh_patched__) {
		const originalRefresh = proto.refresh;
		proto.refresh = function (...args) {
			const result = originalRefresh.apply(this, args);
			Promise.resolve(result)
				.then(() => {
					tryAddButtonForReport(this);
				})
				.catch(() => {
					// no-op: keep original behavior
				});
			return result;
		};
		proto.__crispy_refresh_patched__ = true;
	}

	// Ensure report charts render y-grid lines by default.
	if (proto && !proto.__crispy_chart_axis_patched__) {
		if (typeof proto.get_chart_options === "function") {
			const originalGetChartOptions = proto.get_chart_options;
			proto.get_chart_options = function (...args) {
				const options = originalGetChartOptions.apply(this, args);
				return withSpanYAxisMode(options);
			};
		}

		if (typeof proto.render_chart === "function") {
			const originalRenderChart = proto.render_chart;
			proto.render_chart = function (options, ...rest) {
				return originalRenderChart.call(this, withSpanYAxisMode(options), ...rest);
			};
		}

		proto.__crispy_chart_axis_patched__ = true;
	}
})();

// Format selector dialog
crispy_print.show_format_selector = function (report_name, report_instance) {
	const filters =
		report_instance && typeof report_instance.get_filter_values === "function"
			? report_instance.get_filter_values() || {}
			: {};
	// Check for available formats
	frappe.call({
		method: "crispy_print.api.v1.get_available_formats",
		args: { report: report_name, company: filters.company || null },
		callback: (r) => {
			const formats = r.message;

			if (!formats.formats || !formats.formats.length) {
				frappe.msgprint({
					title: __("No Formats Available"),
					message: __(
						"Please create a Crispy Format for this report first. Go to Crispy Format list and create a new format."
					),
					indicator: "orange",
				});
				return;
			}

			// Show format selector
			crispy_print.show_format_dialog(report_name, formats, report_instance);
		},
	});
};

crispy_print.show_format_dialog = function (report_name, formats, report_instance) {
	// Build options for select field
	let format_options = [];
	let default_value = null;

	if (formats.formats.length > 0) {
		format_options.push({
			label: __("Compatible Formats"),
			options: formats.formats.map((f) => ({
				label: `${f.name} (${f.report_renderer} · ${f.layout_style})`,
				value: f.name,
			})),
		});
		default_value = formats.default_format || formats.formats[0].name;
	}

	// Flatten options for Select field
	let all_options = [];
	format_options.forEach((group) => {
		group.options.forEach((opt) => {
			all_options.push(opt.value);
		});
	});

	const dialog = new frappe.ui.Dialog({
		title: __("Print Settings"),
		fields: [
			{
				fieldtype: "HTML",
				fieldname: "format_info",
				options: `<p class="text-muted">${__(
					"Choose a format for"
				)} <strong>${report_name}</strong></p>`,
			},
			{
				fieldtype: "Select",
				fieldname: "format",
				label: __("Print Format"),
				options: all_options,
				default: default_value,
				reqd: 1,
			},
			{
				fieldtype: "Section Break",
			},
			{
				fieldtype: "Select",
				fieldname: "orientation",
				label: __("Orientation"),
				options: ["Portrait", "Landscape"],
				default: "Landscape",
			},
			{
				fieldtype: "Column Break",
			},
			{
				fieldtype: "Check",
				fieldname: "include_filters",
				label: __("Include Filters"),
				default: 0,
			},
			{
				fieldtype: "Section Break",
				label: __("Columns"),
				collapsible: 1,
			},
			{
				fieldtype: "HTML",
				fieldname: "columns_selector",
				options: crispy_print.build_column_selector_html(report_instance.columns || []),
			},
		],
		primary_action_label: __("Generate PDF"),
		primary_action(values) {
			const selected_format = values.format;
			const orientation = values.orientation || "Landscape";
			const include_filters = values.include_filters || 0;

			// Extract column selections and widths from the HTML interface
			const column_config = crispy_print.get_column_config_from_dialog(dialog);

			// Get current report filters
			const filters = report_instance.get_filter_values
				? report_instance.get_filter_values()
				: {};

			// Show loading
			frappe.show_alert(
				{
					message: __("Generating PDF..."),
					indicator: "blue",
				},
				30
			);

			// Call API
			frappe.call({
				method: "crispy_print.api.v1.generate_report_pdf",
				args: {
					report: report_name,
					filters: JSON.stringify(filters),
					format_name: selected_format,
					orientation: orientation.toLowerCase(),
					include_filters: include_filters,
					column_config: column_config.length > 0 ? JSON.stringify(column_config) : null,
				},
				callback: (r) => {
					if (r.message && r.message.status === "success") {
						// Open PDF in new tab
						window.open(r.message.pdf_url, "_blank");

						frappe.show_alert(
							{
								message: __("PDF generated successfully"),
								indicator: "green",
							},
							5
						);
					}
				},
				error: (r) => {
					// Hide loading alert
					frappe.hide_progress();

					// Extract error message from response
					let error_msg = __("Unknown error occurred");

					if (r && r._server_messages) {
						try {
							const messages = JSON.parse(r._server_messages);
							if (messages && messages.length > 0) {
								const msg = JSON.parse(messages[0]);
								error_msg = msg.message || error_msg;
							}
						} catch (e) {
							logger.error("Error parsing server messages", e);
						}
					} else if (r && r.message) {
						error_msg = r.message;
					} else if (r && r.exc) {
						// Full exception details
						error_msg = r.exc;
					}

					// Log full error details
					logger.error("Typst PDF Generation Failed", {
						errorMessage: error_msg,
						response: r,
						traceback: r && r.exc ? r.exc : null,
					});

					// Show simple error dialog
					frappe.msgprint({
						title: __("PDF Generation Failed"),
						message: error_msg,
						indicator: "red",
					});
				},
			});

			dialog.hide();
		},
	});

	dialog.show();
};

// Build HTML for column selector with 2-column grid layout
crispy_print.build_column_selector_html = function (columns) {
	if (!columns || columns.length === 0) {
		return `<p class="text-muted">${__("No columns available")}</p>`;
	}

	let html = `
		<div class="column-selector">
			<style>
				.column-selector {
					max-height: 400px;
					overflow-y: auto;
					padding: 10px;
					border: 1px solid var(--border-color);
					border-radius: 4px;
				}
				.column-grid {
					display: grid;
					grid-template-columns: 1fr 1fr;
					gap: 8px 16px;
				}
				.column-item {
					display: flex;
					align-items: center;
					gap: 8px;
					padding: 4px;
					border-bottom: 1px solid var(--border-color);
				}
				.column-item:last-child {
					border-bottom: none;
				}
				.column-checkbox {
					flex-shrink: 0;
				}
				.column-label {
					flex-grow: 1;
					font-size: 13px;
					cursor: pointer;
				}
				.column-width {
					width: 70px;
					padding: 2px 6px;
					font-size: 12px;
					border: 1px solid var(--border-color);
					border-radius: 3px;
				}
				.column-width:disabled {
					background-color: var(--control-bg);
					opacity: 0.5;
				}
				.column-selector-header {
					display: flex;
					justify-content: space-between;
					margin-bottom: 10px;
					padding-bottom: 8px;
					border-bottom: 2px solid var(--border-color);
				}
				.column-selector-actions {
					display: flex;
					gap: 8px;
				}
			</style>
			<div class="column-selector-header">
				<span class="text-muted">${__(
					"Select columns and set widths (e.g., auto, 1fr, 2cm, 100pt)"
				)}</span>
				<div class="column-selector-actions">
					<button class="btn btn-xs btn-default" onclick="crispy_print.toggle_all_columns(true)">
						${__("Select All")}
					</button>
					<button class="btn btn-xs btn-default" onclick="crispy_print.toggle_all_columns(false)">
						${__("Deselect All")}
					</button>
				</div>
			</div>
			<div class="column-grid">
	`;

	columns.forEach((col, idx) => {
		const fieldname = col.fieldname || col.id;
		const label = col.label || fieldname;

		html += `
			<div class="column-item">
				<input
					type="checkbox"
					class="column-checkbox"
					id="col_${idx}"
					data-fieldname="${fieldname}"
					onchange="crispy_print.toggle_width_input(this)"
				/>
				<label class="column-label" for="col_${idx}">${label}</label>
				<input
					type="text"
					class="column-width"
					id="width_${idx}"
					value="auto"
					placeholder="${__("auto")}"
					disabled
				/>
			</div>
		`;
	});

	html += `
			</div>
		</div>
	`;

	return html;
};

// Toggle width input based on checkbox state
crispy_print.toggle_width_input = function (checkbox) {
	const idx = checkbox.id.replace("col_", "");
	const widthInput = document.getElementById(`width_${idx}`);
	if (widthInput) {
		widthInput.disabled = !checkbox.checked;
	}
};

// Toggle all column checkboxes
crispy_print.toggle_all_columns = function (select) {
	document.querySelectorAll(".column-checkbox").forEach((cb) => {
		cb.checked = select;
		crispy_print.toggle_width_input(cb);
	});
};

// Extract column configuration from dialog
crispy_print.get_column_config_from_dialog = function (dialog) {
	const config = [];
	const checkboxes = dialog.$wrapper.find(".column-checkbox");

	checkboxes.each(function () {
		if (this.checked) {
			const idx = this.id.replace("col_", "");
			const fieldname = this.dataset.fieldname;
			const widthInput = document.getElementById(`width_${idx}`);
			const width = widthInput ? widthInput.value.trim() : "auto";

			config.push({
				fieldname: fieldname,
				width: width || "auto",
			});
		}
	});

	return config;
};
