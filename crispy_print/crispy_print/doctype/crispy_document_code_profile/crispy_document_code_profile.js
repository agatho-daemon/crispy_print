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
		addSelectedFieldsActions(frm);
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

frappe.ui.form.on("Crispy Document Code Field", {
	form_render(frm, cdt, cdn) {
		defaultSelectedFieldDoctype(frm, cdt, cdn);
		loadSelectedFieldOptions(frm, cdt, cdn);
	},

	source_doctype(frm, cdt, cdn) {
		loadSelectedFieldOptions(frm, cdt, cdn);
	},

	field_key(frm, cdt, cdn) {
		applySelectedFieldMetadata(frm, cdt, cdn);
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
	updateSelectedFieldsControls(frm);
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

	if (frm.doc.content_source !== "Selected Fields") {
		if (frm.doc.selected_fields?.length) {
			frm.clear_table("selected_fields");
			frm.refresh_field("selected_fields");
		}
		if (frm.doc.selected_fields_json) {
			frm.set_value("selected_fields_json", null);
		}
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

function addSelectedFieldsActions(frm) {
	if ((frm.doc.content_source || "") !== "Selected Fields") {
		return;
	}

	frm.add_custom_button(
		__("Business Field Set"),
		() => openBusinessFieldSetDialog(frm),
		__("Add Fields")
	);

	if (frm.doc.code_purpose === "Regulatory" && frm.doc.regulatory_profile) {
		frm.add_custom_button(
			__("Required Authority Fields"),
			() => addRequiredAuthorityFields(frm),
			__("Add Fields")
		);
	}
}

function updateSelectedFieldsControls(frm) {
	const isSelectedFields = (frm.doc.content_source || "") === "Selected Fields";
	frm.set_df_property("selected_fields", "hidden", isSelectedFields ? 0 : 1);
	frm.set_df_property(
		"selected_fields",
		"description",
		isSelectedFields
			? __(
					"Add rows from the backend QR field registry. Field metadata is filled automatically."
			  )
			: ""
	);
	frm.set_df_property("selected_fields_json", "hidden", 1);
	frm.set_df_property("selected_fields_json", "read_only", 1);
}

async function loadSelectedFieldOptions(frm, cdt, cdn) {
	const row = locals[cdt]?.[cdn];
	if (!row?.source_doctype) {
		return;
	}
	const authorityCode = await getAuthorityCode(frm);
	const registry = await getQrRegistryFields(frm, row.source_doctype, authorityCode);
	const options = (registry.fields || []).map((field) => field.key).join("\n");
	frappe.meta.get_docfield(cdt, "field_key", cdn).options = options;
	frm.fields_dict.selected_fields.grid.refresh();

	if (row.field_key) {
		applySelectedFieldMetadata(frm, cdt, cdn, registry);
	}
}

async function applySelectedFieldMetadata(frm, cdt, cdn, registry) {
	const row = locals[cdt]?.[cdn];
	if (!row?.source_doctype || !row?.field_key) {
		return;
	}
	registry =
		registry ||
		(await getQrRegistryFields(frm, row.source_doctype, await getAuthorityCode(frm)));
	const field = (registry.fields || []).find((item) => item.key === row.field_key);
	if (!field) {
		return;
	}
	await frappe.model.set_value(cdt, cdn, "label", field.label || "");
	await frappe.model.set_value(cdt, cdn, "source_path", field.path || "");
	await frappe.model.set_value(cdt, cdn, "source", field.source || "");
	await frappe.model.set_value(cdt, cdn, "datatype", field.datatype || "");
	await frappe.model.set_value(cdt, cdn, "purpose", field.purpose || "");
}

function getTargetDoctypes(frm) {
	const values = (frm.doc.document_rules || [])
		.map((row) => String(row.document_type || "").trim())
		.filter(Boolean);
	return [...new Set(values)].sort();
}

function defaultSelectedFieldDoctype(frm, cdt, cdn) {
	const row = locals[cdt]?.[cdn];
	if (!row || row.source_doctype) {
		return;
	}
	const doctypes = getTargetDoctypes(frm);
	if (doctypes.length === 1) {
		frappe.model.set_value(cdt, cdn, "source_doctype", doctypes[0]);
	}
}

async function getQrRegistryFields(frm, doctype, authorityCode, includeBusinessFields = false) {
	const cacheKey = [doctype, authorityCode || "", includeBusinessFields ? "business" : ""].join(
		"::"
	);
	frm.__qrRegistryFieldCache = frm.__qrRegistryFieldCache || {};
	if (frm.__qrRegistryFieldCache[cacheKey]) {
		return frm.__qrRegistryFieldCache[cacheKey];
	}
	const response = await frappe.call({
		method: "crispy_print.api.v1.get_qr_registry_fields",
		args: {
			doctype,
			authority_code: frm.doc.code_purpose === "Regulatory" ? authorityCode : null,
			include_business_fields: includeBusinessFields ? 1 : 0,
		},
	});
	frm.__qrRegistryFieldCache[cacheKey] = response.message || {};
	return frm.__qrRegistryFieldCache[cacheKey];
}

async function openBusinessFieldSetDialog(frm) {
	const doctypes = getTargetDoctypes(frm);
	if (!doctypes.length) {
		frappe.msgprint({
			title: __("Document Rule Required"),
			indicator: "orange",
			message: __("Add a Document Rule first so Crispy Print knows which registry to load."),
		});
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Add Business Field Set"),
		fields: [
			{
				fieldname: "source_doctype",
				fieldtype: "Select",
				label: __("Source DocType"),
				options: doctypes.join("\n"),
				default: doctypes[0],
				reqd: 1,
				onchange: () => loadBusinessFieldSetOptions(frm, dialog),
			},
			{
				fieldname: "business_field_set",
				fieldtype: "Select",
				label: __("Business Field Set"),
				reqd: 1,
			},
		],
		primary_action_label: __("Add Fields"),
		primary_action: async () => {
			const values = dialog.get_values();
			if (!values) return;
			const registry = await getQrRegistryFields(frm, values.source_doctype, null, true);
			const fieldSet = (registry.business_field_sets || []).find(
				(item) => item.key === values.business_field_set
			);
			if (!fieldSet) {
				frappe.msgprint(__("Selected business field set is no longer available."));
				return;
			}
			await addRegistryFields(frm, values.source_doctype, fieldSet.fields || []);
			dialog.hide();
		},
	});

	dialog.show();
	loadBusinessFieldSetOptions(frm, dialog);
}

async function loadBusinessFieldSetOptions(frm, dialog) {
	const sourceDoctype = dialog.get_value("source_doctype");
	if (!sourceDoctype) return;
	const registry = await getQrRegistryFields(frm, sourceDoctype, null, true);
	const options = (registry.business_field_sets || [])
		.map((fieldSet) => fieldSet.key)
		.join("\n");
	dialog.fields_dict.business_field_set.df.options = options;
	dialog.fields_dict.business_field_set.refresh();
	if (options && !dialog.get_value("business_field_set")) {
		dialog.set_value("business_field_set", options.split("\n")[0]);
	}
}

async function addRequiredAuthorityFields(frm) {
	const doctypes = getTargetDoctypes(frm);
	if (!doctypes.length) {
		frappe.msgprint({
			title: __("Document Rule Required"),
			indicator: "orange",
			message: __("Add a Document Rule first so Crispy Print knows which registry to load."),
		});
		return;
	}
	const authorityCode = await getAuthorityCode(frm);
	let added = 0;
	for (const doctype of doctypes) {
		const registry = await getQrRegistryFields(frm, doctype, authorityCode);
		const required = (registry.fields || [])
			.filter((field) => field.required)
			.map((field) => field.key);
		added += await addRegistryFields(frm, doctype, required);
	}
	if (!added) {
		frappe.show_alert({
			message: __("No new required authority fields to add."),
			indicator: "blue",
		});
	}
}

async function addRegistryFields(frm, sourceDoctype, fieldKeys) {
	let added = 0;
	const existing = new Set(
		(frm.doc.selected_fields || []).map((row) => `${row.source_doctype}::${row.field_key}`)
	);
	for (const fieldKey of fieldKeys) {
		const cacheKey = `${sourceDoctype}::${fieldKey}`;
		if (existing.has(cacheKey)) {
			continue;
		}
		const row = frm.add_child("selected_fields");
		row.source_doctype = sourceDoctype;
		row.field_key = fieldKey;
		existing.add(cacheKey);
		added += 1;
		await applySelectedFieldMetadata(frm, row.doctype, row.name);
	}
	frm.refresh_field("selected_fields");
	if (added) {
		frappe.show_alert({ message: __("Added {0} QR fields.", [added]), indicator: "green" });
	}
	return added;
}

async function getAuthorityCode(frm) {
	if (frm.doc.code_purpose !== "Regulatory" || !frm.doc.regulatory_profile) {
		return null;
	}
	const response = await frappe.db.get_value(
		"Crispy QR Regulatory Profile",
		frm.doc.regulatory_profile,
		"authority_code"
	);
	return response?.message?.authority_code || null;
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
