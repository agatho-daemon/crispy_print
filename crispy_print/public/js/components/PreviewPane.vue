<template>
	<PreviewRenderer
		:format-name="store.formatName.value"
		:layout="store.layout.value"
		:doc-header="store.docHeader.value"
		:doc-footer="store.docFooter.value"
		:typst-preamble="store.typstPreamble.value"
		:typst-code="store.typstCode.value"
		:typst-blocks="store.typstBlocks?.value || []"
		:pdf-standard="store.crispyFormat.value?.pdf_standard || 'PDF/A-2u'"
		:raw-typst="store.rawTypst.value"
		:print-behavior="{
			compact_item_print: store.crispyFormat.value?.compact_item_print ? 1 : 0,
			print_uom_after_quantity: store.crispyFormat.value?.print_uom_after_quantity ? 1 : 0,
			print_taxes_with_zero_amount: store.crispyFormat.value?.print_taxes_with_zero_amount
				? 1
				: 0,
		}"
		:qr-enabled="qrEnabled"
		:letterhead="store.letterhead.value"
		:doc-type="store.docType.value"
		:doc-name="null"
		:presentation_settings="
			store.effective_presentation_settings?.value || store.presentation_settings.value
		"
		:preview-revision="store.previewRevision.value"
		:watch-data-changes="!isReportMode"
		:zoom-mode="zoomMode"
		:zoom-percent="zoomPercent"
		@update:zoom-mode="(value) => emit('update:zoomMode', value)"
		@update:zoom-percent="(value) => emit('update:zoomPercent', value)"
	>
		<template #menu>
			<div class="section-head preview-pane__header">
				<div class="section-head-content preview-pane__header-row">
					<h3 class="section-title preview-pane__title">{{ __("Preview") }}</h3>
					<div class="preview-pane__spacer"></div>
					<div
						class="preview-mode-toggle"
						role="group"
						:aria-label="__('Preview focus')"
					>
						<button
							v-for="mode in previewModes"
							:key="mode.value"
							type="button"
							class="btn btn-default btn-xs preview-mode-toggle__button"
							:class="{ 'is-active': previewMode === mode.value }"
							:title="mode.title"
							:aria-pressed="previewMode === mode.value"
							@click="emit('update:previewMode', mode.value)"
						>
							{{ mode.label }}
						</button>
					</div>
					<div class="preview-pane__help">
						<button
							type="button"
							class="btn btn-default btn-xs preview-pane__help-btn"
							popovertarget="preview-help"
							popovertargetaction="toggle"
							:title="__('Toggle help')"
							aria-haspopup="dialog"
							aria-controls="preview-help"
						>
							?
						</button>
						<div
							id="preview-help"
							popovertargetaction="toggle"
							popover
							class="preview-pane__help-popover"
						>
							<ul class="preview-pane__help-list">
								<li v-if="isReportMode">
									{{
										__(
											"Set report variables in the Report Template panel, then run a live preview."
										)
									}}
								</li>
								<li v-else>{{ __("Pick a document to preview.") }}</li>
								<li>{{ __("Refresh regenerates the preview.") }}</li>
								<li>{{ __("View code shows the generated Typst source.") }}</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
			<ReportPreviewVariables v-if="isReportMode" />

			<div class="preview-pane__controls card">
				<div class="preview-pane__controls-row">
					<div v-if="isReportMode" class="preview-search">
						<div class="preview-search__input-wrap">
							<span class="preview-search__note">
								{{
									store.reportPreviewReady?.value
										? __("Live report preview")
										: __("Waiting for preview variables")
								}}
							</span>
						</div>
					</div>
					<div v-else class="preview-search">
						<div class="preview-search__input-wrap">
							<div class="awesomplete">
								<input
									id="typst-sample-doc-input"
									type="text"
									:placeholder="__('Sample Document...')"
									autocomplete="off"
									class="form-control preview-search__input"
								/>
							</div>
						</div>
					</div>

					<span id="typst-status" class="preview-status">{{ __("idle") }}</span>
					<span
						v-if="isReportMode && chartRenderLabel"
						class="preview-status preview-chart-engine"
						:class="`is-${chartRenderStatus.status}`"
						:title="chartRenderStatus.message || chartRenderStatus.reason"
					>
						{{ chartRenderLabel }}
					</span>

					<div class="preview-pane__spacer"></div>

					<div class="preview-actions">
						<button
							id="typst-refresh"
							class="btn btn-default btn-sm preview-btn"
							type="button"
							:title="__('Refresh preview')"
							@click="onRefreshClick"
						>
							{{ __("Refresh") }}
						</button>
						<button
							id="typst-view-code"
							class="btn btn-default btn-sm preview-btn"
							type="button"
							:title="__('View Typst code')"
						>
							{{ __("View code") }}
						</button>
						<button
							type="button"
							class="btn btn-default btn-sm preview-btn"
							:title="__('Duplicate for another company')"
							@click="emit('duplicateForCompany')"
						>
							{{ __("Duplicate") }}
						</button>
						<button
							type="button"
							class="btn btn-primary btn-sm preview-btn"
							:title="__('Publish Crispy Template')"
							@click="emit('publishTemplate')"
						>
							{{ __("Publish Template") }}
						</button>
					</div>
				</div>
			</div>
		</template>
	</PreviewRenderer>
</template>

<script setup lang="ts">
import PreviewRenderer from "./PreviewRenderer.vue";
import ReportPreviewVariables from "./ReportPreviewVariables.vue";
import { useStore } from "../composables/useStore";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import type { ReportChartRender } from "../api/crispy";
import { getLogger } from "../logger";
import { __ } from "../utils/i18n";

type PreviewMode = "normal" | "half" | "full";
type PreviewZoomMode = "fit" | "manual";

const props = withDefaults(
	defineProps<{
		previewMode?: PreviewMode;
		zoomMode?: PreviewZoomMode;
		zoomPercent?: number;
	}>(),
	{
		previewMode: "normal",
		zoomMode: "fit",
		zoomPercent: 100,
	}
);
const emit = defineEmits<{
	(event: "update:previewMode", value: PreviewMode): void;
	(event: "update:zoomMode", value: PreviewZoomMode): void;
	(event: "update:zoomPercent", value: number): void;
	(event: "publishTemplate"): void;
	(event: "duplicateForCompany"): void;
}>();

const store = useStore();
const logger = getLogger({ component: "PreviewPane" });
const chartRenderStatus = ref<ReportChartRender | null>(null);
const chartRenderLabel = computed(() => {
	const chart = chartRenderStatus.value;
	if (!chart) return "";
	if (chart.engine === "lilaq") return `Lilaq ${chart.lilaq_version || ""}`.trim();
	if (chart.engine === "frappe_svg") return __("Frappe SVG fallback");
	if (chart.status === "omitted") return __("Chart omitted");
	return "";
});
const qrEnabled = computed(() => store.qrEnabled.value);
let reportCompileRequestSeq = 0;
let reportCompileInFlight = false;
let reportCompilePending = false;
const previewMode = computed(() => props.previewMode);
const zoomMode = computed(() => props.zoomMode);
const zoomPercent = computed(() => props.zoomPercent);
const previewModes = computed(() => [
	{ value: "normal" as const, label: __("Normal"), title: __("Regular builder layout") },
	{ value: "half" as const, label: __("Half"), title: __("Preview-focused split") },
	{ value: "full" as const, label: __("Full"), title: __("Maximum preview width") },
]);

const isReportMode = computed(() => {
	const format = store.crispyFormat.value;
	return format?.crispy_format_type === "Report";
});

async function compileSelectedReport(reportName: string) {
	if (!reportName) {
		return;
	}
	const requestSeq = ++reportCompileRequestSeq;
	if (reportCompileInFlight) {
		reportCompilePending = true;
		return;
	}
	reportCompileInFlight = true;

	logger.info("Selected report", reportName);

	try {
		// Show compiling status
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = __("Compiling...");

		// Trigger preview compilation via store
		const result = await store.compileReportPreview(reportName, []);
		chartRenderStatus.value = result?.chart_render || null;
		if (requestSeq !== reportCompileRequestSeq) {
			return;
		}

		// Dispatch custom event with SVG data for PreviewRenderer
		if (result && result.success) {
			window.dispatchEvent(
				new CustomEvent("crispy-report-preview", {
					detail: {
						svg_pages: result.svg_pages,
						page_count: result.page_count,
					},
				})
			);

			if (statusEl) statusEl.textContent = __("{0} page(s)", [result.page_count]);
		}
	} catch (error) {
		if (requestSeq !== reportCompileRequestSeq) {
			return;
		}
		logger.error("Preview compilation failed", error);
		chartRenderStatus.value = null;
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = __("Error");
		frappe.show_alert({ message: __("Preview compilation failed"), indicator: "red" });
	} finally {
		reportCompileInFlight = false;
		if (reportCompilePending) {
			reportCompilePending = false;
			const latestReport = store.selectedReportName?.value;
			if (store.reportPreviewReady?.value && latestReport) {
				void compileSelectedReport(latestReport);
			}
		}
	}
}

function onRefreshClick() {
	if (isReportMode.value) {
		if (store.reportPreviewReady?.value && store.selectedReportName?.value) {
			void compileSelectedReport(store.selectedReportName.value);
		} else {
			frappe.show_alert({
				message: __("Set preview variables and run the report first"),
				indicator: "blue",
			});
		}
		return;
	}
	store.requestPreviewRefresh?.();
}

function handleRefreshShortcut(event: KeyboardEvent) {
	if (event.defaultPrevented) return;
	if (event.key !== "Enter") return;
	if (!event.metaKey && !event.ctrlKey) return;
	event.preventDefault();
	document.getElementById("typst-refresh")?.click();
}

onMounted(() => {
	window.addEventListener("keydown", handleRefreshShortcut);
});

onBeforeUnmount(() => {
	window.removeEventListener("keydown", handleRefreshShortcut);
});

watch(
	() =>
		[
			isReportMode.value,
			store.previewRevision.value,
			store.reportPreviewReady?.value,
			store.selectedReportName?.value,
		] as const,
	([reportMode]) => {
		if (!reportMode || !store.reportPreviewReady?.value || !store.selectedReportName?.value)
			return;
		void compileSelectedReport(store.selectedReportName.value);
	},
	{ immediate: false }
);
</script>

<style scoped>
.preview-pane__header {
	margin: 12px 16px 0;
	padding: 0;
	border: none;
	box-shadow: none;
}

.preview-pane__header :deep(.section-head-content) {
	padding: 0 0 8px;
}

.preview-pane__header-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.preview-pane__title {
	margin: 0;
}

.preview-pane__spacer {
	margin-left: auto;
}

.preview-mode-toggle {
	display: inline-flex;
	align-items: center;
	gap: 2px;
	padding: 2px;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	background: #f8fafc;
}

.preview-mode-toggle__button {
	border: none;
	box-shadow: none;
}

.preview-mode-toggle__button.is-active {
	background: #0f172a;
	color: #fff;
}

.preview-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
	border-color: transparent !important;
	background: transparent !important;
	box-shadow: none !important;
	color: #334155;
	font-size: 13px;
	font-weight: 500;
	transition: color 0.15s ease, font-size 0.15s ease, font-weight 0.15s ease;
}

.preview-pane__help {
	display: flex;
	align-items: center;
}

.preview-pane__help-btn:hover,
.preview-pane__help-btn:focus-visible {
	border-color: transparent !important;
	background: transparent !important;
	color: #0f172a;
	font-size: 14px;
	font-weight: 700;
}

.preview-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
}

.preview-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.preview-pane__controls {
	padding: 12px 16px;
	margin: 0 16px;
	background: transparent;
	border: none;
	box-shadow: none;
}

.preview-pane__controls-row {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 12px;
	padding-bottom: 6px;
}

.preview-status {
	font-size: 12px;
	min-width: 160px;
	white-space: nowrap;
	text-transform: lowercase;
}

.preview-pane__spacer {
	flex: 1;
}

.preview-search {
	display: flex;
	align-items: center;
	gap: 8px;
}

.preview-search__input-wrap {
	position: relative;
}

.preview-search__input {
	width: 200px;
}

.preview-search__note {
	font-size: 12px;
	color: #475569;
}

.preview-btn {
}

.preview-btn:hover {
}

.preview-btn:disabled {
}

.preview-actions {
	display: flex;
	gap: 8px;
}
</style>
