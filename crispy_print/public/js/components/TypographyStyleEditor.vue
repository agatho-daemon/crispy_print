<template>
	<div class="typography-style-editor" :class="`typography-style-editor--${variant}`">
		<label class="typography-style-editor__title">{{ title }}</label>
		<div class="typography-style-editor__grid">
			<div class="typography-style-editor__field">
				<label class="typography-style-editor__label">{{ familyLabel }}</label>
				<select
					v-if="availableFonts.length"
					class="form-control"
					:value="modelValue.fontFamily"
					@change="updateFromEvent('fontFamily', $event)"
				>
					<option v-for="font in availableFonts" :key="font" :value="font">
						{{ font }}
					</option>
				</select>
				<input
					v-else
					class="form-control"
					type="text"
					:value="modelValue.fontFamily"
					@input="updateFromEvent('fontFamily', $event)"
				/>
			</div>
			<div class="typography-style-editor__field">
				<label class="typography-style-editor__label">{{ sizeLabel }}</label>
				<input
					class="form-control"
					type="number"
					min="1"
					:step="variant === 'cbp' ? '0.5' : '1'"
					:value="fontSizePt"
					@input="updateSizeFromEvent($event)"
				/>
			</div>
			<div class="typography-style-editor__field">
				<label class="typography-style-editor__label">{{ styleLabel }}</label>
				<select
					class="form-control"
					:value="modelValue.fontStyle"
					@change="updateFromEvent('fontStyle', $event)"
				>
					<option
						v-for="option in styleOptions"
						:key="option.value"
						:value="optionValue(option)"
					>
						{{ __(option.label) }}
					</option>
				</select>
			</div>
			<div class="typography-style-editor__field">
				<label class="typography-style-editor__label">{{ weightLabel }}</label>
				<select
					class="form-control"
					:value="modelValue.fontWeight"
					@change="updateFromEvent('fontWeight', $event)"
				>
					<option
						v-for="option in weightOptions"
						:key="option.value"
						:value="optionValue(option)"
					>
						{{ __(option.label) }}
					</option>
				</select>
			</div>
			<div class="typography-style-editor__field typography-style-editor__field--color">
				<label class="typography-style-editor__label">{{ colorLabel }}</label>
				<div class="typography-style-editor__color-input">
					<input
						type="color"
						:value="modelValue.color || '#000000'"
						@input="updateFromEvent('color', $event)"
					/>
					<input
						class="form-control"
						type="text"
						:value="modelValue.color"
						@input="updateFromEvent('color', $event)"
					/>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import type { TypographyStyle } from "../utils/presentation_settings";
import { formatPt, parseSize } from "../utils/typstTypography";
import { FONT_STYLE_OPTIONS, FONT_WEIGHT_OPTIONS } from "../utils/typographyOptions";
import { __ } from "../utils/i18n";

type Option = { value: string; label: string };

const props = withDefaults(
	defineProps<{
		modelValue: TypographyStyle;
		title: string;
		availableFonts?: string[];
		variant?: "settings" | "cbp";
		optionValueFormat?: "value" | "label";
		familyLabel?: string;
		sizeLabel?: string;
		styleLabel?: string;
		weightLabel?: string;
		colorLabel?: string;
	}>(),
	{
		availableFonts: () => [],
		variant: "settings",
		optionValueFormat: "value",
		familyLabel: __("Family"),
		sizeLabel: __("Size (pt)"),
		styleLabel: __("Style"),
		weightLabel: __("Weight"),
		colorLabel: __("Color"),
	}
);

const emit = defineEmits<{
	"update:modelValue": [value: TypographyStyle];
}>();

const styleOptions = FONT_STYLE_OPTIONS;
const weightOptions = FONT_WEIGHT_OPTIONS;

const fontSizePt = computed(() => Math.max(1, parseSize(props.modelValue.fontSize).value || 0));

function optionValue(option: Option) {
	return props.optionValueFormat === "label" ? option.label : option.value;
}

function updateField<Key extends keyof TypographyStyle>(field: Key, value: TypographyStyle[Key]) {
	emit("update:modelValue", {
		...props.modelValue,
		[field]: value,
	});
}

function eventValue(event: Event) {
	return (event.target as HTMLInputElement | HTMLSelectElement | null)?.value || "";
}

function updateFromEvent<Key extends keyof TypographyStyle>(field: Key, event: Event) {
	updateField(field, eventValue(event) as TypographyStyle[Key]);
}

function updateSize(value: string) {
	updateField("fontSize", formatPt(Number(value)));
}

function updateSizeFromEvent(event: Event) {
	updateSize(eventValue(event));
}
</script>

<style scoped>
.typography-style-editor {
	display: flex;
	flex-direction: column;
	gap: 10px;
	min-width: 0;
}

.typography-style-editor--settings {
	padding-bottom: 14px;
	border-bottom: 1px solid #edf2f7;
}

.typography-style-editor--settings:last-child {
	padding-bottom: 0;
	border-bottom: 0;
}

.typography-style-editor--cbp {
	margin: 0 12px 14px;
	padding-top: 12px;
}

.typography-style-editor--cbp + .typography-style-editor--cbp {
	border-top: 1px solid #edf2f7;
}

.typography-style-editor__title {
	font-size: 13px;
	font-weight: 600;
	line-height: 1.25;
	color: #525252;
	margin: 0 0 2px;
}

.typography-style-editor__grid {
	display: grid;
	grid-template-columns: minmax(0, 1fr);
	gap: 0;
	min-width: 0;
}

.typography-style-editor--cbp .typography-style-editor__grid {
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 10px 16px;
}

.typography-style-editor__field {
	display: flex;
	flex-direction: column;
	gap: 0;
	min-width: 0;
	margin-bottom: 13px;
}

.typography-style-editor__field:last-child {
	margin-bottom: 0;
}

.typography-style-editor--cbp .typography-style-editor__field {
	margin-bottom: 0;
}

.typography-style-editor__label {
	display: block;
	margin: 0 0 4px;
	font-size: 11px;
	font-weight: 500;
	line-height: 1.25;
	color: #475569;
}

.typography-style-editor :deep(.form-control) {
	width: 100%;
	min-width: 0;
	min-height: 32px;
	border-radius: 8px;
	padding: 6px 10px;
	font-size: 13px;
	line-height: 1.4;
}

.typography-style-editor__field--color {
	max-width: 230px;
}

.typography-style-editor--cbp .typography-style-editor__field--color {
	grid-column: 1 / -1;
}

.typography-style-editor__color-input {
	display: grid;
	grid-template-columns: 36px minmax(0, 1fr);
	gap: 8px;
	align-items: center;
	max-width: 230px;
}

.typography-style-editor__color-input input[type="color"] {
	width: 36px;
	height: 36px;
	padding: 0;
	border: 0;
	border-radius: 8px;
	background: transparent;
	box-shadow: none;
	overflow: hidden;
	appearance: none;
	-webkit-appearance: none;
}

.typography-style-editor__color-input input[type="color"]::-webkit-color-swatch-wrapper {
	padding: 0;
	border: 0;
}

.typography-style-editor__color-input input[type="color"]::-webkit-color-swatch {
	border: 0;
	border-radius: 8px;
}

.typography-style-editor__color-input input[type="color"]::-moz-color-swatch {
	border: 0;
	border-radius: 8px;
}
</style>
