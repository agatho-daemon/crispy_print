<template>
	<div class="chart-palette-field">
		<div class="chart-palette-field__label-row">
			<div>
				<strong>{{ __("Chart palette") }}</strong>
				<span>{{
					__(
						"Choose and reorder colors visually. Color codes are managed automatically."
					)
				}}</span>
			</div>
			<button type="button" class="btn btn-xs btn-default" @click="resetPalette">
				{{ __("Reset") }}
			</button>
		</div>

		<div
			class="chart-palette-field__swatches"
			role="list"
			:aria-label="__('Chart series colors')"
		>
			<button
				v-for="(color, index) in palette"
				:key="`${color}-${index}`"
				type="button"
				class="chart-palette-field__swatch"
				:class="{ 'is-selected': index === selectedIndex }"
				:style="{ '--swatch-color': validColor(color) ? color : '#ffffff' }"
				:aria-label="seriesLabel(index, color)"
				:aria-pressed="index === selectedIndex"
				draggable="true"
				@click="selectColor(index)"
				@dragstart="startDrag(index)"
				@dragover.prevent
				@drop="dropColor(index)"
			>
				<span class="chart-palette-field__color" aria-hidden="true"></span>
				<small>{{ index + 1 }}</small>
			</button>
			<button
				type="button"
				class="btn btn-xs btn-default chart-palette-field__add"
				:disabled="palette.length >= maxColors"
				@click="addColor"
			>
				<span aria-hidden="true">+</span>
				{{ __("Add color") }}
			</button>
		</div>

		<div v-if="palette.length" class="chart-palette-field__editor">
			<label>
				<span>{{ __("Selected series color") }}</span>
				<div class="chart-palette-field__color-input">
					<input
						type="color"
						:value="pickerColor"
						:aria-label="__('Choose selected series color')"
						@input="updateFromPicker"
					/>
					<input
						v-model="hexDraft"
						class="form-control"
						type="text"
						spellcheck="false"
						:aria-invalid="Boolean(hexError)"
						@blur="commitHexDraft"
						@keydown.enter.prevent="commitHexDraft"
					/>
				</div>
			</label>
			<div class="chart-palette-field__order-actions">
				<button
					type="button"
					class="btn btn-xs btn-default"
					:disabled="selectedIndex === 0"
					@click="moveSelected(-1)"
				>
					{{ __("Move left") }}
				</button>
				<button
					type="button"
					class="btn btn-xs btn-default"
					:disabled="selectedIndex >= palette.length - 1"
					@click="moveSelected(1)"
				>
					{{ __("Move right") }}
				</button>
				<button
					type="button"
					class="btn btn-xs btn-default chart-palette-field__remove"
					:disabled="palette.length <= 1"
					@click="removeSelected"
				>
					{{ __("Remove") }}
				</button>
			</div>
		</div>
		<p v-if="hexError" class="chart-palette-field__error">{{ hexError }}</p>

		<div class="chart-palette-field__preview" aria-hidden="true">
			<span>{{ __("Chart preview") }}</span>
			<div class="chart-palette-field__bars">
				<i
					v-for="(color, index) in palette"
					:key="`bar-${index}`"
					:style="{
						backgroundColor: validColor(color) ? color : '#e2e8f0',
						height: `${previewHeight(index)}%`,
					}"
				></i>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { __ } from "../../utils/i18n";

const FALLBACK_PALETTE = ["#1E3A8A", "#2563EB", "#0F766E", "#B45309", "#7C3AED", "#BE123C"];
const HEX_COLOR = /^#[0-9a-f]{6}$/i;

const props = withDefaults(
	defineProps<{
		modelValue?: string;
		defaultPalette?: string[];
		maxColors?: number;
	}>(),
	{
		modelValue: "",
		defaultPalette: () => ["#1E3A8A", "#2563EB", "#0F766E", "#B45309", "#7C3AED", "#BE123C"],
		maxColors: 12,
	}
);
const emit = defineEmits<{ "update:modelValue": [value: string] }>();

const palette = ref(parsePalette(props.modelValue));
const selectedIndex = ref(0);
const draggedIndex = ref<number | null>(null);
const hexDraft = ref(palette.value[0] || "#1E3A8A");
const hexError = ref("");
const pickerColor = computed(() =>
	validColor(palette.value[selectedIndex.value]) ? palette.value[selectedIndex.value] : "#000000"
);

watch(
	() => props.modelValue,
	(value) => {
		const next = parsePalette(value);
		if (serializePalette(next) === serializePalette(palette.value)) return;
		palette.value = next;
		selectedIndex.value = Math.min(selectedIndex.value, Math.max(0, next.length - 1));
		syncDraft();
	}
);

function parsePalette(value?: string): string[] {
	return String(value || "")
		.split(",")
		.map((color) => color.trim().toUpperCase())
		.filter(Boolean)
		.slice(0, props.maxColors);
}

function serializePalette(colors: string[]): string {
	return colors.join(", ");
}

function validColor(color?: string): boolean {
	return HEX_COLOR.test(String(color || ""));
}

function emitPalette() {
	emit("update:modelValue", serializePalette(palette.value));
}

function syncDraft() {
	hexDraft.value = palette.value[selectedIndex.value] || "#000000";
	hexError.value = "";
}

function selectColor(index: number) {
	selectedIndex.value = index;
	syncDraft();
}

function updateSelected(color: string) {
	const next = [...palette.value];
	next[selectedIndex.value] = color.toUpperCase();
	palette.value = next;
	hexDraft.value = next[selectedIndex.value];
	hexError.value = "";
	emitPalette();
}

function updateFromPicker(event: Event) {
	updateSelected((event.target as HTMLInputElement).value);
}

function commitHexDraft() {
	const value = hexDraft.value.trim().toUpperCase();
	if (!validColor(value)) {
		hexError.value = __("Enter a six-digit hex color such as #2563EB.");
		return;
	}
	updateSelected(value);
}

function nextAvailableColor(): string {
	const candidates = [...props.defaultPalette, ...FALLBACK_PALETTE];
	return candidates.find((color) => !palette.value.includes(color.toUpperCase())) || "#64748B";
}

function addColor() {
	if (palette.value.length >= props.maxColors) return;
	palette.value = [...palette.value, nextAvailableColor().toUpperCase()];
	selectedIndex.value = palette.value.length - 1;
	syncDraft();
	emitPalette();
}

function removeSelected() {
	if (palette.value.length <= 1) return;
	const next = [...palette.value];
	next.splice(selectedIndex.value, 1);
	palette.value = next;
	selectedIndex.value = Math.min(selectedIndex.value, next.length - 1);
	syncDraft();
	emitPalette();
}

function moveSelected(offset: number) {
	const target = selectedIndex.value + offset;
	if (target < 0 || target >= palette.value.length) return;
	moveColor(selectedIndex.value, target);
	selectedIndex.value = target;
	syncDraft();
}

function moveColor(from: number, to: number) {
	if (from === to) return;
	const next = [...palette.value];
	const [color] = next.splice(from, 1);
	next.splice(to, 0, color);
	palette.value = next;
	emitPalette();
}

function startDrag(index: number) {
	draggedIndex.value = index;
}

function dropColor(index: number) {
	if (draggedIndex.value === null) return;
	const from = draggedIndex.value;
	moveColor(from, index);
	selectedIndex.value = index;
	draggedIndex.value = null;
	syncDraft();
}

function resetPalette() {
	palette.value = (props.defaultPalette.length ? props.defaultPalette : FALLBACK_PALETTE)
		.slice(0, props.maxColors)
		.map((color) => color.toUpperCase());
	selectedIndex.value = 0;
	syncDraft();
	emitPalette();
}

function seriesLabel(index: number, color: string): string {
	return `${__("Series")} ${index + 1}: ${color}`;
}

function previewHeight(index: number): number {
	return [48, 78, 60, 92, 68, 84, 55, 73, 64, 88, 58, 80][index] || 60;
}
</script>

<style scoped>
.chart-palette-field {
	margin: 14px 12px 12px;
	padding-top: 12px;
	border-top: 1px solid var(--border-color, #e2e8f0);
}

.chart-palette-field__label-row,
.chart-palette-field__editor,
.chart-palette-field__order-actions {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 10px;
}

.chart-palette-field__label-row strong,
.chart-palette-field__label-row span {
	display: block;
}

.chart-palette-field__label-row strong {
	font-size: 12px;
	color: #334155;
}

.chart-palette-field__label-row span {
	margin-top: 2px;
	font-size: 11px;
	color: #64748b;
}

.chart-palette-field__swatches {
	display: flex;
	align-items: flex-end;
	flex-wrap: wrap;
	gap: 7px;
	margin-top: 12px;
}

.chart-palette-field__swatch {
	display: grid;
	justify-items: center;
	gap: 3px;
	min-width: 38px;
	padding: 4px;
	border: 0;
	border-radius: 8px;
	background: transparent;
	cursor: grab;
}

.chart-palette-field__swatch:hover,
.chart-palette-field__swatch.is-selected {
	background: var(--control-bg, #f3f3f3);
}

.chart-palette-field__swatch.is-selected {
	box-shadow: inset 0 0 0 1px var(--primary, #2490ef);
}

.chart-palette-field__color {
	display: block;
	width: 28px;
	height: 28px;
	border: 0;
	border-radius: 6px;
	background: var(--swatch-color);
	box-shadow: inset 0 0 0 1px rgb(15 23 42 / 10%);
}

.chart-palette-field__swatch small {
	font-size: 9px;
	color: #64748b;
}

.chart-palette-field__add {
	min-height: 30px;
	font-size: 11px;
}

.chart-palette-field__add span {
	margin-right: 4px;
	font-size: 16px;
}

.chart-palette-field__editor {
	align-items: flex-end;
	margin-top: 12px;
}

.chart-palette-field__editor label {
	flex: 1;
	margin: 0;
}

.chart-palette-field__color-input {
	display: grid;
	grid-template-columns: 38px minmax(120px, 1fr);
	gap: 8px;
}

.chart-palette-field__color-input input[type="color"] {
	width: 38px;
	height: 34px;
	padding: 0;
	border: 0;
	border-radius: 8px;
	background: transparent;
	appearance: none;
	-webkit-appearance: none;
}

.chart-palette-field__color-input input[type="color"]::-webkit-color-swatch-wrapper {
	padding: 0;
}

.chart-palette-field__color-input input[type="color"]::-webkit-color-swatch,
.chart-palette-field__color-input input[type="color"]::-moz-color-swatch {
	border: 0;
	border-radius: 7px;
}

.chart-palette-field__order-actions {
	justify-content: flex-end;
	flex-wrap: wrap;
}

.chart-palette-field__remove {
	color: #b91c1c;
}

.chart-palette-field__error {
	margin: 6px 0 0;
	font-size: 11px;
	color: #b91c1c;
}

.chart-palette-field__preview {
	margin-top: 12px;
	padding-top: 10px;
}

.chart-palette-field__preview > span {
	display: block;
	margin-bottom: 6px;
	font-size: 10px;
	font-weight: 600;
	color: #64748b;
}

.chart-palette-field__bars {
	display: flex;
	align-items: flex-end;
	gap: 4px;
	height: 46px;
	padding: 5px 7px 0;
	border-bottom: 1px solid #cbd5e1;
	background: repeating-linear-gradient(to top, #e2e8f0 0 1px, transparent 1px 14px);
}

.chart-palette-field__bars i {
	flex: 1;
	min-width: 8px;
	max-width: 42px;
	border-radius: 3px 3px 0 0;
}

@media (max-width: 760px) {
	.chart-palette-field__editor {
		align-items: stretch;
		flex-direction: column;
	}
}
</style>
