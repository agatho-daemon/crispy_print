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
import { useStore } from "@/composables/useStore"
import TableColumnsDialog from "@/components/TableColumnsDialog.vue"
import type { LayoutSection, LayoutColumn, LayoutField, DocField, TableColumn } from "@/utils/layout"
import { getTableColumns } from "@/utils/layout"

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
