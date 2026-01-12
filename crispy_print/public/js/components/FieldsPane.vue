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
				<span class="loading-text">Loading fields...</span>
			</div>
		</div>

		<div class="fields-list">
			<div v-if="filteredFields.length === 0" class="empty-state">
				<p v-if="searchQuery" class="empty-message">No fields match "{{ searchQuery }}!"</p>
				<p v-else class="empty-message">No fields available yet!</p>
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
import type { DocField } from "../utils/layout"

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

<style scoped>
.fields-pane {
	display: flex;
	flex-direction: column;
	border: 1px solid #e2e8f0;
	background: rgba(255, 255, 255, 0.9);
}

.fields-pane__header {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px 16px;
}

.fields-pane__header-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.fields-pane__spacer {
	margin-left: auto;
}

.fields-pane__title {
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
	margin: 0;
}

.fields-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
	border: 1px solid #e2e8f0;
	background: #fff;
	color: #4f46e5;
	font-size: 14px;
	font-weight: 600;
	cursor: pointer;
	transition: background-color 0.2s ease, border-color 0.2s ease;
}

.fields-pane__help-btn:hover {
	background: #eef2ff;
	border-color: #c7d2fe;
}

.fields-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	border: 1px solid #e0e7ff;
	background: #fff;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
	color: #334155;
	box-shadow: 0 10px 25px rgba(148, 163, 184, 0.25), 0 8px 10px rgba(148, 163, 184, 0.15);
}

.fields-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.fields-pane__search-area {
	padding: 12px 16px;
}

.search-box {
	display: block;
}

.search-input {
	width: 100%;
	padding: 8px 12px;
	font-size: 14px;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	background: #fff;
	color: #0f172a;
	box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.04);
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.search-input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.loading-indicator {
	margin-top: 8px;
	font-size: 13px;
	color: #475569;
}

.fields-list {
	border: 1px solid #e2e8f0;
	overflow-y: auto;
	padding: 12px 16px 16px;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.empty-state {
	font-size: 14px;
	color: #475569;
}

.empty-message {
	margin: 0;
}

.field-item {
	width: 100%;
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 8px 12px;
	border: 1px dashed #e2e8f0;
	border-radius: 6px;
	background: #fff;
	transition: border-color 0.15s ease, background-color 0.15s ease;
	cursor: grab;
}

.field-item:hover {
	border-color: #cbd5e1;
	background: #f8fafc;
}

.field-label {
	display: block;
	font-size: 14px;
	font-weight: 600;
	color: #0f172a;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}
</style>
