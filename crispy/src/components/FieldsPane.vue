<template>
	<div class="fields-pane">
		<div class="fields-pane__header">
			<div class="fields-pane__header-row">
				<h3 class="fields-pane__title">Fields</h3>
				<div class="fields-pane__spacer"></div>
				<div>
					<button
						type="button"
						class="fields-pane__help-btn"
						popovertarget="fields-help"
						popovertargetaction="toggle"
						title="Toggle help"
					>
						?
					</button>
					<div id="fields-help" popover class="fields-pane__help-popover">
						<ul class="fields-pane__help-list">
							<li>Use the search box to quickly find specific fields.</li>
							<li>Hover over a field to see its fieldname and type.</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
		<div class="fields-pane__search-area">
			<div class="search-box">
				<input
					v-model="searchQuery"
					type="text"
					:placeholder="`Search ${filteredFields.length} fields...`"
					class="search-input"
				/>
			</div>
			<div v-if="loading" class="loading-indicator">
				<span class="loading-text">Loading fields</span>
			</div>
		</div>

		<div class="fields-list">
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
				class="field-item"
				draggable="true"
				@dragstart="onFieldDragStart($event, field)"
				:title="`(${field.fieldname} — ${field.fieldtype || 'Unknown'})`"
			>
				<div class="field-label">
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
