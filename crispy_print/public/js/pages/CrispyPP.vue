<template>
	<div class="crispy-preview-layout">
		<!-- Left Pane: Settings -->
		<div class="settings-pane">
			<div class="section-head settings-pane__header">
				<h4 class="pull-left">{{ __("Print Settings") }}</h4>
				<div class="pull-right settings-pane__header-actions">
					<button
						type="button"
						class="btn btn-default btn-xs"
						@click="resetFormat"
						:title="__('Reset to saved format')"
					>
						{{ __("Reset") }}
					</button>
					<button
						type="button"
						class="btn btn-default btn-xs"
						popovertarget="preview-settings-help"
						popovertargetaction="toggle"
						:title="__('Toggle help')"
						aria-haspopup="dialog"
						aria-controls="preview-settings-help"
					>
						?
					</button>
					<div id="preview-settings-help" popover class="settings-pane__help-popover">
						<ul class="settings-pane__help-list">
							<li>{{ __("Configure page settings and document options.") }}</li>
							<li>{{ __("Changes apply immediately to the preview.") }}</li>
						</ul>
					</div>
				</div>
			</div>
			<div class="settings-pane__body">
				<div class="form-layout">
					<div v-if="isReportMode" class="settings-pane__section-card card">
						<button
							type="button"
							class="btn btn-link card-header settings-pane__section-header"
							:class="{ 'is-expanded': isReportTemplateExpanded }"
							@click="isReportTemplateExpanded = !isReportTemplateExpanded"
						>
							<span>{{ __("Report Template") }}</span>
							<svg
								:class="[
									'settings-pane__chevron',
									{
										'settings-pane__chevron--expanded':
											isReportTemplateExpanded,
									},
								]"
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<div
							v-if="isReportTemplateExpanded"
							class="settings-pane__section-content card-body"
						>
							<div class="form-group">
								<label class="control-label">{{ __("Report Format") }}</label>
								<select
									v-model="selectedReportFormat"
									class="form-control"
									@change="onReportFormatChange"
								>
									<option v-if="reportLoading" disabled>
										{{ __("Loading formats...") }}
									</option>
									<option
										v-for="fmt in reportFormats"
										:key="fmt.value"
										:value="fmt.value"
									>
										{{ fmt.label }}
									</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">{{ __("Font") }}</label>
								<select v-model="reportFontFamily" class="form-control">
									<option v-if="loadingFonts" disabled>
										{{ __("Loading fonts...") }}
									</option>
									<option
										v-for="font in availableFonts"
										:key="font"
										:value="font"
									>
										{{ font }}
									</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">{{ __("Font Size (pt)") }}</label>
								<input
									v-model.number="reportFontSizePt"
									type="number"
									min="1"
									step="0.5"
									class="form-control"
								/>
							</div>

							<div class="settings-pane__toggles">
								<label class="settings-pane__toggle">
									<input v-model="reportIncludeFilters" type="checkbox" />
									<span>{{ __("Show Filters") }}</span>
								</label>
								<label class="settings-pane__toggle">
									<input v-model="reportShowSummary" type="checkbox" />
									<span>{{ __("Show Summary") }}</span>
								</label>
								<label class="settings-pane__toggle">
									<input
										v-model="reportShowTotalRow"
										type="checkbox"
										:disabled="!reportHasTotalRow"
									/>
									<span>{{ __("Show Totals") }}</span>
								</label>
								<label class="settings-pane__toggle">
									<input
										v-model="reportShowChart"
										type="checkbox"
										:disabled="!reportHasChart"
									/>
									<span>{{ __("Show Chart") }}</span>
								</label>
							</div>
							<p
								v-if="reportTruncationWarning"
								class="settings-pane__report-warning text-warning small"
							>
								{{ reportTruncationWarning }}
							</p>
						</div>
					</div>

					<div v-if="isReportMode" class="settings-pane__section-card card">
						<button
							type="button"
							class="btn btn-link card-header settings-pane__section-header"
							:class="{ 'is-expanded': isReportColumnsExpanded }"
							@click="isReportColumnsExpanded = !isReportColumnsExpanded"
						>
							<span>{{ __("Columns") }}</span>
							<svg
								:class="[
									'settings-pane__chevron',
									{
										'settings-pane__chevron--expanded':
											isReportColumnsExpanded,
									},
								]"
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<div
							v-if="isReportColumnsExpanded"
							class="settings-pane__section-content card-body"
						>
							<p
								v-if="reportColumnsState.length === 0"
								class="help-block text-muted small"
							>
								{{ __("No report columns available.") }}
							</p>
							<div v-else class="report-columns">
								<div
									v-for="col in reportColumnsState"
									:key="col.fieldname"
									class="report-columns__row"
								>
									<input
										v-model="reportColumnSelections[col.fieldname].selected"
										type="checkbox"
										class="input-sm"
									/>
									<span class="report-columns__label">{{ col.label }}</span>
									<input
										v-model.lazy="reportColumnSelections[col.fieldname].width"
										type="text"
										class="form-control input-sm report-columns__width"
										:placeholder="__('auto')"
										:disabled="!reportColumnSelections[col.fieldname].selected"
									/>
								</div>
							</div>
						</div>
					</div>

					<div v-if="!isReportMode" class="settings-pane__section-card card">
						<div class="settings-pane__section-content card-body">
							<div class="form-group">
								<label class="control-label">{{ __("Active Template") }}</label>
								<select
									v-model="selectedTemplate"
									class="form-control"
									:disabled="templatesLoading || activeTemplates.length === 0"
								>
									<option v-if="templatesLoading" value="" disabled>
										{{ __("Loading templates...") }}
									</option>
									<option
										v-else-if="activeTemplates.length === 0"
										value=""
										disabled
									>
										{{ __("No active templates") }}
									</option>
									<option
										v-for="template in activeTemplates"
										:key="template.name"
										:value="template.name"
									>
										{{ template.template_name }} v{{ template.version }} -
										{{ __(template.scope) }}
									</option>
								</select>
								<p v-if="selectedTemplateInfo" class="help-block text-muted small">
									{{
										selectedTemplateInfo.company
											? __("Company template for {0}", [
													selectedTemplateInfo.company_abbr ||
														selectedTemplateInfo.company,
											  ])
											: __("Global fallback template")
									}}
								</p>
								<label class="settings-pane__toggle">
									<input
										v-model="useActiveTemplate"
										type="checkbox"
										:disabled="
											activeTemplates.length === 0 || activeTemplateLoading
										"
									/>
									<span>{{ __("Use Active Template") }}</span>
								</label>
								<p
									v-if="activeTemplateLoading"
									class="help-block text-muted small"
								>
									{{ __("Loading template snapshot...") }}
								</p>
							</div>
						</div>
					</div>

					<div class="settings-pane__section-card card">
						<button
							type="button"
							class="btn btn-link card-header settings-pane__section-header"
							:class="{ 'is-expanded': isOverridesExpanded }"
							@click="isOverridesExpanded = !isOverridesExpanded"
						>
							<span>{{ __("Preview Overrides") }}</span>
							<svg
								:class="[
									'settings-pane__chevron',
									{ 'settings-pane__chevron--expanded': isOverridesExpanded },
								]"
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<div
							v-if="isOverridesExpanded"
							class="settings-pane__section-content card-body"
						>
							<p class="help-block text-muted small">
								{{ __("Preview-only changes. The saved format is unchanged.") }}
							</p>

							<!-- Print Format (doctype source) -->
							<div v-if="!isReportMode" class="form-group">
								<label class="control-label">{{ __("Print Format") }}</label>
								<select
									v-model="selectedFormat"
									class="form-control"
									@change="onFormatChange"
								>
									<option
										v-for="fmt in availableFormats"
										:key="fmt.name"
										:value="fmt.name"
									>
										{{ fmt.name }}{{ fmt.is_default ? " (Default)" : "" }}
									</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">{{ __("Language") }}</label>
								<select
									v-model="presentation_settings.language"
									class="form-control"
									disabled
								>
									<option value="en">{{ __("English") }}</option>
									<option value="ar">{{ __("Arabic") }}</option>
									<option value="fr">{{ __("French") }}</option>
									<option value="de">{{ __("German") }}</option>
									<option value="es">{{ __("Spanish") }}</option>
								</select>
								<p class="help-block text-muted small">
									Default language. More languages coming soon.
								</p>
							</div>
						</div>
					</div>
					<div v-if="isBrandingProfileDriven" class="settings-pane__section-card card">
						<div class="settings-pane__section-content card-body">
							<p class="help-block text-muted small">
								{{
									__("Presentation is controlled by Branding Profile: {0}", [
										activeBrandingProfile,
									])
								}}
							</p>
						</div>
					</div>
					<div v-if="!isBrandingProfileDriven" class="settings-pane__section-card card">
						<button
							type="button"
							class="btn btn-link card-header settings-pane__section-header"
							:class="{ 'is-expanded': isBrandingExpanded }"
							@click="isBrandingExpanded = !isBrandingExpanded"
						>
							<span>{{ __("Branding") }}</span>
							<svg
								:class="[
									'settings-pane__chevron',
									{ 'settings-pane__chevron--expanded': isBrandingExpanded },
								]"
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<div
							v-if="isBrandingExpanded"
							class="settings-pane__section-content card-body"
						>
							<div class="form-group">
								<label class="control-label">{{ __("Branding") }}</label>
								<select v-model="branding_mode" class="form-control">
									<option value="none">{{ __("None") }}</option>
									<option value="letterhead">{{ __("Letterhead") }}</option>
									<option value="logo">{{ __("Logo") }}</option>
								</select>
							</div>

							<div v-if="branding_mode === 'letterhead'" class="form-group">
								<label class="control-label">{{ __("Letter Head") }}</label>
								<select
									v-model="presentation_settings.branding.letterhead"
									class="form-control"
								>
									<option value="">{{ __("None") }}</option>
									<option v-if="loadingLetterheads" disabled>
										{{ __("Loading letterheads...") }}
									</option>
									<option
										v-for="lh in availableLetterheads"
										:key="lh"
										:value="lh"
									>
										{{ lh }}
									</option>
								</select>
							</div>

							<div v-if="branding_mode === 'logo'">
								<p class="help-block text-muted small">
									{{ __("Logo is anchored to top-left using #place().") }}
								</p>
								<div class="form-group">
									<label class="control-label">{{ __("Company") }}</label>
									<select v-model="logo_settings.company" class="form-control">
										<option value="">{{ __("Select company") }}</option>
										<option v-if="loadingCompanies" disabled>
											{{ __("Loading companies...") }}
										</option>
										<option
											v-for="company in availableCompanies"
											:key="company.name"
											:value="company.name"
										>
											{{
												company.abbr
													? `${company.abbr} - ${company.name}`
													: company.name
											}}
										</option>
									</select>
								</div>
								<p
									v-if="logo_settings.company && !logo_settings.image"
									class="help-block text-muted small"
								>
									{{ __("Selected company has no logo set.") }}
								</p>
								<div class="row">
									<div class="col-xs-12 form-group">
										<label class="control-label text-muted small">{{
											__("Size (mm)")
										}}</label>
										<input
											v-model.number="logo_settings.size"
											type="number"
											class="form-control input-sm"
										/>
									</div>
								</div>
								<div class="row">
									<div class="col-xs-6 form-group">
										<label class="control-label text-muted small">{{
											__("dx (mm)")
										}}</label>
										<input
											v-model.number="logo_settings.dx"
											type="number"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<label class="control-label text-muted small">{{
											__("dy (mm)")
										}}</label>
										<input
											v-model.number="logo_settings.dy"
											type="number"
											class="form-control input-sm"
										/>
									</div>
								</div>
							</div>

							<div v-if="!isReportMode" class="checkbox">
								<label>
									<input v-model="removeQr" type="checkbox" />
									{{ __("Remove QRCode") }}
								</label>
							</div>
						</div>
					</div>
					<div v-if="!isBrandingProfileDriven" class="settings-pane__section-card card">
						<button
							type="button"
							class="btn btn-link card-header settings-pane__section-header"
							:class="{ 'is-expanded': isPresentationSettingsExpanded }"
							@click="
								isPresentationSettingsExpanded = !isPresentationSettingsExpanded
							"
						>
							<span>{{ __("Presentation Settings") }}</span>
							<svg
								:class="[
									'settings-pane__chevron',
									{
										'settings-pane__chevron--expanded':
											isPresentationSettingsExpanded,
									},
								]"
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<div
							v-if="isPresentationSettingsExpanded"
							class="settings-pane__section-content card-body"
						>
							<div class="form-group">
								<label class="control-label">{{ __("Page Size") }}</label>
								<select
									v-model="presentation_settings.page.size"
									class="form-control"
								>
									<option value="A3">{{ __("A3 (297 × 420 mm)") }}</option>
									<option value="A4">{{ __("A4 (210 × 297 mm)") }}</option>
									<option value="A5">{{ __("A5 (148 × 210 mm)") }}</option>
									<option value="Letter">
										{{ __("Letter (8.5 × 11 in)") }}
									</option>
									<option value="Legal">{{ __("Legal (8.5 × 14 in)") }}</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">{{ __("Orientation") }}</label>
								<select
									v-model="presentation_settings.page.orientation"
									class="form-control"
								>
									<option value="portrait">{{ __("Portrait") }}</option>
									<option value="landscape">{{ __("Landscape") }}</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">{{ __("Margins (mm)") }}</label>
								<div class="row">
									<div class="col-xs-6 form-group">
										<span class="text-muted small">{{ __("T") }}</span>
										<input
											v-model.number="presentation_settings.page.margins.top"
											type="number"
											:placeholder="__('Top')"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<span class="text-muted small">{{ __("B") }}</span>
										<input
											v-model.number="
												presentation_settings.page.margins.bottom
											"
											type="number"
											:placeholder="__('Bottom')"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<span class="text-muted small">{{ __("L") }}</span>
										<input
											v-model.number="
												presentation_settings.page.margins.left
											"
											type="number"
											:placeholder="__('Left')"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<span class="text-muted small">{{ __("R") }}</span>
										<input
											v-model.number="
												presentation_settings.page.margins.right
											"
											type="number"
											:placeholder="__('Right')"
											class="form-control input-sm"
										/>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Right Pane: Preview -->
		<PreviewRenderer
			:format-name="previewFormatName"
			:layout="layout"
			:doc-header="docHeader"
			:doc-footer="docFooter"
			:typst-preamble="typstPreambleEffective"
			:typst-code="typstCode"
			:pdf-standard="pdfStandard"
			:raw-typst="rawTypst"
			:qr-enabled="qrEnabledEffective"
			:letterhead="letterheadDoc"
			:doc-type="props.doctype || null"
			:doc-name="props.docname || null"
			:presentation_settings="presentation_settings_computed"
			:change-key="changeKey"
			:watch-data-changes="true"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, onMounted, watch, computed } from "vue";
import {
	getFormatsForDoctype,
	loadFormatData,
	parseCrispyFormatDoc,
	resolveLetterheadDoc,
	type FormatInfo,
} from "../utils/formatLoader";
import {
	default_presentation_settings,
	defaultTypography,
	ensure_logo_settings,
	merge_presentation_settings,
	type PresentationSettings,
} from "../utils/presentation_settings";
import { resolve_effective_presentation_settings } from "../utils/effectivePresentationSettings";
import PreviewRenderer from "../components/PreviewRenderer.vue";
import { pickFormatName } from "../utils/formatSelection";
import { useBrandingData } from "../composables/useBrandingData";
import { loadReportState, normalizeReportChartSvg } from "../utils/reportState";
import { dispatchCrispyPreviewSource } from "../utils/events";
import {
	buildReportFormatOptions,
	normalizeReportColumns,
	type ReportColumn,
	type ReportFormatOption,
} from "./reportPrintSettings";
import { getLogger } from "../logger";
import { fetchTypstFonts, formatPt, parseSize } from "../utils/typstTypography";
import { __ } from "../utils/i18n";
import {
	compileReportPreview,
	compileTypst,
	getActiveCrispyTemplatesForDocument,
	getResolvedCrispyTemplateForDocument,
	type ActiveCrispyTemplateOption,
	type ResolvedCrispyTemplate,
} from "../api/crispy";

interface Props {
	doctype?: string;
	docname?: string;
	format?: string;
	source?: string;
	report?: string;
	reportFilters?: Record<string, any>;
	reportColumns?: any[];
	reportChartSvg?: string;
}

const props = defineProps<Props>();
const logger = getLogger({ component: "CrispyPP" });

// Format selection
const availableFormats = ref<FormatInfo[]>([]);
const {
	availableLetterheads,
	loadingLetterheads,
	availableCompanies,
	loadingCompanies,
	resolveCompanyLogo,
	fetchLetterheads,
	fetchCompanies,
} = useBrandingData();
const selectedFormat = ref<string>("");
const activeTemplates = ref<ActiveCrispyTemplateOption[]>([]);
const selectedTemplate = ref("");
const templatesLoading = ref(false);
const useActiveTemplate = ref(false);
const activeTemplateLoading = ref(false);
const activeTemplateSnapshot = ref<ResolvedCrispyTemplate | null>(null);
const isReportMode = computed(() => props.source === "report");
const reportName = computed(() => props.report || "");
const reportFormats = ref<ReportFormatOption[]>([]);
const reportLoading = ref(false);
const selectedReportFormat = ref<string>("");
const reportIncludeFilters = ref(false);
const reportShowSummary = ref(true);
const reportShowTotalRow = ref(true);
const reportShowChart = ref(true);
const reportColumnsState = ref<ReportColumn[]>([]);
const reportColumnSelections = ref<Record<string, { selected: boolean; width: string }>>({});
const reportHasSummary = ref(false);
const reportHasTotalRow = ref(true);
const reportFilters = ref<Record<string, any>>(props.reportFilters || {});
const reportChartSvg = ref<string>(props.reportChartSvg || "");
const reportHasChart = computed(() =>
	Boolean(normalizeReportChartSvg(reportChartSvg.value || ""))
);
const isReportColumnsExpanded = ref(true);
const reportPreviewLoading = ref(false);
const reportPreviewPending = ref(false);
const reportTruncationWarning = ref("");
const REPORT_PREVIEW_DEBOUNCE_MS = 250;
const reportPreviewDebounceTimer = ref<number | null>(null);
const reportPreviewIntentSeq = ref(0);
const reportBrandingInitialized = ref(false);
const reportOrientationInitialized = ref(false);
const reportMarginsInitialized = ref(false);
const lastReportTypstSource = ref<string | null>(null);
const lastReportChartSvg = ref<string>("");
const lastReportAssetFiles = ref<string[]>([]);
const availableFonts = ref<string[]>([]);
const loadingFonts = ref(false);
const reportFontFamily = ref("Inter 18pt");
const reportFontSizePt = ref(10);

function getPreviewCompany(): string | null {
	return (
		presentation_settings.value?.branding?.company ||
		(props.reportFilters?.company ? String(props.reportFilters.company) : "") ||
		null
	);
}

// Settings state (single in-memory copy; PP does not persist)
const presentation_settings = ref<PresentationSettings>(
	merge_presentation_settings(default_presentation_settings, {})
);
const effective_presentation_settings = ref<PresentationSettings>(
	merge_presentation_settings(default_presentation_settings, {})
);
const isBrandingProfileDriven = computed(
	() =>
		presentation_settings.value.source === "branding_profile" &&
		Boolean(presentation_settings.value.branding?.profile)
);
const activeBrandingProfile = computed(
	() => presentation_settings.value.branding?.profile || __("selected profile")
);
const selectedTemplateInfo = computed(
	() =>
		activeTemplates.value.find((template) => template.name === selectedTemplate.value) || null
);
const previewFormatName = computed(() => {
	if (isReportMode.value) return null;
	if (useActiveTemplate.value && activeTemplateSnapshot.value?.source_crispy_format) {
		return activeTemplateSnapshot.value.source_crispy_format;
	}
	return selectedFormat.value;
});

const layout = ref<any>(null);
const loading = ref(true);
const docHeader = ref("");
const docFooter = ref("");
const typstPreamble = ref("");
const typstCode = ref("");
const pdfStandard = ref("PDF/A-2u");
const rawTypst = ref(false);
const removeQr = ref(false);
const letterheadDoc = ref<any | null>(null);
const changeKey = ref(0);
const OVERRIDES_STORAGE_KEY = "crispy-print:pp:preview-overrides-expanded";
const isOverridesExpanded = ref(false);
const isReportTemplateExpanded = ref(true);
const isBrandingExpanded = ref(false);
const isPresentationSettingsExpanded = ref(false);
const qrEnabledEffective = computed(() => {
	const page_qr_enabled = effective_presentation_settings.value.qr?.enabled;
	if (typeof page_qr_enabled === "boolean") {
		return page_qr_enabled && !removeQr.value;
	}
	return false;
});
const logo_settings = computed(() => ensure_logo_settings(effective_presentation_settings.value));

function usesLogoBranding(mode: string): boolean {
	return mode === "logo" || mode === "logo_letterhead";
}

function usesLetterheadBranding(mode: string): boolean {
	return mode === "letterhead" || mode === "logo_letterhead";
}

const branding_mode = computed<string>({
	get: () => {
		const mode = effective_presentation_settings.value.branding.mode;
		if (
			mode === "letterhead" ||
			mode === "logo" ||
			mode === "logo_letterhead" ||
			mode === "none"
		) {
			return mode;
		}
		if (
			effective_presentation_settings.value.branding.logo?.company ||
			effective_presentation_settings.value.branding.logo?.image
		) {
			return "logo";
		}
		if (effective_presentation_settings.value.branding.letterhead) {
			return "letterhead";
		}
		return "none";
	},
	set: (value) => {
		presentation_settings.value.branding.mode = value as "letterhead" | "logo" | "none";
	},
});

function escapeTypstString(value: string): string {
	return String(value || "").replace(/"/g, '\\"');
}

async function fetchFonts() {
	loadingFonts.value = true;
	try {
		availableFonts.value = await fetchTypstFonts({ logger });
	} finally {
		loadingFonts.value = false;
	}
}

const reportFontPreamble = computed(() => {
	if (!reportFontFamily.value) return "";
	const font = escapeTypstString(reportFontFamily.value);
	return `#set text(font: "${font}", size: ${formatPt(reportFontSizePt.value)})`;
});

let effectiveSettingsRequestSeq = 0;

async function refreshEffectivePresentationSettings() {
	const requestSeq = ++effectiveSettingsRequestSeq;
	const resolved = await resolve_effective_presentation_settings(
		presentation_settings.value,
		presentation_settings.value?.branding?.company || null
	);
	if (requestSeq !== effectiveSettingsRequestSeq) return;
	effective_presentation_settings.value = resolved;
}

const typstPreambleEffective = computed(() => {
	if (!isReportMode.value) return typstPreamble.value;
	const prefix = reportFontPreamble.value;
	if (!prefix) return typstPreamble.value;
	const base = typstPreamble.value || "";
	return base ? `${prefix}\n${base}` : prefix;
});

function buildReportTypstCodeOverride(): string {
	const baseCode = String(typstCode.value || "");
	if (!isReportMode.value || !baseCode.trim()) return baseCode;
	const fontSetLine = reportFontPreamble.value.trim();
	if (!fontSetLine) return baseCode;

	// Keep report font controls authoritative by replacing the first template-level
	// global text setting when present (common in generic/basic report templates).
	const replaced = baseCode.replace(/#set\s+text\([^\n]*\)/, fontSetLine);
	if (replaced !== baseCode) return replaced;
	return `${fontSetLine}\n${baseCode}`;
}

function seedReportColumnSelections(columns: ReportColumn[]) {
	const next: Record<string, { selected: boolean; width: string }> = {};
	columns.forEach((col) => {
		const existing = reportColumnSelections.value[col.fieldname];
		next[col.fieldname] = existing || { selected: true, width: "auto" };
	});
	reportColumnSelections.value = next;
}

const reportColumnConfig = computed(() =>
	Object.entries(reportColumnSelections.value)
		.filter(([, value]) => value.selected)
		.map(([fieldname, value]) => ({
			fieldname,
			width: value.width || "auto",
		}))
);

async function initializeReportSettings() {
	if (!reportName.value) {
		return;
	}

	try {
		reportLoading.value = true;
		const response = await frappe.call({
			method: "crispy_print.api.v1.get_available_formats",
			args: { report: reportName.value, company: getPreviewCompany() },
		});
		const { options, defaultValue } = buildReportFormatOptions(response?.message);
		reportFormats.value = options;

		if (defaultValue) {
			selectedReportFormat.value = defaultValue;
			await loadFormatSettings(defaultValue);
		}

		if (!reportBrandingInitialized.value) {
			presentation_settings.value.branding.mode = "none";
			reportBrandingInitialized.value = true;
		}

		if (!reportOrientationInitialized.value) {
			presentation_settings.value.page.orientation = "landscape";
			reportOrientationInitialized.value = true;
		}

		if (!reportMarginsInitialized.value) {
			presentation_settings.value.page.margins = { top: 20, bottom: 10, left: 7, right: 7 };
			reportMarginsInitialized.value = true;
		}

		if (reportColumnsState.value.length === 0) {
			await fetchReportColumns();
		}

		await fetchLetterheads();
		await fetchCompanies();
	} catch (error) {
		logger.error("Failed to load report formats", error);
		frappe.show_alert({
			message: __("Failed to load report formats."),
			indicator: "red",
		});
	} finally {
		reportLoading.value = false;
	}
}

function hydrateReportStateFromStorage() {
	if (!reportName.value || typeof window === "undefined") return;
	const hasFilters = Object.keys(reportFilters.value || {}).length > 0;
	const hasColumns = Array.isArray(props.reportColumns) && props.reportColumns.length > 0;
	const hasChart = Boolean(reportChartSvg.value);
	if (hasFilters && hasColumns && hasChart) return;

	const parsed = loadReportState(reportName.value);
	if (!parsed) return;
	if (!hasFilters && parsed.filters) {
		reportFilters.value = parsed.filters;
	}
	if (!hasColumns && Array.isArray(parsed.columns)) {
		const normalized = normalizeReportColumns(parsed.columns || []);
		reportColumnsState.value = normalized;
		seedReportColumnSelections(normalized);
	}
	if (!hasChart && typeof parsed.chartSvg === "string") {
		reportChartSvg.value = parsed.chartSvg;
	}
}

async function onReportFormatChange() {
	if (!selectedReportFormat.value) return;
	await loadFormatSettings(selectedReportFormat.value);
	requestReportPreviewCompile(true);
}

async function fetchReportColumns() {
	if (!reportName.value) return;

	try {
		const response = await frappe.call({
			method: "frappe.desk.query_report.run",
			args: {
				report_name: reportName.value,
				filters: reportFilters.value || {},
				ignore_prepared_report: 1,
			},
		});

		const columns = response?.message?.columns || [];
		const normalized = normalizeReportColumns(columns);
		reportColumnsState.value = normalized;
		seedReportColumnSelections(normalized);
		const message = response?.message || {};
		const hasSummaryKey = Object.prototype.hasOwnProperty.call(message, "report_summary");
		reportHasSummary.value = hasSummaryKey;
		const rawRows = Array.isArray(message?.result) ? message.result : [];
		const hasExplicitTotalRow = rawRows.some(
			(row: any) => row && typeof row === "object" && Boolean(row.is_total_row)
		);
		const addTotalRowFlag = Boolean(message?.add_total_row);
		reportHasTotalRow.value = hasExplicitTotalRow || addTotalRowFlag;
	} catch (error) {
		logger.error("Failed to load report columns", error);
	}
}

async function compileReportPreview() {
	reportPreviewIntentSeq.value += 1;
	const requestedIntent = reportPreviewIntentSeq.value;
	if (reportPreviewDebounceTimer.value) {
		window.clearTimeout(reportPreviewDebounceTimer.value);
		reportPreviewDebounceTimer.value = null;
	}
	await compileReportPreviewForIntent(requestedIntent);
}

function requestReportPreviewCompile(immediate = false) {
	if (!isReportMode.value) return;

	reportPreviewIntentSeq.value += 1;
	const requestedIntent = reportPreviewIntentSeq.value;

	if (reportPreviewDebounceTimer.value) {
		window.clearTimeout(reportPreviewDebounceTimer.value);
		reportPreviewDebounceTimer.value = null;
	}

	const run = () => {
		reportPreviewDebounceTimer.value = null;
		void compileReportPreviewForIntent(requestedIntent);
	};

	if (immediate) {
		run();
		return;
	}

	reportPreviewDebounceTimer.value = window.setTimeout(run, REPORT_PREVIEW_DEBOUNCE_MS);
}

async function compileReportPreviewForIntent(intentSeq: number) {
	if (!isReportMode.value) return;
	if (!reportName.value || !selectedReportFormat.value) return;
	if (reportPreviewLoading.value) {
		reportPreviewPending.value = true;
		return;
	}

	try {
		reportPreviewLoading.value = true;
		reportTruncationWarning.value = "";
		const chartSvgPayload = reportShowChart.value
			? normalizeReportChartSvg(reportChartSvg.value || "")
			: "";
		const active_branding_mode = branding_mode.value;
		const letterhead_image = usesLetterheadBranding(active_branding_mode)
			? letterheadDoc.value?.image || null
			: null;
		const logoImage = usesLogoBranding(active_branding_mode)
			? logo_settings.value.image || null
			: null;
		const brandingAssetFiles = [letterhead_image, logoImage].filter((value): value is string =>
			Boolean(value)
		);
		logger.info("Report preview compile requested with letterhead", letterheadDoc.value);
		logger.info("Report preview compile requested with letterhead image", letterhead_image);
		logger.info(
			"Report preview compile requested with presentation settings",
			presentation_settings_computed.value
		);
		const result = await compileReportPreview({
			report: reportName.value,
			format_name: selectedReportFormat.value,
			filters: reportFilters.value || {},
			column_config: reportColumnConfig.value,
			include_filters: reportIncludeFilters.value ? 1 : 0,
			include_summary: reportShowSummary.value ? 1 : 0,
			include_total_row: reportShowTotalRow.value ? 1 : 0,
			include_chart: reportShowChart.value ? 1 : 0,
			orientation: effective_presentation_settings.value.page.orientation,
			presentation_settings: presentation_settings_computed.value,
			chart_svg: chartSvgPayload || null,
			typst_preamble_override: reportFontPreamble.value,
			typst_code_override: buildReportTypstCodeOverride(),
			limit: 50,
			asset_files: brandingAssetFiles,
		});

		// Ignore stale response if a newer compile intent exists.
		if (intentSeq !== reportPreviewIntentSeq.value) return;

		const typstSource = result?.typst_source || "";
		const truncation = result?.truncation || null;
		const compileAssetFiles = Array.isArray(result?.asset_files)
			? result.asset_files
			: brandingAssetFiles;
		if (!typstSource) {
			throw new Error("No Typst source returned");
		}
		if (truncation?.is_truncated) {
			const originalRows = Number(truncation?.original_rows || 0);
			const returnedRows = Number(truncation?.returned_rows || 0);
			reportTruncationWarning.value = __(
				"Preview truncated to {0} rows (from {1}). PDF output may also be limited.",
				[String(returnedRows), String(originalRows)]
			);
		}
		dispatchCrispyPreviewSource({ source: typstSource });
		lastReportTypstSource.value = typstSource;
		lastReportChartSvg.value = chartSvgPayload || "";
		lastReportAssetFiles.value = compileAssetFiles;

		if (result?.success) {
			window.dispatchEvent(
				new CustomEvent("crispy-report-preview", {
					detail: {
						svg_pages: result.svg_pages,
						page_count: result.page_count,
					},
				})
			);
		}
	} catch (error) {
		logger.error("Report preview failed", error);
		frappe.show_alert({
			message: __("Report preview failed."),
			indicator: "red",
		});
	} finally {
		reportPreviewLoading.value = false;
		if (reportPreviewPending.value || intentSeq !== reportPreviewIntentSeq.value) {
			reportPreviewPending.value = false;
			requestReportPreviewCompile(true);
		}
	}
}

// Explicit invalidation for preview recompilation (avoids deep watches inside PreviewRenderer).
watch(
	() => [
		layout.value,
		presentation_settings.value,
		letterheadDoc.value,
		docHeader.value,
		docFooter.value,
		typstPreamble.value,
		typstCode.value,
		rawTypst.value,
		removeQr.value,
		reportFontFamily.value,
		reportFontSizePt.value,
	],
	() => {
		changeKey.value++;
	},
	{ deep: true }
);

// Initialize: Load available formats and letterheads
async function initializeData() {
	if (!props.doctype) {
		if (props.source === "report") {
			loading.value = false;
			return;
		}
		logger.warn("No doctype specified");
		loading.value = false;
		return;
	}

	try {
		loading.value = true;

		// Load available formats for this doctype
		const formats = await getFormatsForDoctype(props.doctype, getPreviewCompany());

		// Check is_default flag for each format
		const formatsWithDefault = await Promise.all(
			formats.map(async (fmt) => {
				const isDefault = await frappe.db.get_value(
					"Crispy Format",
					fmt.name,
					"is_default"
				);
				return { ...fmt, is_default: isDefault.message.is_default };
			})
		);

		availableFormats.value = formatsWithDefault;

		await fetchLetterheads();
		await fetchCompanies();

		// Determine which format to use
		const formatToLoad = pickFormatName(formatsWithDefault, props.format || null);

		if (formatToLoad) {
			selectedFormat.value = formatToLoad;
			await loadFormatSettings(formatToLoad);
			await loadActiveTemplates();
		} else {
			logger.warn("No formats available for doctype", props.doctype);
			await loadActiveTemplates();
			loading.value = false;
		}
	} catch (error) {
		logger.error("Error initializing", error);
		frappe.show_alert({
			message: __("Failed to initialize preview: {0}", [error.message]),
			indicator: "red",
		});
		loading.value = false;
	}
}

// Load settings for a specific format
async function loadFormatSettings(formatName: string) {
	try {
		loading.value = true;

		const data = await loadFormatData(formatName, {
			company: getPreviewCompany(),
			source_doctype: props.doctype || null,
			source_docname: props.docname || null,
			report_filters: props.reportFilters || null,
		});

		if (!data) {
			throw new Error("Failed to load format data");
		}

		// Overwrite in-memory presentation settings (ephemeral)
		presentation_settings.value = merge_presentation_settings(
			default_presentation_settings,
			data.presentation_settings || {}
		);
		if (data.formatDoc.effective_company) {
			presentation_settings.value.branding.company = data.formatDoc.effective_company;
			presentation_settings.value.branding.logo.company = data.formatDoc.effective_company;
		}
		await refreshEffectivePresentationSettings();
		if (
			data.presentation_settings?.qr?.enabled === undefined &&
			presentation_settings.value.qr
		) {
			delete (presentation_settings.value.qr as any).enabled;
		}

		// Preload letterhead data if the format has one set
		letterheadDoc.value = await resolveLetterheadDoc(
			effective_presentation_settings.value.branding.letterhead
		);

		// Store layout
		layout.value = data.layout;
		docHeader.value = data.formatDoc.doc_header || "";
		docFooter.value = data.formatDoc.doc_footer || "";
		typstPreamble.value = data.formatDoc.typst_preamble || "";
		typstCode.value = data.formatDoc.typst_code || "";
		pdfStandard.value = data.formatDoc.pdf_standard || "PDF/A-2u";
		rawTypst.value = Boolean(data.formatDoc.raw_typst);

		loading.value = false;
	} catch (error) {
		logger.error("Error loading format settings", error);
		frappe.show_alert({
			message: __("Failed to load format: {0}", [error.message]),
			indicator: "red",
		});
		loading.value = false;
	}
}

async function loadActiveTemplates() {
	if (!props.doctype || isReportMode.value) return;
	templatesLoading.value = true;
	try {
		const templates = await getActiveCrispyTemplatesForDocument({
			source_doctype: props.doctype,
			source_docname: props.docname || null,
			company: presentation_settings.value.branding?.company || null,
		});
		activeTemplates.value = templates;
		selectedTemplate.value = templates[0]?.name || "";
		if (!selectedTemplate.value) {
			useActiveTemplate.value = false;
			activeTemplateSnapshot.value = null;
		}
	} catch (error) {
		logger.error("Error loading active Crispy Templates", error);
		activeTemplates.value = [];
		selectedTemplate.value = "";
		frappe.show_alert({
			message: __("Failed to load active templates"),
			indicator: "red",
		});
	} finally {
		templatesLoading.value = false;
	}
}

async function loadSelectedActiveTemplate() {
	if (!props.doctype || !selectedTemplate.value) return;
	activeTemplateLoading.value = true;
	try {
		const snapshot = await getResolvedCrispyTemplateForDocument({
			source_doctype: props.doctype,
			source_docname: props.docname || null,
			company: presentation_settings.value.branding?.company || null,
			template: selectedTemplate.value,
		});
		activeTemplateSnapshot.value = snapshot;
		const parsed = parseCrispyFormatDoc({
			name: snapshot.source_crispy_format || snapshot.name,
			doc_type: snapshot.source_doctype || props.doctype,
			crispy_format_type: snapshot.crispy_format_type,
			company: snapshot.company || "",
			layout_json: snapshot.layout_json || "",
			presentation_settings: snapshot.presentation_settings || "",
			doc_header: snapshot.doc_header || "",
			doc_footer: snapshot.doc_footer || "",
			typst_preamble: snapshot.typst_preamble || "",
			typst_code: snapshot.typst_code || "",
			pdf_standard: snapshot.pdf_standard || "PDF/A-2u",
			raw_typst: snapshot.raw_typst ? 1 : 0,
			effective_company: snapshot.effective_company || snapshot.company || null,
		});

		presentation_settings.value = merge_presentation_settings(
			default_presentation_settings,
			parsed.presentation_settings || {}
		);
		const effectiveCompany = snapshot.effective_company || snapshot.company || "";
		if (effectiveCompany) {
			presentation_settings.value.branding.company = effectiveCompany;
			presentation_settings.value.branding.logo.company = effectiveCompany;
		}
		await refreshEffectivePresentationSettings();
		letterheadDoc.value = await resolveLetterheadDoc(
			effective_presentation_settings.value.branding.letterhead
		);

		layout.value = parsed.layout;
		docHeader.value = snapshot.doc_header || "";
		docFooter.value = snapshot.doc_footer || "";
		typstPreamble.value = snapshot.typst_preamble || "";
		typstCode.value = snapshot.typst_code || "";
		pdfStandard.value = snapshot.pdf_standard || "PDF/A-2u";
		rawTypst.value = Boolean(snapshot.raw_typst);
	} catch (error) {
		logger.error("Error loading active Crispy Template", error);
		activeTemplateSnapshot.value = null;
		useActiveTemplate.value = false;
		frappe.show_alert({
			message: __("Failed to load active template"),
			indicator: "red",
		});
	} finally {
		activeTemplateLoading.value = false;
	}
}

// Handle format change
async function onFormatChange() {
	await loadFormatSettings(selectedFormat.value);
	await loadActiveTemplates();
	if (useActiveTemplate.value) {
		await loadSelectedActiveTemplate();
	}
}

async function resetFormat() {
	if (!selectedFormat.value) return;
	await loadFormatSettings(selectedFormat.value);
	await loadActiveTemplates();
	if (useActiveTemplate.value) {
		await loadSelectedActiveTemplate();
	}
}

// Expose settings getters for external access
const get_presentation_settings = () => ({
	...effective_presentation_settings.value,
	branding: {
		...effective_presentation_settings.value.branding,
		letterhead_image: usesLetterheadBranding(branding_mode.value)
			? letterheadDoc.value?.image ||
			  effective_presentation_settings.value.branding.letterhead_image ||
			  ""
			: "",
	},
});

const presentation_settings_computed = computed(() => get_presentation_settings());

const getReportSettings = () => ({
	report: reportName.value,
	format: selectedReportFormat.value,
	orientation: effective_presentation_settings.value.page.orientation,
	includeFilters: reportIncludeFilters.value ? 1 : 0,
	includeSummary: reportShowSummary.value ? 1 : 0,
	includeTotalRow: reportShowTotalRow.value ? 1 : 0,
	includeChart: reportShowChart.value ? 1 : 0,
	columnConfig: reportColumnConfig.value,
	filters: reportFilters.value,
});

function triggerRefresh() {
	// Manual refresh (refetch + recompile) for the Crispy Print preview page.
	window.dispatchEvent(new CustomEvent("crispy-preview:refresh"));
}

const getLayout = () => layout.value;
const getLetterhead = () => {
	// Return the letterhead object with image path
	// setupWorker expects an object with .image property
	return letterheadDoc.value;
};

// Fetch letterhead data when letterhead selection changes
watch(
	presentation_settings,
	() => {
		refreshEffectivePresentationSettings();
	},
	{ deep: true, immediate: true }
);

watch(
	() => effective_presentation_settings.value.branding.letterhead,
	async (newLetterhead) => {
		logger.info("Letterhead selection changed", newLetterhead);
		letterheadDoc.value = await resolveLetterheadDoc(newLetterhead);
		logger.info("Letterhead doc resolved", letterheadDoc.value);
	}
);

watch(
	() => letterheadDoc.value,
	() => {
		logger.info("Letterhead doc updated, recompiling preview");
		if (isReportMode.value) {
			requestReportPreviewCompile();
		}
	}
);

watch(useActiveTemplate, async (enabled) => {
	if (enabled) {
		await loadSelectedActiveTemplate();
		return;
	}
	activeTemplateSnapshot.value = null;
	if (selectedFormat.value) {
		await loadFormatSettings(selectedFormat.value);
	}
});

watch(selectedTemplate, async () => {
	if (useActiveTemplate.value) {
		await loadSelectedActiveTemplate();
	}
});

watch(
	() => props.reportColumns,
	(next) => {
		const normalized = normalizeReportColumns(next || []);
		reportColumnsState.value = normalized;
		seedReportColumnSelections(normalized);
	},
	{ immediate: true }
);

watch(
	() => props.reportFilters,
	(next) => {
		reportFilters.value = next || {};
	},
	{ immediate: true }
);

watch(reportHasSummary, (hasSummary) => {
	if (!hasSummary) {
		reportShowSummary.value = true;
	}
});

watch(reportHasTotalRow, (hasTotalRow) => {
	if (!hasTotalRow) {
		reportShowTotalRow.value = true;
	}
});

watch(
	() => [
		selectedReportFormat.value,
		reportColumnConfig.value,
		reportFilters.value,
		reportIncludeFilters.value,
		reportShowSummary.value,
		reportShowTotalRow.value,
		reportShowChart.value,
	],
	() => {
		requestReportPreviewCompile();
	},
	{ deep: true }
);

watch(
	() => presentation_settings.value,
	() => {
		if (isReportMode.value) {
			requestReportPreviewCompile();
		}
	},
	{ deep: true }
);

watch([reportFontFamily, reportFontSizePt], () => {
	if (isReportMode.value) {
		requestReportPreviewCompile();
	}
});

watch(
	() => logo_settings.value.company,
	(newCompany) => {
		logger.info("Logo company changed", newCompany);
		logo_settings.value.image = resolveCompanyLogo(newCompany);
		logger.info("Logo image resolved", logo_settings.value.image);
	}
);

watch(
	() => logo_settings.value.image,
	() => {
		logger.info("Logo image updated, recompiling preview");
		if (isReportMode.value) {
			requestReportPreviewCompile();
		}
	}
);

watch(availableCompanies, () => {
	if (!logo_settings.value.company) return;
	logo_settings.value.image = resolveCompanyLogo(logo_settings.value.company);
});

// No explicit preview events needed: PreviewRenderer/setupWorker reacts to prop changes directly.

onMounted(async () => {
	if (typeof window !== "undefined") {
		const stored = window.localStorage.getItem(OVERRIDES_STORAGE_KEY);
		if (stored !== null) {
			isOverridesExpanded.value = stored === "true";
		}
	}
	hydrateReportStateFromStorage();
	await fetchFonts();
	reportFontSizePt.value =
		parseSize(defaultTypography.fieldValue.fontSize).value || reportFontSizePt.value;
	if (availableFonts.value.length && !availableFonts.value.includes(reportFontFamily.value)) {
		reportFontFamily.value = availableFonts.value[0];
	}
	await initializeData();
	await initializeReportSettings();
	await compileReportPreview();
});

onBeforeUnmount(() => {
	if (reportPreviewDebounceTimer.value) {
		window.clearTimeout(reportPreviewDebounceTimer.value);
		reportPreviewDebounceTimer.value = null;
	}
});

watch(isOverridesExpanded, (next) => {
	if (typeof window === "undefined") return;
	window.localStorage.setItem(OVERRIDES_STORAGE_KEY, String(next));
});

// Generate and open PDF in new tab
async function generatePDF() {
	logger.info("View PDF clicked");
	if (isReportMode.value) {
		await generateReportPdf("view");
		return;
	}
	window.dispatchEvent(
		new CustomEvent("crispy-preview:request-pdf", { detail: { action: "view" } })
	);
}

async function downloadPDF() {
	logger.info("Download PDF clicked");
	if (isReportMode.value) {
		await generateReportPdf("download");
		return;
	}
	window.dispatchEvent(
		new CustomEvent("crispy-preview:request-pdf", { detail: { action: "download" } })
	);
}

async function generateReportPdf(action: "view" | "download") {
	if (!lastReportTypstSource.value) {
		frappe.show_alert({
			message: __("Report preview not ready yet."),
			indicator: "orange",
		});
		return;
	}

	try {
		const result = await compileTypst({
			typst_source: lastReportTypstSource.value,
			output_format: "pdf",
			pdf_standard: pdfStandard.value,
			asset_files: lastReportAssetFiles.value || [],
			chart_svg: lastReportChartSvg.value || null,
		});

		if (!result?.pdf_url && !result?.pdf_data) {
			throw new Error("No PDF data returned");
		}

		let pdfUrl = result.pdf_url as string | undefined;
		if (!pdfUrl && result.pdf_data) {
			const binary = atob(result.pdf_data);
			const bytes = new Uint8Array(binary.length);
			for (let i = 0; i < binary.length; i++) {
				bytes[i] = binary.charCodeAt(i);
			}
			const blob = new Blob([bytes], { type: "application/pdf" });
			pdfUrl = URL.createObjectURL(blob);
			setTimeout(() => URL.revokeObjectURL(pdfUrl as string), 1000);
		}

		if (!pdfUrl) {
			throw new Error("Failed to build PDF URL");
		}

		if (action === "download") {
			const link = document.createElement("a");
			link.href = pdfUrl;
			link.download = `${reportName.value || "report"}.pdf`;
			document.body.appendChild(link);
			link.click();
			document.body.removeChild(link);
			frappe.show_alert({
				message: __("PDF download started."),
				indicator: "green",
			});
		} else {
			window.open(pdfUrl, "_blank");
			frappe.show_alert({
				message: __("PDF opened in a new tab."),
				indicator: "green",
			});
		}
	} catch (error) {
		logger.error("Report PDF generation failed", error);
		frappe.show_alert({
			message: __("Report PDF generation failed."),
			indicator: "red",
		});
	}
}

// Simple readiness check: we consider Typst ready if a prior compile set code in worker
function lastTypstReady() {
	// We can't read lastTypstCode from worker here; rely on layout present and prior refresh
	return Boolean(layout.value);
}

// Expose methods for parent access
defineExpose({
	get_presentation_settings,
	getReportSettings,
	getLayout,
	getLetterhead,
	loadFormatSettings,
	initializeData,
	generatePDF,
	downloadPDF,
});
</script>

<style scoped>
/* Layout */
.crispy-preview-layout {
	display: grid;
	grid-template-columns: 280px 1fr;
	gap: 0;
	background: #f8fafc;
	height: calc(100vh - 110px);
	min-height: 0;
}

/* Settings Pane */
.settings-pane {
	background: white;
	border-right: none;
	padding-right: 12px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.settings-pane__header {
	padding: 16px;
	border-bottom: 1px solid #e5e7eb;
	flex-shrink: 0;
}

.report-columns {
	border: 1px solid #e5e7eb;
	border-radius: 6px;
	padding: 8px;
	max-height: 280px;
	overflow: auto;
}

.report-columns__row {
	display: grid;
	grid-template-columns: 18px 1fr 80px;
	gap: 8px;
	align-items: center;
	padding: 4px 0;
	border-bottom: 1px solid #e5e7eb;
}

.report-columns__row:last-child {
	border-bottom: none;
}

.report-columns__label {
	font-size: 12px;
	color: #111827;
}

.report-columns__width {
	width: 80px;
	padding: 4px 6px;
	font-size: 12px;
	border: 1px solid #d1d5db;
	border-radius: 4px;
}

.settings-pane__header-actions {
	display: flex;
	gap: 6px;
	align-items: center;
}

.settings-pane__help-popover {
	padding: 12px;
	border-radius: 6px;
	border: 1px solid #e5e7eb;
	background: white;
	box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
	max-width: 300px;
}

.settings-pane__help-list {
	margin: 0;
	padding-left: 20px;
	font-size: 13px;
	color: #6b7280;
	line-height: 1.6;
}

.settings-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 16px;
}

.form-layout {
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.settings-pane__section-card {
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	overflow: hidden;
	background: #fff;
}

.settings-pane__section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	cursor: pointer;
	background: #fff;
	border: 0;
	padding: 10px 12px;
	text-align: left;
	color: #334155;
	text-decoration: none;
}

.settings-pane__section-header:hover {
	text-decoration: none;
	background: #f8fafc;
}

.settings-pane__section-content {
	padding: 12px;
	border-top: 1px solid #e2e8f0;
}

.settings-pane__chevron {
	width: 16px;
	height: 16px;
	transition: transform 0.2s ease;
}

.settings-pane__chevron--expanded {
	transform: rotate(-180deg);
}

.settings-pane__toggles {
	display: grid;
	gap: 8px;
}

.settings-pane__toggle {
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 13px;
	color: #334155;
	margin: 0;
}

.settings-pane__report-warning {
	margin: 10px 0 0;
	line-height: 1.4;
}

/* Preview Pane */
.preview-pane {
	background: #f4f5f6;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.preview-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 20px;
}

.typst-preview-container {
	max-width: 900px;
	margin: 0 auto;
}

.preview-placeholder {
	background: white;
	border: 1px solid #d1d8dd;
	border-radius: 4px;
	padding: 60px 40px;
	text-align: center;
	color: #8d99a6;
	font-size: 14px;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Typst page styling (will be populated by setupWorker) */
:global(.typst-page) {
	margin-bottom: 1.5rem;
	box-shadow: 0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2);
	background: white;
}

:global(.typst-page svg) {
	width: 100%;
	height: auto;
	display: block;
}
</style>
