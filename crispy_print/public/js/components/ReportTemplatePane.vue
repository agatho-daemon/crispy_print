<template>
	<div class="report-template-pane">
		<div class="report-template-pane__header">
			<h3 class="report-template-pane__title">{{ __("Report Template") }}</h3>
			<p class="report-template-pane__hint">
				{{
					__(
						"Basic mode is style-preview only. Real report output is rendered by raw Typst templates (CrispyPP/runtime)."
					)
				}}
			</p>
		</div>

		<div v-if="store.reportModeNotice.value" class="report-template-pane__warning">
			<p>{{ store.reportModeNotice.value }}</p>
			<div class="report-template-pane__warning-actions">
				<button
					type="button"
					class="btn btn-default btn-xs"
					@click="store.reportBuilderMode.value = 'advanced'"
				>
					{{ __("Stay in Advanced") }}
				</button>
				<button
					type="button"
					class="btn btn-primary btn-xs"
					@click="store.resetReportBasicTemplate"
				>
					{{ __("Reset to Basic Template") }}
				</button>
			</div>
		</div>

		<div class="report-template-pane__body">
			<div class="report-template-pane__row">
				<label class="report-template-pane__label">{{ __("Preset") }}</label>
				<select
					v-model="store.reportBuilderConfig.value.preset"
					class="form-control"
					:disabled="store.reportBasicReadOnly.value"
				>
					<option value="grid">{{ __("Grid") }}</option>
					<option value="tree">{{ __("Tree") }}</option>
					<option value="summary">{{ __("Summary") }}</option>
					<option value="minimal">{{ __("Minimal") }}</option>
				</select>
			</div>
			<label class="report-template-pane__toggle">
				<input
					v-model="store.reportBuilderConfig.value.show_filters"
					type="checkbox"
					:disabled="store.reportBasicReadOnly.value"
				/>
				<span>{{ __("Show filters block") }}</span>
			</label>
			<label class="report-template-pane__toggle">
				<input
					v-model="store.reportBuilderConfig.value.show_footer_total"
					type="checkbox"
					:disabled="store.reportBasicReadOnly.value"
				/>
				<span>{{ __("Show total records footer") }}</span>
			</label>

			<div class="report-template-pane__source">
				<div class="report-template-pane__source-label">{{ __("Generated Typst") }}</div>
				<textarea
					:value="store.typstCode.value"
					class="report-template-pane__source-text"
					readonly
				></textarea>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { useStore } from "../composables/useStore";
import { __ } from "../utils/i18n";

const store = useStore();
</script>

<style scoped>
.report-template-pane {
	display: flex;
	flex-direction: column;
	border: 1px solid #e2e8f0;
	background: #fff;
	min-height: 0;
}

.report-template-pane__header {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px 16px;
}

.report-template-pane__title {
	margin: 0;
	font-size: 14px;
	font-weight: 600;
	color: #1e293b;
}

.report-template-pane__hint {
	margin: 6px 0 0;
	font-size: 12px;
	color: #64748b;
}

.report-template-pane__warning {
	margin: 12px 16px 0;
	padding: 10px 12px;
	border: 1px solid #fbbf24;
	background: #fffbeb;
	border-radius: 8px;
	font-size: 12px;
}

.report-template-pane__warning p {
	margin: 0;
	color: #92400e;
}

.report-template-pane__warning-actions {
	margin-top: 10px;
	display: flex;
	gap: 8px;
}

.report-template-pane__body {
	flex: 1;
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding: 12px 16px 16px;
	min-height: 0;
}

.report-template-pane__row {
	display: flex;
	flex-direction: column;
	gap: 4px;
}

.report-template-pane__label {
	font-size: 12px;
	font-weight: 600;
	color: #334155;
}

.report-template-pane__toggle {
	display: flex;
	align-items: center;
	gap: 8px;
	font-size: 12px;
	color: #334155;
}

.report-template-pane__source {
	display: flex;
	flex-direction: column;
	gap: 6px;
	flex: 1;
	min-height: 0;
}

.report-template-pane__source-label {
	font-size: 11px;
	font-weight: 600;
	color: #64748b;
	letter-spacing: 0.02em;
	text-transform: uppercase;
}

.report-template-pane__source-text {
	flex: 1;
	min-height: 220px;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	padding: 10px;
	font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
		monospace;
	font-size: 11px;
	line-height: 1.5;
	background: #f8fafc;
	color: #0f172a;
	resize: vertical;
}
</style>
