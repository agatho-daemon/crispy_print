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
					<span
						class="typography-style-editor__color-well"
						:style="{ backgroundColor: modelValue.color || '#000000' }"
					>
						<input
							type="color"
							:value="modelValue.color || '#000000'"
							@input="updateFromEvent('color', $event)"
						/>
					</span>
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
import { computed, watch } from "vue";

import type { TypstFontFamilyFaces } from "../api/crispy";
import type { TypographyStyle } from "../utils/presentation_settings";
import { formatPt, parseSize } from "../utils/typstTypography";
import { FONT_STYLE_OPTIONS, FONT_WEIGHT_OPTIONS } from "../utils/typographyOptions";
import { __ } from "../utils/i18n";

type Option = { value: string; label: string };
type FontOption = typeof FONT_WEIGHT_OPTIONS[number] | typeof FONT_STYLE_OPTIONS[number];

const FONT_WEIGHT_ORDER = [
	"thin",
	"extralight",
	"light",
	"regular",
	"medium",
	"semibold",
	"bold",
	"extrabold",
	"black",
];

const props = withDefaults(
	defineProps<{
		modelValue: TypographyStyle;
		title: string;
		availableFonts?: string[];
		fontFaces?: TypstFontFamilyFaces[];
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
		fontFaces: () => [],
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

const selectedFontFaces = computed(() =>
	props.fontFaces.find((font) => font.family === props.modelValue.fontFamily)
);

const styleOptions = computed<Option[]>(() => {
	const styles = selectedFontFaces.value?.styles?.filter(Boolean) || [];
	if (!styles.length) return [...FONT_STYLE_OPTIONS];
	return styles.map((style) => optionForValue(style, FONT_STYLE_OPTIONS));
});

const weightOptions = computed<Option[]>(() => {
	const weights = selectedFontFaces.value?.weights?.filter(Boolean) || [];
	if (!weights.length) return [...FONT_WEIGHT_OPTIONS];
	return weights
		.slice()
		.sort((a, b) => weightRank(a) - weightRank(b))
		.map((weight) => optionForValue(weight, FONT_WEIGHT_OPTIONS));
});

const fontSizePt = computed(() => Math.max(1, parseSize(props.modelValue.fontSize).value || 0));

function optionValue(option: Option) {
	return props.optionValueFormat === "label" ? option.label : option.value;
}

function optionForValue(value: string, source: readonly FontOption[]): Option {
	const match = source.find((option) => option.value === value);
	return { value, label: match?.label || toLabel(value) };
}

function toLabel(value: string) {
	return value
		.split(/[\s_-]+/)
		.filter(Boolean)
		.map((part) => part.charAt(0).toUpperCase() + part.slice(1))
		.join(" ");
}

function normalizeOptionValue(value: unknown, options: readonly Option[]) {
	const clean = String(value || "")
		.trim()
		.toLowerCase();
	const match = options.find(
		(option) => option.value.toLowerCase() === clean || option.label.toLowerCase() === clean
	);
	return match?.value || "";
}

function outputOptionValue(value: string, options: readonly Option[]) {
	const option = options.find((candidate) => candidate.value === value);
	if (!option) return value;
	return optionValue(option);
}

function weightRank(weight: string) {
	const index = FONT_WEIGHT_ORDER.indexOf(weight);
	return index === -1 ? FONT_WEIGHT_ORDER.indexOf("regular") : index;
}

function closestWeight(currentValue: string, options: readonly Option[]) {
	if (!options.length) return currentValue;
	const currentRank = weightRank(currentValue || "regular");
	return options
		.slice()
		.sort(
			(a, b) =>
				Math.abs(weightRank(a.value) - currentRank) -
				Math.abs(weightRank(b.value) - currentRank)
		)[0].value;
}

function firstPreferredStyle(options: readonly Option[]) {
	return (
		options.find((option) => option.value === "normal")?.value || options[0]?.value || "normal"
	);
}

function normalizeModelValue(value: TypographyStyle) {
	const nextStyleOptions = styleOptions.value;
	const nextWeightOptions = weightOptions.value;
	const currentStyle = normalizeOptionValue(value.fontStyle, nextStyleOptions);
	const currentWeight = normalizeOptionValue(value.fontWeight, nextWeightOptions);
	const fontStyle = currentStyle || firstPreferredStyle(nextStyleOptions);
	const fontWeight =
		currentWeight ||
		closestWeight(
			normalizeOptionValue(value.fontWeight, FONT_WEIGHT_OPTIONS),
			nextWeightOptions
		);
	return {
		fontStyle: outputOptionValue(fontStyle, nextStyleOptions),
		fontWeight: outputOptionValue(fontWeight, nextWeightOptions),
	};
}

watch(
	() => [
		props.modelValue.fontFamily,
		props.modelValue.fontStyle,
		props.modelValue.fontWeight,
		styleOptions.value,
		weightOptions.value,
	],
	() => {
		if (!selectedFontFaces.value) return;
		const normalized = normalizeModelValue(props.modelValue);
		if (
			normalized.fontStyle === props.modelValue.fontStyle &&
			normalized.fontWeight === props.modelValue.fontWeight
		) {
			return;
		}
		emit("update:modelValue", {
			...props.modelValue,
			fontStyle: normalized.fontStyle,
			fontWeight: normalized.fontWeight,
		});
	},
	{ immediate: true }
);

function updateField<Key extends keyof TypographyStyle>(field: Key, value: TypographyStyle[Key]) {
	if (field === "fontFamily") {
		const nextValue = { ...props.modelValue, fontFamily: value as string };
		const nextFamily = props.fontFaces.find((font) => font.family === nextValue.fontFamily);
		if (nextFamily) {
			const nextStyleOptions = nextFamily.styles?.length
				? nextFamily.styles.map((style) => optionForValue(style, FONT_STYLE_OPTIONS))
				: [...FONT_STYLE_OPTIONS];
			const nextWeightOptions = nextFamily.weights?.length
				? nextFamily.weights
						.slice()
						.sort((a, b) => weightRank(a) - weightRank(b))
						.map((weight) => optionForValue(weight, FONT_WEIGHT_OPTIONS))
				: [...FONT_WEIGHT_OPTIONS];
			const currentStyle = normalizeOptionValue(nextValue.fontStyle, nextStyleOptions);
			const currentWeight = normalizeOptionValue(nextValue.fontWeight, nextWeightOptions);
			nextValue.fontStyle = outputOptionValue(
				currentStyle || firstPreferredStyle(nextStyleOptions),
				nextStyleOptions
			);
			nextValue.fontWeight = outputOptionValue(
				currentWeight ||
					closestWeight(
						normalizeOptionValue(nextValue.fontWeight, FONT_WEIGHT_OPTIONS),
						nextWeightOptions
					),
				nextWeightOptions
			);
		}
		emit("update:modelValue", nextValue);
		return;
	}
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

.typography-style-editor__color-well {
	position: relative;
	display: block;
	width: 36px;
	height: 36px;
	border-radius: 8px;
	overflow: hidden;
	box-shadow: inset 0 0 0 1px rgb(15 23 42 / 8%);
}

.typography-style-editor__color-well input[type="color"] {
	position: absolute;
	inset: 0;
	width: 100%;
	height: 100%;
	padding: 0;
	border: 0;
	opacity: 0;
	cursor: pointer;
}
</style>
