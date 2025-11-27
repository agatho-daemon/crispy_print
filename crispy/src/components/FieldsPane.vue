<template>
	<div class="flex h-full flex-col border border-slate-200 bg-white/90">
		<div class="border-b border-slate-200 px-4 py-3">
			<div class="flex items-center justify-between">
				<h3 class="text-sm font-semibold text-slate-800">Fields</h3>
			</div>
			<p class="mt-1 text-xs text-slate-500 py-2">
				Hover to see fieldname and fieldtype.
			</p>
			<div class="mt-2 h-px bg-slate-200 -mx-6 px-6"></div>
			<div class="search-box mt-3">
				<input
					v-model="searchQuery"
					type="text"
					:placeholder="`Search ${filteredFields.length} fields...`"
					class="search-input w-full px-3 py-2 text-sm border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 shadow-inner"
				/>
			</div>
			<div v-if="loading" class="loading-indicator">
				<span class="loading-text">Loading fields</span>
			</div>
		</div>

		<div class="fields-list flex-1 overflow-y-auto px-4 pb-4 pt-3 space-y-3">
			<div v-if="filteredFields.length === 0" class="empty-state">
				<p v-if="searchQuery" class="empty-message">
					No fields match "{{ searchQuery }}"
				</p>
				<p v-else class="empty-message">
					No fields available yet.
				</p>
			</div>

			<div
				v-for="field in filteredFields"
				:key="field.fieldname"
				class="field-item w-full flex items-center gap-2 border-2 border-dotted border-slate-200 transition-all px-3 py-2"
				draggable="true"
				@dragstart="onFieldDragStart($event, field)"
				:title="`(${field.fieldname} — ${field.fieldtype || 'Unknown'})`"
			>
				<div
					class="field-label block text-sm font-semibold text-slate-900 truncate"
				>
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
