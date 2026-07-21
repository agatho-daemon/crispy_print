<template><div ref="host" class="report-filter-control"></div></template>

<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";

const props = withDefaults(
	defineProps<{
		field: Record<string, any>;
		modelValue: any;
		readOnly?: boolean;
	}>(),
	{ readOnly: false }
);
const emit = defineEmits<{ (event: "update:modelValue", value: any): void }>();
const host = ref<HTMLElement | null>(null);
let control: any = null;

function normalizedDefinition() {
	return {
		...props.field,
		fieldname: props.field.fieldname,
		label: props.field.label || props.field.fieldname,
		reqd: props.field.reqd ? 1 : 0,
		read_only: props.readOnly ? 1 : props.field.read_only ? 1 : 0,
	};
}

onMounted(async () => {
	await nextTick();
	if (!host.value || !frappe?.ui?.form?.make_control) return;
	const df = normalizedDefinition();
	df.onchange = () => emit("update:modelValue", control?.get_value?.());
	control = frappe.ui.form.make_control({
		parent: host.value,
		df,
		render_input: true,
	});
	control.refresh?.();
	control.set_value?.(props.modelValue ?? props.field.default ?? "");
});

watch(
	() => props.modelValue,
	(value) => {
		if (control && control.get_value?.() !== value) control.set_value?.(value ?? "");
	}
);

onBeforeUnmount(() => {
	control?.$wrapper?.remove?.();
	control = null;
});
</script>

<style scoped>
.report-filter-control {
	min-width: 0;
}
.report-filter-control :deep(.frappe-control) {
	margin: 0;
}
.report-filter-control :deep(.form-group) {
	margin-bottom: 0;
}
.report-filter-control :deep(.control-label) {
	color: #334155;
	font-size: 11px;
	font-weight: 600;
}
.report-filter-control :deep(.control-input-wrapper),
.report-filter-control :deep(.control-input),
.report-filter-control :deep(.form-control) {
	min-width: 0;
	width: 100%;
	box-sizing: border-box;
}
</style>
