// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Issued Document", {
	refresh(frm) {
		lockIssuedDocumentForm(frm);
		setStatusHeadline(frm);
		addVerificationActions(frm);
		addPdfActions(frm);
		addLifecycleActions(frm);
	},
});

const READ_ONLY_FIELDS = [
	"document_uuid",
	"verification_token",
	"source_doctype",
	"source_docname",
	"company",
	"crispy_format",
	"issuance_status",
	"business_status",
	"integrity_status",
	"issued_at",
	"revoked",
	"revoked_at",
	"superseded_by",
	"amended_from",
	"canonical_payload_json",
	"canonical_payload_hash",
	"typst_source",
	"typst_source_hash",
	"typst_version",
	"artifacts",
	"trust_events",
	"regulatory_submissions",
	"verification_url",
];

function lockIssuedDocumentForm(frm) {
	READ_ONLY_FIELDS.forEach((fieldname) => {
		frm.set_df_property(fieldname, "read_only", 1);
	});
	if (!frm.is_new()) {
		frm.disable_save();
	}
}

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

function addPdfActions(frm) {
	if (frm.is_new() || !frm.doc.typst_source) return;

	frm.add_custom_button(
		__("View PDF"),
		async () => {
			const pdf = await fetchIssuedDocumentPdf(frm);
			openPdf(pdf);
		},
		__("PDF")
	);
	frm.add_custom_button(
		__("Download PDF"),
		async () => {
			const pdf = await fetchIssuedDocumentPdf(frm);
			downloadPdf(pdf);
		},
		__("PDF")
	);
	frm.add_custom_button(
		__("Print PDF"),
		async () => {
			const pdf = await fetchIssuedDocumentPdf(frm);
			printPdf(pdf);
		},
		__("PDF")
	);
}

function addLifecycleActions(frm) {
	if (frm.is_new()) return;

	if (!["Cancelled", "Revoked", "Superseded"].includes(frm.doc.business_status)) {
		frm.add_custom_button(
			__("Cancel"),
			() => {
				promptReasonAndCall(frm, {
					title: __("Cancel Issued Document"),
					method: "crispy_print.api.v1.cancel_issued_document",
					primary_action_label: __("Cancel"),
				});
			},
			__("Actions")
		);

		frm.add_custom_button(
			__("Revoke"),
			() => {
				promptReasonAndCall(frm, {
					title: __("Revoke Issued Document"),
					method: "crispy_print.api.v1.revoke_issued_document",
					primary_action_label: __("Revoke"),
				});
			},
			__("Actions")
		);

		frm.add_custom_button(
			__("Supersede"),
			() => {
				promptSupersedeAndCall(frm);
			},
			__("Actions")
		);
	}

	frm.add_custom_button(
		__("Record Integrity Check"),
		() => {
			promptIntegrityCheckAndCall(frm);
		},
		__("Actions")
	);
}

function promptReasonAndCall(frm, options) {
	frappe.prompt(
		[
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("Reason"),
				reqd: 1,
			},
		],
		async (values) => {
			await callCidAction(frm, options.method, { reason: values.reason });
		},
		options.title,
		options.primary_action_label
	);
}

function promptSupersedeAndCall(frm) {
	frappe.prompt(
		[
			{
				fieldname: "superseded_by",
				fieldtype: "Link",
				label: __("Superseded By"),
				options: "Crispy Issued Document",
				reqd: 1,
				get_query() {
					return {
						filters: {
							name: ["!=", frm.doc.name],
							company: frm.doc.company,
						},
					};
				},
			},
			{
				fieldname: "reason",
				fieldtype: "Small Text",
				label: __("Reason"),
				reqd: 1,
			},
		],
		async (values) => {
			await callCidAction(frm, "crispy_print.api.v1.supersede_issued_document", {
				superseded_by: values.superseded_by,
				reason: values.reason,
			});
		},
		__("Supersede Issued Document"),
		__("Supersede")
	);
}

function promptIntegrityCheckAndCall(frm) {
	frappe.prompt(
		[
			{
				fieldname: "integrity_status",
				fieldtype: "Select",
				label: __("Integrity Status"),
				options: "Pending\nValid\nTampered\nCorrupted\nUnknown",
				reqd: 1,
			},
			{
				fieldname: "message",
				fieldtype: "Small Text",
				label: __("Message"),
			},
		],
		async (values) => {
			await callCidAction(
				frm,
				"crispy_print.api.v1.record_issued_document_integrity_check",
				{
					integrity_status: values.integrity_status,
					message: values.message,
				}
			);
		},
		__("Record Integrity Check"),
		__("Record")
	);
}

async function fetchIssuedDocumentPdf(frm) {
	const result = await frappe.call({
		method: "crispy_print.api.v1.render_issued_document_pdf",
		args: { name: frm.doc.name },
		freeze: true,
		freeze_message: __("Compiling issued PDF..."),
	});
	const pdf = result.message || {};
	if (!pdf.pdf_data) {
		frappe.throw(__("Issued PDF could not be generated."));
	}
	return pdf;
}

function pdfBlobUrl(pdf) {
	const binary = atob(pdf.pdf_data);
	const bytes = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i += 1) {
		bytes[i] = binary.charCodeAt(i);
	}
	const blob = new Blob([bytes], { type: "application/pdf" });
	return URL.createObjectURL(blob);
}

function openPdf(pdf) {
	const url = pdfBlobUrl(pdf);
	window.open(url, "_blank", "noopener,noreferrer");
	setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

function downloadPdf(pdf) {
	const url = pdfBlobUrl(pdf);
	const link = document.createElement("a");
	link.href = url;
	link.download = pdf.filename || `${pdf.name || "crispy-issued-document"}.pdf`;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	setTimeout(() => URL.revokeObjectURL(url), 5_000);
}

function printPdf(pdf) {
	const url = pdfBlobUrl(pdf);
	const iframe = document.createElement("iframe");
	iframe.style.position = "fixed";
	iframe.style.right = "0";
	iframe.style.bottom = "0";
	iframe.style.width = "0";
	iframe.style.height = "0";
	iframe.style.border = "0";
	iframe.src = url;
	iframe.onload = () => {
		iframe.contentWindow?.focus();
		iframe.contentWindow?.print();
		setTimeout(() => {
			iframe.remove();
			URL.revokeObjectURL(url);
		}, 60_000);
	};
	document.body.appendChild(iframe);
}

async function callCidAction(frm, method, args) {
	await frappe.call({
		method,
		args: {
			name: frm.doc.name,
			...args,
		},
	});
	await frm.reload_doc();
}

function getVerificationIndicator(status) {
	if (status === "Valid") return "green";
	if (status === "Superseded") return "orange";
	if (["Revoked", "Tampered", "Corrupted"].includes(status)) return "red";
	return "gray";
}
