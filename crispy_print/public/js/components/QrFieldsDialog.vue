<template>
	<div class="qr-dialog" role="presentation" @keydown.esc="$emit('close')">
		<div class="qr-dialog__card" role="dialog" aria-modal="true" :dir="direction">
			<div class="qr-dialog__header">
				<div>
					<h3 class="qr-dialog__title">{{ __("Custom Document QR fields") }}</h3>
					<p class="qr-dialog__subtitle">
						{{
							__(
								"Choose exact document fieldnames and drag them into payload order. This QR is for internal or general business use and does not certify regulatory compliance."
							)
						}}
					</p>
				</div>
				<button
					class="qr-dialog__close"
					type="button"
					:aria-label="__('Close')"
					@click="$emit('close')"
				>
					&#x2715;
				</button>
			</div>

			<div class="qr-dialog__body">
				<draggable
					v-model="localSelection"
					item-key="fieldname"
					handle=".qr-dialog__drag"
					:animation="180"
					class="qr-dialog__list"
				>
					<template #item="{ element, index }">
						<div class="qr-dialog__item">
							<button
								type="button"
								class="qr-dialog__drag"
								:title="__('Drag to reorder')"
								:aria-label="__('Drag to reorder')"
							>
								&#8942;
							</button>
							<div class="qr-dialog__field">
								<strong>{{ element.label }}</strong>
								<code dir="ltr">{{ element.fieldname }}</code>
							</div>
							<span class="qr-dialog__type">{{
								element.fieldtype || __("Data")
							}}</span>
							<div class="qr-dialog__keyboard">
								<button
									type="button"
									:disabled="index === 0"
									:aria-label="__('Move up')"
									@click="move(index, -1)"
								>
									↑
								</button>
								<button
									type="button"
									:disabled="index === localSelection.length - 1"
									:aria-label="__('Move down')"
									@click="move(index, 1)"
								>
									↓
								</button>
							</div>
							<button
								class="qr-dialog__remove"
								type="button"
								:aria-label="__('Remove')"
								@click="remove(element.fieldname)"
							>
								&#x2715;
							</button>
						</div>
					</template>
				</draggable>

				<p v-if="!localSelection.length" class="qr-dialog__empty">
					{{ __("No fields selected. Add at least one document field.") }}
				</p>

				<div class="qr-dialog__add">
					<label for="qr-field-search">{{ __("Add document field") }}</label>
					<input
						id="qr-field-search"
						v-model="query"
						type="search"
						class="qr-dialog__input"
						:placeholder="__('Search by label or fieldname...')"
					/>
					<select v-model="pendingFieldname" class="qr-dialog__select">
						<option value="" disabled>{{ __("Select field") }}</option>
						<option
							v-for="field in availableFields"
							:key="field.fieldname"
							:value="field.fieldname"
						>
							{{ field.label }} ({{ field.fieldname }}) ·
							{{ field.fieldtype || __("Data") }}
						</option>
					</select>
					<button
						type="button"
						class="btn btn-default btn-sm qr-dialog__btn"
						:disabled="!pendingFieldname"
						@click="add"
					>
						{{ __("Add") }}
					</button>
				</div>

				<section class="qr-dialog__preview">
					<div class="qr-dialog__preview-heading">
						<strong>{{ __("Exact payload preview") }}</strong>
						<span>{{ __("{0} bytes", [payloadBytes]) }}</span>
					</div>
					<pre dir="ltr">{{ payloadPreview || __("No payload") }}</pre>
					<p v-if="payloadDense" class="qr-dialog__warning">
						{{
							__(
								"This payload is becoming dense. Reduce the number or size of fields and verify scanning at the printed QR size."
							)
						}}
					</p>
				</section>
			</div>

			<div class="qr-dialog__footer">
				<span>{{ __("{0} fields selected", [localSelection.length]) }}</span>
				<div class="qr-dialog__footer-actions">
					<button
						class="btn btn-default btn-sm qr-dialog__btn"
						type="button"
						@click="$emit('close')"
					>
						{{ __("Cancel") }}
					</button>
					<button
						class="btn btn-primary btn-sm qr-dialog__btn qr-dialog__btn--primary"
						type="button"
						:disabled="!localSelection.length"
						@click="apply"
					>
						{{ __("Apply") }}
					</button>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import draggable from "vuedraggable";
import type { DocField } from "../utils/layout";
import {
	buildCustomQrPayload,
	customQrPayloadBytes,
	getSafeCustomQrFields,
	isDenseCustomQrPayload,
} from "../utils/customQr";
import { getInterfaceLanguage, getLanguageDirection } from "../utils/direction";
import { __ } from "../utils/i18n";

interface Props {
	fields: DocField[];
	modelValue: string[];
	sampleValues?: Record<string, unknown> | null;
}

const props = defineProps<Props>();
const emit = defineEmits<{
	(e: "update:modelValue", value: string[]): void;
	(e: "close"): void;
}>();

const query = ref("");
const pendingFieldname = ref("");
const direction = computed(() => getLanguageDirection(getInterfaceLanguage()).direction);

const fieldMap = computed(
	() => new Map(getSafeCustomQrFields(props.fields).map((field) => [field.fieldname, field]))
);

const toRows = (fieldnames: string[]) =>
	fieldnames
		.map((fieldname) => fieldMap.value.get(fieldname))
		.filter((field): field is DocField => Boolean(field));

const localSelection = ref<DocField[]>(toRows(props.modelValue || []));

watch(
	[() => props.modelValue, fieldMap],
	([value]) => {
		localSelection.value = toRows(value || []);
	},
	{ deep: true }
);

const availableFields = computed(() => {
	const existing = new Set(localSelection.value.map((field) => field.fieldname));
	const term = query.value.trim().toLowerCase();
	return getSafeCustomQrFields(props.fields)
		.filter((field) => !existing.has(field.fieldname))
		.filter((field) => {
			if (!term) return true;
			return (
				field.fieldname.toLowerCase().includes(term) ||
				(field.label || "").toLowerCase().includes(term)
			);
		});
});

const selectedFieldnames = computed(() => localSelection.value.map((field) => field.fieldname));
const payloadPreview = computed(() =>
	buildCustomQrPayload(props.sampleValues || {}, selectedFieldnames.value)
);
const payloadBytes = computed(() => customQrPayloadBytes(payloadPreview.value));
const payloadDense = computed(() => isDenseCustomQrPayload(payloadBytes.value));

function add() {
	const field = fieldMap.value.get(pendingFieldname.value);
	if (!field || localSelection.value.some((row) => row.fieldname === field.fieldname)) return;
	localSelection.value = [...localSelection.value, field];
	pendingFieldname.value = "";
}

function remove(fieldname: string) {
	localSelection.value = localSelection.value.filter((field) => field.fieldname !== fieldname);
}

function move(index: number, offset: number) {
	const target = index + offset;
	if (target < 0 || target >= localSelection.value.length) return;
	const next = [...localSelection.value];
	[next[index], next[target]] = [next[target], next[index]];
	localSelection.value = next;
}

function apply() {
	emit("update:modelValue", selectedFieldnames.value);
	emit("close");
}
</script>

<style scoped>
.qr-dialog {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.48);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 2000;
}
.qr-dialog__card {
	width: min(760px, 94vw);
	max-height: 88vh;
	background: #fff;
	border: 1px solid #e2e8f0;
	border-radius: 16px;
	box-shadow: 0 24px 56px rgba(15, 23, 42, 0.24);
	display: flex;
	flex-direction: column;
	overflow: hidden;
	text-align: start;
}
.qr-dialog__header,
.qr-dialog__footer {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 16px;
	padding: 16px 20px;
	border-block-end: 1px solid #e2e8f0;
}
.qr-dialog__footer {
	border-block-start: 1px solid #e2e8f0;
	border-block-end: 0;
}
.qr-dialog__title {
	margin: 0;
	font-size: 18px;
}
.qr-dialog__subtitle {
	margin: 6px 0 0;
	color: #64748b;
	font-size: 13px;
}
.qr-dialog__close,
.qr-dialog__remove,
.qr-dialog__keyboard button {
	border: 0;
	background: transparent;
	cursor: pointer;
	color: #64748b;
}
.qr-dialog__body {
	padding: 20px;
	overflow: auto;
	display: grid;
	gap: 18px;
}
.qr-dialog__list {
	display: grid;
	gap: 10px;
}
.qr-dialog__item {
	display: grid;
	grid-template-columns: auto minmax(0, 1fr) auto auto auto;
	align-items: center;
	gap: 12px;
	padding: 12px;
	border: 1px solid #e2e8f0;
	border-radius: 12px;
}
.qr-dialog__drag {
	cursor: grab;
	border: 0;
	background: transparent;
	font-size: 20px;
}
.qr-dialog__field {
	display: grid;
	gap: 3px;
	min-width: 0;
}
.qr-dialog__field code {
	color: #475569;
	overflow-wrap: anywhere;
}
.qr-dialog__type {
	color: #64748b;
	font-size: 12px;
}
.qr-dialog__keyboard {
	display: flex;
	gap: 4px;
}
.qr-dialog__keyboard button {
	border: 1px solid #e2e8f0;
	border-radius: 6px;
}
.qr-dialog__add {
	display: grid;
	grid-template-columns: 1fr 1.4fr auto;
	gap: 10px;
	align-items: end;
}
.qr-dialog__add label {
	grid-column: 1 / -1;
	font-weight: 600;
}
.qr-dialog__input,
.qr-dialog__select {
	width: 100%;
	padding: 8px 10px;
	border: 1px solid #cbd5e1;
	border-radius: 8px;
	background: #fff;
}
.qr-dialog__preview {
	display: grid;
	gap: 8px;
}
.qr-dialog__preview-heading {
	display: flex;
	justify-content: space-between;
	gap: 12px;
}
.qr-dialog__preview pre {
	margin: 0;
	min-height: 90px;
	padding: 12px;
	border-radius: 10px;
	border: 1px solid var(--border-color, #dbe4f0);
	background: var(--control-bg, #f4f7fb);
	color: var(--text-color, #36414c);
	white-space: pre-wrap;
	overflow-wrap: anywhere;
}
.qr-dialog__warning {
	margin: 0;
	color: #b45309;
}
.qr-dialog__empty {
	color: #b45309;
}
.qr-dialog__footer-actions {
	display: flex;
	gap: 8px;
}
.qr-dialog__btn {
	border-radius: 8px;
}
.qr-dialog__btn:disabled,
.qr-dialog__keyboard button:disabled {
	opacity: 0.45;
	cursor: not-allowed;
}
@media (max-width: 700px) {
	.qr-dialog__item {
		grid-template-columns: auto minmax(0, 1fr) auto;
	}
	.qr-dialog__type,
	.qr-dialog__keyboard {
		grid-column: 2;
	}
	.qr-dialog__add {
		grid-template-columns: 1fr;
	}
}
</style>
