// Copyright (c) 2025, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Format", {
	refresh(frm) {
		// Open Builder button - routes to builder with appropriate mode
		frm.add_custom_button(__("Open Builder"), function () {
			const required_field_by_type = {
				DocType: "doc_type",
				Contract: "contract",
			};

			// All-compatible formats don't require a specific report.
			if (
				frm.doc.crispy_format_type === "Report" &&
				frm.doc.report_scope === "All Compatible Reports"
			) {
				if (!frm.doc.report_renderer) {
					frappe.msgprint(__("Please select Report Renderer first"));
					return;
				}
			} else if (frm.doc.crispy_format_type === "Report") {
				const linkedReports = getActiveLinkedReports(frm.doc);
				if (!linkedReports.length) {
					frappe.msgprint(__("Please add at least one linked Report first"));
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

			if (frm.is_new()) {
				frappe.prompt(
					{
						fieldname: "format_name",
						fieldtype: "Data",
						label: __("Format Name"),
						reqd: 1,
					},
					(values) => {
						frappe.route_options = {
							crispy_format_draft: {
								...frm.doc,
								name: String(values.format_name || "").trim(),
								__islocal: 1,
							},
						};
						frappe.set_route("crispy-format-builder", "new");
					},
					__("Preview Unsaved Format"),
					__("Open Builder")
				);
				return;
			}

			frappe.set_route("crispy-format-builder", frm.doc.name);
		});

		// Export button
		if (!frm.is_new()) {
			frm.add_custom_button(__("Export"), async () => {
				await exportFormat(frm.doc.name);
			});
		}

		// Import button
		frm.add_custom_button(__("Import"), async () => {
			await openImportDialog();
		});

		if (frm.doc.is_default) {
			frm.dashboard.set_headline(
				__("Default format for {0}", [getDefaultScopeLabel(frm.doc)]),
				"green"
			);
		}

		// Show alert for generic templates
		if (
			frm.doc.crispy_format_type === "Report" &&
			frm.doc.report_scope === "All Compatible Reports"
		) {
			frm.dashboard.set_headline(
				__("Compatible fallback for {0}", [frm.doc.report_renderer]),
				"blue"
			);
		}
	},

	report_scope(frm) {
		if (frm.doc.crispy_format_type !== "Report") return;

		if (frm.doc.report_scope === "All Compatible Reports") {
			if ((frm.doc.report || []).length) {
				frm.clear_table("report");
				frm.refresh_field("report");
			}
		}
	},
});

function getActiveLinkedReports(doc) {
	return (doc.report || []).filter((row) => row.report && !row.disabled);
}

function getDefaultScopeLabel(doc) {
	if (doc.crispy_format_type === "DocType") {
		return doc.doc_type || __("this DocType");
	}

	if (doc.crispy_format_type === "Contract") {
		return doc.contract || __("this Contract");
	}

	if (doc.crispy_format_type === "Report") {
		if (doc.report_scope === "All Compatible Reports") {
			return doc.report_renderer
				? __("compatible {0} reports", [doc.report_renderer])
				: __("compatible reports");
		}

		const linkedReports = getActiveLinkedReports(doc).map((row) => row.report);
		if (linkedReports.length === 1) {
			return linkedReports[0];
		}
		if (linkedReports.length > 1) {
			return __("{0} linked reports", [linkedReports.length]);
		}
		return __("linked reports");
	}

	return __("this format");
}

async function exportFormat(name) {
	if (!name) {
		frappe.msgprint(__("Please save the format before exporting."));
		return;
	}

	try {
		const response = await frappe.call({
			method: "crispy_print.api.v1.export_crispy_format",
			args: { name },
		});

		const payload = response.message;
		if (!payload) {
			throw new Error(__("Missing export payload"));
		}

		downloadExportPayload(name, payload);
		frappe.show_alert({ message: __("Exported format: {0}", [name]), indicator: "green" });
	} catch (error) {
		frappe.msgprint({
			title: __("Export Failed"),
			message: error?.message || __("Failed to export format."),
			indicator: "red",
		});
	}
}

async function openImportDialog() {
	const fileText = await pickJsonFile();
	if (!fileText) return;

	try {
		const conflictResponse = await frappe.call({
			method: "crispy_print.api.v1.check_import_conflicts",
			args: { payload: fileText },
		});
		const conflict = conflictResponse.message || {};
		const hasConflict = Boolean(conflict.exists || conflict.conflict);

		if (hasConflict) {
			frappe.confirm(
				__(
					"Format <strong>{0}</strong> already exists.<br><br>Yes: overwrite existing.<br>No: import as copy.",
					[escapeHtml(conflict.name || "")]
				),
				async () => {
					await importFormatPayload(fileText, "overwrite");
				},
				async () => {
					await importFormatPayload(fileText, "copy");
				}
			);
			return;
		}

		await importFormatPayload(fileText, "copy");
	} catch (error) {
		frappe.msgprint({
			title: __("Import Failed"),
			message: error?.message || __("Failed to check import payload."),
			indicator: "red",
		});
	}
}

async function importFormatPayload(fileText, action) {
	try {
		const response = await frappe.call({
			method: "crispy_print.api.v1.import_crispy_format",
			args: {
				payload: fileText,
				on_conflict: action,
			},
		});
		const result = response.message || {};
		const importedName = result.name;
		const warnings = Array.isArray(result.warnings) ? result.warnings : [];

		frappe.show_alert(
			{
				message: __("Imported format: {0}", [importedName]),
				indicator: "green",
			},
			7
		);

		if (warnings.length) {
			const warningHtml = [
				`<p>${__("Imported with warnings:")}</p>`,
				"<ul>",
				...warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`),
				"</ul>",
			].join("");

			frappe.msgprint({
				title: __("Import Warnings"),
				message: warningHtml,
				indicator: "orange",
			});
		}

		if (importedName) {
			frappe.set_route("Form", "Crispy Format", importedName);
		}
	} catch (error) {
		frappe.msgprint({
			title: __("Import Failed"),
			message: error?.message || __("Failed to import format."),
			indicator: "red",
		});
	}
}

function pickJsonFile() {
	return new Promise((resolve) => {
		const input = document.createElement("input");
		input.type = "file";
		input.accept = ".json,application/json";
		input.style.display = "none";

		input.addEventListener("change", () => {
			const file = input.files && input.files[0];
			if (!file) {
				resolve(null);
				return;
			}

			const reader = new FileReader();
			reader.onload = () => resolve(String(reader.result || ""));
			reader.onerror = () => resolve(null);
			reader.readAsText(file, "utf-8");
		});

		document.body.appendChild(input);
		input.click();
		setTimeout(() => {
			if (input.parentNode) {
				input.parentNode.removeChild(input);
			}
		}, 0);
	});
}

function downloadExportPayload(formatName, payload) {
	const safeName = String(formatName || "crispy-format")
		.replace(/[^a-zA-Z0-9_-]+/g, "_")
		.replace(/^_+|_+$/g, "");
	const filename = `${safeName || "crispy-format"}.crispy-format.json`;
	const json = JSON.stringify(payload, null, 2);
	const blob = new Blob([json], { type: "application/json;charset=utf-8" });
	const url = URL.createObjectURL(blob);
	const anchor = document.createElement("a");
	anchor.href = url;
	anchor.download = filename;
	document.body.appendChild(anchor);
	anchor.click();
	document.body.removeChild(anchor);
	URL.revokeObjectURL(url);
}

function escapeHtml(text) {
	const value = String(text ?? "");
	return value
		.replaceAll("&", "&amp;")
		.replaceAll("<", "&lt;")
		.replaceAll(">", "&gt;")
		.replaceAll('"', "&quot;")
		.replaceAll("'", "&#39;");
}
