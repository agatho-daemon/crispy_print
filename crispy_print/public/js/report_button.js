// Copyright (c) 2025, Agathodaemon and contributors
// For license information, please see license.txt

frappe.provide("crispy_print");

// Hook into query report after it's loaded
$(document).on("frappe.query_report.after_refresh", function () {
	crispy_print.add_print_button();
});

// Also try to add on route change
frappe.router.on("change", () => {
	if (frappe.get_route()[0] === "query-report") {
		setTimeout(() => {
			crispy_print.add_print_button();
		}, 1000);
	}
});

crispy_print.add_print_button = function () {
	// Check if query report exists
	if (!frappe.query_report || !frappe.query_report.report_name) {
		return;
	}

	// Check if already added
	if (frappe.query_report.page.btn_typst_print) {
		const btn = frappe.query_report.page.btn_typst_print;
		const btnEl = btn && btn.length ? btn[0] : null;
		if (btnEl && document.contains(btnEl)) {
			return;
		}
		frappe.query_report.page.btn_typst_print = null;
	}

	// Add button to page menu
	const btn_label = `<img src="/assets/crispy_print/icons/typst.svg"
        	style="width:45px;height:45px;margin-top:2px;"
            alt="Crispy Print"
            title="Open Crispy Print Preview"/>`;
	frappe.query_report.page.btn_typst_print = frappe.query_report.page.add_inner_button(
		btn_label,
		() => {
			const filters = frappe.query_report.get_filter_values
				? frappe.query_report.get_filter_values()
				: {};
			const columns = frappe.query_report.columns || [];
			frappe.route_options = {
				source: "report",
				filters,
				columns,
			};
			frappe.set_route("crispy-print", "report", frappe.query_report.report_name);
		}
	);
};

// Format selector dialog
crispy_print.show_format_selector = function (report_name, report_instance) {
	// Check for available formats
	frappe.call({
		method: "crispy_print.api.get_available_formats",
		args: { report: report_name },
		callback: (r) => {
			const formats = r.message;

			if (!formats.custom_formats.length && !formats.generic_formats.length) {
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

	// Add custom formats
	if (formats.custom_formats.length > 0) {
		format_options.push({
			label: __("Custom Formats"),
			options: formats.custom_formats.map((f) => ({
				label: f.name,
				value: f.name,
			})),
		});
		default_value = formats.custom_formats[0].name;
	}

	// Add generic formats
	if (formats.generic_formats.length > 0) {
		format_options.push({
			label: __("Generic Templates"),
			options: formats.generic_formats.map((f) => ({
				label: `${f.generic_report_type} Template`,
				value: f.name,
			})),
		});

		if (!default_value) {
			default_value = formats.generic_formats[0].name;
		}
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
				method: "crispy_print.api.generate_report_pdf",
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
							console.error("Error parsing server messages:", e);
						}
					} else if (r && r.message) {
						error_msg = r.message;
					} else if (r && r.exc) {
						// Full exception details
						error_msg = r.exc;
					}

					// Log full error details to console
					console.group("❌ Typst PDF Generation Failed");
					console.error("Error message:", error_msg);
					console.error("Full response:", r);
					if (r && r.exc) {
						console.error("Exception traceback:", r.exc);
					}
					console.groupEnd();

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
		return '<p class="text-muted">No columns available</p>';
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
					placeholder="auto"
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
