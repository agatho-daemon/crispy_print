<template>
	<section class="report-preview-variables">
		<div class="report-preview-variables__heading">
			<button
				type="button"
				class="report-preview-variables__toggle"
				:aria-expanded="expanded"
				aria-controls="report-preview-variables-content"
				@click="expanded = !expanded"
			>
				<span
					class="report-preview-variables__chevron"
					:class="{ 'is-expanded': expanded }"
					aria-hidden="true"
				>
					<svg viewBox="0 0 16 16" focusable="false">
						<path d="M5.75 3.5 10.25 8l-4.5 4.5" />
					</svg>
				</span>
				<span class="report-preview-variables__title">
					<strong>{{ __("Preview Variables") }}</strong>
					<span>{{
						__("Choose report inputs before generating the live preview.")
					}}</span>
				</span>
			</button>
			<button
				type="button"
				class="btn btn-primary btn-sm"
				:disabled="running || !store.selectedReportName.value"
				@click="runPreview"
			>
				{{ running ? __("Running…") : __("Run Preview") }}
			</button>
		</div>
		<div
			v-show="expanded"
			id="report-preview-variables-content"
			class="report-preview-variables__content"
		>
			<div class="report-preview-variables__grid">
				<label class="report-preview-variables__field">
					<span>{{ __("Report") }}</span>
					<select
						:value="store.selectedReportName.value"
						class="form-control"
						@change="selectReport"
					>
						<option value="" disabled>{{ __("Select a report") }}</option>
						<option
							v-for="report in store.reportCandidates.value"
							:key="report.name"
							:value="report.name"
						>
							{{ report.name }}
						</option>
					</select>
				</label>
				<ReportFilterControl
					v-for="field in store.reportFilterFields.value"
					:key="field.fieldname"
					:field="field"
					:model-value="store.reportFilters.value[field.fieldname]"
					@update:model-value="setFilter(field.fieldname, $event)"
				/>
			</div>
			<p v-if="!store.selectedReportName.value" class="report-preview-variables__message">
				{{ __("Select report coverage in Crispy Format before configuring a preview.") }}
			</p>
			<p v-else-if="runError" class="report-preview-variables__message is-error">
				{{ runError }}
			</p>
			<p
				v-else-if="store.reportPreviewReady.value"
				class="report-preview-variables__message is-ready"
			>
				{{ __("Live data loaded") }}
			</p>
		</div>
	</section>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useStore } from "../composables/useStore";
import { __ } from "../utils/i18n";
import ReportFilterControl from "./ReportFilterControl.vue";

const store = useStore();
const running = ref(false);
const runError = ref("");
const expanded = ref(true);

function eventValue(event: Event) {
	return (event.target as HTMLInputElement | HTMLSelectElement | null)?.value || "";
}
function setFilter(fieldname: string, value: any) {
	store.reportFilters.value = { ...store.reportFilters.value, [fieldname]: value };
	store.reportPreviewReady.value = false;
}
async function selectReport(event: Event) {
	runError.value = "";
	await store.setSelectedReport(eventValue(event));
}
async function runPreview() {
	running.value = true;
	runError.value = "";
	try {
		await store.runSelectedReportPreview();
	} catch (error: any) {
		runError.value = error?.message || __("Unable to run report preview");
	} finally {
		running.value = false;
	}
}
</script>

<style scoped>
.report-preview-variables {
	margin: 12px 28px;
	padding: 14px 18px;
	border: 1px solid #bfdbfe;
	border-radius: 8px;
	background: #eff6ff;
	box-sizing: border-box;
	overflow: hidden;
}
.report-preview-variables__heading {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}
.report-preview-variables__toggle {
	flex: 1;
	display: flex;
	align-items: flex-start;
	gap: 8px;
	min-width: 0;
	padding: 0;
	border: 0;
	background: transparent;
	text-align: left;
	cursor: pointer;
}
.report-preview-variables__toggle:focus-visible {
	outline: 2px solid #2563eb;
	outline-offset: 4px;
	border-radius: 4px;
}
.report-preview-variables__chevron {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	flex: 0 0 22px;
	width: 22px;
	height: 22px;
	margin-top: -1px;
	border-radius: 5px;
	color: #1e3a8a;
	transition: background 150ms ease;
}
.report-preview-variables__toggle:hover .report-preview-variables__chevron {
	background: rgb(37 99 235 / 10%);
}
.report-preview-variables__chevron svg {
	width: 15px;
	height: 15px;
	overflow: visible;
	transform: rotate(0deg);
	transition: transform 150ms ease;
}
.report-preview-variables__chevron path {
	fill: none;
	stroke: currentColor;
	stroke-width: 1.8;
	stroke-linecap: round;
	stroke-linejoin: round;
}
.report-preview-variables__chevron.is-expanded svg {
	transform: rotate(90deg);
}
.report-preview-variables__title {
	display: flex;
	flex-direction: column;
	gap: 2px;
}
.report-preview-variables__title strong {
	color: #1e3a8a;
	font-size: 13px;
	line-height: 20px;
}
.report-preview-variables__title > span {
	color: #475569;
	font-size: 11px;
}
.report-preview-variables__content {
	padding-top: 10px;
}
.report-preview-variables__grid {
	display: grid;
	grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
	gap: 10px 14px;
	max-height: 240px;
	overflow: auto;
	padding: 2px 8px 10px;
}
.report-preview-variables__field {
	display: flex;
	flex-direction: column;
	gap: 3px;
	min-width: 0;
}
.report-preview-variables__field > span {
	color: #334155;
	font-size: 11px;
	font-weight: 600;
}
.report-preview-variables__field b {
	color: #dc2626;
}
.report-preview-variables__message {
	margin: 8px 0 0;
	color: #64748b;
	font-size: 11px;
}
.report-preview-variables__message.is-error {
	color: #b91c1c;
}
.report-preview-variables__message.is-ready {
	color: #15803d;
}
</style>
