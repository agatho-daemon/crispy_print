<template>
	<div class="bg-white overflow-y-auto border border border-slate-200 flex flex-col">
		<div class="border-b border-slate-200 px-3 py-3">
			<div class="flex items-center gap-2">
				<h3 class="text-sm font-semibold text-slate-800">Typst Page Settings</h3>
				<div class="ml-auto">
					<button type="button"
						class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 text-sm font-semibold text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50"
						popovertarget="settings-help" popovertargetaction="toggle" title="Toggle help">?</button>
					<div id="settings-help" popover
						class="top-8 rounded-xl border border-indigo-100 bg-white p-3 text-xs leading-relaxed text-slate-700 shadow-xl shadow-slate-400">
						<ul class="list-inside list-disc space-y-1">
							<li>Configure page size, margins, and typography for Typst.</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
		<div class="flex-1 px-4 py-3 overflow-y-auto">
			<div class="space-y-4">
				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Page Size</label>
					<select v-model="pageSettings.pageSize"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none">
						<option value="A4">A4</option>
						<option value="Letter">Letter</option>
						<option value="Legal">Legal</option>
					</select>
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Orientation</label>
					<select v-model="pageSettings.orientation"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none">
						<option value="portrait">Portrait</option>
						<option value="landscape">Landscape</option>
					</select>
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Margins (mm)</label>
					<div class="grid grid-cols-2 gap-2">
						<input v-model.number="pageSettings.margins.top" type="number" placeholder="Top"
							class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						<input v-model.number="pageSettings.margins.bottom" type="number" placeholder="Bottom"
							class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						<input v-model.number="pageSettings.margins.left" type="number" placeholder="Left"
							class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						<input v-model.number="pageSettings.margins.right" type="number" placeholder="Right"
							class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
					</div>
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Font Family</label>
					<input v-model="pageSettings.fontFamily" type="text" placeholder="e.g., Arial, Helvetica"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Font Size (pt)</label>
					<input v-model.number="pageSettings.fontSize" type="number" placeholder="11"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Letterhead/Background</label>
					<select v-model="pageSettings.letterhead"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none">
						<option value="">None</option>
						<option value="default">Default Letterhead</option>
					</select>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { watch } from "vue"

interface PageSettings {
	pageSize: string
	orientation: string
	margins: {
		top: number
		bottom: number
		left: number
		right: number
	}
	fontFamily: string
	fontSize: number
	letterhead: string
}

interface Props {
	pageSettings: PageSettings
	markDirty: () => void
}

const props = defineProps<Props>()

watch(
	() => props.pageSettings,
	() => props.markDirty(),
	{ deep: true }
)
</script>
