<template>
	<div class="fields-pane">
		<div class="section-head fields-pane__header">
			<div class="section-head-content fields-pane__header-row">
				<h3 class="section-title fields-pane__title">
					{{ __("Fields") }}
				</h3>
				<div class="fields-pane__spacer"></div>
				<div class="fields-pane__help">
					<button
						type="button"
						class="btn btn-default btn-xs fields-pane__help-btn"
						popovertarget="fields-help"
						popovertargetaction="toggle"
						:title="__('Toggle help')"
						aria-haspopup="dialog"
						aria-controls="fields-help"
					>
						?
					</button>
					<div id="fields-help" popover class="fields-pane__help-popover">
						<ul class="fields-pane__help-list">
							<li v-if="isReportMode">
								{{
									__(
										"Drag report blocks into the layout builder to compose your print format."
									)
								}}
							</li>
							<li v-else>
								{{ __("Use the search box to quickly find specific fields.") }}
							</li>
							<li>{{ __("Hover over a field to see its fieldname and type.") }}</li>
						</ul>
					</div>
				</div>
				<slot name="header-actions"></slot>
			</div>
		</div>
		<div class="fields-pane__search-area">
			<div class="search-box">
				<input
					v-model="searchQuery"
					type="text"
					:placeholder="__('Search {0} fields...', [filteredFieldCount])"
					class="form-control search-input"
				/>
			</div>
			<div v-if="loading" class="loading-indicator">
				<span class="loading-text">{{ __("Loading fields...") }}</span>
			</div>
		</div>
		<div class="fields-list">
			<div v-if="filteredFieldCount === 0" class="empty-state">
				<p v-if="searchQuery" class="empty-message">
					{{ __("No fields match {0}!", [searchQuery]) }}
				</p>
				<p v-else class="empty-message">{{ __("No fields available yet!") }}</p>
			</div>

			<template v-for="group in groupedFields" :key="group.title || 'fields'">
				<div v-if="group.title && group.fields.length" class="fields-list__subtitle">
					{{ group.title }}
				</div>
				<div
					v-for="field in group.fields"
					:key="field.name || field.fieldname"
					class="field-item"
					draggable="true"
					@dragstart="onFieldDragStart($event, field)"
					:title="`(${field.fieldname} — ${field.fieldtype || __('Unknown')})`"
				>
					<div class="field-label">
						{{ field.label }}
					</div>
					<div v-if="isReportMode && field.fieldtype" class="field-type-badge">
						{{ field.fieldtype }}
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref, unref, type MaybeRef } from "vue";
import type { DocField } from "../utils/layout";
import { __ } from "../utils/i18n";

interface Props {
	fields: MaybeRef<DocField[]>;
	reportFields?: MaybeRef<any[]>;
	isReportMode?: MaybeRef<boolean>;
	loading?: MaybeRef<boolean>;
}

const props = withDefaults(defineProps<Props>(), {
	loading: false,
	isReportMode: false,
	reportFields: () => [],
});

const searchQuery = ref("");
const loading = computed(() => unref(props.loading));
const isReportMode = computed(() => unref(props.isReportMode));
const crispyFieldnames = new Set([
	"doctype",
	"name",
	"_crispy_typst_block",
	"_crispy_image",
	"_typst_snippet",
	"empty",
	"spacer",
	"divider",
]);

// Combine fields and report columns based on mode
const allFields = computed(() => {
	if (isReportMode.value) {
		return unref(props.reportFields) || [];
	}
	const fields = unref(props.fields) || [];
	return fields;
});

const filteredFields = computed(() => {
	const all = allFields.value;
	if (!searchQuery.value) return all;

	const query = searchQuery.value.toLowerCase();
	return all.filter((field) => {
		const label = field.label?.toLowerCase() || "";
		const name = field.fieldname?.toLowerCase() || "";
		const type = field.fieldtype?.toLowerCase() || "";
		return label.includes(query) || name.includes(query) || type.includes(query);
	});
});

const filteredFieldCount = computed(() => filteredFields.value.length);

const groupedFields = computed(() => {
	const fields = filteredFields.value;
	if (isReportMode.value) {
		return [{ title: "", fields }];
	}

	const crispyFields = fields.filter((field) => crispyFieldnames.has(field.fieldname));
	const documentFields = fields.filter((field) => !crispyFieldnames.has(field.fieldname));

	return [
		{ title: __("Crispy Fields"), fields: crispyFields },
		{ title: __("Document Fields"), fields: documentFields },
	];
});

function onFieldDragStart(event: DragEvent, field: DocField) {
	if (event.dataTransfer) {
		event.dataTransfer.effectAllowed = "copy";
		event.dataTransfer.setData("application/json", JSON.stringify(field));
		event.dataTransfer.setData("text/plain", field.fieldname);
	}
}
</script>

<style scoped>
.fields-pane {
	display: flex;
	border: 1px solid #e2e8f0;
	flex-direction: column;
	background: #fff;
}

.fields-pane__header {
	margin: 12px 16px 0;
	padding: 0;
}

.fields-pane__header-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.fields-pane__spacer {
	margin-left: auto;
}

.fields-pane__title {
	margin: 0;
}

.fields-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
	border-color: transparent !important;
	background: transparent !important;
	box-shadow: none !important;
	color: #334155;
	font-size: 13px;
	font-weight: 500;
	transition: color 0.15s ease, font-size 0.15s ease, font-weight 0.15s ease;
}

.fields-pane__help-btn:hover,
.fields-pane__help-btn:focus-visible {
	border-color: transparent !important;
	background: transparent !important;
	color: #0f172a;
	font-size: 14px;
	font-weight: 700;
}

.fields-pane__help {
	display: flex;
	align-items: center;
}

.fields-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
}

.fields-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.fields-pane__search-area {
	padding: 12px 16px;
}

.search-box {
	display: block;
}

.search-input {
	width: 100%;
}

.loading-indicator {
	margin-top: 8px;
	font-size: 13px;
}

.fields-list {
	overflow-y: auto;
	padding: 12px 16px 16px;
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.fields-list__subtitle {
	margin: 4px 2px 0;
	color: #64748b;
	font-size: 11px;
	font-weight: 700;
	text-transform: uppercase;
}

.empty-state {
	font-size: 14px;
}

.empty-message {
	margin: 0;
}

.field-item {
	width: 100%;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
	padding: 8px 12px;
	border-radius: 6px;
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	cursor: grab;
}

.field-item:hover {
	background: var(--control-bg, #f8f9fa);
}

.field-label {
	display: block;
	font-size: 14px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	flex: 1;
}

.field-type-badge {
	font-size: 11px;
	padding: 2px 8px;
	border-radius: 3px;
	white-space: nowrap;
	flex-shrink: 0;
}

.fields-pane__header :deep(.section-head-content) {
	padding: 0 0 8px;
}
</style>
