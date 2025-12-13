<template>
	<div ref="previewPaneEl" class="preview-pane">
		<!-- Optional controls/menu (used by builder) -->
		<slot name="menu"></slot>

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
import { setupWorker } from "../typst/setupWorker"

interface Props {
	formatName: string | null
	layout: any
	pageSettings: any
	letterhead: any
	docType: string | null
	// Optional trigger value to force refresh (e.g., external events)
	changeKey?: string | number | null
}

const props = defineProps<Props>()

const previewPaneEl = ref<HTMLElement | null>(null)
let teardown: (() => void) | null = null
let manualRefreshCallback: (() => void) | null = null

function createAdapter() {
	return {
		getLayout: () => props.layout,
		getLetterhead: () => props.letterhead,
		getDoctype: () => props.docType,
		getPageSettings: () => props.pageSettings,
		// Temporarily disable change-driven hook to test single trigger path
		// hookDataChanges: (callback: () => void) => {
		// 	manualRefreshCallback = callback
		// 	const stop = watch(
		// 		() => [props.layout, props.pageSettings, props.letterhead, props.changeKey],
		// 		() => callback(),
		// 		{ deep: true }
		// 	)
		// 	return () => stop()
		// },
		hookDoctypeChanges: (callback: (doctype: string | null | undefined) => void) => {
			const stop = watch(
				() => props.docType,
				(next) => callback(next),
				{ immediate: true }
			)
			return () => stop()
		},
	}
}

	watch(
	() => props.formatName,
	(formatName) => {
		if (!formatName || !previewPaneEl.value) {
			console.warn("[PreviewRenderer] Cannot setup worker:", { formatName, hasElement: !!previewPaneEl.value })
			return
		}

		console.log("[PreviewRenderer] Setting up worker for format:", formatName)

		if (teardown) {
			console.log("[PreviewRenderer] Tearing down previous worker")
			teardown()
			teardown = null
		}

		teardown = setupWorker(formatName, previewPaneEl.value, createAdapter())
		console.log("[PreviewRenderer] Worker initialized")
	},
	{ immediate: true }
)

onBeforeUnmount(() => {
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

.preview-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 16px;
	background: #f8fafc;
}

.preview-placeholder {
	padding: 20px;
	border: 1px dashed #cbd5e1;
	border-radius: 6px;
	text-align: center;
	color: #94a3b8;
	font-size: 14px;
	background: #fff;
}

/* When Typst pages render, we add .has-pages class; keep the same styles as current flow */
#typst-svg-container.has-pages {
	display: grid;
	gap: 16px;
}
</style>
