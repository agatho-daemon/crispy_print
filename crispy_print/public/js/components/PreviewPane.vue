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
		:watch-data-changes="true"
	>
		<template #menu>
			<div class="section-head preview-pane__header">
				<div class="section-head-content preview-pane__header-row">
					<h3 class="section-title preview-pane__title">Typst Preview</h3>
					<div class="preview-pane__spacer"></div>
					<div class="preview-pane__help">
						<button
							type="button"
							class="btn btn-default btn-xs preview-pane__help-btn"
							popovertarget="preview-help"
							popovertargetaction="toggle"
							title="Toggle help"
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
								<li>Pick a document to preview.</li>
								<li>Refresh regenerates the preview.</li>
								<li>View code shows the generated Typst source.</li>
							</ul>
						</div>
					</div>
				</div>
			</div>

			<div class="preview-pane__controls card">
				<div class="preview-pane__controls-row">
					<!-- Sample Report Selector (for generic Report formats) -->
					<div v-if="isGenericReport" class="preview-search">
						<div class="preview-search__input-wrap">
							<select
								id="sample-report-select"
								class="form-control preview-search__input"
								:disabled="store.sampleReports.value.length === 0"
								@change="handleReportSelection"
							>
								<option value="">Sample Report...</option>
								<option
									v-for="report in store.sampleReports.value"
									:key="report.name"
									:value="report.name"
								>
									{{ report.name }}
								</option>
							</select>
						</div>
					</div>
					<div v-else class="preview-search">
						<div class="preview-search__input-wrap">
							<div class="awesomplete">
								<input
									id="typst-sample-doc-input"
									type="text"
									placeholder="Sample Document..."
									autocomplete="off"
									class="form-control preview-search__input"
								/>
							</div>
						</div>
					</div>

					<span id="typst-status" class="preview-status">idle</span>

					<div class="preview-pane__spacer"></div>

					<div class="preview-actions">
						<button
							id="typst-refresh"
							class="btn btn-default btn-sm preview-btn"
							type="button"
							title="Refresh preview"
						>
							Refresh
						</button>
						<button
							id="typst-view-code"
							class="btn btn-default btn-sm preview-btn"
							type="button"
							title="View Typst code"
						>
							View code
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
import { computed, ref } from "vue";
import { getLogger } from "../logger";

const store = useStore();
const logger = getLogger({ component: "PreviewPane" });
const qrEnabled = computed(() => store.qrEnabled.value);
const selectedReport = ref<string>("");

// Check if this is a generic Report format
const isGenericReport = computed(() => {
	const format = store.crispyFormat.value;
	return (
		format?.crispy_format_type === "Report" && format?.is_generic === 1 && store.rawTypst.value
	);
});

/**
 * Handle report selection and trigger preview compilation
 */
async function handleReportSelection(event: Event) {
	const target = event.target as HTMLSelectElement;
	const reportName = target.value;

	if (!reportName) {
		selectedReport.value = "";
		return;
	}

	selectedReport.value = reportName;
	logger.info("Selected report", reportName);

	try {
		// Show compiling status
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = "Compiling...";

		// Trigger preview compilation via store
		const result = await store.compileReportPreview(reportName, []);

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

			if (statusEl) statusEl.textContent = `${result.page_count} page(s)`;
		}
	} catch (error) {
		logger.error("Preview compilation failed", error);
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = "Error";
		frappe.show_alert({ message: "Preview compilation failed", indicator: "red" });
	}
}
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

.preview-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
}

.preview-pane__help {
	display: flex;
	align-items: center;
}

.preview-pane__help-btn:hover {
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
