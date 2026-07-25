<template>
	<div class="box-sides-editor">
		<label v-if="label" class="box-sides-editor__label">{{ label }}</label>
		<div class="box-sides-editor__grid">
			<div v-for="side in sides" :key="side.key" class="box-sides-editor__input">
				<span class="box-sides-editor__prefix">{{ side.label }}</span>
				<input
					:value="modelValue[side.key]"
					type="number"
					:placeholder="side.label"
					class="form-control box-sides-editor__control"
					@input="updateSide(side.key, $event)"
				/>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { __ } from "../utils/i18n";

type SideKey = "top" | "bottom" | "left" | "right";
type SideValues = Record<SideKey, number>;

const props = defineProps<{
	modelValue: SideValues;
	label?: string;
}>();

const emit = defineEmits<{
	"update:modelValue": [value: SideValues];
}>();

const sides = computed<{ key: SideKey; label: string }[]>(() => [
	{ key: "top", label: __("Top") },
	{ key: "bottom", label: __("Bottom") },
	{ key: "left", label: __("Left") },
	{ key: "right", label: __("Right") },
]);

function eventValue(event: Event) {
	return (event.target as HTMLInputElement | null)?.value || "";
}

function updateSide(key: SideKey, event: Event) {
	const value = eventValue(event);
	const numericValue = value === "" ? 0 : Number(value);
	emit("update:modelValue", {
		...props.modelValue,
		[key]: Number.isFinite(numericValue) ? numericValue : props.modelValue[key],
	});
}
</script>

<style scoped>
.box-sides-editor {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.box-sides-editor__label {
	font-size: 13px;
	font-weight: 600;
}

.box-sides-editor__grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 8px;
}

.box-sides-editor__input {
	position: relative;
}

.box-sides-editor__prefix {
	position: absolute;
	inset-inline-start: 10px;
	top: 50%;
	transform: translateY(-50%);
	font-size: 10px;
	font-weight: 600;
	pointer-events: none;
}

.box-sides-editor__control {
	padding-inline-start: 50px;
}
</style>
