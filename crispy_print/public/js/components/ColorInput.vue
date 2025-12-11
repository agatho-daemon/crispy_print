<template>
	<div class="color-input" ref="colorPicker"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue"

declare const frappe: any

interface Props {
	modelValue: string
}

const props = defineProps<Props>()
const emit = defineEmits<{
	"update:modelValue": [value: string]
}>()

const colorPicker = ref<HTMLElement>()
let colorControl: any = null

onMounted(() => {
	if (!colorPicker.value) return

	colorControl = frappe.ui.form.make_control({
		parent: colorPicker.value,
		df: {
			fieldname: "color",
			fieldtype: "Color",
		},
		render_input: true,
	})

	// Set initial value
	colorControl.set_input(props.modelValue || "#000000")

	// Customize picker swatches to include black and grayscale
	if (colorControl.picker) {
		colorControl.picker.swatches = [
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
		]
		colorControl.picker.setup_swatches()
	}

	// Update parent when user picks a color
	const updateColor = () => {
		const newColor = colorControl.get_value()
		if (newColor && newColor !== props.modelValue) {
			emit("update:modelValue", newColor)
		}
	}

	// Hook into the color picker's internal on_change
	if (colorControl.picker) {
		colorControl.picker.on_change = (color: string) => {
			colorControl.set_input(color)
			emit("update:modelValue", color)
		}
	}

	// Also listen to input changes for manual entry
	colorControl.$input.on("change", updateColor)
	colorControl.$input.on("blur", updateColor)
})

// Watch for external changes to modelValue
watch(() => props.modelValue, (newValue) => {
	if (colorControl && newValue !== colorControl.get_value()) {
		colorControl.set_input(newValue)
	}
})
</script>

<style scoped>
.color-input :deep(.control-label) {
	display: none;
}
</style>
