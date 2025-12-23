<template>
	<div class="layout-pane">
		<div class="layout-pane__header">
			<div class="layout-pane__header-row">
				<h3 class="layout-pane__title">Layout Builder</h3>
				<div class="layout-pane__controls">
					<button class="lp-btn lp-btn--secondary" @click="resetLayout">Reset</button>
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
								<li>Use the &#8943; menu on a section for add/remove/page break/orientation.</li>
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
								<button
									type="button"
									class="section-card__menu-btn"
									title="Section menu"
									@click.stop="toggleSectionMenu(section, sectionIndex, $event)"
								>
									&#8943;
								</button>
								<div
									v-if="openSectionMenuId === getSectionMenuId(section, sectionIndex)"
									class="section-card__menu"
									:style="sectionMenuStyle"
									@click.stop
								>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onAddSectionAbove(sectionIndex)"
									>
										Add section above
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onAddSectionBelow(sectionIndex)"
									>
										Add section below
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										:disabled="section.columns.length >= 4"
										@click="onAddColumn(section)"
									>
										Add column
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										:disabled="section.columns.length <= 1"
										@click="onRemoveLastColumn(section)"
									>
										Remove column
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onTogglePageBreak(section)"
									>
										{{ section.page_break ? "Remove page break" : "Add page break" }}
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onToggleFieldOrientation(section)"
									>
										Field orientation ({{ getFieldOrientationLabel(section) }})
									</button>
									<div class="section-card__menu-divider"></div>
									<button
										type="button"
										class="section-card__menu-item section-card__menu-item--danger"
										@click="onRemoveSection(sectionIndex)"
									>
										Remove section
									</button>
								</div>
							</div>
						</div>

						<div class="section-grid" :style="gridStyle(section)">
							<div
								v-for="(column, colIndex) in section.columns"
								:key="colIndex"
								:class="['section-column', { 'section-column--empty': !column.fields.length }]"
								@dragover.prevent
								@drop="onDropField($event, column)"
							>
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
													<span class="field-grip" title="Drag field"> &#8942; </span>
													<input
														v-model="field.label"
														type="text"
														class="field-card__label field-card__label-input"
														:placeholder="field.fieldname"
														@blur="markDirty()"
														@keydown.enter.prevent="onLabelEnter"
													/>
												</div>
												<div class="field-card__actions">
													<button
														class="lp-btn lp-btn--small lp-btn--icon"
														type="button"
														@click="cycleAlignment(field)"
														:title="`Alignment: ${field.align || 'left'}`"
													>
														{{ getAlignIcon(field.align) }}
													</button>
													<button
														class="lp-btn lp-btn--small lp-btn--icon lp-btn--label-toggle"
														type="button"
														@click="toggleFieldLabel(field)"
														:title="field.label?.trim() ? 'Hide label' : 'Show label'"
													>
														Aa
													</button>
													<button
														v-if="field.fieldtype === 'Table'"
														class="lp-btn lp-btn--small"
														type="button"
														@click="configureColumns(field)"
													>
														Configure columns
													</button>
													<button
														class="field-card__remove"
														@click="removeField(column, fieldIndex)"
														title="Remove"
														type="button"
													>
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

						<div v-if="section.page_break" class="section-page-break">Page Break</div>
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
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import { useStore } from "../composables/useStore"
import TableColumnsDialog from "../components/TableColumnsDialog.vue"
import type {
	LayoutSection,
	LayoutColumn,
	LayoutField,
	DocField,
	TableColumn,
} from "../utils/layout"
import { getTableColumns } from "../utils/layout"

type Section = LayoutSection & {
	id?: number
	page_break?: boolean
	field_orientation?: "left-right" | "top-down"
}
type Column = LayoutColumn
type Field = LayoutField
type TableEditorContext = {
	field: Field
}

const store = useStore()
const layout = store.layout
const columnEditor = ref<TableEditorContext | null>(null)
const editingColumns = ref<TableColumn[]>([])

const openSectionMenuId = ref<string | null>(null)
const sectionMenuStyle = ref<Record<string, string>>({})

const sectionKey = (section: Section, index: number) => {
	return (section as any).id || index
}

function getSectionMenuId(section: Section, index: number) {
	return String(section.id || index)
}

function closeSectionMenu() {
	openSectionMenuId.value = null
	sectionMenuStyle.value = {}
}

function toggleSectionMenu(section: Section, index: number, event: MouseEvent) {
	const id = getSectionMenuId(section, index)
	if (openSectionMenuId.value === id) {
		closeSectionMenu()
		return
	}

	openSectionMenuId.value = id

	const target = event.currentTarget as HTMLElement | null
	if (!target) return

	const rect = target.getBoundingClientRect()
	const top = rect.bottom + 6
	const left = rect.right

	sectionMenuStyle.value = {
		position: "fixed",
		top: `${top}px`,
		left: `${left}px`,
		transform: "translateX(-100%)",
		zIndex: "1000",
	}
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

function ensureAtLeastOneSection() {
	if (!layout.value) {
		layout.value = { sections: [] }
	}
	if (!layout.value.sections?.length) {
		layout.value.sections = [createEmptySection()]
	}
}

onMounted(() => {
	ensureLayout()
	ensureAtLeastOneSection()
})

const onDocClick = () => closeSectionMenu()
const onKeyDown = (e: KeyboardEvent) => {
	if (e.key === "Escape") closeSectionMenu()
}

onMounted(() => {
	document.addEventListener("click", onDocClick)
	document.addEventListener("keydown", onKeyDown)
})

onBeforeUnmount(() => {
	document.removeEventListener("click", onDocClick)
	document.removeEventListener("keydown", onKeyDown)
})

watch(
	() => store.meta.value,
	() => {
		ensureLayout()
		ensureAtLeastOneSection()
	},
	{ immediate: false }
)

function addSection() {
	if (!layout.value) {
		layout.value = { sections: [] }
	}
	layout.value.sections.push(createEmptySection())
	store.markDirty()
}

function addSectionAbove(index: number) {
	if (!layout.value) {
		layout.value = { sections: [] }
	}
	layout.value.sections.splice(Math.max(0, index), 0, createEmptySection())
	store.markDirty()
}

function onAddSectionAbove(index: number) {
	addSectionAbove(index)
	closeSectionMenu()
}

function addSectionBelow(index: number) {
	if (!layout.value) {
		layout.value = { sections: [] }
	}
	layout.value.sections.splice(Math.max(0, index + 1), 0, createEmptySection())
	store.markDirty()
}

function onAddSectionBelow(index: number) {
	addSectionBelow(index)
	closeSectionMenu()
}

function createEmptySection(): Section {
	return {
		label: "",
		columns: [{ label: "", fields: [] }],
		id: Date.now() + Math.random(),
		field_orientation: "left-right",
	}
}

function removeSection(index: number) {
	layout.value?.sections.splice(index, 1)
	store.markDirty()
}

function onRemoveSection(index: number) {
	removeSection(index)
	closeSectionMenu()
}

function addColumn(section: Section) {
	if (!section.columns) section.columns = []
	if (section.columns.length >= 4) {
		return
	}
	section.columns.push({ label: "", fields: [] })
	store.markDirty()
}

function onAddColumn(section: Section) {
	addColumn(section)
	closeSectionMenu()
}

function removeColumn(section: Section, colIndex: number) {
	if (section.columns.length <= 1) return
	const removed = section.columns.splice(colIndex, 1)[0]
	const targetIndex = Math.max(colIndex - 1, 0)
	section.columns[targetIndex].fields.push(...removed.fields)
	store.markDirty()
}

function removeLastColumn(section: Section) {
	if (section.columns.length <= 1) return
	removeColumn(section, section.columns.length - 1)
}

function onRemoveLastColumn(section: Section) {
	removeLastColumn(section)
	closeSectionMenu()
}

function removeField(column: Column, fieldIndex: number) {
	column.fields.splice(fieldIndex, 1)
	store.markDirty()
}

function cycleAlignment(field: Field) {
	// Cycle through: left → center → right → left
	const current = field.align || "left"
	const alignments: Array<"left" | "center" | "right"> = ["left", "center", "right"]
	const currentIndex = alignments.indexOf(current)
	const nextIndex = (currentIndex + 1) % alignments.length
	field.align = alignments[nextIndex]
	store.markDirty()
}

function getAlignIcon(align?: "left" | "center" | "right"): string {
	// Unicode alignment icons
	switch (align) {
		case "center":
			return "≡" // Center align
		case "right":
			return "⇥" // Right align
		default:
			return "⇤" // Left align
	}
}

function getDefaultAlignment(fieldtype?: string): "left" | "center" | "right" {
	// Numeric fields default to right alignment, like Frappe
	const numericTypes = ["Int", "Float", "Currency", "Percent"]
	return numericTypes.includes(fieldtype || "") ? "right" : "left"
}

function togglePageBreak(section: Section) {
	;(section as any).page_break = !(section as any).page_break
	store.markDirty()
}

function onTogglePageBreak(section: Section) {
	togglePageBreak(section)
	closeSectionMenu()
}

function toggleFieldOrientation(section: Section) {
	const current = section.field_orientation || "left-right"
	section.field_orientation = current === "left-right" ? "top-down" : "left-right"
	store.markDirty()
}

function onToggleFieldOrientation(section: Section) {
	toggleFieldOrientation(section)
	closeSectionMenu()
}

function getFieldOrientationLabel(section: Section) {
	return (section.field_orientation || "left-right") === "left-right" ? "Left-Right" : "Top-Down"
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
			align: getDefaultAlignment(parsed.fieldtype), // Add default alignment
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
			ensureAtLeastOneSection()
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
		ensureAtLeastOneSection()
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

function markDirty() {
	store.markDirty()
}

function onLabelEnter(event: KeyboardEvent) {
	const el = event.target as HTMLInputElement | null
	el?.blur()
}

function getDefaultLabel(field: Field): string {
	const meta = store.meta.value as any
	const df = meta?.fields?.find?.((f: any) => f?.fieldname === field.fieldname)
	return df?.label || field.fieldname
}

function toggleFieldLabel(field: Field) {
	const current = (field.label || "").trim()
	if (current) {
		field.label = ""
	} else {
		field.label = getDefaultLabel(field)
	}
	store.markDirty()
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
	transition:
		background-color 0.2s ease,
		border-color 0.2s ease;
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
	transition:
		border-color 0.15s ease,
		box-shadow 0.15s ease;
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

.section-card__menu-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 28px;
	height: 28px;
	border-radius: 8px;
	border: none;
	background: transparent;
	color: #475569;
	cursor: pointer;
	font-size: 18px;
	line-height: 1;
	transition:
		background-color 0.2s ease,
		border-color 0.2s ease;
}

.section-card__menu-btn:hover {
	background: #f8fafc;
}

.section-card__menu {
	border-radius: 12px;
	border: 1px solid #e2e8f0;
	background: #fff;
	padding: 6px;
	width: 260px;
	max-width: calc(100vw - 32px);
	box-shadow:
		0 10px 25px rgba(148, 163, 184, 0.25),
		0 8px 10px rgba(148, 163, 184, 0.15);
}

.section-card__menu-item {
	width: 100%;
	text-align: left;
	border: 0;
	background: transparent;
	padding: 8px 10px;
	border-radius: 8px;
	font-size: 13px;
	color: #0f172a;
	cursor: pointer;
	white-space: nowrap;
}

.section-card__menu-item:hover {
	background: #f1f5f9;
}

.section-card__menu-item:disabled {
	color: #94a3b8;
	cursor: not-allowed;
}

.section-card__menu-divider {
	height: 1px;
	margin: 6px 6px;
	background: #e2e8f0;
}

.section-card__menu-item--danger {
	color: #b91c1c;
}

.section-card__menu-item--danger:hover {
	background: #fee2e2;
}

.section-grid {
	display: grid;
	gap: 12px;
}

.section-column {
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding: 0;
	min-height: 0;
}

.section-column--empty {
	min-height: 56px;
	border: 1px dashed #e2e8f0;
	border-radius: 12px;
	background: #fafafa;
	padding: 10px;
	transition:
		border-color 0.15s ease,
		background-color 0.15s ease;
}

.section-column--empty:hover,
.section-column--empty:focus-within {
	border-color: #c7d2fe;
	background: rgba(238, 242, 255, 0.25);
}

.section-column__fields {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.section-column__empty {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	text-align: center;
	font-size: 12px;
	color: #94a3b8;
	padding: 12px;
}

.field-card {
	border: 1px dashed #cbd5e1;
	background: rgba(255, 255, 255, 0.9);
	padding: 12px;
	border-radius: 8px;
	transition:
		border-color 0.15s ease,
		background-color 0.15s ease;
}

.field-card:hover,
.field-card:focus-within {
	border-color: #c7d2fe;
	background: #fff;
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

.field-card__label-input {
	width: 100%;
	border: none;
	outline: none;
	background: transparent;
	padding: 0;
	min-width: 0;
}

.field-card__label-input:focus {
	background: #fff;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.18);
	border-radius: 6px;
	padding: 4px 6px;
}

.field-card__actions {
	display: flex;
	align-items: center;
	gap: 8px;
	opacity: 0;
	pointer-events: none;
	transition: opacity 0.15s ease;
}

.field-card:hover .field-card__actions,
.field-card:focus-within .field-card__actions {
	opacity: 1;
	pointer-events: auto;
}

.field-card__remove {
	background: transparent;
	border: none;
	cursor: pointer;
	color: #cbd5e1;
	transition: color 0.15s ease;
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
	transition:
		border-color 0.15s ease,
		background-color 0.15s ease,
		color 0.15s ease;
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

.lp-btn--icon {
	padding: 8px 12px;
	min-width: 40px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	font-size: 18px;
	font-family: monospace;
	font-weight: bold;
}

.lp-btn--label-toggle {
	font-size: 14px;
	font-family: inherit;
	letter-spacing: -0.02em;
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
