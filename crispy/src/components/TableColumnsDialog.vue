<template>
	<div class="table-dialog">
		<div class="table-dialog__card">
			<div class="table-dialog__header">
				<div>
					<h3 class="table-dialog__title">Configure columns</h3>
					<p class="table-dialog__subtitle">
						Drag to reorder. Widths are percentages; total should stay at or below 100.
					</p>
				</div>
				<button class="table-dialog__close" @click="$emit('close')" type="button">
					&#x2715;
				</button>
			</div>

			<div class="table-dialog__body">
				<div class="table-dialog__row">
					<span>Columns</span>
					<span :class="totalWidth > 100 ? 'table-dialog__total--over' : 'table-dialog__total'">
						Total width: {{ totalWidth }}%
					</span>
				</div>

				<draggable
					v-model="localColumns"
					item-key="fieldname"
					handle=".drag-handle"
					:animation="180"
					class="table-dialog__list"
				>
					<template #item="{ element: column }">
						<div class="table-dialog__item">
							<div class="drag-handle" title="Drag">&#8942;</div>
							<div class="table-dialog__item-main">
								<input
									v-model="column.label"
									type="text"
									class="table-dialog__input"
									placeholder="Column label"
								/>
								<p class="table-dialog__fieldname">{{ column.fieldname }}</p>
							</div>
							<div class="table-dialog__item-controls">
								<input
									v-model.number="column.width"
									type="number"
									min="0"
									max="100"
									step="5"
									class="table-dialog__width-input"
									:class="column.invalid_width ? 'table-dialog__width-input--invalid' : ''"
								/>
								<button class="table-dialog__remove" title="Remove" @click="removeColumn(column)" type="button">
									&#x2715;
								</button>
							</div>
						</div>
					</template>
				</draggable>

				<div v-if="!localColumns.length" class="table-dialog__empty">
					No columns yet. Add one below.
				</div>

				<div class="table-dialog__add">
					<label class="table-dialog__add-label" for="add-column">Add column</label>
					<select
						id="add-column"
						v-model="pendingFieldname"
						class="table-dialog__select"
					>
						<option value="" disabled>Select field</option>
						<option v-for="option in availableColumns" :key="option.fieldname" :value="option.fieldname">
							{{ option.label }}
						</option>
					</select>
					<button
						class="table-dialog__add-btn"
						:disabled="!pendingFieldname"
						@click="addColumn"
						type="button"
					>
						Add
					</button>
				</div>
			</div>

			<div class="table-dialog__footer">
				<button class="table-dialog__footer-btn" type="button" @click="$emit('close')">
					Close
				</button>
				<button class="table-dialog__footer-btn table-dialog__footer-btn--primary" type="button" @click="$emit('close')">
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
