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
import { useStore } from "@/composables/useStore"
import { setupWorker } from "@/lib/typst/setupWorker"

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
