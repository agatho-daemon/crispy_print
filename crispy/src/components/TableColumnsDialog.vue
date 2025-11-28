<template>
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 px-4">
		<div class="w-full max-w-3xl rounded-2xl bg-white shadow-2xl">
			<div class="flex items-start justify-between border-b border-slate-200 px-5 py-4">
				<div>
					<h3 class="text-base font-semibold text-slate-900">Configure columns</h3>
					<p class="text-sm text-slate-600">
						Drag to reorder. Widths are percentages; total should stay at or below 100.
					</p>
				</div>
				<button
					class="rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
					@click="$emit('close')"
					type="button"
				>
					&#x2715;
				</button>
			</div>

			<div class="px-5 py-4">
				<div class="mb-3 flex items-center justify-between text-sm text-slate-600">
					<span>Columns</span>
					<span :class="totalWidth > 100 ? 'text-rose-600' : 'text-slate-500'">
						Total width: {{ totalWidth }}%
					</span>
				</div>

				<draggable
					v-model="localColumns"
					item-key="fieldname"
					handle=".drag-handle"
					:animation="180"
					class="space-y-2"
				>
					<template #item="{ element: column }">
						<div class="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2">
							<div class="drag-handle cursor-grab text-slate-400" title="Drag">&#8942;</div>
							<div class="flex-1">
								<input
									v-model="column.label"
									type="text"
									class="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200"
									placeholder="Column label"
								/>
								<p class="mt-1 text-[11px] text-slate-500 truncate">{{ column.fieldname }}</p>
							</div>
							<div class="flex items-center gap-2">
								<input
									v-model.number="column.width"
									type="number"
									min="0"
									max="100"
									step="5"
									class="w-20 rounded-lg border px-2 py-1 text-sm text-right"
									:class="column.invalid_width ? 'border-rose-400 text-rose-700' : 'border-slate-200 text-slate-800'"
								/>
								<button
									class="rounded-full p-1 text-slate-400 hover:bg-slate-100 hover:text-rose-600"
									title="Remove"
									@click="removeColumn(column)"
									type="button"
								>
									&#x2715;
								</button>
							</div>
						</div>
					</template>
				</draggable>

				<div v-if="!localColumns.length" class="mt-3 rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-3 text-center text-sm text-slate-500">
					No columns yet. Add one below.
				</div>

				<div class="mt-4 flex flex-wrap items-center gap-3">
					<label class="text-sm font-semibold text-slate-700" for="add-column">Add column</label>
					<select
						id="add-column"
						v-model="pendingFieldname"
						class="w-64 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:border-indigo-300 focus:ring-2 focus:ring-indigo-200"
					>
						<option value="" disabled>Select field</option>
						<option v-for="option in availableColumns" :key="option.fieldname" :value="option.fieldname">
							{{ option.label }}
						</option>
					</select>
					<button
						class="rounded-lg bg-indigo-600 px-3 py-2 text-xs font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-slate-300"
						:disabled="!pendingFieldname"
						@click="addColumn"
						type="button"
					>
						Add
					</button>
				</div>
			</div>

			<div class="flex items-center justify-end gap-3 border-t border-slate-200 px-5 py-3">
				<button class="rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-100" type="button" @click="$emit('close')">
					Close
				</button>
				<button class="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-700" type="button" @click="$emit('close')">
					Done
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue"
import draggable from "vuedraggable"
import type { TableColumn } from "@/utils/layout"

declare const frappe: any

interface Props {
	modelValue: TableColumn[]
	doctype: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
	(e: "update:modelValue", value: TableColumn[]): void
	(e: "close"): void
}>()

const cloneColumns = (cols?: TableColumn[] | null) => JSON.parse(JSON.stringify(cols || []))
const localColumns = ref<TableColumn[]>(cloneColumns(props.modelValue || []))
const childMeta = ref<any>(null)
const pendingFieldname = ref<string>("")
const syncingFromProp = ref(false)

watch(
	() => props.modelValue,
	(value) => {
		syncingFromProp.value = true
		localColumns.value = cloneColumns(value || [])
		validateWidths(localColumns.value)
		nextTick(() => {
			syncingFromProp.value = false
		})
	},
	{ deep: true }
)

watch(
	localColumns,
	(cols) => {
		if (syncingFromProp.value) return
		validateWidths(cols)
		emit("update:modelValue", cols)
	},
	{ deep: true }
)

const totalWidth = computed(() =>
	localColumns.value.reduce((total, col) => total + (col.width || 0), 0)
)

const availableColumns = computed(() => {
	const existing = new Set(localColumns.value.map((c) => c.fieldname))
	const base: { label: string; fieldname: string; fieldtype: string }[] = [
		{ label: "Sr No.", fieldname: "idx", fieldtype: "Data" },
	]

	if (!childMeta.value?.fields) {
		return base
	}

	const metaFields = childMeta.value.fields
		.filter(
			(f: any) =>
				f.fieldname &&
				f.label &&
				f.fieldtype &&
				!["Section Break", "Column Break"].includes(f.fieldtype) &&
				(!frappe?.model?.no_value_type || !frappe.model.no_value_type.includes(f.fieldtype))
		)
		.map((f: any) => ({
			label: f.label,
			fieldname: f.fieldname,
			fieldtype: f.fieldtype,
		}))

	return [...base, ...metaFields].filter((f) => !existing.has(f.fieldname))
})

function removeColumn(column: TableColumn) {
	localColumns.value = localColumns.value.filter((col) => col !== column)
}

function addColumn() {
	if (!pendingFieldname.value) return
	const option = availableColumns.value.find((opt) => opt.fieldname === pendingFieldname.value)
	if (!option) return

	const newCol: TableColumn = {
		fieldname: option.fieldname,
		label: option.label,
		fieldtype: option.fieldtype || "Data",
		width: 10,
	}
	localColumns.value = [...localColumns.value, newCol]
	pendingFieldname.value = ""
}

function validateWidths(cols: TableColumn[]) {
	let runningTotal = 0
	for (const col of cols) {
		if (typeof col.width !== "number" || Number.isNaN(col.width)) {
			col.width = 10
		}
		runningTotal += col.width
		;(col as any).invalid_width = runningTotal > 100
	}
}

function loadChildMeta() {
	if (!props.doctype || typeof frappe === "undefined") return
	if (typeof frappe.model?.with_doctype === "function") {
		frappe.model.with_doctype(props.doctype, () => {
			childMeta.value = frappe.get_meta(props.doctype)
		})
	} else {
		childMeta.value = frappe.get_meta(props.doctype)
	}
}

onMounted(() => {
	loadChildMeta()
	validateWidths(localColumns.value)
})

watch(
	() => props.doctype,
	() => loadChildMeta()
)
</script>
