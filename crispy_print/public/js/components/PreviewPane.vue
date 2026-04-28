<template>
	<PreviewRenderer
		:format-name="store.formatName.value"
		:layout="store.layout.value"
		:doc-header="store.docHeader.value"
		:doc-footer="store.docFooter.value"
		:typst-preamble="store.typstPreamble.value"
		:typst-code="store.typstCode.value"
		:raw-typst="store.rawTypst.value"
		:qr-enabled="qrEnabled"
		:letterhead="store.letterhead.value"
		:doc-type="store.docType.value"
		:doc-name="null"
		:page-settings="store.pageSettings.value"
		:change-key="store.changeKey.value"
		:watch-data-changes="!isReportMode"
		:zoom-mode="zoomMode"
		:zoom-percent="zoomPercent"
		@update:zoom-mode="(value) => emit('update:zoomMode', value)"
		@update:zoom-percent="(value) => emit('update:zoomPercent', value)"
	>
		<template #menu>
			<div class="section-head preview-pane__header">
				<div class="section-head-content preview-pane__header-row">
					<h3 class="section-title preview-pane__title">{{ __("Typst Preview") }}</h3>
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
									{{ __("Style preview uses deterministic sample data.") }}
								</li>
								<li v-else>{{ __("Pick a document to preview.") }}</li>
								<li>{{ __("Refresh regenerates the preview.") }}</li>
								<li>{{ __("View code shows the generated Typst source.") }}</li>
							</ul>
						</div>
					</div>
				</div>
			</div>

			<div class="preview-pane__controls card">
				<div class="preview-pane__controls-row">
					<!-- Sample Report Selector (shared with LayoutPane for Report formats) -->
					<div v-if="isReportMode" class="preview-search">
						<div class="preview-search__input-wrap">
							<span class="preview-search__note">
								{{ __("Style preview with placeholder data") }}
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
					</div>
				</div>
			</div>
		</template>
	</PreviewRenderer>
</template>

<script setup lang="ts">
import PreviewRenderer from "./PreviewRenderer.vue";
import { useStore } from "../composables/useStore";
import { computed, watch } from "vue";
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
}>();

const store = useStore();
const logger = getLogger({ component: "PreviewPane" });
const qrEnabled = computed(() => store.qrEnabled.value);
let reportCompileRequestSeq = 0;
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
	if (!reportName || !store.formatName.value) {
		return;
	}
	const requestSeq = ++reportCompileRequestSeq;

	logger.info("Selected report", reportName);

	try {
		// Show compiling status
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = __("Compiling...");

		// Trigger preview compilation via store
		const result = await store.compileReportPreview(reportName, []);
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
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = __("Error");
		frappe.show_alert({ message: __("Preview compilation failed"), indicator: "red" });
	}
}

function onRefreshClick() {
	if (!isReportMode.value) return;
	void compileSelectedReport("Style Preview");
}

watch(
	() =>
		[
			isReportMode.value,
			store.changeKey.value,
			store.rawTypst.value,
			store.reportBuilderConfig?.value?.show_filters,
			store.reportBuilderConfig?.value?.show_summary,
			store.reportBuilderConfig?.value?.include_total_row,
		] as const,
	([reportMode]) => {
		if (!reportMode) return;
		void compileSelectedReport("Style Preview");
	},
	{ immediate: true }
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
