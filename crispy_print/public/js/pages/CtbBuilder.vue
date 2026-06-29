<template>
	<div class="ctb-builder">
		<aside class="ctb-builder__sidebar">
			<section class="ctb-panel">
				<h3>{{ __("Page Settings") }}</h3>
				<label class="ctb-check">
					<input v-model="useAutoSizePreview" type="checkbox" />
					<span>{{ __("Auto-size preview page") }}</span>
				</label>
				<div class="ctb-preview-note">
					{{
						useAutoSizePreview
							? __(
									"Preview shrinks to content with 2.5cm margins. Use for compact self-sizing blocks, not tables, grids, or long text."
							  )
							: __(
									"Preview uses A4 with 2.5cm margins. Best for document blocks, tables, grids, and long text."
							  )
					}}
				</div>
				<div class="ctb-preview-note">
					{{ __("Click Refresh or Command/Ctrl-Enter to compile after every change.") }}
				</div>
				<div v-if="!useAutoSizePreview">
					<div class="ctb-grid ctb-grid--two">
						<label>
							<span>{{ __("Size") }}</span>
							<select v-model="preview.page_size" class="form-control">
								<option v-for="size in pageSizes" :key="size" :value="size">
									{{ size }}
								</option>
							</select>
						</label>
						<label>
							<span>{{ __("Orientation") }}</span>
							<select v-model="preview.orientation" class="form-control">
								<option value="portrait">{{ __("Portrait") }}</option>
								<option value="landscape">{{ __("Landscape") }}</option>
							</select>
						</label>
					</div>
					<div v-if="preview.page_size === 'Custom'" class="ctb-grid ctb-grid--two">
						<label>
							<span>{{ __("Width") }}</span>
							<input v-model="preview.page_width" class="form-control" type="text" />
						</label>
						<label>
							<span>{{ __("Height") }}</span>
							<input
								v-model="preview.page_height"
								class="form-control"
								type="text"
							/>
						</label>
					</div>
					<div class="ctb-grid ctb-grid--four">
						<label>
							<span>{{ __("Top") }}</span>
							<input v-model="preview.margin_top" class="form-control" type="text" />
						</label>
						<label>
							<span>{{ __("Bottom") }}</span>
							<input
								v-model="preview.margin_bottom"
								class="form-control"
								type="text"
							/>
						</label>
						<label>
							<span>{{ __("Left") }}</span>
							<input
								v-model="preview.margin_left"
								class="form-control"
								type="text"
							/>
						</label>
						<label>
							<span>{{ __("Right") }}</span>
							<input
								v-model="preview.margin_right"
								class="form-control"
								type="text"
							/>
						</label>
					</div>
				</div>
			</section>

			<section class="ctb-panel ctb-panel--code">
				<h3>{{ __("Typst Code") }}</h3>
				<textarea
					v-model="doc.typst_code"
					class="form-control ctb-code-editor"
					spellcheck="false"
				></textarea>
			</section>
		</aside>

		<main class="ctb-builder__preview">
			<div class="ctb-preview-toolbar">
				<div>
					<strong>{{ __("Preview") }}</strong>
					<span>{{ statusLabel }}</span>
				</div>
				<div class="ctb-preview-toolbar__actions">
					<button class="btn btn-default btn-sm" type="button" @click="load">
						{{ __("Reload") }}
					</button>
					<button
						class="btn btn-primary btn-sm"
						type="button"
						:title="__('Command/Ctrl-Enter')"
						@click="compilePreview"
					>
						{{ __("Refresh") }}
					</button>
				</div>
			</div>

			<div class="ctb-preview-scroll">
				<div v-if="status !== 'ready'" class="ctb-status" :class="`is-${status}`">
					<strong>{{ statusLabel }}</strong>
					<pre v-if="errorMessage">{{ errorMessage }}</pre>
				</div>
				<div v-else class="ctb-pages">
					<div
						v-for="(svg, index) in svgPages"
						:key="index"
						class="ctb-page"
						v-html="sanitizeSvg(svg)"
					></div>
				</div>
			</div>
		</main>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
	compileTypstSvg,
	getCrispyTypstBlock,
	saveCrispyTypstBlock,
	type CrispyTypstBlockDoc,
} from "../api/crispy";
import { resolveTypstPaper } from "../typst/page";
import { __ } from "../utils/i18n";
import { sanitizeSvg } from "../utils/safeSvg";

const props = defineProps<{
	blockName: string;
}>();

const pageSizes = ["A4", "Letter", "Legal", "A5", "Custom"];
const status = ref<"idle" | "loading" | "compiling" | "ready" | "error">("idle");
const errorMessage = ref("");
const svgPages = ref<string[]>([]);
const baselineTypstCode = ref("");

interface PreviewSettings {
	auto_size: number;
	page_size: string;
	orientation: "portrait" | "landscape";
	page_width: string;
	page_height: string;
	margin_top: string;
	margin_bottom: string;
	margin_left: string;
	margin_right: string;
}

const doc = reactive<CrispyTypstBlockDoc>({
	name: props.blockName,
	block_name: "",
	block_key: "",
	typst_code: "",
	version: "1.0",
	enabled: 1,
	category: "",
});

const preview = reactive<PreviewSettings>({
	auto_size: 0,
	page_size: "A4",
	orientation: "portrait",
	page_width: "auto",
	page_height: "auto",
	margin_top: "2.5cm",
	margin_bottom: "2.5cm",
	margin_left: "2.5cm",
	margin_right: "2.5cm",
});

const useAutoSizePreview = computed({
	get: () => Boolean(preview.auto_size),
	set: (value: boolean) => {
		preview.auto_size = value ? 1 : 0;
		if (value) applyDefaultPreviewPage();
	},
});

const dirty = computed(() => normalizeCode(doc.typst_code) !== baselineTypstCode.value);

const statusLabel = computed(() => {
	if (status.value === "loading") return __("Loading block");
	if (status.value === "compiling") return __("Compiling preview");
	if (status.value === "ready") return __("{0} page(s)", [svgPages.value.length]);
	if (status.value === "error") return __("Preview failed");
	return __("Ready");
});

watch(
	() => props.blockName,
	() => {
		void load();
	}
);

onMounted(() => {
	window.addEventListener("keydown", onPreviewShortcutKeydown);
	void load();
});

onBeforeUnmount(() => {
	window.removeEventListener("keydown", onPreviewShortcutKeydown);
});

function applyDefaultPreviewPage() {
	preview.page_width = "auto";
	preview.page_height = "auto";
	preview.margin_top = "2.5cm";
	preview.margin_bottom = "2.5cm";
	preview.margin_left = "2.5cm";
	preview.margin_right = "2.5cm";
}

async function load() {
	status.value = "loading";
	errorMessage.value = "";
	try {
		const loaded = await getCrispyTypstBlock(props.blockName);
		Object.assign(doc, normalizeLoadedBlock(loaded));
		baselineTypstCode.value = normalizeCode(doc.typst_code);
		await compilePreview();
	} catch (error) {
		status.value = "error";
		errorMessage.value = getErrorMessage(error);
	}
}

async function save() {
	await saveCrispyTypstBlock(props.blockName, {
		typst_code: doc.typst_code,
	});
	baselineTypstCode.value = normalizeCode(doc.typst_code);
	frappe.show_alert({ message: __("Crispy Typst Block saved"), indicator: "green" });
}

async function compilePreview() {
	status.value = "compiling";
	errorMessage.value = "";
	svgPages.value = [];
	try {
		const result = await compileTypstSvg({
			typst_source: previewSource(),
		});
		svgPages.value = result.svg_pages || [];
		status.value = "ready";
	} catch (error) {
		status.value = "error";
		errorMessage.value = getErrorMessage(error);
	}
}

function previewSource(): string {
	const code = String(doc.typst_code || "").trim() || "[]";
	return [
		renderPageSettings(),
		"#let doc = (",
		'  doctype: "Crispy Typst Block Preview",',
		`  name: "${escapeTypstString(doc.name || props.blockName)}",`,
		`  block_name: "${escapeTypstString(doc.block_name || "")}",`,
		`  block_key: "${escapeTypstString(doc.block_key || "")}",`,
		`  version: "${escapeTypstString(doc.version || "1.0")}",`,
		")",
		"",
		code,
	].join("\n");
}

function renderPageSettings(): string {
	const margins = `margin: (top: ${valueOr(preview.margin_top, "2.5cm")}, bottom: ${valueOr(
		preview.margin_bottom,
		"2.5cm"
	)}, left: ${valueOr(preview.margin_left, "2.5cm")}, right: ${valueOr(
		preview.margin_right,
		"2.5cm"
	)})`;
	if (useAutoSizePreview.value) {
		return `#set page(width: auto, height: auto, ${margins})`;
	}
	if (preview.page_size === "Custom") {
		return `#set page(width: ${valueOr(preview.page_width, "auto")}, height: ${valueOr(
			preview.page_height,
			"auto"
		)}, ${margins})`;
	}
	const paper = resolveTypstPaper(preview.page_size);
	const flipped = preview.orientation === "landscape" ? "true" : "false";
	return `#set page(paper: "${paper}", flipped: ${flipped}, ${margins})`;
}

function normalizeLoadedBlock(block: CrispyTypstBlockDoc): CrispyTypstBlockDoc {
	return { ...block };
}

function onPreviewShortcutKeydown(event: KeyboardEvent) {
	if ((!event.metaKey && !event.ctrlKey) || event.key !== "Enter") return;
	event.preventDefault();
	void compilePreview();
}

function normalizeCode(value: string | null | undefined): string {
	return String(value || "");
}

function valueOr(value: string | null | undefined, fallback: string): string {
	return String(value || "").trim() || fallback;
}

function escapeTypstString(value: string): string {
	return String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}

function getErrorMessage(error: unknown): string {
	if (error instanceof Error) return error.message;
	return String(error || __("Unknown error"));
}

defineExpose({ save, dirty });
</script>

<style scoped>
.ctb-builder {
	display: grid;
	grid-template-columns: minmax(380px, 42%) minmax(0, 1fr);
	height: calc(100vh - 108px);
	min-height: 620px;
	overflow: hidden;
	background: #f6f7f9;
	border-top: 1px solid #e5e7eb;
}

.ctb-builder__sidebar {
	display: flex;
	min-height: 0;
	overflow: auto;
	flex-direction: column;
	padding: 16px;
	border-right: 1px solid #e5e7eb;
	background: #fff;
}

.ctb-panel__heading,
.ctb-preview-toolbar {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}

.ctb-panel {
	padding-top: 14px;
}

.ctb-panel + .ctb-panel {
	margin-top: 14px;
	border-top: 1px solid #e5e7eb;
}

.ctb-panel h3 {
	margin: 0 0 10px;
	font-size: 13px;
	font-weight: 700;
}

.ctb-grid {
	display: grid;
	gap: 10px;
	margin-bottom: 10px;
}

.ctb-grid--two {
	grid-template-columns: repeat(2, minmax(0, 1fr));
}

.ctb-grid--four {
	grid-template-columns: repeat(4, minmax(0, 1fr));
}

.ctb-grid label span,
.ctb-check span {
	display: block;
	margin-bottom: 4px;
	color: #475569;
	font-size: 12px;
	font-weight: 600;
}

.ctb-check {
	display: flex;
	align-items: center;
	gap: 8px;
	margin-bottom: 10px;
}

.ctb-check span {
	margin: 0;
}

.ctb-preview-note {
	color: #475569;
	font-size: 12px;
	line-height: 1.45;
}

.ctb-panel--code {
	display: flex;
	min-height: 420px;
	flex: 1 1 auto;
	flex-direction: column;
}

.ctb-code-editor {
	min-height: 360px;
	flex: 1 1 auto;
	overflow: auto;
	resize: vertical;
	font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
	font-size: 12px;
	line-height: 1.5;
}

.ctb-builder__preview {
	display: grid;
	grid-template-rows: auto minmax(0, 1fr);
	min-width: 0;
	min-height: 0;
	overflow: hidden;
}

.ctb-preview-toolbar {
	padding: 10px 14px;
	border-bottom: 1px solid #e5e7eb;
	background: #fff;
}

.ctb-preview-toolbar span {
	display: block;
	color: #64748b;
	font-size: 12px;
}

.ctb-preview-toolbar__actions {
	display: flex;
	gap: 8px;
}

.ctb-preview-scroll {
	min-height: 0;
	overflow: auto;
	padding: 20px;
	background: #eef1f5;
}

.ctb-status {
	max-width: 720px;
	margin: 40px auto;
	padding: 16px;
	border: 1px solid #dbe3ef;
	border-radius: 8px;
	background: #fff;
	color: #334155;
}

.ctb-status.is-error {
	border-color: #fecaca;
	background: #fff7f7;
	color: #7f1d1d;
}

.ctb-status pre {
	overflow: auto;
	margin: 10px 0 0;
	white-space: pre-wrap;
	font-size: 12px;
}

.ctb-pages {
	display: grid;
	gap: 18px;
	justify-content: center;
}

.ctb-page {
	background: #fff;
	box-shadow: 0 8px 28px rgba(15, 23, 42, 0.16);
}

.ctb-page :deep(svg) {
	display: block;
	max-width: min(100%, 980px);
	height: auto;
}

@media (max-width: 900px) {
	.ctb-builder {
		grid-template-columns: 1fr;
		height: auto;
		overflow: visible;
	}

	.ctb-builder__sidebar {
		overflow: visible;
		border-right: 0;
		border-bottom: 1px solid #e5e7eb;
	}
}
</style>
