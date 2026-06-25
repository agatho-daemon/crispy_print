<template>
	<div v-if="open" class="diagnostics" role="dialog" aria-modal="false">
		<div class="diagnostics__header">
			<h3>{{ __("Preview Diagnostics") }}</h3>
		</div>
		<div class="diagnostics__body">
			<div class="diagnostics__grid">
				<div v-for="item in normalizedItems" :key="item.label" class="diagnostics__item">
					<span class="diagnostics__label">{{ item.label }}</span>
					<span class="diagnostics__value">{{ item.value }}</span>
				</div>
			</div>
			<p v-if="!normalizedItems.length" class="diagnostics__empty">
				{{ __("No diagnostics available yet.") }}
			</p>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { __ } from "../utils/i18n";

export interface PreviewDiagnosticItem {
	label: string;
	value: string | number | boolean | null | undefined;
}

const props = defineProps<{
	open: boolean;
	items: PreviewDiagnosticItem[];
}>();

const normalizedItems = computed(() =>
	(props.items || []).map((item) => ({
		label: item.label,
		value:
			item.value === undefined || item.value === null || item.value === ""
				? __("Not available")
				: typeof item.value === "boolean"
				? item.value
					? __("Yes")
					: __("No")
				: String(item.value),
	}))
);
</script>

<style scoped>
.diagnostics {
	position: absolute;
	top: calc(100% + 8px);
	right: 0;
	z-index: 5;
	width: min(520px, calc(100vw - 32px));
	max-height: min(680px, calc(100vh - 220px));
	display: flex;
	flex-direction: column;
	border: 1px solid #cbd5e1;
	border-radius: 8px;
	background: #fff;
	box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
	overflow: hidden;
}

.diagnostics__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	padding: 10px 12px;
	border-bottom: 1px solid #e2e8f0;
	background: #f8fafc;
}

.diagnostics__header h3 {
	margin: 0;
	font-size: 14px;
	font-weight: 700;
	color: #0f172a;
}

.diagnostics__body {
	overflow: auto;
	padding: 12px;
}

.diagnostics__grid {
	display: grid;
	gap: 8px;
}

.diagnostics__item {
	display: grid;
	grid-template-columns: minmax(110px, 0.8fr) minmax(0, 1.2fr);
	gap: 10px;
	align-items: start;
	padding-bottom: 8px;
	border-bottom: 1px solid #f1f5f9;
}

.diagnostics__label {
	font-size: 11px;
	font-weight: 700;
	color: #64748b;
	text-transform: uppercase;
}

.diagnostics__value {
	min-width: 0;
	overflow-wrap: anywhere;
	font-size: 12px;
	color: #0f172a;
}

.diagnostics__empty {
	margin: 0;
	color: #64748b;
	font-size: 12px;
}
</style>
