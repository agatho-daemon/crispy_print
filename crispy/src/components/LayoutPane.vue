<template>
	<div class="flex h-full flex-col border border-slate-200 bg-white/90">
		<div class="border-b border-slate-200 px-4 py-3">
			<div class="flex items-center justify-between">
				<h3 class="text-sm font-semibold text-slate-800">Layout Builder</h3>
				<div class="flex gap-2">
					<button class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50" @click="addSection">
						+ Section
					</button>
					<button class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-rose-200 hover:bg-rose-50" @click="resetLayout">
						Reset
					</button>
				</div>
			</div>
			<p class="mt-1 text-xs text-slate-500">
				Drag fields from the left into columns. Reorder sections, columns, and fields in place.
			</p>
		</div>

		<div v-if="!layout" class="flex flex-1 items-center justify-center text-sm text-slate-500">
			No layout loaded. <button class="ml-2 text-indigo-600 underline" @click="ensureLayout">Load default</button>
		</div>

		<div v-else class="flex-1 space-y-4 overflow-auto px-4 py-3">
			<draggable
				v-model="layout.sections"
				:item-key="sectionKey"
				handle=".section-grip"
				:animation="200"
				class="space-y-4"
			>
				<template #item="{ element: section, index: sectionIndex }">
					<div class="rounded-xl border border-slate-200 bg-white p-4 shadow-md shadow-slate-200/70">
						<div class="mb-2 flex items-center justify-between gap-3">
							<div class="flex items-center gap-2">
								<span class="section-grip cursor-grab text-slate-400" title="Drag section">&#8942;</span>
								<input
									v-model="section.label"
									type="text"
									class="w-48 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200"
									placeholder="Section title"
								/>
							</div>
							<div class="flex items-center gap-2">
								<button
									class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50 disabled:cursor-not-allowed disabled:border-slate-200 disabled:bg-slate-100 disabled:text-slate-400"
									:disabled="section.columns.length >= 4"
									@click="addColumn(section)"
								>
									+ Column
								</button>
								<button class="rounded-lg border border-slate-200 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:border-indigo-300 hover:bg-indigo-50" @click="togglePageBreak(section)">
									{{ section.page_break ? "Remove page break" : "Add page break" }}
								</button>
								<button class="px-3 py-1 text-xs font-semibold text-slate-400 hover:text-rose-600"
								@click="removeSection(sectionIndex)">
									&#x2715;
								</button>
							</div>
						</div>

						<div class="grid gap-3" :style="gridStyle(section)">
							<div
								v-for="(column, colIndex) in section.columns"
								:key="colIndex"
								class="flex min-h-[140px] flex-col gap-2 rounded-lg border border-dashed border-slate-300 bg-gradient-to-b from-slate-50 to-slate-100 px-3 py-3"
								@dragover.prevent
								@drop="onDropField($event, column)"
							>
								<div class="flex items-center justify-between text-[11px] text-slate-500">
									<span>Column {{ colIndex + 1 }}</span>
									<button
										v-if="section.columns.length > 1"
										class="text-slate-400 hover:text-rose-700"
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
									class="space-y-2"
								>
									<template #item="{ element: field, index: fieldIndex }">
										<div class="group border border-gray-300 bg-white px-2 py-2">
											<div class="flex items-start justify-between gap-2">
												<div class="flex min-w-0 flex-1 items-center gap-2">
													<span
														class="field-grip -ml-1 cursor-grab pl-0.5 text-xs leading-none text-slate-500"
														title="Drag field"
													>
														&#8942;
													</span>
													<div class="truncate text-sm font-semibold text-slate-900">
														{{ field.label }}
													</div>
												</div>
												<button
													class="self-start text-sm text-slate-400 hover:text-rose-600 opacity-0 group-hover:opacity-100 pointer-events-none group-hover:pointer-events-auto transition-opacity duration-150"
													@click="removeField(column, fieldIndex)"
													title="Remove"
													type="button"
												>
													&#x2715;
												</button>
											</div>
										</div>
									</template>
									</draggable>

								<div v-if="!column.fields.length" class="rounded-lg border border-dashed border-slate-300 bg-white px-3 py-3 text-center text-xs text-slate-400">
									Drop fields here
								</div>
							</div>
						</div>

						<div v-if="section.page_break" class="mt-2 border-t border-dashed border-slate-300 pt-2 text-center text-xs text-slate-500">
							Page Break
						</div>
					</div>
				</template>
			</draggable>
		</div>
	</div>
</template>

<script setup lang="ts">
import draggable from "vuedraggable"
import { onMounted, watch } from "vue"
import { useStore } from "@/composables/useStore"
import type { LayoutSection, LayoutColumn, LayoutField, DocField } from "@/utils/layout"

type Section = LayoutSection & { id?: number; page_break?: boolean }
type Column = LayoutColumn
type Field = LayoutField

const store = useStore()
const layout = store.layout

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
	;(section as any).page_break = !(section as any).page_break
	store.markDirty()
}

function onDropField(event: DragEvent, column: Column) {
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
		if (parsed.fieldtype === "Table" && parsed.options) {
			field.table_columns = []
		}
		column.fields.push(field)
		store.markDirty()
	} catch (e) {
		console.warn("Failed to drop field", e)
	}
}

function resetLayout() {
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
</script>
