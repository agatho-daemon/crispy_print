<template>
	<div ref="previewPaneEl" class="preview-pane">
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
					<div id="preview-help" popovertargetaction="toggle" popover class="preview-pane__help-popover">
						<ul class="preview-pane__help-list">
							<li>Pick a document to preview.</li>
							<li>View opens the PDF in a new tab.</li>
							<li>Download saves the PDF to your device.</li>
							<li>Refresh regenerates the preview.</li>
							<li>View code shows the generated Typst source.</li>
						</ul>
					</div>
				</div>
			</div>
		</div>

		<div class="preview-pane__controls">
			<div class="preview-pane__controls-row">
				<span id="typst-status" class="preview-status">idle</span>

				<div class="preview-search">
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
					<button
						id="typst-refresh"
						class="preview-btn"
						type="button"
						title="Refresh preview"
					>
						Refresh
					</button>
				</div>

				<div class="preview-actions">
					<button
						id="typst-view-pdf"
						class="preview-btn"
						type="button"
						disabled
						title="View PDF in new tab"
					>
						View PDF
					</button>
					<button
						id="typst-download"
						class="preview-btn"
						type="button"
						disabled
						title="Download PDF"
					>
						Download
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

		<div class="preview-pane__body">
			<div id="typst-svg-container">
				<div id="typst-preview-placeholder" class="preview-placeholder">
					Preview output will render here.
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useStore } from "../composables/useStore"
import { setupWorker } from "../lib/typst/setupWorker"

const previewPaneEl = ref<HTMLElement | null>(null)
const store = useStore()

let teardown: (() => void) | null = null
let stopFormatWatch: (() => void) | null = null

onMounted(() => {
	stopFormatWatch = watch(
		() => store.formatName.value,
		(formatName) => {
			if (!formatName || !previewPaneEl.value) return

			if (teardown) {
				teardown()
				teardown = null
			}

			teardown = setupWorker(formatName, previewPaneEl.value, {
				getLayout: () => store.layout.value,
				getLetterhead: () => store.letterhead.value,
				getDoctype: () => store.docType.value,
				getPageSettings: () => store.pageSettings.value,
				hookDataChanges: (callback: () => void) => {
					const stop = watch(
						() => [store.layout.value, store.pageSettings.value],
						() => callback(),
						{ deep: true }
					)
					return () => stop()
				},
				hookDoctypeChanges: (callback: (doctype: string | null | undefined) => void) => {
					const stop = watch(
						() => store.docType.value,
						(next) => callback(next),
						{ immediate: true }
					)
					return () => stop()
				},
			})
		},
		{ immediate: true }
	)
})

onBeforeUnmount(() => {
	if (stopFormatWatch) stopFormatWatch()
	if (teardown) teardown()
})
</script>

<style scoped>
.preview-pane {
	background: #fff;
	border: 1px solid #e2e8f0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

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
	box-shadow:
		0 10px 25px rgba(148, 163, 184, 0.25),
		0 8px 10px rgba(148, 163, 184, 0.15);
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
}

.preview-search {
	display: flex;
	align-items: center;
	gap: 8px;
}

.preview-search__input-wrap {
	position: relative;
	min-width: 240px;
	flex: 1;
}

.preview-search__input {
	width: 100%;
	padding: 8px 12px;
	font-size: 14px;
	color: #0f172a;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	background: #fff;
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.preview-search__input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.preview-actions {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-left: auto;
}

.preview-btn {
	border: 1px solid #e2e8f0;
	background: #fff;
	color: #334155;
	font-size: 12px;
	font-weight: 600;
	border-radius: 8px;
	padding: 6px 12px;
	cursor: pointer;
	transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}

.preview-btn:hover {
	border-color: #c7d2fe;
	background: #eef2ff;
}

.preview-btn:disabled {
	cursor: not-allowed;
	border-color: #e2e8f0;
	background: #f8fafc;
	color: #cbd5e1;
}

.preview-pane__body {
	flex: 1;
	overflow-y: auto;
	background: #e2e8f0;
	padding: 16px;
	width: 100%;
	box-sizing: border-box;
}

.preview-placeholder {
	padding: 24px;
	text-align: center;
	font-size: 14px;
	color: #94a3b8;
	background: #fff;
	border-radius: 8px;
	box-shadow:
		0 4px 12px rgba(148, 163, 184, 0.25),
		0 2px 6px rgba(148, 163, 184, 0.2);
}

</style>