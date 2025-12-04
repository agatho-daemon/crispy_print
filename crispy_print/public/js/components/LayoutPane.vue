<template>
	<div class="layout-pane">
		<div class="layout-pane__header">
			<div class="layout-pane__header-row">
				<h3 class="layout-pane__title">Layout Builder</h3>
				<div class="layout-pane__controls">
					<button class="lp-btn" @click="addSection">
						+ Section
					</button>
					<button class="lp-btn lp-btn--secondary" @click="resetLayout">
						Reset
					</button>
					<div class="layout-pane__spacer"></div>
					<div>
						<button
							type="button"
							class="layout-pane__help-btn"
							popovertarget="layout-help"
							popovertargetaction="toggle"
							title="Toggle help"
						>
							?
						</button>
						<div id="layout-help" popover class="layout-pane__help-popover">
							<ul class="layout-pane__help-list">
								<li>Drag fields from Fields pane into columns.</li>
								<li>Use handles to reorder sections, columns, and fields in place.</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div v-if="!layout" class="layout-pane__empty">
			No layout loaded.
			<button class="lp-link" @click="ensureLayout">Load default</button>
		</div>

		<div v-else class="layout-pane__body">
			<draggable
				v-model="layout.sections"
				:item-key="sectionKey"
				handle=".section-grip"
				:animation="200"
				class="layout-pane__sections"
			>
				<template #item="{ element: section, index: sectionIndex }">
					<div class="section-card">
						<div class="section-card__header">
							<div class="section-card__title-row">
								<span class="section-grip" title="Drag section">&#8942;</span>
								<input
									v-model="section.label"
									type="text"
									class="section-title-input"
									placeholder="Section title"
								/>
							</div>
							<div class="section-card__actions">
								<button class="lp-btn" :disabled="section.columns.length >= 4" @click="addColumn(section)">
									+ Column
								</button>
								<button class="lp-btn" @click="togglePageBreak(section)">
									{{ section.page_break ? "Remove page break" : "Add page break" }}
								</button>
								<button class="section-card__remove" @click="removeSection(sectionIndex)">
									&#x2715;
								</button>
							</div>
						</div>

						<div class="section-grid" :style="gridStyle(section)">
							<div
								v-for="(column, colIndex) in section.columns"
								:key="colIndex"
								class="section-column"
								@dragover.prevent
								@drop="onDropField($event, column)"
							>
								<div class="section-column__header">
									<span>Column {{ colIndex + 1 }}</span>
									<button
										v-if="section.columns.length > 1"
										class="section-column__remove"
										title="Remove column"
										@click="removeColumn(section, colIndex)"
									>
										&#x2715;
									</button>
								</div>

								<draggable
									v-model="column.fields"
									group="layout-fields"
									item-key="fieldname"
									handle=".field-grip"
									:animation="150"
									class="section-column__fields"
								>
									<template #item="{ element: field, index: fieldIndex }">
										<div class="field-card">
											<div class="field-card__row">
												<div class="field-card__info">
													<span class="field-grip" title="Drag field">
														&#8942;
													</span>
													<div class="field-card__label">
														{{ field.label }}
													</div>
												</div>
												<div class="field-card__actions">
													<button
														v-if="field.fieldtype === 'Table'"
														class="lp-btn lp-btn--small"
														type="button"
														@click="configureColumns(field)"
													>
														Configure columns
													</button>
													<button class="field-card__remove" @click="removeField(column, fieldIndex)" title="Remove" type="button">
														&#x2715;
													</button>
												</div>
											</div>
											<div
												v-if="field.fieldtype === 'Table' && field.table_columns?.length"
												class="field-card__columns"
											>
												<div
													v-for="col in field.table_columns"
													:key="col.fieldname"
													class="field-card__column-pill"
													:title="`Width: ${col.width ?? 'auto'}%`"
												>
													{{ col.label }}
												</div>
											</div>
										</div>
									</template>
								</draggable>

								<div v-if="!column.fields.length" class="section-column__empty">
									Drop fields here
								</div>
							</div>
						</div>

						<div v-if="section.page_break" class="section-page-break">
							Page Break
						</div>
					</div>
				</template>
			</draggable>
		</div>
		<TableColumnsDialog
			v-if="columnEditor"
			:model-value="editingColumns"
			:doctype="columnEditor.field.options || ''"
			@update:modelValue="onColumnsUpdate"
			@close="closeColumnEditor"
		/>
	</div>
</template>

<script setup lang="ts">
import draggable from "vuedraggable"
import { onMounted, ref, watch } from "vue"
import { useStore } from "../composables/useStore"
import TableColumnsDialog from "../components/TableColumnsDialog.vue"
import type { LayoutSection, LayoutColumn, LayoutField, DocField, TableColumn } from "../utils/layout"
import { getTableColumns } from "../utils/layout"

declare const frappe: any
declare const __: any

type Section = LayoutSection & { id?: number; page_break?: boolean }
type Column = LayoutColumn
type Field = LayoutField
type TableEditorContext = {
	field: Field
}

const store = useStore()
const layout = store.layout
const columnEditor = ref<TableEditorContext | null>(null)
const editingColumns = ref<TableColumn[]>([])

const sectionKey = (section: Section, index: number) => {
	return (section as any).id || index
}

function ensureLayout() {
	if (!layout.value || !layout.value.sections?.length) {
		if (!store.meta.value) return
		const fresh = store.getDefaultLayout()
		if (fresh) {
			store.layout.value = fresh
			store.markDirty()
		}
	}
}

onMounted(() => {
	ensureLayout()
})

watch(
	() => store.meta.value,
	() => ensureLayout(),
	{ immediate: false }
)

function addSection() {
	if (!layout.value) {
		layout.value = { sections: [] }
	}
	const newSection: Section = {
		label: "",
		columns: [{ label: "", fields: [] }],
		id: Date.now() + Math.random(),
	}
	layout.value.sections.push(newSection)
	store.markDirty()
}

function removeSection(index: number) {
	layout.value?.sections.splice(index, 1)
	store.markDirty()
}

function addColumn(section: Section) {
	if (!section.columns) section.columns = []
	if (section.columns.length >= 4) {
		return
	}
	section.columns.push({ label: "", fields: [] })
	store.markDirty()
}

function removeColumn(section: Section, colIndex: number) {
	if (section.columns.length <= 1) return
	const removed = section.columns.splice(colIndex, 1)[0]
	const targetIndex = Math.max(colIndex - 1, 0)
	section.columns[targetIndex].fields.push(...removed.fields)
	store.markDirty()
}

function removeField(column: Column, fieldIndex: number) {
	column.fields.splice(fieldIndex, 1)
	store.markDirty()
}

function togglePageBreak(section: Section) {
	; (section as any).page_break = !(section as any).page_break
	store.markDirty()
}

async function ensureTableColumns(field: Field) {
	if (field.fieldtype !== "Table" || (field.table_columns && field.table_columns.length)) {
		return
	}
	if (!field.options) {
		field.table_columns = []
		return
	}
	try {
		if (typeof frappe !== "undefined" && frappe.model?.with_doctype) {
			await new Promise<void>((resolve) => {
				frappe.model.with_doctype(field.options, () => resolve())
			})
		}
		field.table_columns = getTableColumns(field.options)
	} catch (e) {
		field.table_columns = []
		console.warn("Failed to load table columns", e)
	}
}

async function onDropField(event: DragEvent, column: Column) {
	if (!event.dataTransfer) return
	try {
		const data = event.dataTransfer.getData("application/json")
		if (!data) return
		const parsed: DocField = JSON.parse(data)
		if (!parsed.fieldname) return
		const field: LayoutField = {
			fieldname: parsed.fieldname,
			label: parsed.label || parsed.fieldname,
			fieldtype: parsed.fieldtype || "Data",
		}
		if (parsed.fieldtype === "Table") {
			field.table_columns = []
			field.options = parsed.options
			await ensureTableColumns(field)
		}
		column.fields.push(field)
		store.markDirty()
	} catch (e) {
		console.warn("Failed to drop field", e)
	}
}

function resetLayout() {
	const confirmReset = () => {
		const fresh = store.getDefaultLayout()
		if (fresh) {
			store.layout.value = fresh
			store.markDirty()
		}
	}

	if (typeof frappe !== "undefined" && typeof frappe.confirm === "function") {
		frappe.confirm(
			__("Reset layout to default? This will discard your changes."),
			() => confirmReset(),
			() => {}
		)
		return
	}

	if (!window.confirm("Reset layout to default? This will discard your changes.")) {
		return
	}
	const fresh = store.getDefaultLayout()
	if (fresh) {
		store.layout.value = fresh
		store.markDirty()
	}
}

function gridStyle(section: Section) {
	const cols = Math.max(1, section.columns.length)
	return {
		gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
	}
}

async function configureColumns(field: Field) {
	if (field.fieldtype !== "Table") return
	await ensureTableColumns(field)
	editingColumns.value = JSON.parse(JSON.stringify(field.table_columns || []))
	columnEditor.value = { field }
}

function onColumnsUpdate(columns: TableColumn[]) {
	if (!columnEditor.value) return
	editingColumns.value = JSON.parse(JSON.stringify(columns || []))
	columnEditor.value.field.table_columns = columns
	store.markDirty()
}

function closeColumnEditor() {
	columnEditor.value = null
}
</script>

<style scoped>
/* LayoutPane.vue */
.layout-pane {
	display: flex;
	flex-direction: column;
	overflow-y: auto;
	border: 1px solid #e2e8f0;
	background: rgba(255, 255, 255, 0.9);
}

.layout-pane__header {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px;
}

.layout-pane__header-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
}

.layout-pane__title {
	margin: 0;
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
}

.layout-pane__controls {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}

.layout-pane__spacer {
	margin-left: auto;
}

.layout-pane__help-btn {
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

.layout-pane__help-btn:hover {
	background: #eef2ff;
	border-color: #c7d2fe;
}

.layout-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	border: 1px solid #e0e7ff;
	background: #fff;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
	color: #334155;
	box-shadow:
		0 10px 25px rgba(148, 163, 184, 0.25),
		0 8px 10px rgba(148, 163, 184, 0.15);
}

.layout-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.layout-pane__empty {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	font-size: 14px;
	color: #64748b;
	padding: 12px;
}

.layout-pane__body {
	flex: 1;
	overflow: auto;
	padding: 12px 16px;
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.layout-pane__sections {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.section-card {
	border: 1px solid #e2e8f0;
	background: #fff;
	padding: 16px;
	border-radius: 12px;
	box-shadow:
		0 8px 20px rgba(226, 232, 240, 0.55),
		0 2px 6px rgba(148, 163, 184, 0.25);
}

.section-card__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	margin-bottom: 8px;
}

.section-card__title-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.section-grip {
	cursor: grab;
	color: #94a3b8;
	font-size: 16px;
}

.section-title-input {
	width: 190px;
	padding: 8px 12px;
	font-size: 14px;
	font-weight: 600;
	color: #0f172a;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	outline: none;
	background: #fff;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.section-title-input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.section-card__actions {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}

.section-card__remove {
	padding: 6px 10px;
	font-size: 12px;
	font-weight: 600;
	color: #94a3b8;
	background: transparent;
	border: none;
	cursor: pointer;
	transition: color 0.15s ease;
}

.section-card__remove:hover {
	color: #e11d48;
}

.section-grid {
	display: grid;
	gap: 12px;
}

.section-column {
	min-height: 140px;
	display: flex;
	flex-direction: column;
	gap: 8px;
	border: 1px dashed #cbd5e1;
	border-radius: 10px;
	background: linear-gradient(180deg, #f8fafc 0%, #e2e8f0 100%);
	padding: 12px;
}

.section-column__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	font-size: 11px;
	color: #64748b;
}

.section-column__remove {
	background: transparent;
	border: none;
	cursor: pointer;
	color: #94a3b8;
	transition: color 0.15s ease;
}

.section-column__remove:hover {
	color: #e11d48;
}

.section-column__fields {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.section-column__empty {
	border: 1px dashed #cbd5e1;
	border-radius: 10px;
	background: #fff;
	padding: 12px;
	text-align: center;
	font-size: 12px;
	color: #94a3b8;
}

.field-card {
	border: 1px solid #d1d5db;
	background: #fff;
	padding: 10px;
	border-radius: 8px;
}

.field-card__row {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 8px;
}

.field-card__info {
	display: flex;
	align-items: center;
	gap: 8px;
	min-width: 0;
	flex: 1;
}

.field-grip {
	cursor: grab;
	color: #94a3b8;
	font-size: 12px;
	line-height: 1;
}

.field-card__label {
	font-size: 14px;
	font-weight: 600;
	color: #0f172a;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.field-card__actions {
	display: flex;
	align-items: center;
	gap: 8px;
}

.field-card__remove {
	background: transparent;
	border: none;
	cursor: pointer;
	color: #cbd5e1;
	opacity: 0;
	transition: color 0.15s ease, opacity 0.15s ease;
}

.field-card:hover .field-card__remove {
	opacity: 1;
	pointer-events: auto;
}

.field-card__remove:hover {
	color: #e11d48;
}

.field-card__columns {
	margin-top: 8px;
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	font-size: 11px;
	color: #64748b;
}

.field-card__column-pill {
	border: 1px solid #e2e8f0;
	background: #f8fafc;
	border-radius: 6px;
	padding: 4px 8px;
}

.section-page-break {
	margin-top: 8px;
	border-top: 1px dashed #cbd5e1;
	padding-top: 8px;
	text-align: center;
	font-size: 12px;
	color: #64748b;
}

.lp-btn {
	border: 1px solid #e2e8f0;
	background: #fff;
	color: #334155;
	font-size: 12px;
	font-weight: 600;
	border-radius: 8px;
	padding: 6px 12px;
	cursor: pointer;
	transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}

.lp-btn:hover {
	border-color: #c7d2fe;
	background: #eef2ff;
}

.lp-btn:disabled {
	cursor: not-allowed;
	border-color: #e2e8f0;
	background: #f8fafc;
	color: #cbd5e1;
}

.lp-btn--secondary {
	border-color: #fecdd3;
	color: #be123c;
}

.lp-btn--secondary:hover {
	background: #ffe4e6;
	border-color: #fecdd3;
}

.lp-btn--small {
	padding: 4px 8px;
	font-size: 11px;
}

.lp-link {
	margin-left: 8px;
	padding: 0;
	border: none;
	background: transparent;
	color: #4f46e5;
	text-decoration: underline;
	font-size: 14px;
	cursor: pointer;
}

</style>