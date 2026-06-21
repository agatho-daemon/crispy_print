<template>
	<div
		class="settings-pane__section-card card"
		:class="{ 'settings-pane__section-card--content-border': contentBorder }"
	>
		<button
			type="button"
			class="btn btn-link card-header settings-pane__section-header"
			:class="{ 'is-expanded': modelValue }"
			@click="emit('update:modelValue', !modelValue)"
		>
			<span>{{ title }}</span>
			<svg
				class="settings-pane__chevron"
				:class="{ 'settings-pane__chevron--expanded': modelValue }"
				xmlns="http://www.w3.org/2000/svg"
				viewBox="0 0 20 20"
				fill="currentColor"
			>
				<path
					fill-rule="evenodd"
					d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
					clip-rule="evenodd"
				/>
			</svg>
		</button>
		<div v-if="modelValue" class="settings-pane__section-content card-body">
			<slot></slot>
		</div>
	</div>
</template>

<script setup lang="ts">
defineProps<{
	modelValue: boolean;
	title: string;
	contentBorder?: boolean;
}>();

const emit = defineEmits<{
	"update:modelValue": [value: boolean];
}>();
</script>

<style scoped>
.settings-pane__section-card {
	border: 1px solid #dbe3ee;
	border-radius: 12px;
	overflow: hidden;
	background: #fff;
	box-shadow: none !important;
}

.settings-pane__section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	cursor: pointer;
	margin: 0;
	padding: 10px 12px;
	text-align: left;
	background: #fff;
	color: #334155;
	border: none !important;
	border-bottom: none !important;
	box-shadow: none !important;
	text-decoration: none;
}

.settings-pane__section-header.is-expanded {
	border-left: 0;
	padding-left: 12px;
}

.settings-pane__section-header:hover {
	background: #f8fafc;
	color: #334155;
	text-decoration: none;
}

.settings-pane__section-header:focus {
	background: #fff;
	color: #334155;
	text-decoration: none;
	outline: none;
	box-shadow: none;
}

.settings-pane__section-header:focus-visible {
	background: #f8fafc;
	outline: 2px solid #cbd5e1;
	outline-offset: -2px;
}

.settings-pane__chevron {
	width: 16px;
	height: 16px;
	transition: transform 0.2s ease;
}

.settings-pane__chevron--expanded {
	transform: rotate(-180deg);
}

.settings-pane__section-content {
	display: flex;
	flex-direction: column;
	gap: 12px;
	padding: 12px;
	border-top: none !important;
	box-shadow: none !important;
}

.settings-pane__section-card--content-border .settings-pane__section-content {
	border-top: 1px solid #e2e8f0 !important;
}
</style>
