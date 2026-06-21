<template>
	<div class="cbp-builder">
		<aside class="cbp-builder__controls">
			<div class="cbp-builder__controls-header">
				<div>
					<div class="cbp-builder__eyebrow">{{ __("Crispy Branding Profile") }}</div>
					<h2>{{ model.profile_name || profileName }}</h2>
				</div>
				<span v-if="dirty" class="cbp-builder__dirty">{{ __("Unsaved") }}</span>
			</div>

			<section class="cbp-panel">
				<h3>{{ __("General") }}</h3>
				<div class="cbp-grid">
					<label>
						<span>{{ __("Profile Name") }}</span>
						<input v-model="model.profile_name" class="form-control" type="text" />
					</label>
					<label>
						<span>{{ __("Company") }}</span>
						<select v-model="model.company" class="form-control">
							<option
								v-for="company in companies"
								:key="company.name"
								:value="company.name"
							>
								{{ company.name }}
							</option>
						</select>
					</label>
					<label class="cbp-check">
						<input v-model="isDefault" type="checkbox" />
						<span>{{ __("Default for company") }}</span>
					</label>
					<label v-if="showCodeMode" class="cbp-check">
						<input v-model="codeOnly" type="checkbox" />
						<span>{{ __("Code only") }}</span>
					</label>
				</div>
			</section>

			<section v-if="showCodeMode && codeOnly" class="cbp-panel">
				<h3>{{ __("Custom Typst Code") }}</h3>
				<div class="cbp-code-panel">
					<textarea
						v-model="model.custom_typst_code"
						class="form-control cbp-code-editor"
						spellcheck="false"
					></textarea>
					<div class="cbp-code-panel__hint">
						{{ __("Press Ctrl+Enter or Cmd+Enter to refresh the preview.") }}
					</div>
				</div>
			</section>

			<section v-if="!effectiveCodeOnly" class="cbp-panel">
				<h3>{{ __("Page") }}</h3>
				<div class="cbp-grid cbp-grid--two">
					<label>
						<span>{{ __("Size") }}</span>
						<select v-model="model.page_size" class="form-control">
							<option v-for="size in pageSizes" :key="size" :value="size">
								{{ size }}
							</option>
						</select>
					</label>
					<label>
						<span>{{ __("Orientation") }}</span>
						<select v-model="model.orientation" class="form-control">
							<option value="portrait">{{ __("Portrait") }}</option>
							<option value="landscape">{{ __("Landscape") }}</option>
						</select>
					</label>
				</div>
				<div class="cbp-grid cbp-grid--four">
					<number-field v-model="model.margin_top_mm" :label="__('Top')" />
					<number-field v-model="model.margin_bottom_mm" :label="__('Bottom')" />
					<number-field v-model="model.margin_left_mm" :label="__('Left')" />
					<number-field v-model="model.margin_right_mm" :label="__('Right')" />
				</div>
			</section>

			<section v-if="!effectiveCodeOnly" class="cbp-panel">
				<h3>{{ __("Typography") }}</h3>
				<typography-editor
					v-model="sectionLabelTypography"
					:title="__('Section Label')"
					variant="cbp"
					option-value-format="label"
				/>
				<typography-editor
					v-model="fieldLabelTypography"
					:title="__('Field Label')"
					variant="cbp"
					option-value-format="label"
				/>
				<typography-editor
					v-model="fieldValueTypography"
					:title="__('Field Value')"
					variant="cbp"
					option-value-format="label"
				/>
			</section>

			<section v-if="!effectiveCodeOnly" class="cbp-panel">
				<h3>{{ __("Table") }}</h3>
				<div class="cbp-section-heading">{{ __("Cell inset") }}</div>
				<div class="cbp-grid cbp-grid--four">
					<number-field v-model="model.table_cell_inset_top_pt" :label="__('Top')" />
					<number-field v-model="model.table_cell_inset_right_pt" :label="__('Right')" />
					<number-field
						v-model="model.table_cell_inset_bottom_pt"
						:label="__('Bottom')"
					/>
					<number-field v-model="model.table_cell_inset_left_pt" :label="__('Left')" />
				</div>
				<div class="cbp-grid cbp-grid--two">
					<number-field
						v-model="model.table_border_stroke_width_pt"
						:label="__('Border')"
					/>
					<color-field v-model="model.table_border_color" :label="__('Border Color')" />
					<color-field
						v-model="model.table_header_background_color"
						:label="__('Header Fill')"
					/>
				</div>
				<label class="cbp-check">
					<input v-model="tableStriping" type="checkbox" />
					<span>{{ __("Stripe alternating rows") }}</span>
				</label>
				<div v-if="tableStriping" class="cbp-grid cbp-grid--two">
					<color-field v-model="model.table_stripe_color" :label="__('Stripe Fill')" />
				</div>
				<typography-editor
					v-model="tableHeaderTypography"
					:title="__('Table Header')"
					variant="cbp"
					option-value-format="label"
				/>
				<typography-editor
					v-model="tableBodyTypography"
					:title="__('Table Body')"
					variant="cbp"
					option-value-format="label"
				/>
			</section>

			<section v-if="!effectiveCodeOnly" class="cbp-panel">
				<h3>{{ __("Branding") }}</h3>
				<div class="cbp-grid">
					<label>
						<span>{{ __("Mode") }}</span>
						<select v-model="model.branding_mode" class="form-control">
							<option value="None">{{ __("None") }}</option>
							<option value="Logo Only">{{ __("Logo Only") }}</option>
							<option value="Letterhead Only">{{ __("Letterhead Only") }}</option>
							<option value="Logo + Letterhead">
								{{ __("Logo + Letterhead") }}
							</option>
						</select>
					</label>
				</div>

				<div v-if="usesLogo" class="cbp-nested">
					<div class="cbp-grid cbp-grid--two">
						<label>
							<span>{{ __("Logo Source") }}</span>
							<select v-model="model.branding_logo_source" class="form-control">
								<option value="Company logo">{{ __("Company logo") }}</option>
								<option value="Upload image">{{ __("Upload image") }}</option>
							</select>
						</label>
						<number-field
							v-model="model.branding_logo_width_mm"
							:label="__('Width')"
						/>
					</div>
					<div v-if="model.branding_logo_source === 'Upload image'" class="cbp-file-row">
						<input
							v-model="model.branding_logo_upload"
							class="form-control"
							type="text"
						/>
						<button
							class="btn btn-default btn-xs"
							type="button"
							@click="uploadImage('logo')"
						>
							{{ __("Upload") }}
						</button>
					</div>
					<div class="cbp-grid cbp-grid--two">
						<number-field
							v-model="model.branding_logo_offset_x_mm"
							:label="__('X')"
							:min="0"
						/>
						<number-field
							v-model="model.branding_logo_offset_y_mm"
							:label="__('Y')"
							:min="0"
						/>
					</div>
				</div>

				<div v-if="usesLetterhead" class="cbp-nested">
					<div class="cbp-grid cbp-grid--two">
						<label>
							<span>{{ __("Letterhead Source") }}</span>
							<select
								v-model="model.branding_letterhead_source"
								class="form-control"
							>
								<option value="Use System Letterhead">
									{{ __("Use System Letterhead") }}
								</option>
								<option value="Upload Letterhead">
									{{ __("Upload Letterhead") }}
								</option>
							</select>
						</label>
						<label v-if="model.branding_letterhead_source === 'Use System Letterhead'">
							<span>{{ __("Letterhead") }}</span>
							<select v-model="model.frappe_company_letterhead" class="form-control">
								<option value="">{{ __("Select") }}</option>
								<option
									v-for="letterhead in letterheads"
									:key="letterhead"
									:value="letterhead"
								>
									{{ letterhead }}
								</option>
							</select>
						</label>
						<div v-else class="cbp-file-row">
							<input
								v-model="model.branding_letterhead_upload"
								class="form-control"
								type="text"
							/>
							<button
								class="btn btn-default btn-xs"
								type="button"
								@click="uploadImage('letterhead')"
							>
								{{ __("Upload") }}
							</button>
						</div>
					</div>
				</div>
			</section>

			<section v-if="!effectiveCodeOnly" class="cbp-panel">
				<h3>{{ __("QR Code") }}</h3>
				<label class="cbp-check">
					<input v-model="qrEnabled" type="checkbox" />
					<span>{{ __("Enable QR code") }}</span>
				</label>
				<div class="cbp-grid cbp-grid--two">
					<label class="cbp-field">
						<span>{{ __("Symbology") }}</span>
						<select v-model="model.qr_symbology">
							<option value="QR Code">{{ __("QR Code") }}</option>
							<option value="DataMatrix">{{ __("DataMatrix") }}</option>
						</select>
					</label>
					<label v-if="model.qr_symbology !== 'DataMatrix'" class="cbp-field">
						<span>{{ __("Error correction") }}</span>
						<select v-model="model.qr_error_correction">
							<option value="Low">{{ __("Low") }}</option>
							<option value="Medium">{{ __("Medium") }}</option>
							<option value="Quartile">{{ __("Quartile") }}</option>
							<option value="High">{{ __("High") }}</option>
						</select>
					</label>
					<label v-if="model.qr_symbology === 'DataMatrix'" class="cbp-field">
						<span>{{ __("Encodation") }}</span>
						<select v-model="model.datamatrix_encodation">
							<option value="">{{ __("Auto") }}</option>
							<option value="ASCII">ASCII</option>
							<option value="C40">C40</option>
							<option value="Text">Text</option>
							<option value="X12">X12</option>
							<option value="EDIFACT">EDIFACT</option>
							<option value="Base256">Base256</option>
						</select>
					</label>
					<label v-if="model.qr_symbology === 'DataMatrix'" class="cbp-field">
						<span>{{ __("Symbols") }}</span>
						<select v-model="model.datamatrix_symbols">
							<option value="">{{ __("Square") }}</option>
							<option value="Rectangular">{{ __("Rectangular") }}</option>
							<option value="DMRE">DMRE</option>
						</select>
					</label>
				</div>
				<div class="cbp-grid cbp-grid--three">
					<number-field v-model="model.qr_code_size_mm" :label="__('Size')" />
					<number-field v-model="model.qr_quiet_zone" :label="__('Quiet')" :min="0" />
					<number-field
						v-model="model.qr_module_size_pt"
						:label="__('Module')"
						:min="0"
					/>
					<number-field v-model="model.qr_dx_mm" :label="__('X')" :min="0" />
					<number-field v-model="model.qr_dy_mm" :label="__('Y')" />
				</div>
			</section>
		</aside>

		<main class="cbp-builder__preview-wrap">
			<div class="cbp-preview-toolbar">
				<div>
					<strong>{{ __("Branding Profile Specimen") }}</strong>
					<span>{{ __("Live rendering of this CBP record") }}</span>
				</div>
				<div class="cbp-preview-toolbar__actions">
					<button
						class="btn btn-default btn-xs"
						type="button"
						:disabled="codePreviewStatus === 'compiling'"
						:title="__('Refresh preview') + ' (Ctrl/Cmd+Enter)'"
						@click="refreshCodePreview"
					>
						{{ __("Refresh") }}
					</button>
					<button
						class="btn btn-default btn-xs"
						type="button"
						@click="resetPreviewDefaults"
					>
						{{ __("Reset View Defaults") }}
					</button>
				</div>
			</div>

			<div class="cbp-preview-scroll">
				<div v-if="codePreviewStatus !== 'ready'" class="cbp-preview-status-panel">
					<div class="cbp-preview-status-panel__body" :class="`is-${codePreviewStatus}`">
						<div class="cbp-builder__eyebrow">
							{{ previewModeLabel }}
						</div>
						<strong>{{ codePreviewTitle }}</strong>
						<p>{{ codePreviewMessage }}</p>
					</div>
				</div>
				<article
					class="cbp-specimen-page cbp-code-preview"
					:class="{ 'is-ready': codePreviewPages.length }"
					:style="codePreviewPages.length ? undefined : pageStyle"
				>
					<div class="cbp-code-preview__body">
						<div
							v-for="(svg, index) in codePreviewPages"
							:key="index"
							class="cbp-typst-page"
							v-html="sanitizeSvg(svg)"
						></div>
					</div>
				</article>
			</div>
		</main>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
	compileTypst,
	getBrandingProfile,
	getCompanies,
	getLetterheadDoc,
	getLetterheads,
	saveBrandingProfile,
	type CompanyOption,
	type CrispyBrandingProfileDoc,
} from "../api/crispy";
import TypographyEditor from "../components/TypographyStyleEditor.vue";
import { __ } from "../utils/i18n";
import { sanitizeSvg } from "../utils/safeSvg";
import { cbpTypographyModel } from "./cbpTypographyAdapter";
import {
	createFallbackModel,
	defaultCodeOnlyTypst,
	pageDimensions,
	pageSizes,
	showCodeMode,
} from "./cbpBuilderSupport";
import {
	buildCodePreviewTypst as renderCodePreviewTypst,
	buildVisualPreviewTypst as renderVisualPreviewTypst,
	type CbpPreviewTypstContext,
} from "./cbpBuilderTypst";
import ColorField from "./cbpFields/ColorField";
import NumberField from "./cbpFields/NumberField";

const props = defineProps<{ profileName: string }>();
const emit = defineEmits<{ (event: "dirty", value: boolean): void }>();

const fallbackModel = createFallbackModel(props.profileName);
const codeReferenceComment = defaultCodeOnlyTypst.split("*/")[0] + "*/";
const model = reactive<CrispyBrandingProfileDoc>({ ...fallbackModel });
const companies = ref<CompanyOption[]>([]);
const letterheads = ref<string[]>([]);
const selectedLetterheadImage = ref("");
const initialSnapshot = ref("");
const saving = ref(false);
const codePreviewStatus = ref<"idle" | "compiling" | "ready" | "error">("idle");
const codePreviewPages = ref<string[]>([]);
const codePreviewError = ref("");
let codePreviewTimer: ReturnType<typeof setTimeout> | null = null;
let codePreviewSeq = 0;

const isDefault = computed({
	get: () => Boolean(Number(model.is_default || 0)),
	set: (value: boolean) => (model.is_default = value ? 1 : 0),
});
const codeOnly = computed({
	get: () => Boolean(Number(model.code_only || 0)),
	set: (value: boolean) => {
		model.code_only = value ? 1 : 0;
		if (value) {
			model.custom_typst_code = ensureCodeReference(model.custom_typst_code || "");
		}
	},
});
const effectiveCodeOnly = computed(() => showCodeMode && codeOnly.value);
const tableStriping = computed({
	get: () => Boolean(Number(model.table_row_striping || 0)),
	set: (value: boolean) => (model.table_row_striping = value ? 1 : 0),
});
const sectionLabelTypography = cbpTypographyModel(model, "section_label");
const fieldLabelTypography = cbpTypographyModel(model, "field_label");
const fieldValueTypography = cbpTypographyModel(model, "field_value");
const tableHeaderTypography = cbpTypographyModel(model, "table_header");
const tableBodyTypography = cbpTypographyModel(model, "table_body");
const qrEnabled = computed({
	get: () => Boolean(Number(model.enable_qr_code || 0)),
	set: (value: boolean) => (model.enable_qr_code = value ? 1 : 0),
});

const usesLogo = computed(() =>
	["Logo Only", "Logo + Letterhead"].includes(model.branding_mode || "")
);
const usesLetterhead = computed(() =>
	["Letterhead Only", "Logo + Letterhead"].includes(model.branding_mode || "")
);
const dirty = computed(() => JSON.stringify(savableModel()) !== initialSnapshot.value);

watch(dirty, (value) => emit("dirty", value), { immediate: true });
watch(
	() => model.frappe_company_letterhead,
	async (name) => {
		selectedLetterheadImage.value = "";
		if (!name) return;
		try {
			const doc = await getLetterheadDoc(name);
			selectedLetterheadImage.value = doc?.image || "";
		} catch {
			selectedLetterheadImage.value = "";
		}
	}
);
watch(
	() => model.company,
	() => {
		refreshLetterheadOptions();
	}
);
watch(
	() => [model.branding_mode, model.branding_logo_source, model.branding_letterhead_source],
	() => {
		if (
			usesLogo.value &&
			!["Company logo", "Upload image"].includes(model.branding_logo_source || "")
		) {
			model.branding_logo_source = "Company logo";
		}
		if (
			usesLetterhead.value &&
			!["Use System Letterhead", "Upload Letterhead"].includes(
				model.branding_letterhead_source || ""
			)
		) {
			model.branding_letterhead_source = "Use System Letterhead";
		}
		if (!usesLogo.value) model.branding_logo_upload = "";
		if (!usesLetterhead.value) {
			model.frappe_company_letterhead = "";
			model.branding_letterhead_upload = "";
		}
		if (model.branding_logo_source === "Company logo") model.branding_logo_upload = "";
		if (model.branding_letterhead_source === "Use System Letterhead")
			model.branding_letterhead_upload = "";
		if (model.branding_letterhead_source === "Upload Letterhead")
			model.frappe_company_letterhead = "";
	}
);

const currentCompany = computed(() =>
	companies.value.find((company) => company.name === model.company)
);
const logoImage = computed(() => {
	if (model.branding_logo_source === "Upload image") return model.branding_logo_upload || "";
	return currentCompany.value?.company_logo || "";
});
const letterheadImage = computed(() => {
	if (!usesLetterhead.value) return "";
	if (model.branding_letterhead_source === "Upload Letterhead") {
		return model.branding_letterhead_upload || "";
	}
	return selectedLetterheadImage.value || "";
});
const letterheadLabel = computed(() => {
	if (!usesLetterhead.value) return __("Not used");
	if (model.branding_letterhead_source === "Upload Letterhead") {
		return model.branding_letterhead_upload || __("No upload selected");
	}
	return model.frappe_company_letterhead || __("No letterhead selected");
});
const letterheadSourceLabel = computed(() =>
	model.branding_letterhead_source === "Use System Letterhead"
		? __("Use System Letterhead")
		: model.branding_letterhead_source || "Upload Letterhead"
);

const pageStyle = computed(() => {
	const size = pageDimensions(model.page_size || "A4", model.orientation || "portrait");
	return {
		width: `${size.width}mm`,
		minHeight: `${size.height}mm`,
	};
});
const codePreviewTitle = computed(() => {
	if (codePreviewStatus.value === "compiling") return __("Compiling preview");
	if (codePreviewStatus.value === "error") return __("Typst Error");
	return effectiveCodeOnly.value ? __("Code-only profile") : __("Branding Profile Specimen");
});
const codePreviewMessage = computed(() => {
	if (codePreviewStatus.value === "compiling")
		return effectiveCodeOnly.value
			? __("Rendering custom Typst with branding profile specimen data.")
			: __("Rendering branding profile settings through Typst.");
	if (codePreviewStatus.value === "error")
		return codePreviewError.value || __("Typst compilation failed.");
	return effectiveCodeOnly.value
		? __("Add Typst code on the left to render a live preview.")
		: __("Waiting for branding profile settings.");
});
const previewModeLabel = computed(() =>
	effectiveCodeOnly.value ? __("Code-only Typst preview") : __("Typst specimen preview")
);

watch(
	() =>
		JSON.stringify({
			codeOnly: effectiveCodeOnly.value,
			settings: previewTriggerModel(),
			logo: logoImage.value,
			letterhead: letterheadImage.value,
		}),
	() => scheduleCodePreview(),
	{ immediate: true }
);

function savableModel() {
	const { name, modified, ...values } = model as any;
	void name;
	void modified;
	return values;
}

function previewTriggerModel() {
	const values = savableModel() as Record<string, any>;
	if (!effectiveCodeOnly.value) return values;
	const { custom_typst_code, ...withoutCode } = values;
	void custom_typst_code;
	return withoutCode;
}

function ensureCodeReference(source: string) {
	const code = String(source || "").trim();
	if (!code) return defaultCodeOnlyTypst;
	if (
		code.includes("CBP code-only template for the Branding Profile Specimen preview") ||
		code.includes("CBP code-only template for the dummy e-invoice preview") ||
		code.includes("CBP dummy e-invoice data available in code-only preview")
	) {
		return source;
	}
	return `${codeReferenceComment}\n\n${source}`;
}

function scheduleCodePreview() {
	if (codePreviewTimer) clearTimeout(codePreviewTimer);
	codePreviewTimer = setTimeout(() => {
		void compileCodePreview();
	}, 450);
}

function refreshCodePreview() {
	if (codePreviewTimer) {
		clearTimeout(codePreviewTimer);
		codePreviewTimer = null;
	}
	void compileCodePreview();
}

async function compileCodePreview() {
	const source = effectiveCodeOnly.value
		? String(model.custom_typst_code || "").trim()
		: renderVisualPreviewTypst(previewTypstContext());
	if (!source) {
		codePreviewStatus.value = "idle";
		codePreviewPages.value = [];
		codePreviewError.value = "";
		return;
	}

	const seq = ++codePreviewSeq;
	codePreviewStatus.value = "compiling";
	codePreviewError.value = "";
	try {
		const result = await compileTypst({
			typst_source: effectiveCodeOnly.value
				? renderCodePreviewTypst(source, previewTypstContext())
				: source,
			output_format: "svg",
			asset_files: getCodePreviewAssetFiles(),
		});
		if (seq !== codePreviewSeq) return;
		codePreviewPages.value = result.svg_pages || [];
		codePreviewStatus.value = codePreviewPages.value.length ? "ready" : "error";
		if (!codePreviewPages.value.length) {
			codePreviewError.value = __("Typst compilation returned no SVG pages.");
		}
	} catch (error: any) {
		if (seq !== codePreviewSeq) return;
		codePreviewStatus.value = "error";
		codePreviewError.value =
			error?.message || String(error || __("Typst compilation failed."));
	}
}

function handlePreviewShortcut(event: KeyboardEvent) {
	if (!(event.ctrlKey || event.metaKey) || event.altKey || event.shiftKey) return;
	if (event.key !== "Enter") return;
	event.preventDefault();
	refreshCodePreview();
}

function previewTypstContext(): CbpPreviewTypstContext {
	return {
		model,
		profileName: props.profileName,
		isDefault: isDefault.value,
		effectiveCodeOnly: effectiveCodeOnly.value,
		tableStriping: tableStriping.value,
		qrEnabled: qrEnabled.value,
		usesLogo: usesLogo.value,
		logoImage: logoImage.value,
		letterheadImage: letterheadImage.value,
		letterheadLabel: letterheadLabel.value,
		letterheadSourceLabel: letterheadSourceLabel.value,
	};
}

function getCodePreviewAssetFiles() {
	const assets = [logoImage.value, letterheadImage.value].filter(Boolean);
	return Array.from(new Set(assets));
}

async function save() {
	if (saving.value) return;
	saving.value = true;
	try {
		await saveBrandingProfile(props.profileName, savableModel());
		initialSnapshot.value = JSON.stringify(savableModel());
		frappe?.show_alert?.({ message: __("Branding Profile saved"), indicator: "green" });
	} finally {
		saving.value = false;
	}
}

function uploadImage(target: "logo" | "letterhead") {
	const uploader = new frappe.ui.FileUploader({
		allow_multiple: false,
		restrictions: { allowed_file_types: ["image/*"] },
		on_success(file: any) {
			if (target === "logo") {
				model.branding_logo_upload = file.file_url;
			} else {
				model.branding_letterhead_upload = file.file_url;
			}
		},
	});
	uploader.show?.();
}

function resetPreviewDefaults() {
	model.page_size = "A4";
	model.orientation = "portrait";
	model.margin_top_mm = 20;
	model.margin_bottom_mm = 20;
	model.margin_left_mm = 20;
	model.margin_right_mm = 20;
}

async function load() {
	const doc = await getBrandingProfile(props.profileName);
	Object.assign(model, fallbackModel, doc);
	if (Number(model.code_only || 0)) {
		model.custom_typst_code = ensureCodeReference(model.custom_typst_code || "");
	}
	companies.value = await getCompanies({ include_current: model.company || null });
	if (!model.company && companies.value.length) {
		model.company = companies.value[0].name;
	}
	await refreshLetterheadOptions();
	await nextTick();
	initialSnapshot.value = JSON.stringify(savableModel());
}

async function refreshLetterheadOptions() {
	letterheads.value = await getLetterheads({
		company: model.company || null,
		include_current: model.frappe_company_letterhead || null,
	});
}

onMounted(() => {
	window.addEventListener("keydown", handlePreviewShortcut);
	void load();
});
onBeforeUnmount(() => {
	window.removeEventListener("keydown", handlePreviewShortcut);
	if (codePreviewTimer) {
		clearTimeout(codePreviewTimer);
		codePreviewTimer = null;
	}
});
defineExpose({ save, dirty });
</script>

<style scoped>
:global(.cbp-builder-page .layout-main-section-wrapper) {
	overflow: hidden;
}

:global(.cbp-builder-host) {
	height: calc(100vh - 118px);
	min-height: 0;
	overflow: hidden;
}

:global(.cbp-builder-host #cbp-builder-root) {
	height: 100%;
	min-height: 0;
	overflow: hidden;
}

.cbp-builder {
	display: grid;
	grid-template-columns: minmax(500px, 560px) minmax(0, 1fr);
	height: 100%;
	min-height: 0;
	overflow: hidden;
	background: #f8fafc;
	color: #111827;
}

.cbp-builder__controls {
	overflow: auto;
	min-height: 0;
	overscroll-behavior: contain;
	border-right: 1px solid #dfe3e8;
	background: #fff;
	padding: 16px;
}

.cbp-builder__controls-header,
.cbp-preview-toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	margin-bottom: 12px;
}

.cbp-builder__controls-header h2 {
	margin: 2px 0 0;
	font-size: 18px;
	font-weight: 700;
}

.cbp-builder__eyebrow,
.cbp-preview-toolbar span,
.cbp-subtitle {
	font-size: 11px;
	color: #64748b;
}

.cbp-builder__dirty {
	border: 1px solid #fed7aa;
	background: #fff7ed;
	color: #9a3412;
	border-radius: 999px;
	padding: 2px 8px;
	font-size: 11px;
}

.cbp-panel {
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	overflow: hidden;
	background: #fff;
	padding: 0;
	margin: 0 0 16px;
}

.cbp-panel h3 {
	margin: 0;
	padding: 10px 12px;
	border-bottom: 1px solid #e2e8f0;
	background: #fff;
	color: #334155;
	font-size: 13px;
	font-weight: 600;
}

.cbp-section-heading {
	padding: 12px 12px 0;
	color: #111827;
	font-size: 13px;
	font-weight: 700;
}

.cbp-grid {
	display: grid;
	grid-template-columns: 1fr;
	gap: 8px 16px;
	padding: 12px;
}

.cbp-grid--two {
	grid-template-columns: repeat(2, minmax(0, 1fr));
}

.cbp-grid--three {
	grid-template-columns: repeat(3, minmax(0, 1fr));
}

.cbp-grid--four {
	grid-template-columns: repeat(2, minmax(0, 1fr));
}

@media (max-width: 1300px) {
	.cbp-builder {
		grid-template-columns: minmax(460px, 520px) minmax(0, 1fr);
	}

	.cbp-grid--four {
		grid-template-columns: repeat(2, minmax(0, 1fr));
	}
}

label,
.cbp-field {
	min-width: 0;
}

label span,
.cbp-field span {
	display: block;
	margin-bottom: 4px;
	font-size: 11px;
	font-weight: 500;
	color: #475569;
}

.cbp-check {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 12px;
}

.cbp-check span {
	margin: 0;
}

.cbp-nested {
	margin: 0 12px 12px;
	padding-top: 12px;
	border-top: 1px solid #edf2f7;
}

.cbp-file-row,
.cbp-color-input {
	display: grid;
	grid-template-columns: minmax(0, 1fr) auto;
	gap: 8px;
	align-items: center;
	margin: 0;
}

.cbp-code-panel {
	padding: 12px;
}

.cbp-code-editor {
	min-height: 360px;
	font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
	font-size: 12px;
	line-height: 1.5;
	resize: vertical;
}

.cbp-code-panel__hint {
	margin-top: 8px;
	font-size: 12px;
	color: #64748b;
}

.cbp-color-input {
	grid-template-columns: 36px minmax(0, 1fr);
	margin: 0;
}

.cbp-color-input input[type="color"] {
	width: 36px;
	height: 36px;
	padding: 0;
	border: 0;
	border-radius: 8px;
	background: transparent;
	box-shadow: none;
	overflow: hidden;
	appearance: none;
	-webkit-appearance: none;
}

.cbp-builder :deep(.form-control) {
	width: 100%;
	min-width: 0;
	min-height: 32px;
	border-radius: 8px;
	padding: 6px 10px;
	font-size: 13px;
	line-height: 1.4;
}

.cbp-builder__preview-wrap {
	display: flex;
	flex-direction: column;
	min-width: 0;
	min-height: 0;
	overflow: hidden;
	padding: 14px;
}

.cbp-preview-toolbar {
	flex: 0 0 auto;
}

.cbp-preview-toolbar__actions {
	display: flex;
	align-items: center;
	gap: 8px;
}

.cbp-preview-toolbar strong {
	display: block;
}

.cbp-preview-scroll {
	position: relative;
	overflow: auto;
	min-height: 0;
	flex: 1;
	overscroll-behavior: contain;
	padding: 22px;
	background: #e9edf2;
}

.cbp-preview-status-panel {
	position: sticky;
	top: 12px;
	z-index: 5;
	display: flex;
	justify-content: flex-end;
	height: 0;
	pointer-events: none;
}

.cbp-preview-status-panel__body {
	width: min(360px, calc(100vw - 72px));
	min-height: 104px;
	margin-right: 12px;
	padding: 18px 18px;
	border: 1px solid #bfdbfe;
	border-radius: 8px;
	background: rgba(239, 246, 255, 0.96);
	box-shadow: 0 10px 26px rgba(30, 64, 175, 0.14);
	pointer-events: auto;
}

.cbp-preview-status-panel__body strong {
	display: block;
	margin-top: 8px;
	font-size: 14px;
	color: #1e3a8a;
}

.cbp-preview-status-panel__body p {
	margin: 8px 0 0;
	font-size: 13px;
	line-height: 1.4;
	color: #475569;
}

.cbp-preview-status-panel__body.is-error {
	border-color: #fecaca;
	background: rgba(255, 247, 247, 0.96);
}

.cbp-preview-status-panel__body.is-error strong {
	color: #991b1b;
}

.cbp-specimen-page {
	position: relative;
	margin: 0 auto 24px;
	background: #fff;
	box-shadow: 0 10px 24px rgba(15, 23, 42, 0.18);
	overflow: hidden;
}

.cbp-letterhead {
	position: absolute;
	inset: 0 auto auto 0;
	width: 100%;
	pointer-events: none;
	z-index: 0;
}

.cbp-page-content {
	position: relative;
	z-index: 1;
	min-height: inherit;
	box-sizing: border-box;
}

.cbp-logo {
	position: absolute;
	height: auto;
	object-fit: contain;
}

.cbp-specimen-title {
	margin-bottom: 9mm;
}

.cbp-specimen-title h1 {
	margin: 0 0 2mm;
	font-size: 22pt;
	font-weight: 800;
	line-height: 1.1;
}

.cbp-specimen-title p,
.cbp-specimen-stack p {
	margin: 0;
}

.cbp-specimen-h1 {
	margin: 7mm 0 3mm;
	padding-bottom: 1.5mm;
	border-bottom: 1px solid #e5e7eb;
}

.cbp-specimen-h2 {
	margin: 0 0 1.5mm;
}

.cbp-specimen-stack {
	display: grid;
	gap: 5mm;
}

.cbp-specimen-grid {
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 5mm;
}

.cbp-preview-field span {
	display: block;
	margin-bottom: 1mm;
}

.cbp-preview-field strong {
	display: block;
	font-weight: inherit;
}

.cbp-specimen-table {
	width: 100%;
	border-collapse: collapse;
	border-style: solid;
	margin-top: 4mm;
}

.cbp-specimen-table th,
.cbp-specimen-table td {
	border: inherit;
	padding: var(--cell-top) var(--cell-right) var(--cell-bottom) var(--cell-left);
	text-align: left;
	vertical-align: top;
}

.cbp-specimen-table .num,
.cbp-specimen-table th:nth-child(3) {
	text-align: right;
}

.cbp-qr {
	position: absolute;
	display: grid;
	place-items: center;
	border: 1px solid #111827;
	background: linear-gradient(90deg, #111827 20%, transparent 20% 80%, #111827 80%) 0 0 / 18px
			18px,
		linear-gradient(#111827 20%, transparent 20% 80%, #111827 80%) 0 0 / 18px 18px, #fff;
}

.cbp-qr span {
	padding: 2px 5px;
	background: #fff;
	font-size: 9px;
	font-weight: 700;
}

.cbp-code-preview {
	min-height: 297mm;
}

.cbp-code-preview.is-ready {
	width: auto;
	min-height: 0;
	background: transparent;
	box-shadow: none;
	overflow: visible;
}

.cbp-code-preview__body {
	display: grid;
	gap: 16px;
	padding: 24mm;
}

.cbp-code-preview.is-ready .cbp-code-preview__body {
	padding: 0;
}

.cbp-code-preview__body h1 {
	margin: 2px 0 6px;
	font-size: 22px;
}

.cbp-code-preview__body p {
	margin: 0;
	color: #64748b;
}

.cbp-code-preview__body pre {
	margin: 0;
	padding: 14px;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	background: #f8fafc;
	color: #111827;
	font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, "Liberation Mono", monospace;
	font-size: 11px;
	line-height: 1.5;
	white-space: pre-wrap;
	overflow-wrap: anywhere;
}

.cbp-typst-page {
	width: max-content;
	margin: 0 auto;
	background: #fff;
	box-shadow: 0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2);
}

.cbp-typst-page :deep(svg) {
	display: block;
	width: auto;
	height: auto;
}

@media (max-width: 1100px) {
	:global(.cbp-builder-page .layout-main-section-wrapper),
	:global(.cbp-builder-host),
	:global(.cbp-builder-host #cbp-builder-root) {
		height: auto;
		overflow: visible;
	}

	.cbp-builder {
		grid-template-columns: 1fr;
		height: auto;
		overflow: visible;
	}

	.cbp-builder__controls {
		max-height: none;
		overflow: visible;
		border-right: 0;
		border-bottom: 1px solid #dfe3e8;
	}

	.cbp-builder__preview-wrap,
	.cbp-preview-scroll {
		overflow: visible;
	}
}
</style>
