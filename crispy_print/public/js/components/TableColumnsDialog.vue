<template>
	<div class="table-dialog">
		<div class="table-dialog__card">
			<div class="table-dialog__header">
				<div>
					<h3 class="table-dialog__title">{{ __("Configure columns") }}</h3>
					<p class="table-dialog__subtitle">
						{{
							__(
								"Drag to reorder. Widths use Typst units: auto, 1fr, 2fr, 100pt, 50%, etc."
							)
						}}
					</p>
				</div>
				<button class="table-dialog__close" @click="$emit('close')" type="button">
					&#x2715;
				</button>
			</div>

			<div class="table-dialog__body">
				<section v-if="presetOptions.length" class="table-dialog__presets">
					<div class="table-dialog__preset-heading">
						<div>
							<strong>{{ __("Compact table preset") }}</strong>
							<p>
								{{
									__(
										"Presets replace the current columns with an RTL-safe logical layout."
									)
								}}
							</p>
						</div>
						<div class="table-dialog__preset-actions">
							<select v-model="selectedPresetId" class="table-dialog__select">
								<option value="">{{ __("Select preset") }}</option>
								<option
									v-for="option in presetOptions"
									:key="option.preset.id"
									:value="option.preset.id"
								>
									{{
										presetMessages[option.preset.id]?.label ||
										option.preset.label
									}}
								</option>
							</select>
							<button
								type="button"
								class="table-dialog__add-btn"
								:disabled="!selectedPreset?.applicable"
								@click="confirmApplyPreset"
							>
								{{ __("Apply preset") }}
							</button>
						</div>
					</div>
					<div v-if="selectedPreset" class="table-dialog__preset-preview">
						<p>
							{{
								presetMessages[selectedPreset.preset.id]?.description ||
								selectedPreset.preset.description
							}}
						</p>
						<div class="table-dialog__preset-columns">
							<span
								v-for="column in selectedPreset.columns"
								:key="column.fieldname"
								class="table-dialog__preset-column"
							>
								{{ column.label }}
								<code>{{ column.fieldname }}</code>
							</span>
						</div>
						<p
							v-if="selectedPreset.missingRequired.length"
							class="table-dialog__preset-warning"
						>
							{{
								__("Required fields unavailable: {0}", [
									selectedPreset.missingRequired.join(", "),
								])
							}}
						</p>
						<p
							v-if="selectedPreset.missingOptional.length"
							class="table-dialog__preset-note"
						>
							{{
								__("Optional fields unavailable: {0}", [
									selectedPreset.missingOptional.join(", "),
								])
							}}
						</p>
					</div>
				</section>

				<div class="table-dialog__row">
					<span>{{ __("Columns") }}</span>
					<label class="table-dialog__order">
						<span>{{ __("Column order") }}</span>
						<select
							:value="order"
							class="table-dialog__select"
							@change="onOrderChange"
						>
							<option value="logical">{{ __("Logical (direction-aware)") }}</option>
							<option value="physical">{{ __("Physical (fixed)") }}</option>
						</select>
					</label>
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
							<div class="drag-handle" :title="__('Drag')">&#8942;</div>
							<div class="table-dialog__item-main">
								<input
									v-model="column.label"
									type="text"
									class="table-dialog__input"
									:placeholder="__('Column label')"
								/>
							</div>
							<div class="table-dialog__item-controls">
								<button
									class="table-dialog__align-btn"
									type="button"
									@click="cycleColumnAlignment(column)"
									:title="__('Align: {0}', [column.align || 'left'])"
								>
									{{ getAlignIcon(column.align) }}
								</button>
								<input
									v-model="column.width"
									type="text"
									:placeholder="__('auto')"
									class="table-dialog__width-input"
									:class="
										column.invalid_width
											? 'table-dialog__width-input--invalid'
											: ''
									"
									:title="__('Typst width: auto, 1fr, 2fr, 100pt, etc.')"
								/>
								<button
									class="table-dialog__remove"
									:title="__('Remove')"
									@click="removeColumn(column)"
									type="button"
								>
									&#x2715;
								</button>
							</div>
						</div>
					</template>
				</draggable>

				<div v-if="!localColumns.length" class="table-dialog__empty">
					{{ __("No columns yet. Add one below.") }}
				</div>

				<div class="table-dialog__add">
					<label class="table-dialog__add-label" for="add-column">{{
						__("Add column")
					}}</label>
					<select
						id="add-column"
						v-model="pendingFieldname"
						class="table-dialog__select"
					>
						<option value="" disabled>{{ __("Select field") }}</option>
						<option
							v-for="option in availableColumnOptions"
							:key="option.fieldname"
							:value="option.fieldname"
						>
							{{ option.label }}
						</option>
					</select>
					<button
						class="table-dialog__add-btn"
						:disabled="!pendingFieldname"
						@click="addColumn"
						type="button"
					>
						{{ __("Add") }}
					</button>
				</div>
			</div>

			<div class="table-dialog__footer">
				<button class="table-dialog__footer-btn" type="button" @click="$emit('close')">
					{{ __("Close") }}
				</button>
				<button
					class="table-dialog__footer-btn table-dialog__footer-btn--primary"
					type="button"
					@click="$emit('close')"
				>
					{{ __("Done") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from "vue";
import draggable from "vuedraggable";
import type { TableColumn } from "../utils/layout";
import { getDefaultAlignment } from "../utils/tableColumns";
import {
	TABLE_PRESETS,
	resolveTablePreset,
	type ResolvedTablePreset,
	type TablePresetFieldOption,
} from "../utils/tablePresets";
import { deepClone } from "../utils/json";
import { __ } from "../utils/i18n";
import type { LogicalAlignment, TableOrder } from "../utils/direction";

interface Props {
	modelValue: TableColumn[];
	doctype: string;
	availableColumns?: Array<{ label: string; fieldname: string; fieldtype?: string }>;
	order?: TableOrder;
}

const props = defineProps<Props>();
const emit = defineEmits<{
	(e: "update:modelValue", value: TableColumn[]): void;
	(e: "update:order", value: TableOrder): void;
	(e: "close"): void;
}>();
const order = computed(() => props.order || "physical");

function onOrderChange(event: Event) {
	emit("update:order", (event.target as HTMLSelectElement).value as TableOrder);
}

const cloneColumns = (cols?: TableColumn[] | null) => deepClone(cols || []);
const localColumns = ref<TableColumn[]>(cloneColumns(props.modelValue || []));
const childMeta = ref<any>(null);
const pendingFieldname = ref<string>("");
const selectedPresetId = ref("");
const presetMessages: Record<string, { label: string; description: string }> = {
	"invoice-items": {
		label: __("Invoice items"),
		description: __("Item, description, quantity, rate, and amount."),
	},
	"service-rows": {
		label: __("Service rows"),
		description: __("Description-led rows for services and professional work."),
	},
	"tax-rows": {
		label: __("Tax rows"),
		description: __("Tax description, rate, tax amount, and running total."),
	},
	"serial-batch": {
		label: __("Serial and batch rows"),
		description: __("Item identity, serial/batch values, quantity, and warehouse."),
	},
	"pos-compact": {
		label: __("Compact POS rows"),
		description: __("Compact item, quantity, rate, and amount receipt rows."),
	},
};
const syncingFromProp = ref(false);
const validationMessage = ref<string>("");
let validationDebounceTimer: ReturnType<typeof setTimeout> | null = null;

const hasInvalidWidths = computed(() => {
	return localColumns.value.some((col: any) => col.invalid_width);
});

watch(
	() => props.modelValue,
	(value) => {
		syncingFromProp.value = true;
		localColumns.value = cloneColumns(value || []);
		validateWidths(localColumns.value);
		nextTick(() => {
			syncingFromProp.value = false;
		});
	},
	{ deep: true }
);

watch(
	localColumns,
	(cols) => {
		if (syncingFromProp.value) return;
		validateWidths(cols);

		// Clear any existing debounce timer
		if (validationDebounceTimer) {
			clearTimeout(validationDebounceTimer);
		}

		// Check if any column has invalid width
		const invalidCols = cols.filter((col: any) => col.invalid_width);
		if (invalidCols.length > 0) {
			// Debounce: only show alert after user stops typing for 800ms
			validationDebounceTimer = setTimeout(() => {
				const invalidValues = invalidCols.map((col) => col.width || "(empty)").join(", ");
				validationMessage.value = __(
					"Invalid column width values: {0}. Use Typst units like: auto, 1fr, 2fr, 100pt, 50%, 2cm, etc.",
					[invalidValues]
				);

				if (typeof frappe !== "undefined") {
					frappe.show_alert({
						message: validationMessage.value,
						indicator: "orange",
					});
				}
			}, 200);

			// Do NOT emit update to prevent compilation
			return;
		}

		// Clear validation message if all are valid
		validationMessage.value = "";
		emit("update:modelValue", cols);
	},
	{ deep: true }
);

const allColumnOptions = computed<TablePresetFieldOption[]>(() => {
	const base: { label: string; fieldname: string; fieldtype: string }[] = [
		{ label: __("Sr No."), fieldname: "idx", fieldtype: "Data" },
	];

	if (Array.isArray(props.availableColumns) && props.availableColumns.length) {
		return [...base, ...props.availableColumns]
			.filter((f) => f?.fieldname && f?.label)
			.map((f) => ({
				label: f.label,
				fieldname: f.fieldname,
				fieldtype: f.fieldtype || "Data",
			}));
	}

	if (!childMeta.value?.fields) {
		return base;
	}

	const metaFields = childMeta.value.fields
		.filter(
			(f: any) =>
				f.fieldname &&
				f.label &&
				f.fieldtype &&
				!["Section Break", "Column Break"].includes(f.fieldtype) &&
				(!frappe?.model?.no_value_type ||
					!frappe.model.no_value_type.includes(f.fieldtype))
		)
		.map((f: any) => ({
			label: f.label,
			fieldname: f.fieldname,
			fieldtype: f.fieldtype,
		}));

	return [...base, ...metaFields];
});

const availableColumnOptions = computed(() => {
	const existing = new Set(localColumns.value.map((c) => c.fieldname));
	return allColumnOptions.value.filter((field) => !existing.has(field.fieldname));
});

const presetOptions = computed<ResolvedTablePreset[]>(() => {
	if (Array.isArray(props.availableColumns) && props.availableColumns.length) return [];
	return TABLE_PRESETS.map((preset) => resolveTablePreset(preset, allColumnOptions.value));
});

const selectedPreset = computed(
	() => presetOptions.value.find((option) => option.preset.id === selectedPresetId.value) || null
);

function applySelectedPreset() {
	if (!selectedPreset.value?.applicable) return;
	localColumns.value = cloneColumns(selectedPreset.value.columns);
	emit("update:order", "logical");
}

function confirmApplyPreset() {
	if (!selectedPreset.value?.applicable) return;
	const message = __("Apply preset? This replaces the current table columns.");
	if (typeof frappe !== "undefined" && typeof frappe.confirm === "function") {
		frappe.confirm(message, applySelectedPreset);
		return;
	}
	if (window.confirm(message)) applySelectedPreset();
}

function removeColumn(column: TableColumn) {
	localColumns.value = localColumns.value.filter((col) => col !== column);
}

function addColumn() {
	if (!pendingFieldname.value) return;
	const option = availableColumnOptions.value.find(
		(opt) => opt.fieldname === pendingFieldname.value
	);
	if (!option) return;

	const newCol: TableColumn = {
		fieldname: option.fieldname,
		label: option.label,
		fieldtype: option.fieldtype || "Data",
		width: "auto",
		align: getDefaultAlignment(option.fieldtype),
	};
	localColumns.value = [...localColumns.value, newCol];
	pendingFieldname.value = "";
}

function cycleColumnAlignment(column: TableColumn) {
	const current = column.align || "auto";
	const alignments: LogicalAlignment[] = ["auto", "start", "center", "end", "left", "right"];
	const currentIndex = alignments.indexOf(current);
	const nextIndex = (currentIndex + 1) % alignments.length;
	column.align = alignments[nextIndex];
}

function getAlignIcon(align?: LogicalAlignment): string {
	switch (align) {
		case "auto":
			return "A";
		case "start":
			return "⇤";
		case "center":
			return "≡";
		case "end":
			return "⇥";
		case "right":
			return "R";
		case "left":
			return "L";
		default:
			return "A";
	}
}

function validateWidths(cols: TableColumn[]) {
	// Validate Typst width values
	for (const col of cols) {
		if (!col.width || typeof col.width !== "string") {
			col.width = "auto";
		}
		// Basic validation: should be like "1fr", "auto", "100pt", etc.
		const valid = /^(\d+\.?\d*)(fr|pt|em|rem|%|cm|mm|in)$|^auto$/i.test(col.width.trim());
		(col as any).invalid_width = !valid;
	}
}

function loadChildMeta() {
	if (!props.doctype || typeof frappe === "undefined") return;
	if (typeof frappe.model?.with_doctype === "function") {
		frappe.model.with_doctype(props.doctype, () => {
			childMeta.value = frappe.get_meta(props.doctype);
		});
	} else {
		childMeta.value = frappe.get_meta(props.doctype);
	}
}

onMounted(() => {
	loadChildMeta();
	validateWidths(localColumns.value);
});

watch(
	() => props.doctype,
	() => loadChildMeta()
);
</script>

<style scoped>
/* TableColumnsDialog.vue */
.table-dialog {
	position: absolute;
	inset: 0;
	z-index: 50;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(15, 23, 42, 0.5);
	padding: 16px;
}

.table-dialog__card {
	width: 100%;
	max-width: 768px;
	max-height: 70vh;
	background: #fff;
	border-radius: 16px;
	box-shadow: 0 25px 50px rgba(15, 23, 42, 0.25), 0 10px 20px rgba(15, 23, 42, 0.18);
	overflow: hidden;
	display: flex;
	flex-direction: column;
}

.table-dialog__header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	border-bottom: 1px solid #e2e8f0;
	padding: 16px 20px;
	gap: 12px;
}

.table-dialog__title {
	margin: 0;
	font-size: 16px;
	font-weight: 600;
	color: #0f172a;
}

.table-dialog__subtitle {
	margin: 4px 0 0;
	font-size: 14px;
	color: #475569;
}

.table-dialog__close {
	border: none;
	background: transparent;
	border-radius: 9999px;
	padding: 8px;
	color: #94a3b8;
	cursor: pointer;
	transition: background-color 0.15s ease, color 0.15s ease;
}

.table-dialog__close:hover {
	background: #f1f5f9;
	color: #475569;
}

.table-dialog__body {
	padding: 16px 20px;
	display: flex;
	flex-direction: column;
	gap: 12px;
	overflow: hidden;
	flex: 1;
}

.table-dialog__row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	font-size: 14px;
	color: #475569;
}

.table-dialog__presets {
	padding: 12px;
	border: 1px solid #d8e2f0;
	border-radius: 10px;
	background: #f8fafc;
}

.table-dialog__preset-heading {
	display: flex;
	align-items: flex-end;
	justify-content: space-between;
	gap: 12px;
}

.table-dialog__preset-heading p,
.table-dialog__preset-preview p {
	margin: 3px 0 0;
	color: #64748b;
	font-size: 12px;
}

.table-dialog__preset-actions {
	display: flex;
	align-items: center;
	gap: 8px;
}

.table-dialog__preset-preview {
	margin-top: 10px;
	padding-top: 10px;
	border-top: 1px solid #d8e2f0;
}

.table-dialog__preset-columns {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	margin-top: 8px;
}

.table-dialog__preset-column {
	display: inline-flex;
	gap: 5px;
	align-items: center;
	padding: 4px 7px;
	border: 1px solid #d8e2f0;
	border-radius: 6px;
	background: #fff;
	font-size: 12px;
}

.table-dialog__preset-column code {
	color: #64748b;
	direction: ltr;
	unicode-bidi: isolate;
}

.table-dialog__preset-preview .table-dialog__preset-warning {
	color: #b42318;
}

.table-dialog__preset-preview .table-dialog__preset-note {
	color: #8a6116;
}

.table-dialog__total {
	color: #64748b;
}

.table-dialog__total--over {
	color: #e11d48;
}

.table-dialog__list {
	display: flex;
	flex-direction: column;
	gap: 10px;
	overflow: auto;
	padding-inline-end: 4px;
}

.table-dialog__item {
	display: flex;
	align-items: center;
	gap: 12px;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	background: #f8fafc;
	padding: 12px;
}

.drag-handle {
	cursor: grab;
	color: #94a3b8;
	font-size: 16px;
	padding: 0 4px;
}

.table-dialog__item-main {
	flex: 1;
	min-width: 0;
}

.table-dialog__input {
	width: 100%;
	padding: 8px 12px;
	font-size: 14px;
	font-weight: 600;
	color: #0f172a;
	border: 1px solid #e2e8f0;
	border-radius: 10px;
	background: #fff;
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.table-dialog__input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.table-dialog__fieldname {
	margin: 4px 0 0;
	font-size: 11px;
	color: #64748b;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.table-dialog__item-controls {
	display: flex;
	align-items: center;
	gap: 8px;
}

.table-dialog__align-btn {
	border: 1px solid #e2e8f0;
	background: #fff;
	border-radius: 8px;
	padding: 6px 10px;
	min-width: 36px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	font-size: 16px;
	font-family: monospace;
	font-weight: bold;
	color: #334155;
	cursor: pointer;
	transition: border-color 0.15s ease, background-color 0.15s ease;
}

.table-dialog__align-btn:hover {
	border-color: #c7d2fe;
	background: #eef2ff;
}

.table-dialog__width-input {
	width: 80px;
	padding: 6px 8px;
	font-size: 14px;
	text-align: end;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	background: #fff;
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease, color 0.15s ease;
}

.table-dialog__width-input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.table-dialog__width-input--invalid {
	border-color: #fb7185;
	color: #be123c;
}

.table-dialog__remove {
	border: none;
	background: transparent;
	border-radius: 9999px;
	padding: 6px;
	color: #94a3b8;
	cursor: pointer;
	transition: background-color 0.15s ease, color 0.15s ease;
}

.table-dialog__remove:hover {
	background: #f1f5f9;
	color: #e11d48;
}

.table-dialog__empty {
	margin-top: 8px;
	border: 1px dashed #cbd5e1;
	border-radius: 10px;
	background: #f8fafc;
	padding: 12px;
	text-align: center;
	font-size: 14px;
	color: #94a3b8;
	flex-shrink: 0;
}

.table-dialog__add {
	margin-top: 12px;
	display: flex;
	flex-wrap: wrap;
	align-items: center;
	gap: 10px;
	flex-shrink: 0;
	padding-top: 8px;
	border-top: 1px solid #e2e8f0;
}

.table-dialog__add-label {
	font-size: 14px;
	font-weight: 600;
	color: #334155;
}

.table-dialog__select {
	width: 256px;
	max-width: 100%;
	padding: 8px 12px;
	font-size: 14px;
	color: #0f172a;
	border: 1px solid #e2e8f0;
	border-radius: 10px;
	background: #fff;
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.table-dialog__select:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.table-dialog__add-btn {
	border: none;
	background: #4f46e5;
	color: #fff;
	font-size: 12px;
	font-weight: 600;
	border-radius: 10px;
	padding: 8px 14px;
	cursor: pointer;
	transition: background-color 0.15s ease, box-shadow 0.15s ease;
}

.table-dialog__add-btn:hover {
	background: #4338ca;
}

.table-dialog__add-btn:disabled {
	cursor: not-allowed;
	background: #cbd5e1;
}

.table-dialog__footer {
	display: flex;
	align-items: center;
	justify-content: flex-end;
	gap: 10px;
	border-top: 1px solid #e2e8f0;
	padding: 12px 20px;
}

.table-dialog__footer-btn {
	border: none;
	background: transparent;
	color: #475569;
	font-size: 14px;
	font-weight: 600;
	border-radius: 10px;
	padding: 8px 12px;
	cursor: pointer;
	transition: background-color 0.15s ease, color 0.15s ease;
}

.table-dialog__footer-btn:hover {
	background: #f1f5f9;
}

.table-dialog__footer-btn--primary {
	background: #4f46e5;
	color: #fff;
}

.table-dialog__footer-btn--primary:hover {
	background: #4338ca;
}
</style>
