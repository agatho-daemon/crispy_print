<template>
	<div class="crispy-preview-layout">
		<!-- Left Pane: Settings -->
		<div class="settings-pane">
			<div class="section-head settings-pane__header">
				<h4 class="pull-left">Print Settings</h4>
				<div class="pull-right settings-pane__header-actions">
					<button
						type="button"
						class="btn btn-default btn-xs"
						@click="resetFormat"
						title="Reset to saved format"
					>
						Reset
					</button>
					<button
						type="button"
						class="btn btn-default btn-xs"
						popovertarget="preview-settings-help"
						popovertargetaction="toggle"
						title="Toggle help"
						aria-haspopup="dialog"
						aria-controls="preview-settings-help"
					>
						?
					</button>
					<div id="preview-settings-help" popover class="settings-pane__help-popover">
						<ul class="settings-pane__help-list">
							<li>Configure page settings and document options.</li>
							<li>Changes apply immediately to the preview.</li>
						</ul>
					</div>
				</div>
			</div>
			<div class="settings-pane__body">
				<div class="form-layout">
					<div v-if="isReportMode" class="form-group">
						<label class="control-label">Report Format</label>
						<select
							v-model="selectedReportFormat"
							class="form-control"
							@change="onReportFormatChange"
						>
							<option v-if="reportLoading" disabled>Loading formats...</option>
							<option
								v-for="fmt in reportFormats"
								:key="fmt.value"
								:value="fmt.value"
							>
								{{ fmt.label }}
							</option>
						</select>
					</div>

					<div v-if="isReportMode" class="checkbox">
						<label>
							<input v-model="reportIncludeFilters" type="checkbox" />
							Include Filters
						</label>
					</div>

					<div v-if="isReportMode" class="form-section">
						<button
							type="button"
							class="section-head"
							@click="isReportColumnsExpanded = !isReportColumnsExpanded"
						>
							<span>Columns</span>
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
						<div v-if="isReportColumnsExpanded" class="section-body">
							<p
								v-if="reportColumnsState.length === 0"
								class="help-block text-muted small"
							>
								No report columns available.
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
										placeholder="auto"
										:disabled="!reportColumnSelections[col.fieldname].selected"
									/>
								</div>
							</div>
						</div>
					</div>

					<!-- Print Format (doctype source) -->
					<div v-if="!isReportMode" class="form-group">
						<label class="control-label">Print Format</label>
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

					<div class="form-section">
						<button
							type="button"
							class="section-head"
							@click="isOverridesExpanded = !isOverridesExpanded"
						>
							<span>Preview Overrides</span>
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
						<div v-if="isOverridesExpanded" class="section-body">
							<p class="help-block text-muted small">
								Preview-only changes. The saved format is unchanged.
							</p>

							<div class="form-group">
								<label class="control-label">Language</label>
								<select
									v-model="pageSettings.language"
									class="form-control"
									disabled
								>
									<option value="en">English</option>
									<option value="ar">Arabic</option>
									<option value="fr">French</option>
									<option value="de">German</option>
									<option value="es">Spanish</option>
								</select>
								<p class="help-block text-muted small">
									Default language. More languages coming soon.
								</p>
							</div>

							<div v-if="isReportMode" class="form-group">
								<label class="control-label">Font</label>
								<select v-model="reportFontFamily" class="form-control">
									<option v-if="loadingFonts" disabled>Loading fonts...</option>
									<option
										v-for="font in availableFonts"
										:key="font"
										:value="font"
									>
										{{ font }}
									</option>
								</select>
							</div>

							<div v-if="isReportMode" class="form-group">
								<label class="control-label">Font Size (pt)</label>
								<input
									v-model.number="reportFontSizePt"
									type="number"
									min="1"
									step="0.5"
									class="form-control"
								/>
								<p class="help-block text-muted small">
									Applied via #set text(...) before the template.
								</p>
							</div>

							<div class="form-group">
								<label class="control-label">Branding</label>
								<select v-model="brandingMode" class="form-control">
									<option value="none">None</option>
									<option value="letterhead">Letterhead</option>
									<option value="logo">Logo</option>
								</select>
							</div>

							<div v-if="brandingMode === 'letterhead'" class="form-group">
								<label class="control-label">Letter Head</label>
								<select v-model="pageSettings.letterhead" class="form-control">
									<option value="">None</option>
									<option v-if="loadingLetterheads" disabled>
										Loading letterheads...
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

							<div v-if="brandingMode === 'logo'">
								<p class="help-block text-muted small">
									Logo is anchored to top-left using #place().
								</p>
								<div class="form-group">
									<label class="control-label">Company</label>
									<select v-model="logoSettings.company" class="form-control">
										<option value="">Select company</option>
										<option v-if="loadingCompanies" disabled>
											Loading companies...
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
									v-if="logoSettings.company && !logoSettings.image"
									class="help-block text-muted small"
								>
									Selected company has no logo set.
								</p>
								<div class="row">
									<div class="col-xs-12 form-group">
										<label class="control-label text-muted small"
											>Size (mm)</label
										>
										<input
											v-model.number="logoSettings.size"
											type="number"
											class="form-control input-sm"
										/>
									</div>
								</div>
								<div class="row">
									<div class="col-xs-6 form-group">
										<label class="control-label text-muted small"
											>dx (mm)</label
										>
										<input
											v-model.number="logoSettings.dx"
											type="number"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<label class="control-label text-muted small"
											>dy (mm)</label
										>
										<input
											v-model.number="logoSettings.dy"
											type="number"
											class="form-control input-sm"
										/>
									</div>
								</div>
							</div>

							<div v-if="!isReportMode" class="checkbox">
								<label>
									<input v-model="removeQr" type="checkbox" />
									Remove QRCode
								</label>
							</div>

							<div class="form-group">
								<label class="control-label">Page Size</label>
								<select v-model="pageSettings.pageSize" class="form-control">
									<option value="A3">A3 (297 × 420 mm)</option>
									<option value="A4">A4 (210 × 297 mm)</option>
									<option value="A5">A5 (148 × 210 mm)</option>
									<option value="Letter">Letter (8.5 × 11 in)</option>
									<option value="Legal">Legal (8.5 × 14 in)</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">Orientation</label>
								<select v-model="pageSettings.orientation" class="form-control">
									<option value="portrait">Portrait</option>
									<option value="landscape">Landscape</option>
								</select>
							</div>

							<div class="form-group">
								<label class="control-label">Margins (mm)</label>
								<div class="row">
									<div class="col-xs-6 form-group">
										<span class="text-muted small">T</span>
										<input
											v-model.number="pageSettings.margins.top"
											type="number"
											placeholder="Top"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<span class="text-muted small">B</span>
										<input
											v-model.number="pageSettings.margins.bottom"
											type="number"
											placeholder="Bottom"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<span class="text-muted small">L</span>
										<input
											v-model.number="pageSettings.margins.left"
											type="number"
											placeholder="Left"
											class="form-control input-sm"
										/>
									</div>
									<div class="col-xs-6 form-group">
										<span class="text-muted small">R</span>
										<input
											v-model.number="pageSettings.margins.right"
											type="number"
											placeholder="Right"
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
			:format-name="isReportMode ? null : selectedFormat"
			:layout="layout"
			:doc-header="docHeader"
			:doc-footer="docFooter"
			:typst-preamble="typstPreambleEffective"
			:typst-code="typstCode"
			:raw-typst="rawTypst"
			:qr-enabled="qrEnabledEffective"
			:letterhead="letterheadDoc"
			:doc-type="props.doctype || null"
			:doc-name="props.docname || null"
			:page-settings="pageSettingsComputed"
			:change-key="changeKey"
			:watch-data-changes="true"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue";
import {
	getFormatsForDoctype,
	loadFormatData,
	resolveLetterheadDoc,
	type FormatInfo,
} from "../utils/formatLoader";
import {
	defaultPageSettings,
	defaultTypography,
	ensureLogoSettings,
	type PageSettings,
} from "../utils/pageSettings";
import PreviewRenderer from "../components/PreviewRenderer.vue";
import { pickFormatName } from "../utils/formatSelection";
import { useBrandingData } from "../composables/useBrandingData";
import { loadReportState, normalizeReportChartSvg } from "../utils/reportState";
import {
	buildReportFormatOptions,
	normalizeReportColumns,
	type ReportColumn,
	type ReportFormatOption,
} from "./reportPrintSettings";
import { getLogger } from "../logger";
import { fetchTypstFonts, formatPt, parseSize } from "../utils/typstTypography";

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
const isReportMode = computed(() => props.source === "report");
const reportName = computed(() => props.report || "");
const reportFormats = ref<ReportFormatOption[]>([]);
const reportLoading = ref(false);
const selectedReportFormat = ref<string>("");
const reportIncludeFilters = ref(false);
const reportColumnsState = ref<ReportColumn[]>([]);
const reportColumnSelections = ref<Record<string, { selected: boolean; width: string }>>({});
const reportFilters = ref<Record<string, any>>(props.reportFilters || {});
const reportChartSvg = ref<string>(props.reportChartSvg || "");
const isReportColumnsExpanded = ref(true);
const reportPreviewLoading = ref(false);
const reportPreviewPending = ref(false);
const reportBrandingInitialized = ref(false);
const reportOrientationInitialized = ref(false);
const reportMarginsInitialized = ref(false);
const lastReportTypstSource = ref<string | null>(null);
const lastReportChartSvg = ref<string>("");
const availableFonts = ref<string[]>([]);
const loadingFonts = ref(false);
const reportFontFamily = ref("Inter 18pt");
const reportFontSizePt = ref(10);

// Settings state (single in-memory copy; PP does not persist)
const pageSettings = ref<PageSettings>({ ...defaultPageSettings });

const layout = ref<any>(null);
const loading = ref(true);
const docHeader = ref("");
const docFooter = ref("");
const typstPreamble = ref("");
const typstCode = ref("");
const rawTypst = ref(false);
const removeQr = ref(false);
const letterheadDoc = ref<any | null>(null);
const changeKey = ref(0);
const OVERRIDES_STORAGE_KEY = "crispy-print:pp:preview-overrides-expanded";
const isOverridesExpanded = ref(false);
const qrEnabledEffective = computed(() => {
	const pageQrEnabled = pageSettings.value.qr?.enabled;
	if (typeof pageQrEnabled === "boolean") {
		return pageQrEnabled && !removeQr.value;
	}
	return false;
});
const logoSettings = computed(() => ensureLogoSettings(pageSettings.value));

const brandingMode = computed<string>({
	get: () => {
		const mode = pageSettings.value.brandingMode;
		if (mode === "letterhead" || mode === "logo" || mode === "none") {
			return mode;
		}
		if (pageSettings.value.logo?.company || pageSettings.value.logo?.image) {
			return "logo";
		}
		if (pageSettings.value.letterhead) {
			return "letterhead";
		}
		return "none";
	},
	set: (value) => {
		pageSettings.value.brandingMode = value as "letterhead" | "logo" | "none";
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

const typstPreambleEffective = computed(() => {
	if (!isReportMode.value) return typstPreamble.value;
	const prefix = reportFontPreamble.value;
	if (!prefix) return typstPreamble.value;
	const base = typstPreamble.value || "";
	return base ? `${prefix}\n${base}` : prefix;
});

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
			args: { report: reportName.value },
		});
		const { options, defaultValue } = buildReportFormatOptions(response?.message);
		reportFormats.value = options;

		if (defaultValue) {
			selectedReportFormat.value = defaultValue;
			await loadFormatSettings(defaultValue);
		}

		if (!reportBrandingInitialized.value) {
			pageSettings.value.brandingMode = "none";
			reportBrandingInitialized.value = true;
		}

		if (!reportOrientationInitialized.value) {
			pageSettings.value.orientation = "landscape";
			reportOrientationInitialized.value = true;
		}

		if (!reportMarginsInitialized.value) {
			pageSettings.value.margins = { top: 20, bottom: 10, left: 7, right: 7 };
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
	await compileReportPreview();
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
	} catch (error) {
		logger.error("Failed to load report columns", error);
	}
}

async function compileReportPreview() {
	if (!isReportMode.value) return;
	if (!reportName.value || !selectedReportFormat.value) return;
	if (reportPreviewLoading.value) {
		reportPreviewPending.value = true;
		return;
	}

	try {
		reportPreviewLoading.value = true;
		const chartSvgPayload = normalizeReportChartSvg(reportChartSvg.value || "");
		const letterheadImage = letterheadDoc.value?.image || null;
		const logoImage = logoSettings.value.image || null;
		logger.info("Report preview compile requested with letterhead", letterheadDoc.value);
		logger.info("Report preview compile requested with letterhead image", letterheadImage);
		logger.info(
			"Report preview compile requested with page settings",
			pageSettingsComputed.value
		);
		const sourceResponse = await frappe.call({
			method: "crispy_print.api.v1.get_report_typst_source",
			args: {
				report: reportName.value,
				format_name: selectedReportFormat.value,
				filters: reportFilters.value || {},
				column_config: reportColumnConfig.value,
				include_filters: reportIncludeFilters.value ? 1 : 0,
				orientation: pageSettings.value.orientation,
				page_settings: pageSettingsComputed.value,
				chart_svg: chartSvgPayload || null,
				typst_preamble_override: reportFontPreamble.value,
				letterhead_image: letterheadImage,
				limit: 50,
			},
		});

		const typstSource = sourceResponse?.message;
		if (!typstSource) {
			throw new Error("No Typst source returned");
		}
		lastReportTypstSource.value = typstSource;
		lastReportChartSvg.value = chartSvgPayload || "";

		const compileResponse = await frappe.call({
			method: "crispy_print.api.v1.compile_typst",
			args: {
				typst_source: typstSource,
				output_format: "svg",
				letterhead_image: letterheadImage,
				logo_image: logoImage,
				chart_svg: chartSvgPayload || null,
			},
		});

		const result = compileResponse?.message;
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
		if (reportPreviewPending.value) {
			reportPreviewPending.value = false;
			compileReportPreview();
		}
	}
}

// Explicit invalidation for preview recompilation (avoids deep watches inside PreviewRenderer).
watch(
	() => [
		layout.value,
		pageSettings.value,
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
		const formats = await getFormatsForDoctype(props.doctype);

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
		} else {
			logger.warn("No formats available for doctype", props.doctype);
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

		const data = await loadFormatData(formatName);

		if (!data) {
			throw new Error("Failed to load format data");
		}

		// Overwrite in-memory page settings (ephemeral)
		pageSettings.value = data.pageSettings || { ...defaultPageSettings };
		if (data.pageSettings?.qr?.enabled === undefined && pageSettings.value.qr) {
			delete (pageSettings.value.qr as any).enabled;
		}

		// Preload letterhead data if the format has one set
		letterheadDoc.value = await resolveLetterheadDoc(pageSettings.value.letterhead);

		// Store layout
		layout.value = data.layout;
		docHeader.value = data.formatDoc.doc_header || "";
		docFooter.value = data.formatDoc.doc_footer || "";
		typstPreamble.value = data.formatDoc.typst_preamble || "";
		typstCode.value = data.formatDoc.typst_code || "";
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

// Handle format change
async function onFormatChange() {
	await loadFormatSettings(selectedFormat.value);
}

async function resetFormat() {
	if (!selectedFormat.value) return;
	await loadFormatSettings(selectedFormat.value);
}

// Expose settings getters for external access
const getPageSettings = () => ({
	...pageSettings.value,
	letterheadImage: letterheadDoc.value?.image || null, // Include image path for change detection
});

const pageSettingsComputed = computed(() => getPageSettings());

const getReportSettings = () => ({
	report: reportName.value,
	format: selectedReportFormat.value,
	orientation: pageSettings.value.orientation,
	includeFilters: reportIncludeFilters.value ? 1 : 0,
	columnConfig: reportColumnConfig.value,
	filters: reportFilters.value,
});

function triggerRefresh() {
	// Manual refresh (refetch + recompile) for crispy-print page.
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
	() => pageSettings.value.letterhead,
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
			compileReportPreview();
		}
	}
);

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

watch(
	() => [
		selectedReportFormat.value,
		reportColumnConfig.value,
		reportFilters.value,
		reportIncludeFilters.value,
	],
	() => {
		compileReportPreview();
	},
	{ deep: true }
);

watch(
	() => pageSettings.value,
	() => {
		if (isReportMode.value) {
			compileReportPreview();
		}
	},
	{ deep: true }
);

watch([reportFontFamily, reportFontSizePt], () => {
	if (isReportMode.value) {
		compileReportPreview();
	}
});

watch(
	() => logoSettings.value.company,
	(newCompany) => {
		logger.info("Logo company changed", newCompany);
		logoSettings.value.image = resolveCompanyLogo(newCompany);
		logger.info("Logo image resolved", logoSettings.value.image);
	}
);

watch(
	() => logoSettings.value.image,
	() => {
		logger.info("Logo image updated, recompiling preview");
		if (isReportMode.value) {
			compileReportPreview();
		}
	}
);

watch(availableCompanies, () => {
	if (!logoSettings.value.company) return;
	logoSettings.value.image = resolveCompanyLogo(logoSettings.value.company);
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
		const letterheadImage = letterheadDoc.value?.image || null;
		const logoImage = logoSettings.value.image || null;
		const compileResponse = await frappe.call({
			method: "crispy_print.api.v1.compile_typst",
			args: {
				typst_source: lastReportTypstSource.value,
				output_format: "pdf",
				letterhead_image: letterheadImage,
				logo_image: logoImage,
				chart_svg: lastReportChartSvg.value || null,
			},
		});

		const result = compileResponse?.message;
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
	getPageSettings,
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

.settings-pane .section-head {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	cursor: pointer;
	background: transparent;
	border: 0;
	padding: 8px 0;
	text-align: left;
}

.settings-pane .section-body {
	padding: 8px 0 12px;
}

.settings-pane .form-group {
	float: none;
	width: 100%;
}

.settings-pane__chevron {
	width: 16px;
	height: 16px;
	transition: transform 0.2s ease;
}

.settings-pane__chevron--expanded {
	transform: rotate(-180deg);
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
