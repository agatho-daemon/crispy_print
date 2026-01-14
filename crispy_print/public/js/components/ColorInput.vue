<template>
	<div class="color-input">
		<div ref="pickrContainer"></div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from "vue";
import Pickr from "@simonwep/pickr";
import "@simonwep/pickr/dist/themes/nano.min.css"; // Or classic.min.css, monolith.min.css

interface Props {
	modelValue: string;
}

const props = defineProps<Props>();
const emit = defineEmits<{
	"update:modelValue": [value: string];
}>();

const pickrContainer = ref<HTMLElement>();
let pickr: Pickr | null = null;

onMounted(() => {
	if (!pickrContainer.value) return;

	pickr = Pickr.create({
		el: pickrContainer.value,
		theme: "nano", // 'classic', 'monolith', or 'nano'
		default: props.modelValue || "#000000",

		swatches: [
			// Colorful standards
			"#ef4444",
			"#f97316",
			"#f59e0b",
			"#eab308",
			"#84cc16",
			"#22c55e",
			"#10b981",
			"#14b8a6",
			"#06b6d4",
			"#0ea5e9",
			"#3b82f6",
			"#6366f1",
			"#8b5cf6",
			"#a855f7",
			"#d946ef",
			"#ec4899",
			// Grayscale
			"#000000",
			"#1a1a1a",
			"#333333",
			"#4d4d4d",
			"#666666",
			"#808080",
			"#999999",
			"#b3b3b3",
			"#cccccc",
			"#e6e6e6",
			"#f5f5f5",
			"#ffffff",
		],

		components: {
			preview: true,
			opacity: true, // Disable if you don't need transparency
			hue: true,

			interaction: {
				hex: true,
				rgba: false,
				hsla: false,
				hsva: false,
				cmyk: false,
				input: true,
				clear: false,
				save: true,
			},
		},
	});

	// Update parent when color changes
	pickr.on("save", (color: any) => {
		const hexColor = color.toHEXA().toString();
		emit("update:modelValue", hexColor);
		pickr?.hide();
	});

	pickr.on("change", (color: any) => {
		const hexColor = color.toHEXA().toString();
		emit("update:modelValue", hexColor);
	});
});

// Watch for external changes
watch(
	() => props.modelValue,
	(newValue) => {
		if (pickr && newValue) {
			pickr.setColor(newValue);
		}
	}
);

// Cleanup on unmount
onUnmounted(() => {
	pickr?.destroyAndRemove();
});
</script>

<style scoped>
.color-input {
	display: inline-block;
}
</style>
