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
import { onBeforeUnmount, ref, watch } from "vue"
import { setupWorker } from "../typst/setupWorker"

interface Props {
	formatName: string | null
	layout: any
	docHeader: string
	typstPreamble: string
	pageSettings: any
	letterhead: any
	docType: string | null
	docName?: string | null
	changeKey?: number
	watchDataChanges?: boolean
}

const props = defineProps<Props>()

const previewPaneEl = ref<HTMLElement | null>(null)
let teardown: (() => void) | null = null

function createAdapter() {
	const enableDataWatch = props.watchDataChanges !== false
	return {
		getLayout: () => props.layout,
		getDocHeader: () => props.docHeader,
		getTypstPreamble: () => props.typstPreamble,
		getLetterhead: () => props.letterhead,
		getDoctype: () => props.docType,
		getDocname: () => props.docName,
		getPageSettings: () => props.pageSettings,
		hookDataChanges: enableDataWatch
			? (callback: () => void) => {
					// Prefer explicit invalidation via changeKey to avoid expensive deep watches.
					if (props.changeKey !== undefined) {
						const stop = watch(
							() => props.changeKey,
							(_newVal, oldVal) => {
								if (oldVal !== undefined) {
									callback()
								}
							}
						)
						return () => stop()
					}

					// Fallback for callers that don't provide changeKey.
					const stop = watch(
						() => [
							props.layout,
							props.pageSettings,
							props.letterhead,
							props.docHeader,
							props.typstPreamble,
						],
						() => callback(),
						{ deep: true }
					)
					return () => stop()
				}
			: undefined,
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
	() => [props.formatName, previewPaneEl.value] as const,
	([formatName, element]) => {
		if (!formatName || !element) return

		teardown?.()
		teardown = setupWorker(formatName, element, createAdapter())
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
