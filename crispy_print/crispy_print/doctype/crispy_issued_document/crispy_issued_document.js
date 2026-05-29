// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Issued Document", {
	refresh(frm) {
		setStatusHeadline(frm);
		addVerificationActions(frm);
	},
});

function setStatusHeadline(frm) {
	if (frm.is_new()) return;

	const businessStatus = frm.doc.business_status || __("Unknown");
	const integrityStatus = frm.doc.integrity_status || __("Unknown");
	const indicator = getBusinessIndicator(frm.doc.business_status);
	frm.dashboard.set_headline(
		__("Business: {0} | Integrity: {1}", [businessStatus, integrityStatus]),
		indicator
	);
}

function getBusinessIndicator(status) {
	if (["Active"].includes(status)) return "green";
	if (["Superseded", "Expired"].includes(status)) return "orange";
	if (["Cancelled", "Revoked"].includes(status)) return "red";
	return "gray";
}

function addVerificationActions(frm) {
	if (frm.is_new()) return;

	if (frm.doc.verification_url) {
		frm.add_custom_button(__("Copy Verification URL"), () => {
			frappe.utils.copy_to_clipboard(frm.doc.verification_url);
		});
	}

	if (frm.doc.verification_token) {
		frm.add_custom_button(__("Verify Token"), async () => {
			const result = await frappe.call({
				method: "crispy_print.api.v1.verify_issued_document_token",
				args: { verification_token: frm.doc.verification_token },
			});
			const message = result.message || {};
			frappe.msgprint({
				title: __("Verification Result"),
				message: __("{0}", [message.verification_status || "Unknown"]),
				indicator: getVerificationIndicator(message.verification_status),
			});
		});
	}
}

function getVerificationIndicator(status) {
	if (status === "Valid") return "green";
	if (status === "Superseded") return "orange";
	if (["Revoked", "Tampered", "Corrupted"].includes(status)) return "red";
	return "gray";
}
