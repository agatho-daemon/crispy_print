<template>
	<div v-if="open" class="sample-formats" role="presentation">
		<div class="sample-formats__backdrop" @click="emit('close')"></div>
		<section
			class="sample-formats__dialog"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Create from Example')"
		>
			<header class="sample-formats__header">
				<h3>{{ __("Create from Example") }}</h3>
				<button
					type="button"
					class="btn btn-default btn-xs"
					:title="__('Close')"
					@click="emit('close')"
				>
					×
				</button>
			</header>

			<div class="sample-formats__body">
				<div class="sample-formats__list" role="listbox" :aria-label="__('Examples')">
					<button
						v-for="sample in samples"
						:key="sample.id"
						type="button"
						class="sample-formats__item"
						:class="{ 'is-active': form.sample_id === sample.id }"
						@click="selectSample(sample)"
					>
						<span class="sample-formats__item-title">{{ sample.title }}</span>
						<span class="sample-formats__item-meta">
							{{ sample.target_type }}
							<template v-if="sample.doc_type"> · {{ sample.doc_type }}</template>
							<template v-if="sample.report_kind">
								· {{ sample.report_kind }}</template
							>
						</span>
						<span class="sample-formats__item-description">{{
							sample.description
						}}</span>
					</button>
					<div v-if="!loadingSamples && !samples.length" class="sample-formats__empty">
						{{ __("No examples are available.") }}
					</div>
					<div v-if="loadingSamples" class="sample-formats__empty">
						{{ __("Loading examples...") }}
					</div>
				</div>

				<div class="sample-formats__details">
					<div v-if="selectedSample" class="sample-formats__summary">
						<h4>{{ selectedSample.title }}</h4>
						<p>{{ selectedSample.recommended_use || selectedSample.description }}</p>
						<div v-if="selectedSample.tags.length" class="sample-formats__tags">
							<span
								v-for="tag in selectedSample.tags"
								:key="tag"
								class="sample-formats__tag"
							>
								{{ tag }}
							</span>
						</div>
					</div>

					<div class="sample-formats__field">
						<label>{{ __("Target Company") }}</label>
						<select v-model="form.company" class="form-control">
							<option value="">
								{{ loadingCompanies ? __("Loading...") : __("Select company") }}
							</option>
							<option
								v-for="company in companies"
								:key="company.name"
								:value="company.name"
							>
								{{
									company.abbr
										? `${company.abbr} - ${company.name}`
										: company.name
								}}
							</option>
						</select>
					</div>

					<div class="sample-formats__field">
						<label>{{ __("Format Name") }}</label>
						<input
							v-model.trim="form.name"
							class="form-control"
							:placeholder="
								selectedSample?.format_name || __('Optional custom name')
							"
						/>
					</div>

					<label class="sample-formats__check">
						<input v-model="form.set_default" type="checkbox" />
						<span>{{ __("Set created format as default") }}</span>
					</label>
				</div>
			</div>

			<footer class="sample-formats__footer">
				<button type="button" class="btn btn-default btn-sm" @click="emit('close')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="btn btn-primary btn-sm"
					:disabled="submitting || !canSubmit"
					@click="confirm"
				>
					{{ submitting ? __("Creating...") : __("Create Format") }}
				</button>
			</footer>
		</section>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import {
	getCompanies,
	listSampleFormats,
	type CompanyOption,
	type SampleFormatCatalogItem,
} from "../api/crispy";
import { getLogger } from "../logger";
import { __ } from "../utils/i18n";

const props = defineProps<{
	open: boolean;
	submitting: boolean;
}>();

const emit = defineEmits<{
	close: [];
	confirm: [
		value: {
			sample_id: string;
			company: string;
			name?: string | null;
			set_default: boolean;
		}
	];
}>();

const logger = getLogger({ component: "SampleFormatsDialog" });
const samples = ref<SampleFormatCatalogItem[]>([]);
const companies = ref<CompanyOption[]>([]);
const loadingSamples = ref(false);
const loadingCompanies = ref(false);
const form = reactive({
	sample_id: "",
	company: "",
	name: "",
	set_default: false,
});

const selectedSample = computed(
	() => samples.value.find((sample) => sample.id === form.sample_id) || null
);
const canSubmit = computed(() => Boolean(form.sample_id && form.company));

watch(
	() => props.open,
	(open) => {
		if (!open) return;
		form.sample_id = "";
		form.company = "";
		form.name = "";
		form.set_default = false;
		fetchCatalog();
		fetchCompanies();
	},
	{ immediate: true }
);

async function fetchCatalog() {
	loadingSamples.value = true;
	try {
		samples.value = await listSampleFormats();
		if (samples.value.length) {
			selectSample(samples.value[0]);
		}
	} catch (error) {
		logger.warn("Failed to load sample formats", error);
		samples.value = [];
	} finally {
		loadingSamples.value = false;
	}
}

async function fetchCompanies() {
	loadingCompanies.value = true;
	try {
		companies.value = await getCompanies();
	} catch (error) {
		logger.warn("Failed to load companies for sample format dialog", error);
		companies.value = [];
	} finally {
		loadingCompanies.value = false;
	}
}

function selectSample(sample: SampleFormatCatalogItem) {
	form.sample_id = sample.id;
	if (!form.name) {
		form.name = sample.format_name || sample.title;
	}
}

function confirm() {
	if (!canSubmit.value) return;
	emit("confirm", {
		sample_id: form.sample_id,
		company: form.company,
		name: form.name || null,
		set_default: form.set_default,
	});
}
</script>

<style scoped>
.sample-formats {
	position: fixed;
	inset: 0;
	z-index: 1040;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
}

.sample-formats__backdrop {
	position: absolute;
	inset: 0;
	background: rgba(15, 23, 42, 0.42);
}

.sample-formats__dialog {
	position: relative;
	width: min(860px, 100%);
	max-height: min(760px, calc(100vh - 48px));
	display: flex;
	flex-direction: column;
	background: #fff;
	border: 1px solid #d8dbe0;
	border-radius: 8px;
	box-shadow: 0 18px 48px rgba(15, 23, 42, 0.22);
	overflow: hidden;
}

.sample-formats__header,
.sample-formats__footer {
	display: flex;
	align-items: center;
	gap: 16px;
	padding: 18px 24px;
	border-bottom: 1px solid #e5e7eb;
}

.sample-formats__footer {
	justify-content: flex-end;
	border-top: 1px solid #e5e7eb;
	border-bottom: 0;
}

.sample-formats__header h3 {
	flex: 1;
	margin: 0;
	color: #1f272e;
	font-size: 20px;
	font-weight: 700;
	line-height: 1.35;
}

.sample-formats__body {
	display: grid;
	grid-template-columns: minmax(260px, 1fr) minmax(280px, 0.9fr);
	min-height: 0;
	overflow: hidden;
}

.sample-formats__list {
	min-height: 0;
	max-height: 560px;
	overflow: auto;
	padding: 16px;
	border-right: 1px solid #e5e7eb;
	background: #f8fafc;
}

.sample-formats__item {
	width: 100%;
	display: flex;
	flex-direction: column;
	gap: 4px;
	padding: 12px;
	margin: 0 0 8px;
	text-align: left;
	border: 1px solid #d8dbe0;
	border-radius: 8px;
	background: #fff;
	color: #1f272e;
	box-shadow: none;
	cursor: pointer;
}

.sample-formats__item:hover,
.sample-formats__item.is-active {
	border-color: #2563eb;
}

.sample-formats__item-title {
	font-size: 14px;
	font-weight: 700;
	line-height: 1.35;
}

.sample-formats__item-meta {
	color: #64748b;
	font-size: 12px;
	line-height: 1.35;
}

.sample-formats__item-description {
	color: #334155;
	font-size: 13px;
	line-height: 1.4;
}

.sample-formats__details {
	min-height: 0;
	overflow: auto;
	padding: 20px 24px;
}

.sample-formats__summary h4 {
	margin: 0 0 8px;
	font-size: 16px;
	font-weight: 700;
	line-height: 1.35;
}

.sample-formats__summary p {
	margin: 0 0 12px;
	color: #334155;
	font-size: 13px;
	line-height: 1.5;
}

.sample-formats__tags {
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	margin-bottom: 16px;
}

.sample-formats__tag {
	padding: 2px 8px;
	border: 1px solid #d8dbe0;
	border-radius: 999px;
	background: #f8fafc;
	color: #475569;
	font-size: 12px;
	line-height: 1.5;
}

.sample-formats__field {
	display: grid;
	gap: 6px;
	margin-bottom: 14px;
}

.sample-formats__field label,
.sample-formats__check {
	color: #334155;
	font-size: 13px;
	font-weight: 600;
}

.sample-formats__check {
	display: flex;
	align-items: center;
	gap: 8px;
	margin: 8px 0 0;
}

.sample-formats__empty {
	padding: 16px;
	color: #64748b;
	font-size: 13px;
	text-align: center;
}

@media (max-width: 760px) {
	.sample-formats {
		padding: 12px;
	}

	.sample-formats__body {
		grid-template-columns: 1fr;
	}

	.sample-formats__list {
		max-height: 260px;
		border-right: 0;
		border-bottom: 1px solid #e5e7eb;
	}
}
</style>
