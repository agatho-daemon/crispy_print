<template>
	<div
		class="fields-pane bg-white/90 border border-slate-200 rounded-xl h-full flex flex-col"
	>
		<div
			class="pane-header border-b border-slate-200 bg-gradient-to-r from-slate-50 via-white to-slate-50 px-4 py-3"
		>
			<div class="flex items-center justify-between gap-3">
				<h3 class="header-title text-sm font-semibold text-slate-800">Fields</h3>
				<span class="badge-soft inline-flex items-center gap-2 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] border border-indigo-100 rounded-full bg-indigo-50 text-indigo-700 shadow-inner">
					Drag to layout
				</span>
			</div>
			<div class="search-box mt-3">
				<input
					v-model="searchQuery"
					type="text"
					:placeholder="`Search ${filteredFields.length} fields...`"
					class="search-input w-full px-3 py-2 text-sm rounded-lg border border-slate-200 bg-white focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-indigo-400 shadow-inner"
				/>
			</div>
			<div v-if="loading" class="loading-indicator">
				<span class="loading-text">Loading fields</span>
			</div>
		</div>

		<div class="fields-list flex-1 overflow-y-auto px-3 pb-4 space-y-3">
			<div class="list-header">
				<span
					v-if="searchQuery"
					class="pill pill-muted inline-flex items-center gap-2 px-3 py-1 text-[11px] font-semibold rounded-full border border-slate-200 bg-slate-100 text-slate-700"
				>
					Filtered
				</span>
			</div>

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
				class="field-item w-full flex flex-col gap-2 rounded-xl border px-3 py-3 bg-gradient-to-br from-white via-indigo-50 to-slate-50 hover:from-indigo-50 hover:to-cyan-50 transition-all"
				draggable="true"
				@dragstart="onFieldDragStart($event, field)"
				:title="`${field.label} (${field.fieldtype})`"
			>
				<div
					class="field-label block text-sm font-semibold text-slate-900 truncate"
					:title="field.label"
				>
					{{ field.label }}
				</div>
				<div class="field-meta flex items-center gap-2 min-w-0">
					<span
						class="field-name block text-[11px] text-slate-500 truncate min-w-0 flex-1"
						:title="field.fieldname"
					>
						{{ field.fieldname }}
					</span>
					<span
						class="field-type shrink-0 inline-flex items-center justify-center px-3 py-1 text-[8px] font-bold uppercase tracking-wide rounded-full border bg-indigo-50 text-indigo-700"
						:class="`type-${(field.fieldtype || 'unknown').toLowerCase()}`"
					>
						{{ field.fieldtype || "Unknown" }}
					</span>
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

<style scoped>
/* Custom styles retained for reference; Tailwind utilities currently drive the visuals.
.fields-pane {
	display: flex;
	flex-direction: column;
	overflow: hidden;
	height: 100%;
	min-height: 0;
}

.pane-header {
	padding: 16px;
}

.badge-soft {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 6px 10px;
	font-size: 11px;
	font-weight: 700;
	color: #4338ca;
	background: #eef2ff;
	border: 1px solid #e0e7ff;
	border-radius: 999px;
	text-transform: uppercase;
	letter-spacing: 0.05em;
	box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.badge-soft::before {
	content: "•";
	color: #7c3aed;
}

.search-input {
	transition: border-color 0.2s, box-shadow 0.2s, transform 0.1s;
}

.loading-indicator {
	padding: 8px 0;
}

.loading-text {
	font-size: 12px;
	color: #6b7280;
	font-style: italic;
}

.fields-list {
	flex: 1;
	overflow-y: auto;
	padding: 8px;
	max-height: calc(100vh - 220px);
	min-height: 16rem;
	background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.06), transparent 35%),
		radial-gradient(circle at 90% 10%, rgba(14, 165, 233, 0.06), transparent 30%),
		linear-gradient(180deg, rgba(248, 250, 252, 0.9) 0%, rgba(241, 245, 249, 0.9) 100%);
	border-left: 1px solid #e0e7ff;
	border-right: 1px solid #e0f2fe;
}

.list-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 4px 6px 4px 6px;
}

.pill {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	font-size: 11px;
	color: #1f2937;
	background: #eef2ff;
	border: 1px solid #e0e7ff;
	border-radius: 999px;
	padding: 4px 10px;
	font-weight: 600;
}

.pill::before {
	content: "";
	width: 8px;
	height: 8px;
	border-radius: 999px;
	background: #4f46e5;
}

.pill-muted {
	background: #f3f4f6;
	border-color: #e5e7eb;
	color: #4b5563;
}

.empty-state {
	padding: 32px 16px;
	text-align: center;
}

.empty-message {
	font-size: 13px;
	color: #9ca3af;
	margin: 0;
}

.field-item {
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 10px 12px;
	margin-bottom: 4px;
	background: linear-gradient(135deg, #ffffff 0%, #eef2ff 100%);
	border: 1px solid #c7d2fe;
	border-radius: 12px;
	cursor: grab;
	transition: all 0.2s ease;
	box-shadow: 0 10px 30px rgba(79, 70, 229, 0.1), 0 1px 3px rgba(15, 23, 42, 0.08);
	width: 100%;
	position: relative;
	overflow: hidden;
}

.field-item:hover {
	background: linear-gradient(135deg, #e0e7ff 0%, #e0f2fe 100%);
	border-color: #93c5fd;
	box-shadow: 0 14px 40px rgba(79, 70, 229, 0.2);
	transform: translateY(-1px) scale(1.01);
}

.field-item:active {
	cursor: grabbing;
	transform: translateY(0);
}

.field-item::after {
	content: "";
	position: absolute;
	inset: 0;
	pointer-events: none;
	background: linear-gradient(120deg, rgba(99, 102, 241, 0.12), rgba(14, 165, 233, 0.12));
	opacity: 0;
	transition: opacity 0.2s ease;
}

.field-item:hover::after {
	opacity: 1;
}

.field-main {
	display: flex;
	flex-direction: column;
	gap: 2px;
	min-width: 0;
	flex: 1;
}

.field-label {
	font-size: 13px;
	font-weight: 600;
	color: #111827;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
	font-weight: 700;
}

.field-name {
	font-size: 11px;
	color: #6b7280;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.field-type {
	font-size: 11px;
	color: #312e81;
	background: linear-gradient(120deg, #eef2ff, #c7d2fe);
	padding: 6px 12px;
	border-radius: 999px;
	border: 1px solid #a5b4fc;
	white-space: nowrap;
	font-weight: 700;
	letter-spacing: 0.04em;
	text-transform: uppercase;
	box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
	align-self: center;
	flex-shrink: 0;
	margin-left: 12px;
}

 Field type color coding 
.field-type.type-data,
.field-type.type-text {
	color: #059669;
	background: #ecfdf5;
	border-color: #d1fae5;
}

.field-type.type-link {
	color: #1d4ed8;
	background: #e0ebff;
	border-color: #bfdbfe;
}

.field-type.type-select {
	color: #8b5cf6;
	background: #f5f3ff;
	border-color: #ede9fe;
}

.field-type.type-date,
.field-type.type-datetime {
	color: #f59e0b;
	background: #fffbeb;
	border-color: #fef3c7;
}

.field-type.type-currency,
.field-type.type-float,
.field-type.type-int {
	color: #10b981;
	background: #f0fdf4;
	border-color: #dcfce7;
}

.field-type.type-table {
	color: #ef4444;
	background: #fef2f2;
	border-color: #fee2e2;
}

.field-type.type-check {
	color: #06b6d4;
	background: #ecfeff;
	border-color: #cffafe;
}

 Scrollbar styling 
.fields-list::-webkit-scrollbar {
	width: 6px;
}

.fields-list::-webkit-scrollbar-track {
	background: #f9fafb;
}

.fields-list::-webkit-scrollbar-thumb {
	background: #d1d5db;
	border-radius: 3px;
}

.fields-list::-webkit-scrollbar-thumb:hover {
	background: #9ca3af;
}
*/

.loading-text {
	position: relative;
}

.loading-text::after {
	content: "...";
	display: inline-block;
	width: 0;
	overflow: hidden;
	vertical-align: bottom;
	animation: dots 1s steps(4, end) infinite;
}

@keyframes dots {
	to {
		width: 1.2em;
	}
}
</style>
