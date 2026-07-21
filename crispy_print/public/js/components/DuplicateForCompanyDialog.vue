<template>
	<div v-if="open" class="duplicate-company" role="presentation">
		<div class="duplicate-company__backdrop" @click="emit('close')"></div>
		<section
			class="duplicate-company__dialog"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Duplicate for Company')"
		>
			<header class="duplicate-company__header">
				<h3>{{ __("Duplicate for Company") }}</h3>
				<button
					type="button"
					class="btn btn-default btn-xs"
					:title="__('Close')"
					@click="emit('close')"
				>
					×
				</button>
			</header>

			<div class="duplicate-company__body">
				<div class="duplicate-company__field">
					<label>{{ __("Duplicate") }}</label>
					<div class="duplicate-company__segments">
						<button
							type="button"
							class="btn btn-default btn-sm duplicate-company__segment"
							:class="{ 'is-active': form.source_type === 'format' }"
							@click="form.source_type = 'format'"
						>
							{{ __("Current Format") }}
						</button>
						<button
							type="button"
							class="btn btn-default btn-sm duplicate-company__segment"
							:class="{ 'is-active': form.source_type === 'template' }"
							@click="form.source_type = 'template'"
						>
							{{ __("Template Snapshot") }}
						</button>
					</div>
				</div>

				<div class="duplicate-company__field">
					<label>{{ __("Target Company") }}</label>
					<select v-model="form.target_company" class="form-control">
						<option value="">
							{{ loadingCompanies ? __("Loading...") : __("Select company") }}
						</option>
						<option
							v-for="company in companies"
							:key="company.name"
							:value="company.name"
						>
							{{ company.name }}
						</option>
					</select>
				</div>

				<div v-if="form.source_type === 'template'" class="duplicate-company__field">
					<label>{{ __("Source Template") }}</label>
					<input
						v-model.trim="form.source_template"
						class="form-control"
						:placeholder="__('Crispy Template ID')"
					/>
				</div>

				<div v-if="form.source_type === 'template'" class="duplicate-company__field">
					<label>{{ __("Template Source") }}</label>
					<div class="duplicate-company__segments">
						<button
							type="button"
							class="btn btn-default btn-sm duplicate-company__segment"
							:class="{ 'is-active': form.clone_mode === 'snapshot' }"
							@click="form.clone_mode = 'snapshot'"
						>
							{{ __("Frozen Snapshot") }}
						</button>
						<button
							type="button"
							class="btn btn-default btn-sm duplicate-company__segment"
							:class="{ 'is-active': form.clone_mode === 'current_format' }"
							@click="form.clone_mode = 'current_format'"
						>
							{{ __("Current Format") }}
						</button>
					</div>
				</div>

				<label v-if="form.source_type === 'format'" class="duplicate-company__check">
					<input v-model="form.set_default" type="checkbox" />
					<span>{{ __("Set cloned format as default") }}</span>
				</label>

				<label v-if="form.source_type === 'template'" class="duplicate-company__check">
					<input v-model="form.make_active" type="checkbox" />
					<span>{{ __("Make cloned template active") }}</span>
				</label>
			</div>

			<footer class="duplicate-company__footer">
				<button type="button" class="btn btn-default btn-sm" @click="emit('close')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="btn btn-primary btn-sm"
					:disabled="submitting || !canSubmit"
					@click="confirm"
				>
					{{ submitting ? __("Duplicating...") : __("Duplicate") }}
				</button>
			</footer>
		</section>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { getCompanies, type CompanyOption } from "../api/crispy";
import { getLogger } from "../logger";
import { __ } from "../utils/i18n";

const props = defineProps<{
	open: boolean;
	submitting: boolean;
}>();

const emit = defineEmits<{
	close: [];
	confirm: [
		value:
			| {
					source_type: "format";
					target_company: string;
					set_default: boolean;
			  }
			| {
					source_type: "template";
					target_company: string;
					source_template: string;
					clone_mode: "snapshot" | "current_format";
					make_active: boolean;
			  }
	];
}>();

const logger = getLogger({ component: "DuplicateForCompanyDialog" });
const companies = ref<CompanyOption[]>([]);
const loadingCompanies = ref(false);
const form = reactive({
	source_type: "format" as "format" | "template",
	target_company: "",
	source_template: "",
	clone_mode: "snapshot" as "snapshot" | "current_format",
	set_default: false,
	make_active: false,
});

const canSubmit = computed(() => {
	if (!form.target_company) return false;
	if (form.source_type === "template") return Boolean(form.source_template);
	return true;
});

watch(
	() => props.open,
	(open) => {
		if (!open) return;
		form.source_type = "format";
		form.target_company = "";
		form.source_template = "";
		form.clone_mode = "snapshot";
		form.set_default = false;
		form.make_active = false;
		fetchCompanies();
	}
);

async function fetchCompanies() {
	loadingCompanies.value = true;
	try {
		companies.value = await getCompanies();
	} catch (error) {
		logger.warn("Failed to load companies for duplicate dialog", error);
		companies.value = [];
	} finally {
		loadingCompanies.value = false;
	}
}

function confirm() {
	if (!canSubmit.value) return;
	if (form.source_type === "template") {
		emit("confirm", {
			source_type: "template",
			target_company: form.target_company,
			source_template: form.source_template,
			clone_mode: form.clone_mode,
			make_active: form.make_active,
		});
		return;
	}
	emit("confirm", {
		source_type: "format",
		target_company: form.target_company,
		set_default: form.set_default,
	});
}
</script>

<style scoped>
.duplicate-company {
	position: fixed;
	inset: 0;
	z-index: 1040;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
}

.duplicate-company__backdrop {
	position: absolute;
	inset: 0;
	background: rgba(15, 23, 42, 0.42);
}

.duplicate-company__dialog {
	position: relative;
	width: min(620px, 100%);
	max-height: min(720px, calc(100vh - 48px));
	display: flex;
	flex-direction: column;
	background: #fff;
	border: 1px solid #d8dbe0;
	border-radius: 8px;
	box-shadow: 0 18px 48px rgba(15, 23, 42, 0.22);
	overflow: hidden;
}

.duplicate-company__header,
.duplicate-company__footer {
	display: flex;
	align-items: center;
	gap: 16px;
	padding: 18px 24px;
	border-bottom: 1px solid #e5e7eb;
}

.duplicate-company__header h3 {
	flex: 1;
	margin: 0;
	color: #1f272e;
	font-size: 20px;
	font-weight: 700;
	line-height: 1.35;
}

.duplicate-company__body {
	display: flex;
	flex-direction: column;
	gap: 18px;
	padding: 22px 24px 24px;
	overflow: auto;
}

.duplicate-company__footer {
	justify-content: flex-end;
	border-top: 1px solid #e5e7eb;
	border-bottom: 0;
}

.duplicate-company__field {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.duplicate-company__field label,
.duplicate-company__check {
	font-size: 12px;
	font-weight: 700;
	color: #4c5a67;
}

.duplicate-company__segments {
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.duplicate-company__segment.is-active {
	background: #1f272e;
	border-color: #1f272e;
	color: #fff;
}

.duplicate-company__check {
	display: inline-flex;
	align-items: center;
	gap: 8px;
}
</style>
