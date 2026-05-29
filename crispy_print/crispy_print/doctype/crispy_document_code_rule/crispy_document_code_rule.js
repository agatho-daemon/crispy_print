// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Document Code Rule", {
	form_render(frm, cdt, cdn) {
		syncRuleRow(frm, cdt, cdn);
	},

	condition_type(frm, cdt, cdn) {
		syncRuleRow(frm, cdt, cdn);
	},
});

function syncRuleRow(frm, cdt, cdn) {
	const row = locals[cdt]?.[cdn];
	if (!row) {
		return;
	}

	const conditionType = row.condition_type || "Always";
	if (conditionType === "Always") {
		if (row.condition_json) {
			frappe.model.set_value(cdt, cdn, "condition_json", null);
		}
		if (row.condition_expression) {
			frappe.model.set_value(cdt, cdn, "condition_expression", "");
		}
		return;
	}

	if (conditionType === "Filter JSON" && row.condition_expression) {
		frappe.model.set_value(cdt, cdn, "condition_expression", "");
		return;
	}

	if (["Python Expression", "Custom Method"].includes(conditionType) && row.condition_json) {
		frappe.model.set_value(cdt, cdn, "condition_json", null);
	}
}
