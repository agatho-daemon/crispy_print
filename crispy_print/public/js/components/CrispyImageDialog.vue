<template>
	<div class="crispy-image-dialog">
		<div class="crispy-image-dialog__card">
			<div class="crispy-image-dialog__header">
				<div>
					<h3 class="crispy-image-dialog__title">{{ __("Choose image") }}</h3>
					<p class="crispy-image-dialog__subtitle">
						{{ __("Private files only. Stored as filename.") }}
					</p>
				</div>
				<button type="button" class="crispy-image-dialog__close" @click="$emit('close')">
					&#x2715;
				</button>
			</div>

			<div class="crispy-image-dialog__toolbar">
				<input
					v-model="query"
					type="search"
					class="form-control crispy-image-dialog__search"
					:placeholder="__('Search images...')"
					@keydown.enter.prevent="refresh"
				/>
				<button type="button" class="btn btn-default btn-sm" @click="refresh">
					{{ __("Refresh") }}
				</button>
				<button type="button" class="btn btn-primary btn-sm" @click="uploadImage">
					{{ __("Upload") }}
				</button>
			</div>

			<div class="crispy-image-dialog__settings">
				<div class="crispy-image-dialog__field crispy-image-dialog__field--wide">
					<label class="crispy-image-dialog__label">{{ __("Selected image") }}</label>
					<input
						v-model="selectedFilename"
						type="text"
						class="form-control"
						:placeholder="__('filename.svg')"
					/>
				</div>
				<div class="crispy-image-dialog__field">
					<label class="crispy-image-dialog__label">{{ __("Width") }}</label>
					<input
						v-model="settings.width"
						type="text"
						class="form-control"
						:placeholder="__('100%')"
					/>
				</div>
				<div class="crispy-image-dialog__field">
					<label class="crispy-image-dialog__label">{{ __("Height") }}</label>
					<input
						v-model="settings.height"
						type="text"
						class="form-control"
						:placeholder="__('auto')"
					/>
				</div>
				<div class="crispy-image-dialog__field">
					<label class="crispy-image-dialog__label">{{ __("Fit") }}</label>
					<select v-model="settings.fit" class="form-control">
						<option value="">{{ __("Auto") }}</option>
						<option value="contain">{{ __("Contain") }}</option>
						<option value="cover">{{ __("Cover") }}</option>
						<option value="stretch">{{ __("Stretch") }}</option>
					</select>
				</div>
			</div>

			<div class="crispy-image-dialog__body">
				<div v-if="loading" class="crispy-image-dialog__state">
					{{ __("Loading images...") }}
				</div>
				<div v-else-if="!filteredImages.length" class="crispy-image-dialog__state">
					{{ __("No private images found.") }}
				</div>
				<template v-else>
					<button
						v-for="image in filteredImages"
						:key="image.filename"
						type="button"
						class="crispy-image-dialog__item"
						:class="{
							'crispy-image-dialog__item--selected':
								image.filename === selectedFilename,
						}"
						@click="selectImage(image)"
					>
						<span class="crispy-image-dialog__filename">{{ image.filename }}</span>
						<span class="crispy-image-dialog__meta">{{
							image.file_name || image.filename
						}}</span>
					</button>
				</template>
			</div>

			<div class="crispy-image-dialog__footer">
				<button type="button" class="btn btn-default btn-sm" @click="$emit('close')">
					{{ __("Close") }}
				</button>
				<button
					type="button"
					class="btn btn-primary btn-sm"
					:disabled="!selectedFilename"
					@click="applySelection"
				>
					{{ __("Apply") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { getPrivateImageFiles, type CrispyPrivateImageOption } from "../api/crispy";
import { __ } from "../utils/i18n";

export interface CrispyImageSettings {
	filename: string;
	width: string;
	height: string;
	fit: string;
}

const props = defineProps<{
	selectedFilename?: string | null;
	settings?: Partial<CrispyImageSettings> | null;
}>();

const emit = defineEmits<{
	(event: "select", settings: CrispyImageSettings): void;
	(event: "close"): void;
}>();

const query = ref("");
const images = ref<CrispyPrivateImageOption[]>([]);
const loading = ref(false);
const selectedFilename = ref(props.selectedFilename || "");
const settings = ref<CrispyImageSettings>(
	normalizeSettings(props.settings, selectedFilename.value)
);

const filteredImages = computed(() => {
	const search = query.value.trim().toLowerCase();
	if (!search) return images.value;
	return images.value.filter((image) => {
		return [image.filename, image.file_name].some((value) =>
			String(value || "")
				.toLowerCase()
				.includes(search)
		);
	});
});

watch(
	() => props.selectedFilename,
	(value) => {
		selectedFilename.value = value || "";
		settings.value.filename = selectedFilename.value;
	}
);

watch(
	() => props.settings,
	(value) => {
		settings.value = normalizeSettings(value, selectedFilename.value);
	},
	{ deep: true }
);

watch(selectedFilename, (value) => {
	settings.value.filename = value || "";
});

function normalizeSettings(
	value: Partial<CrispyImageSettings> | null | undefined,
	filename: string
): CrispyImageSettings {
	return {
		filename: value?.filename || filename || "",
		width: value?.width ?? "100%",
		height: value?.height ?? "",
		fit: value?.fit ?? "",
	};
}

async function refresh() {
	loading.value = true;
	try {
		images.value = await getPrivateImageFiles({
			query: query.value || null,
			limit: 200,
		});
	} catch {
		images.value = [];
		if (typeof frappe !== "undefined") {
			frappe.show_alert({
				message: __("Failed to load private images"),
				indicator: "red",
			});
		}
	} finally {
		loading.value = false;
	}
}

function selectImage(image: CrispyPrivateImageOption) {
	selectedFilename.value = image.filename;
}

function applySelection() {
	if (!selectedFilename.value) return;
	emit("select", {
		...settings.value,
		filename: selectedFilename.value,
	});
}

function filenameFromFile(file: any): string {
	const fileUrl = String(file?.file_url || "");
	if (fileUrl.startsWith("/private/files/")) {
		return fileUrl.slice("/private/files/".length).split("/").pop() || "";
	}
	return (
		String(file?.file_name || "")
			.split("/")
			.pop() || ""
	);
}

function uploadImage() {
	if (typeof frappe === "undefined" || !frappe.ui?.FileUploader) return;
	const uploader = new frappe.ui.FileUploader({
		allow_multiple: false,
		restrictions: {
			allowed_file_types: [
				"image/png",
				"image/jpeg",
				"image/svg+xml",
				"image/gif",
				"image/webp",
				"image/bmp",
				"image/tiff",
				"image/avif",
			],
		},
		on_success: async (file: any) => {
			const filename = filenameFromFile(file);
			await refresh();
			if (filename) {
				selectedFilename.value = filename;
			}
		},
	});
	uploader.show?.();
	if (uploader.dialog?.set_value) {
		uploader.dialog.set_value("is_private", 1);
	}
}

onMounted(() => {
	refresh();
});
</script>

<style scoped>
.crispy-image-dialog {
	position: absolute;
	inset: 0;
	z-index: 50;
	display: flex;
	align-items: center;
	justify-content: center;
	background: rgba(15, 23, 42, 0.5);
	padding: 16px;
}

.crispy-image-dialog__card {
	width: min(720px, 100%);
	max-height: 70vh;
	display: flex;
	flex-direction: column;
	overflow: hidden;
	background: #fff;
	border-radius: 8px;
	box-shadow: 0 25px 50px rgba(15, 23, 42, 0.25), 0 10px 20px rgba(15, 23, 42, 0.18);
}

.crispy-image-dialog__header,
.crispy-image-dialog__toolbar,
.crispy-image-dialog__footer {
	display: flex;
	align-items: center;
	gap: 8px;
	padding: 12px 16px;
	border-bottom: 1px solid #e2e8f0;
}

.crispy-image-dialog__settings {
	display: grid;
	grid-template-columns: minmax(180px, 2fr) repeat(3, minmax(90px, 1fr));
	gap: 10px;
	padding: 12px 16px;
	border-bottom: 1px solid #e2e8f0;
	background: #f8fafc;
}

.crispy-image-dialog__field {
	display: flex;
	flex-direction: column;
	gap: 4px;
	min-width: 0;
}

.crispy-image-dialog__field--wide {
	grid-column: span 1;
}

.crispy-image-dialog__label {
	margin: 0;
	font-size: 11px;
	font-weight: 600;
	color: #475569;
}

.crispy-image-dialog__header {
	justify-content: space-between;
	align-items: flex-start;
}

.crispy-image-dialog__footer {
	justify-content: flex-end;
	border-top: 1px solid #e2e8f0;
	border-bottom: none;
}

.crispy-image-dialog__title {
	margin: 0;
	font-size: 16px;
	font-weight: 600;
}

.crispy-image-dialog__subtitle {
	margin: 4px 0 0;
	font-size: 12px;
	color: #64748b;
}

.crispy-image-dialog__close {
	border: none;
	background: transparent;
	color: #94a3b8;
	cursor: pointer;
	padding: 6px;
}

.crispy-image-dialog__search {
	flex: 1;
}

.crispy-image-dialog__body {
	flex: 1;
	min-height: 180px;
	overflow: auto;
	padding: 8px;
}

.crispy-image-dialog__state {
	padding: 24px;
	text-align: center;
	color: #64748b;
}

.crispy-image-dialog__item {
	width: 100%;
	border: 1px solid #e2e8f0;
	background: #fff;
	border-radius: 6px;
	padding: 10px 12px;
	margin-bottom: 8px;
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	text-align: start;
	cursor: pointer;
}

.crispy-image-dialog__item--selected {
	border-color: #4f46e5;
	background: #eef2ff;
}

.crispy-image-dialog__filename {
	font-weight: 600;
	color: #0f172a;
}

.crispy-image-dialog__meta {
	font-size: 12px;
	color: #64748b;
	overflow: hidden;
	text-overflow: ellipsis;
	white-space: nowrap;
}

@media (max-width: 720px) {
	.crispy-image-dialog__settings {
		grid-template-columns: 1fr 1fr;
	}

	.crispy-image-dialog__field--wide {
		grid-column: 1 / -1;
	}
}
</style>
