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
						<option value="A3">A3 (297 × 420 mm)</option>
						<option value="A4">A4 (210 × 297 mm)</option>
						<option value="A5">A5 (148 × 210 mm)</option>
						<option value="Letter">Letter (8.5 × 11 in)</option>
						<option value="Legal">Legal (8.5 × 14 in)</option>
						<option value="Tabloid">Tabloid (11 × 17 in)</option>
						<option value="Executive">Executive (7.25 × 10.5 in)</option>
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
						<div class="relative">
							<span class="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-500 pointer-events-none">T</span>
							<input v-model.number="pageSettings.margins.top" type="number" placeholder="Top"
								class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						</div>
						<div class="relative">
							<span class="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-500 pointer-events-none">B</span>
							<input v-model.number="pageSettings.margins.bottom" type="number" placeholder="Bottom"
								class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						</div>
						<div class="relative">
							<span class="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-500 pointer-events-none">L</span>
							<input v-model.number="pageSettings.margins.left" type="number" placeholder="Left"
								class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						</div>
						<div class="relative">
							<span class="absolute left-3 top-1/2 -translate-y-1/2 text-xs font-medium text-slate-500 pointer-events-none">R</span>
							<input v-model.number="pageSettings.margins.right" type="number" placeholder="Right"
								class="w-full rounded-lg border border-slate-200 bg-white pl-7 pr-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
						</div>
					</div>
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Font Family</label>
					<select v-model="pageSettings.fontFamily"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none">
						<option v-if="loadingFonts" disabled>Loading fonts...</option>
						<option v-for="font in availableFonts" :key="font" :value="font">{{ font }}</option>
					</select>
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Font Size (pt)</label>
					<input v-model.number="pageSettings.fontSize" type="number" placeholder="11"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none" />
				</div>

				<div>
					<label class="block text-[13px] font-semibold text-slate-700 mb-2">Letterhead / Logo</label>
					<select v-model="pageSettings.letterhead"
						class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200 focus:outline-none">
						<option value="">None</option>
						<option v-if="loadingLetterheads" disabled>Loading letterheads...</option>
						<option v-for="letterhead in availableLetterheads" :key="letterhead" :value="letterhead">{{ letterhead }}</option>
					</select>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue"

declare const frappe: any

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

const availableFonts = ref<string[]>([])
const loadingFonts = ref(false)
const availableLetterheads = ref<string[]>([])
const loadingLetterheads = ref(false)

// Fetch available fonts from Typst
async function fetchFonts() {
	if (typeof frappe === "undefined") {
		// Dev mode fallback
		availableFonts.value = ["Arial", "Helvetica", "Times New Roman", "Courier"]
		return
	}

	loadingFonts.value = true
	try {
		const response = await frappe.call({
			method: "crispy_print.api.get_typst_local_fonts",
		})
		availableFonts.value = response.message || []
	} catch (error) {
		console.error("[SettingsPane] Failed to fetch fonts:", error)
		// Fallback fonts
		availableFonts.value = ["Arial", "Helvetica", "Times New Roman"]
	} finally {
		loadingFonts.value = false
	}
}

// Fetch available letterheads
async function fetchLetterheads() {
	if (typeof frappe === "undefined") {
		// Dev mode fallback
		availableLetterheads.value = []
		return
	}

	loadingLetterheads.value = true
	try {
		const response = await frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Letter Head",
				fields: ["name"],
				filters: { disabled: 0 },
				order_by: "name asc",
			},
		})
		availableLetterheads.value = (response.message || []).map((lh: any) => lh.name)
	} catch (error) {
		console.error("[SettingsPane] Failed to fetch letterheads:", error)
		availableLetterheads.value = []
	} finally {
		loadingLetterheads.value = false
	}
}

onMounted(() => {
	fetchFonts()
	fetchLetterheads()
})

watch(
	() => props.pageSettings,
	() => props.markDirty(),
	{ deep: true }
)
</script>
