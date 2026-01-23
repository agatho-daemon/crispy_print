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
			<div class="preview-pane__header">
				<div class="preview-pane__header-row">
					<h3 class="preview-pane__title">Typst Preview</h3>
					<div class="preview-pane__spacer"></div>
					<div>
						<button
							type="button"
							class="preview-pane__help-btn"
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

			<div class="preview-pane__controls">
				<div class="preview-pane__controls-row">
					<!-- Sample Report Selector (for generic Report formats) -->
					<div v-if="isGenericReport" class="preview-search">
						<div class="preview-search__input-wrap">
							<select
								id="sample-report-select"
								class="preview-search__input"
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
									class="preview-search__input"
								/>
							</div>
						</div>
					</div>

					<span id="typst-status" class="preview-status">idle</span>

					<div class="preview-pane__spacer"></div>

					<div class="preview-actions">
						<button
							id="typst-refresh"
							class="preview-btn"
							type="button"
							title="Refresh preview"
						>
							Refresh
						</button>
						<button
							id="typst-view-code"
							class="preview-btn"
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

const store = useStore();
const qrEnabled = computed(() => store.qrEnabled.value && !store.removeQr.value);
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
	console.log("[PreviewPane] Selected report:", reportName);

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
		console.error("[PreviewPane] Preview compilation failed:", error);
		const statusEl = document.getElementById("typst-status");
		if (statusEl) statusEl.textContent = "Error";
		frappe.show_alert({ message: "Preview compilation failed", indicator: "red" });
	}
}
</script>

<style scoped>
.preview-pane__header {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px 16px;
}

.preview-pane__header-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.preview-pane__title {
	margin: 0;
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
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
	border: 1px solid #e2e8f0;
	background: #fff;
	color: #4f46e5;
	font-size: 14px;
	font-weight: 600;
	cursor: pointer;
	transition: background-color 0.2s ease, border-color 0.2s ease;
}

.preview-pane__help-btn:hover {
	background: #eef2ff;
	border-color: #c7d2fe;
}

.preview-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	border: 1px solid #e0e7ff;
	background: #fff;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
	color: #334155;
	box-shadow: 0 10px 25px rgba(148, 163, 184, 0.25), 0 8px 10px rgba(148, 163, 184, 0.15);
}

.preview-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.preview-pane__controls {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px 16px;
}

.preview-pane__controls-row {
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 12px;
}

.preview-status {
	font-size: 12px;
	color: #64748b;
	min-width: 120px;
	white-space: nowrap;
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
	width: 220px;
	padding: 8px 12px;
	font-size: 14px;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.preview-search__input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.preview-btn {
	border: 1px solid #e2e8f0;
	background: #f8fafc;
	color: #334155;
	padding: 8px 12px;
	border-radius: 6px;
	font-size: 13px;
	font-weight: 600;
	cursor: pointer;
	transition: background-color 0.2s ease, border-color 0.2s ease;
}

.preview-btn:hover {
	background: #eef2ff;
	border-color: #c7d2fe;
}

.preview-btn:disabled {
	background: #f8fafc;
	color: #94a3b8;
	cursor: not-allowed;
}

.preview-actions {
	display: flex;
	gap: 8px;
}
</style>
