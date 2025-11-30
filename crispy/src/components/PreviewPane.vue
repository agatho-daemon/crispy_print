<template>
	<div ref="previewPaneEl" class="bg-white border border-slate-200 flex flex-col overflow-hidden">
		<div class="border-b border-slate-200 px-4 py-3">
			<div class="flex items-center gap-2">
				<h3 class="text-sm font-semibold text-slate-800">Typst Preview</h3>
				<div class="ml-auto">
					<button type="button"
						class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 text-sm font-semibold text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50"
						popovertarget="preview-help" popovertargetaction="toggle" title="Toggle help">?</button>
					<div id="preview-help" popovertargetaction="toggle" popover
						class="top-8 rounded-xl border border-indigo-100 bg-white p-3 text-xs leading-relaxed text-slate-700 shadow-xl shadow-slate-400">
						<ul class="list-inside list-disc space-y-1">
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

		<div class="px-4 py-3 border-b border-slate-200">
			<div class="flex flex-wrap items-center gap-3">
				<span id="typst-status" class="text-[12px] text-slate-500">idle</span>

				<div class="flex items-center gap-2">
					<div class="relative w-full">
						<div class="awesomplete">
							<input id="typst-sample-doc-input" type="text" placeholder="Sample Document..."
								autocomplete="off" class="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900
                   focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						</div>
					</div> <button id="typst-refresh"
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50"
						type="button" title="Refresh preview">
						Refresh
					</button>
				</div>

				<div class="flex items-center gap-2 ml-auto">
					<button id="typst-view-pdf"
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:text-slate-400"
						type="button" disabled title="View PDF in new tab">
						View PDF
					</button>
					<button id="typst-download"
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:text-slate-400"
						type="button" disabled title="Download PDF">
						Download
					</button>
					<button id="typst-view-code"
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50"
						type="button" title="View Typst code">
						View code
					</button>
				</div>
			</div>
		</div>

		<div class="flex-1 overflow-y-auto bg-slate-200 px-4 py-4">
			<div class="mx-auto w-full max-w-5xl">
				<div id="typst-svg-container" class="space-y-8 bg-transparent">
					<div id="typst-preview-placeholder"
						class="px-6 py-10 text-center text-sm">
						Preview output will render here.
					</div>
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
