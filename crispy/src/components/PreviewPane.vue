<template>
	<div class="bg-white border border-slate-200 flex flex-col overflow-hidden">
		<div class="border-b border-slate-200 px-4 py-3">
			<div class="flex items-center gap-2">
				<h3 class="text-sm font-semibold text-slate-800">Typst Preview</h3>
								<div class="ml-auto">
					<button type="button"
						class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 text-sm font-semibold text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50"
						popovertarget="preview-help" popovertargetaction="toggle" title="Toggle help">?</button>
					<div id="preview-help" popover
						class="top-8 rounded-xl border border-indigo-100 bg-white p-3 text-xs leading-relaxed text-slate-700 shadow-xl shadow-slate-400">
						<ul class="list-inside list-disc space-y-1">
							<li>Configure page size, margins, and typography for Typst.</li>
						</ul>
					</div>
				</div>

			</div>
		</div>

		<div class="px-4 py-3 border-b border-slate-200">
			<div class="flex flex-wrap items-center gap-3">
				<span class="text-[12px] text-slate-500">{{ statusText }}</span>

				<div class="flex items-center gap-2">
					<input v-model="sampleDoc" type="text" placeholder="Sample Document..."
						class="w-52 rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
					<button
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50"
						type="button" @click="refreshPreview" title="Refresh preview">
						Refresh
					</button>
				</div>

				<div class="flex items-center gap-2 ml-auto">
					<button
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:text-slate-400"
						type="button" :disabled="!canViewPdf" @click="viewPdf" title="View PDF in new tab">
						View PDF
					</button>
					<button
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:text-slate-400"
						type="button" :disabled="!canDownload" @click="downloadPdf" title="Download PDF">
						Download
					</button>
					<button
						class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50"
						type="button" @click="viewCode" title="View Typst code">
						View code
					</button>
				</div>
			</div>
		</div>

		<div class="flex-1 px-4 py-3 overflow-y-auto bg-slate-50">
			<div
				class="rounded-lg border border-dashed border-slate-300 bg-white px-4 py-6 text-center text-sm text-slate-500">
				Preview output will render here.
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref } from "vue"

const statusText = ref("idle")
const sampleDoc = ref("")
const canViewPdf = ref(false)
const canDownload = ref(false)

function refreshPreview() {
	// TODO: wire up Typst worker refresh
}

function viewPdf() {
	// TODO: open generated PDF
}

function downloadPdf() {
	// TODO: trigger PDF download
}

function viewCode() {
	// TODO: show Typst source
}
</script>
