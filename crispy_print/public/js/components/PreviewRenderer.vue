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
			<div v-if="errorPanel" class="preview-error">
				<div class="preview-error__header">
					<span class="preview-error__title">Typst Error</span>
					<button class="preview-error__copy" type="button" @click="copyError">Copy</button>
				</div>
				<pre class="preview-error__body">{{ errorPanel }}</pre>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import { setupWorker } from "../typst/setupWorker"
import { CrispyPreviewEvents, type CrispyPreviewStatusDetail } from "../utils/events"

interface Props {
	formatName: string | null
	layout: any
	docHeader: string
	docFooter: string
	typstPreamble: string
	typstCode?: string
	rawTypst?: boolean
	qrEnabled: boolean
	pageSettings: any
	letterhead: any
	docType: string | null
	docName?: string | null
	changeKey?: number
	watchDataChanges?: boolean
}

const props = defineProps<Props>()

const previewPaneEl = ref<HTMLElement | null>(null)
const errorPanel = ref<string | null>(null)
let teardown: (() => void) | null = null

function createAdapter() {
	const enableDataWatch = props.watchDataChanges !== false
	return {
		getLayout: () => props.layout,
		getDocHeader: () => props.docHeader,
		getDocFooter: () => props.docFooter,
		getTypstPreamble: () => props.typstPreamble,
		getTypstCode: () => props.typstCode || "",
		getRawTypst: () => Boolean(props.rawTypst),
		getQrEnabled: () => props.qrEnabled,
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
							props.docFooter,
							props.typstPreamble,
							props.typstCode,
							props.rawTypst,
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

function onPreviewStatus(event: Event) {
	const detail = (event as CustomEvent<CrispyPreviewStatusDetail>).detail
	if (!detail) return
	if (detail.status === "error") {
		errorPanel.value = detail.message || "Typst compilation failed."
	} else if (detail.status === "ready" || detail.status === "compiling") {
		errorPanel.value = null
	}
}

function copyError() {
	if (!errorPanel.value) return
	if (navigator?.clipboard?.writeText) {
		navigator.clipboard.writeText(errorPanel.value)
		return
	}
	const textarea = document.createElement("textarea")
	textarea.value = errorPanel.value
	document.body.appendChild(textarea)
	textarea.select()
	document.execCommand("copy")
	document.body.removeChild(textarea)
}

onMounted(() => {
	window.addEventListener(CrispyPreviewEvents.Status, onPreviewStatus)
})

onBeforeUnmount(() => {
	console.log("[PreviewRenderer] Component unmounting - cleaning up")
	if (teardown) teardown()
	window.removeEventListener(CrispyPreviewEvents.Status, onPreviewStatus)
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

.preview-error {
	margin-top: 16px;
	border: 1px solid #fecaca;
	background: #fff1f2;
	border-radius: 8px;
	overflow: hidden;
	box-shadow: 0 6px 16px rgba(239, 68, 68, 0.15);
}

.preview-error__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 10px 12px;
	background: #fee2e2;
	border-bottom: 1px solid #fecaca;
}

.preview-error__title {
	font-size: 12px;
	font-weight: 700;
	color: #991b1b;
	letter-spacing: 0.02em;
	text-transform: uppercase;
}

.preview-error__copy {
	border: 1px solid #fca5a5;
	background: #fff;
	color: #b91c1c;
	border-radius: 6px;
	padding: 4px 8px;
	font-size: 12px;
	cursor: pointer;
}

.preview-error__body {
	margin: 0;
	padding: 12px;
	font-size: 12px;
	line-height: 1.5;
	color: #7f1d1d;
	white-space: pre-wrap;
	font-family:
		"SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}
</style>
