<template>
	<section class="health-panel" aria-live="polite">
		<div class="health-panel__header">
			<div>
				<h3>{{ __("Format Health") }}</h3>
				<p>{{ summary }}</p>
			</div>
			<span class="health-panel__badge" :class="`health-panel__badge--${status}`">
				{{ statusLabel }}
			</span>
		</div>
		<ul v-if="items.length" class="health-panel__list">
			<li
				v-for="item in items"
				:key="`${item.level}-${item.message}`"
				class="health-panel__item"
				:class="`health-panel__item--${item.level}`"
			>
				<strong>{{ levelLabel(item.level) }}</strong>
				<span>{{ item.message }}</span>
			</li>
		</ul>
		<p v-else class="health-panel__empty">
			{{ __("No obvious format issues found.") }}
		</p>
	</section>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { __ } from "../utils/i18n";

export type FormatHealthLevel = "error" | "warning" | "info";

export interface FormatHealthItem {
	level: FormatHealthLevel;
	message: string;
}

const props = defineProps<{
	items: FormatHealthItem[];
}>();

const status = computed(() => {
	if (props.items.some((item) => item.level === "error")) return "error";
	if (props.items.some((item) => item.level === "warning")) return "warning";
	if (props.items.some((item) => item.level === "info")) return "info";
	return "ok";
});

const statusLabel = computed(() => {
	if (status.value === "error") return __("Needs attention");
	if (status.value === "warning") return __("Review");
	if (status.value === "info") return __("Info");
	return __("Ready");
});

const summary = computed(() => {
	if (!props.items.length) return __("Checks passed for the current builder state.");
	return __("{0} check(s) need review.", [props.items.length]);
});

function levelLabel(level: FormatHealthLevel) {
	if (level === "error") return __("Error");
	if (level === "warning") return __("Warning");
	return __("Info");
}
</script>

<style scoped>
.health-panel {
	margin-bottom: 12px;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	background: #fff;
	overflow: hidden;
}

.health-panel__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	padding: 12px;
	background: #f8fafc;
	border-bottom: 1px solid #e2e8f0;
}

.health-panel__header h3 {
	margin: 0;
	font-size: 13px;
	font-weight: 700;
	color: #0f172a;
}

.health-panel__header p {
	margin: 2px 0 0;
	font-size: 12px;
	color: #64748b;
}

.health-panel__badge {
	flex: 0 0 auto;
	padding: 3px 8px;
	border-radius: 999px;
	font-size: 11px;
	font-weight: 700;
	background: #dcfce7;
	color: #166534;
}

.health-panel__badge--warning,
.health-panel__badge--info {
	background: #fef3c7;
	color: #92400e;
}

.health-panel__badge--error {
	background: #fee2e2;
	color: #991b1b;
}

.health-panel__list {
	display: grid;
	gap: 0;
	margin: 0;
	padding: 0;
	list-style: none;
}

.health-panel__item {
	display: grid;
	grid-template-columns: 72px minmax(0, 1fr);
	gap: 8px;
	padding: 9px 12px;
	border-top: 1px solid #f1f5f9;
	font-size: 12px;
}

.health-panel__item:first-child {
	border-top: 0;
}

.health-panel__item strong {
	font-size: 11px;
	text-transform: uppercase;
	color: #64748b;
}

.health-panel__item span {
	min-width: 0;
	color: #0f172a;
}

.health-panel__item--error strong {
	color: #b91c1c;
}

.health-panel__item--warning strong {
	color: #b45309;
}

.health-panel__empty {
	margin: 0;
	padding: 12px;
	font-size: 12px;
	color: #64748b;
}
</style>
