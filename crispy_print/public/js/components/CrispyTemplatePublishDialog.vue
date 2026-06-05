<template>
	<div v-if="open" class="template-publish" role="presentation">
		<div class="template-publish__backdrop" @click="emit('close')"></div>
		<section
			class="template-publish__dialog"
			role="dialog"
			aria-modal="true"
			:aria-label="__('Publish Crispy Template')"
		>
			<header class="template-publish__header">
				<h3>{{ __("Publish Crispy Template") }}</h3>
				<button
					type="button"
					class="btn btn-default btn-xs"
					:title="__('Close')"
					@click="emit('close')"
				>
					×
				</button>
			</header>

			<div class="template-publish__body">
				<div class="template-publish__field">
					<label>{{ __("Template ID") }}</label>
					<input
						class="form-control"
						:value="preview?.template_id || __('Loading...')"
						readonly
					/>
				</div>

				<div class="template-publish__grid">
					<div class="template-publish__field">
						<label>{{ __("Company") }}</label>
						<input class="form-control" :value="companyLabel" readonly />
					</div>
					<div class="template-publish__field">
						<label>{{ __("Branding Profile") }}</label>
						<input class="form-control" :value="brandingProfileLabel" readonly />
					</div>
				</div>

				<div v-if="isFirstTemplateVersion" class="template-publish__first-version">
					<div>
						<span class="template-publish__first-label">{{
							__("First Template Version")
						}}</span>
						<span class="template-publish__first-help">{{
							__("This template stream will start at version 1.0.")
						}}</span>
					</div>
					<strong>v{{ preview?.next_version || "1.0" }}</strong>
				</div>

				<div v-else class="template-publish__field">
					<label>{{ __("Version Bump") }}</label>
					<div class="template-publish__segments">
						<button
							type="button"
							class="btn btn-default btn-sm template-publish__segment"
							:class="{ 'is-active': form.version_bump === 'minor' }"
							@click="form.version_bump = 'minor'"
						>
							{{ __("Minor") }}
						</button>
						<button
							type="button"
							class="btn btn-default btn-sm template-publish__segment"
							:class="{ 'is-active': form.version_bump === 'major' }"
							@click="form.version_bump = 'major'"
						>
							{{ __("Major") }}
						</button>
					</div>
					<div class="template-publish__version">
						<span
							>{{ __("Current") }}:
							{{ preview?.current_version || __("None") }}</span
						>
						<span>{{ __("Next") }}: {{ preview?.next_version || "..." }}</span>
					</div>
				</div>

				<label class="template-publish__check">
					<input v-model="form.make_active" type="checkbox" />
					<span>{{ __("Make Active") }}</span>
				</label>

				<div class="template-publish__field">
					<label>{{ __("Effective From") }}</label>
					<input
						v-model="form.effective_from"
						type="datetime-local"
						class="form-control"
					/>
				</div>

				<div class="template-publish__field">
					<label>{{ __("Publish Notes") }}</label>
					<textarea
						v-model="form.notes"
						rows="4"
						class="form-control template-publish__notes"
					></textarea>
				</div>
			</div>

			<footer class="template-publish__footer">
				<button type="button" class="btn btn-default btn-sm" @click="emit('close')">
					{{ __("Cancel") }}
				</button>
				<button
					type="button"
					class="btn btn-primary btn-sm"
					:disabled="loading || publishing || !preview"
					@click="confirm"
				>
					{{ publishing ? __("Publishing...") : __("Publish Template") }}
				</button>
			</footer>
		</section>
	</div>
</template>

<script setup lang="ts">
import { computed, reactive, watch } from "vue";
import type { CrispyTemplatePublishPreview } from "../api/crispy";
import { __ } from "../utils/i18n";

const props = defineProps<{
	open: boolean;
	loading: boolean;
	publishing: boolean;
	preview: CrispyTemplatePublishPreview | null;
}>();

const emit = defineEmits<{
	close: [];
	"version-bump-change": [value: "minor" | "major"];
	confirm: [
		value: {
			version_bump: "minor" | "major";
			make_active: boolean;
			effective_from: string | null;
			notes: string | null;
		}
	];
}>();

const form = reactive({
	version_bump: "minor" as "minor" | "major",
	make_active: true,
	effective_from: "",
	notes: "",
});

const companyLabel = computed(() => {
	if (!props.preview?.company) return __("Global");
	return props.preview.company_abbr
		? `${props.preview.company_abbr} - ${props.preview.company}`
		: props.preview.company;
});

const brandingProfileLabel = computed(
	() => props.preview?.source_branding_profile || __("Custom presentation")
);

const isFirstTemplateVersion = computed(
	() => Boolean(props.preview) && !props.preview?.current_version
);

watch(
	() => props.open,
	(open) => {
		if (!open) return;
		form.version_bump = "minor";
		form.make_active = true;
		form.effective_from = "";
		form.notes = "";
		emit("version-bump-change", form.version_bump);
	}
);

watch(
	() => form.version_bump,
	(value) => {
		if (props.open) emit("version-bump-change", value);
	}
);

function confirm() {
	emit("confirm", {
		version_bump: form.version_bump,
		make_active: form.make_active,
		effective_from: form.effective_from || null,
		notes: form.notes || null,
	});
}
</script>

<style scoped>
.template-publish {
	position: fixed;
	inset: 0;
	z-index: 1040;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
}

.template-publish__backdrop {
	position: absolute;
	inset: 0;
	background: rgba(15, 23, 42, 0.42);
}

.template-publish__dialog {
	position: relative;
	width: min(720px, 100%);
	max-height: min(760px, calc(100vh - 48px));
	display: flex;
	flex-direction: column;
	background: #fff;
	border: 1px solid #d8dbe0;
	border-radius: 8px;
	box-shadow: 0 18px 48px rgba(15, 23, 42, 0.22);
	overflow: hidden;
}

.template-publish__header,
.template-publish__footer {
	display: flex;
	align-items: center;
	gap: 16px;
	padding: 18px 24px;
	border-bottom: 1px solid #e5e7eb;
}

.template-publish__header h3 {
	flex: 1;
	margin: 0;
	color: #1f272e;
	font-size: 20px;
	font-weight: 700;
	line-height: 1.35;
}

.template-publish__footer {
	justify-content: flex-end;
	border-top: 1px solid #e5e7eb;
	border-bottom: 0;
}

.template-publish__body {
	display: flex;
	flex-direction: column;
	gap: 18px;
	padding: 22px 24px 24px;
	overflow: auto;
}

.template-publish__grid {
	display: grid;
	grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
	gap: 16px;
}

.template-publish__field {
	display: flex;
	flex-direction: column;
	gap: 8px;
	min-width: 0;
}

.template-publish__field label {
	margin: 0;
	color: #4b5563;
	font-size: 13px;
	font-weight: 600;
	line-height: 1.3;
}

.template-publish__field :deep(.form-control) {
	min-height: 36px;
	border-color: #dce0e5;
	border-radius: 6px;
	background-color: #f8f8f8;
	color: #36414c;
	font-size: 14px;
	line-height: 1.4;
	box-shadow: none;
}

.template-publish__field input.form-control {
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

.template-publish__segments {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 12px;
}

.template-publish__first-version {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 18px;
	padding: 16px 18px;
	border: 1px solid #dce0e5;
	border-radius: 8px;
	background: #f8fafc;
}

.template-publish__first-label,
.template-publish__first-help {
	display: block;
}

.template-publish__first-label {
	color: #1f272e;
	font-size: 15px;
	font-weight: 700;
	line-height: 1.35;
}

.template-publish__first-help {
	margin-top: 3px;
	color: #64748b;
	font-size: 12px;
	line-height: 1.4;
}

.template-publish__first-version strong {
	flex: 0 0 auto;
	color: #1f5fbf;
	font-size: 24px;
	font-weight: 700;
	line-height: 1;
}

.template-publish__segment {
	height: 36px;
	border-color: #dce0e5;
	border-radius: 6px;
	font-size: 14px;
	font-weight: 500;
}

.template-publish__segment.is-active {
	border-color: #b8d3f8;
	background: #edf5ff;
	color: #1f5fbf;
}

.template-publish__version {
	display: flex;
	justify-content: space-between;
	gap: 16px;
	color: #64748b;
	font-size: 12px;
	line-height: 1.4;
}

.template-publish__check {
	display: inline-flex;
	align-items: center;
	gap: 10px;
	margin: 0;
	color: #36414c;
	font-size: 14px;
	font-weight: 600;
}

.template-publish__check input {
	margin: 0;
}

.template-publish__notes {
	min-height: 104px;
	resize: vertical;
}

.template-publish__footer .btn {
	min-height: 36px;
	padding-inline: 16px;
	font-size: 14px;
}

@media (max-width: 620px) {
	.template-publish {
		padding: 16px;
	}

	.template-publish__header,
	.template-publish__footer,
	.template-publish__body {
		padding-left: 16px;
		padding-right: 16px;
	}

	.template-publish__grid {
		grid-template-columns: minmax(0, 1fr);
	}

	.template-publish__first-version {
		align-items: flex-start;
		flex-direction: column;
	}
}
</style>
