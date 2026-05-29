// Copyright (c) 2026, Agathodaemon and contributors
// For license information, please see license.txt

frappe.ui.form.on("Crispy Document Code Profile", {
	onload(frm) {
		setupQueries(frm);
		syncProfileForm(frm);
	},

	refresh(frm) {
		setupQueries(frm);
		syncProfileForm(frm);
		addLinkedRecordButtons(frm);
		refreshCredentialStatus(frm);
	},

	company(frm) {
		setupQueries(frm);
		refreshCredentialStatus(frm);
	},

	environment(frm) {
		setupQueries(frm);
		refreshCredentialStatus(frm);
	},

	code_purpose(frm) {
		clearIrrelevantFields(frm);
		syncProfileForm(frm);
		setupQueries(frm);
		refreshCredentialStatus(frm);
	},

	regulatory_profile(frm) {
		setupQueries(frm);
		applyRegulatoryProfileDefaults(frm);
		refreshCredentialStatus(frm);
	},

	fiscal_credential(frm) {
		refreshCredentialStatus(frm);
	},

	content_source(frm) {
		clearIrrelevantFields(frm);
		syncProfileForm(frm);
	},

	code_format(frm) {
		clearIrrelevantFields(frm);
		syncProfileForm(frm);
	},

	requires_signature(frm) {
		clearIrrelevantFields(frm);
		syncProfileForm(frm);
		refreshCredentialStatus(frm);
	},

	include_hash(frm) {
		clearIrrelevantFields(frm);
		syncProfileForm(frm);
	},

	requires_verification_url(frm) {
		clearIrrelevantFields(frm);
		syncProfileForm(frm);
	},
});

function setupQueries(frm) {
	frm.set_query("regulatory_profile", () => ({
		filters: { enabled: 1 },
	}));

	frm.set_query("fiscal_credential", () => {
		const filters = { enabled: 1 };
		if (frm.doc.company) filters.company = frm.doc.company;
		if (frm.doc.environment) filters.environment = frm.doc.environment;
		if (frm.doc.regulatory_profile) filters.regulatory_profile = frm.doc.regulatory_profile;
		return { filters };
	});
}

function syncProfileForm(frm) {
	applySymbologyDefaults(frm);
	updateProfileIntro(frm);
}

function clearIrrelevantFields(frm) {
	frm.set_df_property(
		"regulatory_profile",
		"reqd",
		frm.doc.code_purpose === "Regulatory" ? 1 : 0
	);
	frm.set_df_property("fiscal_credential", "reqd", frm.doc.requires_signature ? 1 : 0);

	if (
		frm.doc.content_source !== "Payload Template" &&
		frm.doc.payload_template &&
		!isStaticText(frm)
	) {
		frm.set_value("payload_template", "");
	}

	if (frm.doc.content_source !== "Selected Fields" && frm.doc.selected_fields_json) {
		frm.set_value("selected_fields_json", null);
	}

	if (
		frm.doc.content_source !== "Verification URL" &&
		!frm.doc.requires_verification_url &&
		frm.doc.verification_url_template
	) {
		frm.set_value("verification_url_template", "");
	}

	if (!frm.doc.requires_signature) {
		if (frm.doc.signature_method) {
			frm.set_value("signature_method", "");
		}
	}

	if (!frm.doc.include_hash && frm.doc.hash_method) {
		frm.set_value("hash_method", "");
	}

	if (["Text", "URL"].includes(frm.doc.code_format || "")) {
		if (frm.doc.code_symbology) {
			frm.set_value("code_symbology", "");
		}
		if (frm.doc.error_correction) {
			frm.set_value("error_correction", "");
		}
	}
}

function applySymbologyDefaults(frm) {
	if (frm.doc.code_symbology) return;

	const defaults = {
		"QR Code": "QR Code",
		DataMatrix: "DataMatrix",
		Barcode: "Code 128",
	};
	const nextValue = defaults[frm.doc.code_format || ""];
	if (nextValue) {
		frm.set_value("code_symbology", nextValue);
	}
}

function applyRegulatoryProfileDefaults(frm) {
	if (!frm.doc.regulatory_profile) {
		return;
	}

	frappe.db
		.get_value("Crispy QR Regulatory Profile", frm.doc.regulatory_profile, [
			"payload_format",
			"output_encoding",
			"error_correction",
			"include_hash",
			"requires_online_verification",
			"verification_url_template",
			"encoder_key",
			"encoder_settings_json",
		])
		.then((response) => {
			const values = response.message || {};
			const updates = {};

			maybeApplyDefault(frm, updates, "payload_format", values.payload_format);
			maybeApplyDefault(frm, updates, "output_encoding", values.output_encoding);
			if ((frm.doc.code_format || "") === "QR Code") {
				maybeApplyDefault(frm, updates, "error_correction", values.error_correction);
			}
			if (!frm.doc.include_hash && values.include_hash) {
				updates.include_hash = values.include_hash;
			}
			if (!frm.doc.requires_verification_url && values.requires_online_verification) {
				updates.requires_verification_url = values.requires_online_verification;
			}
			if (
				!String(frm.doc.verification_url_template || "").trim() &&
				values.verification_url_template
			) {
				updates.verification_url_template = values.verification_url_template;
			}
			maybeApplyDefault(frm, updates, "encoder_key", values.encoder_key);
			maybeApplyDefault(frm, updates, "encoder_settings_json", values.encoder_settings_json);

			if (Object.keys(updates).length) {
				frm.set_value(updates);
			}
		});
}

function maybeApplyDefault(frm, updates, fieldname, nextValue) {
	if (nextValue === undefined || nextValue === null || nextValue === "") {
		return;
	}
	const currentValue = frm.doc[fieldname];
	const field = frm.get_field(fieldname);
	const defaultValue = field?.df?.default;
	if (
		currentValue === undefined ||
		currentValue === null ||
		currentValue === "" ||
		String(currentValue) === String(defaultValue || "")
	) {
		updates[fieldname] = nextValue;
	}
}

function addLinkedRecordButtons(frm) {
	if (frm.is_new()) return;

	if (frm.doc.regulatory_profile) {
		frm.add_custom_button(__("Regulatory Profile"), () => {
			frappe.set_route("Form", "Crispy QR Regulatory Profile", frm.doc.regulatory_profile);
		});
	}

	if (frm.doc.fiscal_credential) {
		frm.add_custom_button(__("Fiscal Credential"), () => {
			frappe.set_route("Form", "Crispy Fiscal Credential", frm.doc.fiscal_credential);
		});
	}

	frm.add_custom_button(__("Generated Profiles"), () => {
		frappe.set_route("List", "Crispy Document Code Profile", {
			company: frm.doc.company || undefined,
			environment: frm.doc.environment || undefined,
		});
	});
}

function refreshCredentialStatus(frm) {
	if (!frm.doc.company || !frm.doc.environment || !frm.doc.regulatory_profile) {
		updateProfileIntro(frm);
		return;
	}

	if (!frm.doc.requires_signature && frm.doc.fiscal_credential) {
		updateProfileIntro(frm, {
			message: __(
				"Linked fiscal credential is optional unless signature support is enabled."
			),
			indicator: "blue",
		});
		return;
	}

	const requestToken = [
		frm.doc.company,
		frm.doc.regulatory_profile,
		frm.doc.environment,
		frm.doc.fiscal_credential || "",
		frm.doc.requires_signature ? "1" : "0",
	].join("::");
	frm.__documentCodeCredentialStatusToken = requestToken;

	frappe.call({
		method: "crispy_print.api.v1.get_fiscal_credential_status",
		args: {
			company: frm.doc.company,
			regulatory_profile: frm.doc.regulatory_profile,
			environment: frm.doc.environment,
		},
		callback: (response) => {
			if (frm.__documentCodeCredentialStatusToken !== requestToken) {
				return;
			}
			const status = response?.message;
			if (!status) {
				updateProfileIntro(frm);
				return;
			}

			if (frm.doc.requires_signature && !status.valid) {
				updateProfileIntro(frm, {
					message:
						status.warnings?.[0] ||
						__("No active fiscal credential currently matches this profile context."),
					indicator: "orange",
				});
				return;
			}

			if (status.valid && status.credential?.name) {
				updateProfileIntro(frm, {
					message: __("Active fiscal credential available: {0}", [
						status.credential.name,
					]),
					indicator: "green",
				});
				return;
			}

			updateProfileIntro(frm);
		},
	});
}

function updateProfileIntro(frm, status) {
	const baseMessage = __(
		"This profile is resolved by the backend document-code generator for matching preview and print requests."
	);
	if (!status?.message) {
		frm.set_intro(baseMessage, "blue");
		return;
	}
	frm.set_intro(`${baseMessage} ${status.message}`, status.indicator || "blue");
}

function isStaticText(frm) {
	return (frm.doc.content_source || "") === "Static Text";
}
