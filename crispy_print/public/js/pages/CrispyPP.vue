<template>
	<div class="crispy-preview-layout">
		<!-- Left Pane: Settings -->
		<div class="settings-pane">
			<div class="settings-pane__body">
				<div class="form-layout">
					<SettingsSection
						v-if="isReportMode"
						v-model="isReportTemplateExpanded"
						:title="__('Report Template')"
						content-border
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
								<option v-for="font in availableFonts" :key="font" :value="font">
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
							<button
								v-if="reportPreviewNeedsRefresh"
								type="button"
								class="btn btn-xs btn-default"
								@click="runReportPreviewAgain"
							>
								{{ __("Run Preview again") }}
							</button>
						</p>
					</SettingsSection>

					<SettingsSection
						v-if="isReportMode"
						v-model="isReportColumnsExpanded"
						:title="__('Columns')"
						content-border
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
					</SettingsSection>

					<div v-if="!isReportMode" class="settings-pane__template-section card">
						<div class="settings-pane__template-content card-body">
							<div class="form-group">
								<div class="settings-pane__template-head">
									<label class="control-label">{{ __("Template") }}</label>
									<button
										type="button"
										class="btn btn-default btn-xs settings-pane__help-button"
										popovertarget="preview-template-help"
										popovertargetaction="toggle"
										:title="__('Toggle help')"
										aria-haspopup="dialog"
										aria-controls="preview-template-help"
									>
										?
									</button>
									<div
										id="preview-template-help"
										popover
										class="settings-pane__help-popover"
									>
										<ul class="settings-pane__help-list">
											<li>
												{{
													__(
														"Select an approved template for this preview."
													)
												}}
											</li>
											<li>
												{{
													__(
														"Runtime previews use frozen template snapshots."
													)
												}}
											</li>
										</ul>
									</div>
								</div>
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
										{{ templateOptionLabel(template) }}
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
								<p
									v-if="activeTemplateLoading"
									class="help-block text-muted small"
								>
									{{ __("Loading template snapshot...") }}
								</p>
							</div>
						</div>
					</div>

					<SettingsSection
						v-if="isReportMode && !isBrandingProfileDriven"
						v-model="isBrandingExpanded"
						:title="__('Branding')"
						content-border
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
								<option v-for="lh in availableLetterheads" :key="lh" :value="lh">
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
										{{ company.name }}
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
										__("Anchor")
									}}</label>
									<select
										v-model="logo_settings.anchor"
										class="form-control input-sm"
									>
										<option value="left">{{ __("Left (physical)") }}</option>
										<option value="right">{{ __("Right (physical)") }}</option>
										<option value="start">{{ __("Start") }}</option>
										<option value="end">{{ __("End") }}</option>
									</select>
								</div>
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
					</SettingsSection>
					<SettingsSection
						v-if="isReportMode && !isBrandingProfileDriven"
						v-model="isPresentationSettingsExpanded"
						:title="__('Presentation Settings')"
						content-border
					>
						<div class="form-group">
							<label class="control-label">{{ __("Page Size") }}</label>
							<select v-model="presentation_settings.page.size" class="form-control">
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
										v-model.number="presentation_settings.page.margins.bottom"
										type="number"
										:placeholder="__('Bottom')"
										class="form-control input-sm"
									/>
								</div>
								<div class="col-xs-6 form-group">
									<span class="text-muted small">{{ __("L") }}</span>
									<input
										v-model.number="presentation_settings.page.margins.left"
										type="number"
										:placeholder="__('Left')"
										class="form-control input-sm"
									/>
								</div>
								<div class="col-xs-6 form-group">
									<span class="text-muted small">{{ __("R") }}</span>
									<input
										v-model.number="presentation_settings.page.margins.right"
										type="number"
										:placeholder="__('Right')"
										class="form-control input-sm"
									/>
								</div>
							</div>
						</div>
					</SettingsSection>
				</div>
			</div>
		</div>

		<!-- Right Pane: Preview -->
		<div v-if="runtimeTemplateMessage" class="runtime-template-warning">
			{{ runtimeTemplateMessage }}
		</div>
		<PreviewRenderer
			v-else
			:format-name="previewFormatName"
			:layout="layout"
			:doc-header="docHeader"
			:doc-footer="docFooter"
			:typst-preamble="typstPreambleEffective"
			:typst-code="typstCode"
			:pdf-standard="pdfStandard"
			:raw-typst="rawTypst"
			:print-behavior="printBehavior"
			:qr-enabled="qrEnabledEffective"
			:letterhead="letterheadDoc"
			:doc-type="props.doctype || null"
			:doc-name="props.docname || null"
			:presentation_settings="presentation_settings_computed"
			:preview-revision="previewRevision"
			:report-pdf-bytes="reportPdfBytes"
			:report-pdf-revision="reportPdfRevision"
			:watch-data-changes="true"
			:zoom-mode="runtimeZoomMode"
			:zoom-percent="runtimeZoomPercent"
			:issue-pdf-snapshot="recordIssuedDocumentSnapshot"
			@update:zoom-mode="(value) => (runtimeZoomMode = value)"
			@update:zoom-percent="(value) => (runtimeZoomPercent = value)"
		>
			<template #toolbar-actions>
				<div class="preview-diagnostics-action">
					<button
						type="button"
						class="btn btn-default btn-xs preview-diagnostics-button"
						:title="__('Show preview diagnostics')"
						@click.stop.prevent="diagnosticsOpen = !diagnosticsOpen"
					>
						{{ __("Diagnostics") }}
					</button>
					<PreviewDiagnosticsDrawer :open="diagnosticsOpen" :items="diagnosticItems" />
				</div>
			</template>
		</PreviewRenderer>
	</div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount, onMounted, watch, computed } from "vue";
import { loadFormatData, parseCrispyFormatDoc, resolveLetterheadDoc } from "../utils/formatLoader";
import {
	default_presentation_settings,
	defaultTypography,
	ensure_logo_settings,
	merge_presentation_settings,
	type PresentationSettings,
} from "../utils/presentation_settings";
import { resolve_effective_presentation_settings } from "../utils/effectivePresentationSettings";
import PreviewRenderer from "../components/PreviewRenderer.vue";
import PreviewDiagnosticsDrawer, {
	type PreviewDiagnosticItem,
} from "../components/PreviewDiagnosticsDrawer.vue";
import SettingsSection from "../components/SettingsSection.vue";
import { useBrandingData } from "../composables/useBrandingData";
import { loadReportState, normalizeReportChartSvg } from "../utils/reportState";
import { dispatchCrispyPreviewSource, dispatchCrispyPreviewStatus } from "../utils/events";
import { CrispyPreviewEvents, type CrispyPreviewStatusDetail } from "../utils/events";
import {
	buildReportFormatOptions,
	getReportColumnDefault,
	normalizeReportColumns,
	serializeReportPreviewIntent,
	type ReportColumn,
	type ReportFormatOption,
} from "./reportPrintSettings";
import { getLogger } from "../logger";
import { fetchTypstFonts, formatPt, parseSize } from "../utils/typstTypography";
import { escapeTypstString } from "../utils/typstEscape";
import { __ } from "../utils/i18n";
import { decodePdfData } from "../utils/pdfBytes";
import {
	compileReportPreview as compileReportPreviewRequest,
	createIssuedDocumentSnapshot,
	getActiveCrispyTemplatesForDocument,
	getResolvedCrispyTemplateForDocument,
	getSampleReportData,
	type ActiveCrispyTemplateOption,
	type ResolvedCrispyTemplate,
} from "../api/crispy";
import type { TypstPdfReadyContext } from "../typst/setupWorker";
import { printPdfBlob } from "../typst/workerPdf";

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

const {
	availableLetterheads,
	loadingLetterheads,
	availableCompanies,
	loadingCompanies,
	resolveCompanyLogo,
	fetchLetterheads,
	fetchCompanies,
} = useBrandingData();
const activeTemplates = ref<ActiveCrispyTemplateOption[]>([]);
const selectedTemplate = ref("");
const templatesLoading = ref(false);
const activeTemplateLoading = ref(false);
const activeTemplateSnapshot = ref<ResolvedCrispyTemplate | null>(null);
const issuedSnapshotKeys = new Set<string>();
const diagnosticsOpen = ref(false);
const previewStatus = ref<CrispyPreviewStatusDetail>({ status: "fetching" });
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
const reportPdfBytes = ref<Uint8Array | null>(null);
const reportPdfRevision = ref(0);
const reportTruncationWarning = ref("");
const reportPreviewNeedsRefresh = ref(false);
const REPORT_PREVIEW_DEBOUNCE_MS = 250;
const reportPreviewDebounceTimer = ref<number | null>(null);
const reportPreviewIntentSeq = ref(0);
const reportPreviewSnapshotId = ref("");
const reportPreviewDataKey = ref("");
const reportPreviewTabId =
	globalThis.crypto?.randomUUID?.() ||
	`crispy-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
let lastRequestedReportPreviewKey = "";
const reportBrandingInitialized = ref(false);
const reportOrientationInitialized = ref(false);
const reportMarginsInitialized = ref(false);
const availableFonts = ref<string[]>([]);
const loadingFonts = ref(false);
const reportFontFamily = ref("Inter");
const reportFontSizePt = ref(10);

function getPreviewCompany(): string | null {
	return (
		presentation_settings.value?.branding?.company ||
		(props.reportFilters?.company ? String(props.reportFilters.company) : "") ||
		null
	);
}

function fetchScopedLetterheads() {
	return fetchLetterheads({
		company: getPreviewCompany(),
		include_current: presentation_settings.value.branding?.letterhead || null,
	});
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
const selectedTemplateInfo = computed(
	() =>
		activeTemplates.value.find((template) => template.name === selectedTemplate.value) || null
);
const diagnosticItems = computed<PreviewDiagnosticItem[]>(() => {
	const template = activeTemplateSnapshot.value;
	const renderPayload = template?.render_payload || {};
	return [
		{ label: __("Status"), value: previewStatus.value.status },
		{ label: __("Format"), value: renderPayload.name || template?.source_crispy_format },
		{ label: __("Template"), value: template?.template_id || template?.name },
		{ label: __("Template Version"), value: template?.version },
		{
			label: __("Company"),
			value: template?.effective_company || template?.company || getPreviewCompany(),
		},
		{
			label: __("Branding Profile"),
			value:
				template?.source_branding_profile ||
				presentation_settings.value?.branding?.profile ||
				__("Custom"),
		},
		{
			label: __("PDF Standard"),
			value: pdfStandard.value || template?.pdf_standard || "PDF/A-2u",
		},
		{
			label: __("Typst Version"),
			value: previewStatus.value.typstVersion || template?.typst_version || null,
		},
		{ label: __("Pages"), value: previewStatus.value.pageCount || null },
		{
			label: __("Render Time"),
			value:
				typeof previewStatus.value.renderMs === "number"
					? `${previewStatus.value.renderMs} ms`
					: null,
		},
		{ label: __("Cache Hit"), value: previewStatus.value.cacheHit },
		{ label: __("Raw Typst"), value: rawTypst.value },
	];
});
const previewFormatName = computed(() => {
	if (isReportMode.value) return null;
	return (
		activeTemplateSnapshot.value?.source_crispy_format ||
		activeTemplateSnapshot.value?.name ||
		null
	);
});
const runtimeTemplateMessage = computed(() => {
	if (isReportMode.value) return "";
	if (loading.value || templatesLoading.value || activeTemplateLoading.value) return "";
	if (activeTemplateSnapshot.value) return "";
	return __("No approved Crispy Template is available for this document context.");
});

function templateOptionLabel(template: ActiveCrispyTemplateOption): string {
	if (template.template_id) return template.template_id;
	return template.template_name || template.name || "";
}

const layout = ref<any>(null);
const loading = ref(true);
const docHeader = ref("");
const docFooter = ref("");
const typstPreamble = ref("");
const typstCode = ref("");
const pdfStandard = ref("PDF/A-2u");
const rawTypst = ref(false);
const printBehavior = ref({
	compact_item_print: 0,
	print_uom_after_quantity: 0,
	print_taxes_with_zero_amount: 0,
});
const removeQr = ref(false);
const letterheadDoc = ref<any | null>(null);
const previewRevision = ref(0);
const runtimeZoomMode = ref<"fit" | "manual">("fit");
const runtimeZoomPercent = ref(100);
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
		next[col.fieldname] = existing || getReportColumnDefault(reportName.value, col.fieldname);
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

		await fetchScopedLetterheads();
		await fetchCompanies({ include_current: getPreviewCompany() });
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

async function compileCurrentReportPreview() {
	lastRequestedReportPreviewKey = getReportPreviewRequestKey();
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
	const requestKey = getReportPreviewRequestKey();
	if (requestKey === lastRequestedReportPreviewKey) return;
	lastRequestedReportPreviewKey = requestKey;

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

function getReportPreviewRequestKey(): string {
	return serializeReportPreviewIntent([
		reportName.value,
		selectedReportFormat.value,
		reportFilters.value,
		reportColumnConfig.value,
		reportIncludeFilters.value,
		reportShowSummary.value,
		reportShowTotalRow.value,
		reportShowChart.value,
		reportShowChart.value ? normalizeReportChartSvg(reportChartSvg.value || "") : "",
		presentation_settings_computed.value,
		letterheadDoc.value?.image || "",
		logo_settings.value.image || "",
		reportFontFamily.value,
		reportFontSizePt.value,
		buildReportTypstCodeOverride(),
		pdfStandard.value,
	]);
}

function getReportDataRequestKey(): string {
	return serializeReportPreviewIntent([reportName.value, reportFilters.value || {}]);
}

async function ensureReportPreviewSnapshot(): Promise<string> {
	const dataKey = getReportDataRequestKey();
	if (reportPreviewSnapshotId.value && reportPreviewDataKey.value === dataKey) {
		return reportPreviewSnapshotId.value;
	}
	const previewData = await getSampleReportData({
		report: reportName.value,
		filters: reportFilters.value || {},
		limit: 0,
		store_snapshot: 1,
		preview_tab_id: reportPreviewTabId,
	});
	const snapshotId = String(previewData?.preview_snapshot_id || "");
	if (!snapshotId) throw new Error("Report preview snapshot was not created");
	reportPreviewSnapshotId.value = snapshotId;
	reportPreviewDataKey.value = dataKey;
	return snapshotId;
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
		dispatchCrispyPreviewStatus({ status: "compiling" });
		reportTruncationWarning.value = "";
		reportPreviewNeedsRefresh.value = false;
		const previewSnapshotId = await ensureReportPreviewSnapshot();
		if (intentSeq !== reportPreviewIntentSeq.value) return;
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
		logger.debug("Report preview compile requested", {
			intentSeq,
			format: selectedReportFormat.value,
			hasLetterhead: Boolean(letterhead_image),
			hasLogo: Boolean(logoImage),
		});
		const compileArgs = {
			report: reportName.value,
			format_name: selectedReportFormat.value,
			filters: reportFilters.value || {},
			preview_snapshot_id: previewSnapshotId,
			preview_tab_id: reportPreviewTabId,
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
			limit: 0,
			asset_files: brandingAssetFiles,
			pdf_standard: pdfStandard.value || null,
		};
		const result = await compileReportPreviewRequest(compileArgs);

		// Ignore stale response if a newer compile intent exists.
		if (intentSeq !== reportPreviewIntentSeq.value) return;

		const typstSource = result?.typst_source || "";
		const truncation = result?.truncation || null;
		if (!typstSource) {
			throw new Error("No Typst source returned");
		}
		if (truncation?.is_truncated) {
			const originalRows = Number(truncation?.rows?.original || 0);
			const returnedRows = Number(truncation?.rows?.returned || 0);
			reportTruncationWarning.value = __(
				"Preview truncated to {0} rows (from {1}). PDF output may also be limited.",
				[String(returnedRows), String(originalRows)]
			);
		}
		dispatchCrispyPreviewSource({ source: typstSource });

		if (result?.success) {
			const bytes = decodePdfData(result.pdf_data);
			if (!bytes.byteLength) throw new Error("Report preview returned an empty PDF");
			reportPdfBytes.value = bytes;
			reportPdfRevision.value += 1;
		}
	} catch (error) {
		logger.error("Report preview failed", error);
		const errorMessage = String((error as any)?.message || error || "");
		if (/Report preview (?:data has expired|access has changed)/i.test(errorMessage)) {
			reportPreviewSnapshotId.value = "";
			reportPreviewDataKey.value = "";
			reportPreviewNeedsRefresh.value = true;
			reportTruncationWarning.value = __(
				"Report preview access expired. Run Preview again."
			);
		}
		frappe.show_alert({
			message: reportPreviewNeedsRefresh.value
				? __("Report preview access expired. Run Preview again.")
				: __("Report preview failed."),
			indicator: "red",
		});
	} finally {
		reportPreviewLoading.value = false;
		if (reportPreviewPending.value || intentSeq !== reportPreviewIntentSeq.value) {
			reportPreviewPending.value = false;
			if (reportPreviewDebounceTimer.value) {
				window.clearTimeout(reportPreviewDebounceTimer.value);
				reportPreviewDebounceTimer.value = null;
			}
			void compileReportPreviewForIntent(reportPreviewIntentSeq.value);
		}
	}
}

function runReportPreviewAgain() {
	reportPreviewNeedsRefresh.value = false;
	reportTruncationWarning.value = "";
	reportPreviewSnapshotId.value = "";
	reportPreviewDataKey.value = "";
	void compileCurrentReportPreview();
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
		previewRevision.value++;
	},
	{ deep: true }
);

// Initialize: document runtime uses approved frozen templates only.
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
		await fetchScopedLetterheads();
		await fetchCompanies({ include_current: getPreviewCompany() });
		await loadActiveTemplates();
		await loadSelectedActiveTemplate();
		loading.value = false;
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
		printBehavior.value = {
			compact_item_print: data.formatDoc.compact_item_print ? 1 : 0,
			print_uom_after_quantity: data.formatDoc.print_uom_after_quantity ? 1 : 0,
			print_taxes_with_zero_amount: data.formatDoc.print_taxes_with_zero_amount ? 1 : 0,
		};

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
		const renderPayload = snapshot.render_payload || {};
		const parsed = parseCrispyFormatDoc({
			name: renderPayload.name || snapshot.source_crispy_format || snapshot.name,
			doc_type: renderPayload.doc_type || snapshot.source_doctype || props.doctype,
			crispy_format_type: renderPayload.crispy_format_type || snapshot.crispy_format_type,
			company: renderPayload.company || snapshot.company || "",
			layout_json: renderPayload.layout_json || snapshot.layout_json || "",
			presentation_settings:
				renderPayload.presentation_settings || snapshot.presentation_settings || "",
			doc_header: renderPayload.doc_header || snapshot.doc_header || "",
			doc_footer: renderPayload.doc_footer || snapshot.doc_footer || "",
			typst_preamble: renderPayload.typst_preamble || snapshot.typst_preamble || "",
			typst_code: renderPayload.typst_code || snapshot.typst_code || "",
			pdf_standard: renderPayload.pdf_standard || snapshot.pdf_standard || "PDF/A-2u",
			raw_typst: renderPayload.raw_typst ?? (snapshot.raw_typst ? 1 : 0),
			effective_company:
				renderPayload.effective_company ||
				snapshot.effective_company ||
				snapshot.company ||
				null,
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
		docHeader.value = renderPayload.doc_header || snapshot.doc_header || "";
		docFooter.value = renderPayload.doc_footer || snapshot.doc_footer || "";
		typstPreamble.value = renderPayload.typst_preamble || snapshot.typst_preamble || "";
		typstCode.value = renderPayload.typst_code || snapshot.typst_code || "";
		pdfStandard.value = renderPayload.pdf_standard || snapshot.pdf_standard || "PDF/A-2u";
		rawTypst.value = Boolean(renderPayload.raw_typst ?? snapshot.raw_typst);
		printBehavior.value = {
			compact_item_print:
				renderPayload.compact_item_print || snapshot.compact_item_print ? 1 : 0,
			print_uom_after_quantity:
				renderPayload.print_uom_after_quantity || snapshot.print_uom_after_quantity
					? 1
					: 0,
			print_taxes_with_zero_amount:
				renderPayload.print_taxes_with_zero_amount || snapshot.print_taxes_with_zero_amount
					? 1
					: 0,
		};
	} catch (error) {
		logger.error("Error loading active Crispy Template", error);
		activeTemplateSnapshot.value = null;
		frappe.show_alert({
			message: __("Failed to load active template"),
			indicator: "red",
		});
	} finally {
		activeTemplateLoading.value = false;
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
	async () => {
		await refreshEffectivePresentationSettings();
		if (isReportMode.value) {
			requestReportPreviewCompile();
		}
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

watch(selectedTemplate, async () => {
	await loadSelectedActiveTemplate();
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
		fetchScopedLetterheads();
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

onMounted(async () => {
	window.addEventListener(CrispyPreviewEvents.Status, onPreviewStatus);
	hydrateReportStateFromStorage();
	await fetchFonts();
	reportFontSizePt.value =
		parseSize(defaultTypography.fieldValue.fontSize).value || reportFontSizePt.value;
	if (availableFonts.value.length && !availableFonts.value.includes(reportFontFamily.value)) {
		reportFontFamily.value = availableFonts.value[0];
	}
	await initializeData();
	await initializeReportSettings();
	await compileCurrentReportPreview();
});

onBeforeUnmount(() => {
	window.removeEventListener(CrispyPreviewEvents.Status, onPreviewStatus);
	if (reportPreviewDebounceTimer.value) {
		window.clearTimeout(reportPreviewDebounceTimer.value);
		reportPreviewDebounceTimer.value = null;
	}
});

function onPreviewStatus(event: Event) {
	const detail = (event as CustomEvent<CrispyPreviewStatusDetail>).detail;
	if (!detail) return;
	previewStatus.value = detail;
}

function hashTypstSource(source: string): string {
	let hash = 5381;
	for (let i = 0; i < source.length; i += 1) {
		hash = (hash * 33) ^ source.charCodeAt(i);
	}
	return (hash >>> 0).toString(16);
}

async function recordIssuedDocumentSnapshot(context: TypstPdfReadyContext) {
	if (isReportMode.value) return;
	if (!props.doctype || !props.docname || !context.typstSource) return;

	const templateName = activeTemplateSnapshot.value?.name || selectedTemplate.value;
	if (!templateName) return;

	const snapshotKey = [
		props.doctype,
		props.docname,
		templateName,
		hashTypstSource(context.typstSource),
	].join("\u001f");
	if (issuedSnapshotKeys.has(snapshotKey)) return;

	const issuedDocument = await createIssuedDocumentSnapshot({
		source_doctype: props.doctype,
		source_docname: props.docname,
		crispy_format:
			activeTemplateSnapshot.value?.source_crispy_format || previewFormatName.value,
		crispy_template: templateName,
		typst_source: context.typstSource,
	});
	issuedSnapshotKeys.add(snapshotKey);

	frappe.show_alert({
		message: __("Issued document snapshot recorded: {0}", [issuedDocument.name]),
		indicator: "green",
	});
}

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

async function printPDF() {
	logger.info("Print PDF clicked");
	if (!isReportMode.value) {
		window.dispatchEvent(
			new CustomEvent("crispy-preview:request-pdf", { detail: { action: "print" } })
		);
		return;
	}
	if (!reportPdfBytes.value?.byteLength) {
		frappe.show_alert({
			message: __("Report preview not ready yet."),
			indicator: "orange",
		});
		return;
	}

	const blob = new Blob([reportPdfBytes.value.slice()], { type: "application/pdf" });
	const printOpened = printPdfBlob(blob, {
		onPrint: () => {
			frappe.show_alert({
				message: __("Print dialog opened."),
				indicator: "green",
			});
		},
		onError: (error) => {
			logger.error("Report printing failed", error);
			frappe.show_alert({
				message: __("Report printing failed."),
				indicator: "red",
			});
		},
	});
	if (!printOpened) {
		frappe.show_alert({
			message: __("Report printing was blocked by the browser."),
			indicator: "orange",
		});
	}
}

async function generateReportPdf(action: "view" | "download") {
	if (!reportPdfBytes.value?.byteLength) {
		frappe.show_alert({
			message: __("Report preview not ready yet."),
			indicator: "orange",
		});
		return;
	}

	try {
		const blob = new Blob([reportPdfBytes.value.slice()], { type: "application/pdf" });
		const pdfUrl = URL.createObjectURL(blob);

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
		window.setTimeout(() => URL.revokeObjectURL(pdfUrl), 60_000);
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
	printPDF,
});
</script>

<style scoped>
/* Layout */
.crispy-preview-layout {
	position: relative;
	display: grid;
	grid-template-columns: 280px 1fr;
	gap: 0;
	background: #f8fafc;
	height: calc(100vh - 110px);
	min-height: 0;
}

.preview-diagnostics-action {
	position: relative;
	flex: 0 0 auto;
}

/* Settings Pane */
.settings-pane {
	background: white;
	border-inline-end: none;
	padding-inline-end: 12px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
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
	padding-inline-start: 20px;
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

.settings-pane__template-section {
	border: 0;
	box-shadow: none;
	background: transparent;
}

.settings-pane__template-content {
	padding: 0;
}

.settings-pane__template-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
	margin-bottom: 10px;
}

.settings-pane__template-head .control-label {
	margin-bottom: 0;
	font-size: 18px;
	font-weight: 700;
	color: #111827;
}

.settings-pane__help-button {
	flex: 0 0 auto;
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

.runtime-template-warning {
	align-self: start;
	margin: 24px;
	padding: 12px 14px;
	border: 1px solid #f59e0b;
	border-radius: 6px;
	background: #fffbeb;
	color: #92400e;
	font-size: 13px;
	line-height: 1.5;
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
