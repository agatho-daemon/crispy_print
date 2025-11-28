<template>
	<div class="flex flex-col border border-slate-200 bg-white/90">
		<div class="border-b border-slate-200 px-4 py-3">
			<div class="flex items-center gap-2">
				<h3 class="text-sm font-semibold text-slate-800">Fields</h3>
				<div class="ml-auto">
					<button type="button"
						class="inline-flex h-6 w-6 items-center justify-center rounded-full border border-slate-200 text-sm font-semibold text-indigo-600 hover:border-indigo-300 hover:bg-indigo-50"
						popovertarget="fields-help" popovertargetaction="toggle" title="Toggle help">?</button>
					<div id="fields-help" popover
						class="top-8 rounded-xl border border-indigo-100 bg-white p-3 text-xs leading-relaxed text-slate-700 shadow-xl shadow-slate-400">
						<ul class="list-inside list-disc space-y-1">
							<li>Use the search box to quickly find specific fields.</li>
							<li>Hover over a field to see its fieldname and type.</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
		<div class=" px-4 py-3">
			<div class="search-box">
				<input v-model="searchQuery" type="text" :placeholder="`Search ${filteredFields.length} fields...`"
					class="search-input w-full px-3 py-2 text-sm border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 shadow-inner" />
			</div>
			<div v-if="loading" class="loading-indicator mt-2">
				<span class="loading-text">Loading fields</span>
			</div>
		</div>

		<div class="fields-list border overflow-y-auto px-4 pb-4 pt-3 space-y-3">
			<div v-if="filteredFields.length === 0" class="empty-state">
				<p v-if="searchQuery" class="empty-message">
					No fields match "{{ searchQuery }}"
				</p>
				<p v-else class="empty-message">
					No fields available yet.
				</p>
			</div>

			<div v-for="field in filteredFields" :key="field.fieldname"
				class="field-item w-full flex items-center gap-2 border-2 border-dotted border-slate-200 transition-all px-3 py-2"
				draggable="true" @dragstart="onFieldDragStart($event, field)"
				:title="`(${field.fieldname} — ${field.fieldtype || 'Unknown'})`">
				<div class="field-label block text-sm font-semibold text-slate-900 truncate">
					{{ field.label }}
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, unref, type MaybeRef } from "vue"
import type { DocField } from "@/utils/layout"

interface Props {
	fields: MaybeRef<DocField[]>
	loading?: MaybeRef<boolean>
}

const props = withDefaults(defineProps<Props>(), { loading: false })
const searchQuery = ref("")
const loading = computed(() => unref(props.loading))
// const showHelp = ref(false)

const filteredFields = computed(() => {
	const all = unref(props.fields)
	if (!searchQuery.value) return all

	const query = searchQuery.value.toLowerCase()
	return all.filter((field) => {
		const label = field.label?.toLowerCase() || ""
		const name = field.fieldname?.toLowerCase() || ""
		const type = field.fieldtype?.toLowerCase() || ""
		return label.includes(query) || name.includes(query) || type.includes(query)
	})
})

function onFieldDragStart(event: DragEvent, field: DocField) {
	if (event.dataTransfer) {
		event.dataTransfer.effectAllowed = "copy"
		event.dataTransfer.setData("application/json", JSON.stringify(field))
		event.dataTransfer.setData("text/plain", field.fieldname)
	}
}
</script>
