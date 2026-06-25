<template>
	<div
		id="crispy-print-root"
		class="crispy-layout"
		:class="{ 'crispy-layout--resizing': isResizing }"
		:style="layoutStyle"
	>
		<div
			class="pane-shell pane-shell--fields"
			:class="{ 'pane-shell--collapsed': effectiveFieldsCollapsed }"
		>
			<div v-if="effectiveFieldsCollapsed" class="pane-rail">
				<button
					type="button"
					class="pane-toggle pane-toggle--rail pane-toggle--fields pane-toggle--right"
					:title="__('Expand Fields')"
					:aria-label="__('Expand Fields')"
					:aria-expanded="false"
					@click="toggleFieldsPane"
				>
					<svg class="es-icon icon-md pane-toggle__placeholder" aria-hidden="true">
						<use href="#es-line-align-justify"></use>
					</svg>
					<span class="pane-toggle__icon">
						<svg class="es-icon icon-md" aria-hidden="true">
							<use href="#es-line-sidebar-collapse"></use>
						</svg>
					</span>
				</button>
				<span class="pane-rail__label">{{
					store.isReportMode.value ? __("Report Fields") : __("Fields")
				}}</span>
			</div>
			<FieldsPane
				v-else
				class="pane pane--fields"
				:fields="store.fields"
				:report-fields="store.reportBuilderFields"
				:is-report-mode="store.isReportMode"
				:loading="store.loading"
			>
				<template #header-actions>
					<button
						type="button"
						class="pane-toggle pane-toggle--inline pane-toggle--fields pane-toggle--left"
						:title="__('Collapse Fields')"
						:aria-label="__('Collapse Fields')"
						:aria-expanded="true"
						@click="toggleFieldsPane"
					>
						<svg class="es-icon icon-md pane-toggle__placeholder" aria-hidden="true">
							<use href="#es-line-align-justify"></use>
						</svg>
						<span class="pane-toggle__icon">
							<svg class="es-icon icon-md" aria-hidden="true">
								<use href="#es-line-sidebar-expand"></use>
							</svg>
						</span>
					</button>
				</template>
			</FieldsPane>
		</div>
		<LayoutPane v-if="!store.rawTypst.value" class="pane pane--layout" />
		<TypstCodePane v-else class="pane pane--layout" />
		<button
			type="button"
			class="middle-resize-handle"
			:title="__('Drag to resize builder and preview')"
			:aria-label="__('Resize builder and preview panes')"
			@pointerdown="onResizePointerDown"
			@dblclick="resetMiddleSplit"
		></button>
		<PreviewPane
			class="pane pane--preview"
			:preview-mode="previewMode"
			:zoom-mode="previewZoomMode"
			:zoom-percent="previewZoomPercent"
			@update:preview-mode="setPreviewMode"
			@update:zoom-mode="setPreviewZoomMode"
			@update:zoom-percent="setPreviewZoomPercent"
			@publish-template="openPublishDialog"
		/>
		<div
			class="pane-shell pane-shell--settings"
			:class="{ 'pane-shell--collapsed': effectiveSettingsCollapsed }"
		>
			<div v-if="effectiveSettingsCollapsed" class="pane-rail">
				<button
					type="button"
					class="pane-toggle pane-toggle--rail pane-toggle--settings pane-toggle--left"
					:title="__('Expand Presentation')"
					:aria-label="__('Expand Presentation')"
					:aria-expanded="false"
					@click="toggleSettingsPane"
				>
					<svg class="es-icon icon-md pane-toggle__placeholder" aria-hidden="true">
						<use href="#es-line-align-justify"></use>
					</svg>
					<span class="pane-toggle__icon">
						<svg class="es-icon icon-md" aria-hidden="true">
							<use href="#es-line-sidebar-expand"></use>
						</svg>
					</span>
				</button>
				<span class="pane-rail__label">{{ __("Settings") }}</span>
			</div>
			<SettingsPane
				v-else
				class="pane pane--settings"
				:presentation_settings="presentation_settings"
				:mark-dirty="store.markDirty"
			>
				<template #header-actions>
					<button
						type="button"
						class="pane-toggle pane-toggle--inline pane-toggle--settings pane-toggle--right"
						:title="__('Collapse Presentation')"
						:aria-label="__('Collapse Presentation')"
						:aria-expanded="true"
						@click="toggleSettingsPane"
					>
						<svg class="es-icon icon-md pane-toggle__placeholder" aria-hidden="true">
							<use href="#es-line-align-justify"></use>
						</svg>
						<span class="pane-toggle__icon">
							<svg class="es-icon icon-md" aria-hidden="true">
								<use href="#es-line-sidebar-collapse"></use>
							</svg>
						</span>
					</button>
				</template>
				<template #before-form>
					<SettingsSection
						v-model="isDiagnosticsExpanded"
						:title="__('Diagnostics')"
						content-border
					>
						<FormatHealthPanel :items="formatHealthItems" />
					</SettingsSection>
				</template>
			</SettingsPane>
		</div>
		<CrispyTemplatePublishDialog
			:open="publishDialogOpen"
			:loading="publishPreviewLoading"
			:publishing="publishSubmitting"
			:preview="publishPreview"
			@close="publishDialogOpen = false"
			@version-bump-change="loadPublishPreview"
			@confirm="publishTemplate"
		/>
	</div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import FieldsPane from "../components/FieldsPane.vue";
import LayoutPane from "../components/LayoutPane.vue";
import TypstCodePane from "../components/TypstCodePane.vue";
import PreviewPane from "../components/PreviewPane.vue";
import SettingsPane from "../components/SettingsPane.vue";
import SettingsSection from "../components/SettingsSection.vue";
import CrispyTemplatePublishDialog from "../components/CrispyTemplatePublishDialog.vue";
import FormatHealthPanel, { type FormatHealthItem } from "../components/FormatHealthPanel.vue";
import { useStore } from "../composables/useStore";
import type { CrispyTemplatePublishPreview } from "../api/crispy";
import { getCrispyBuilderFormatName } from "../utils/routes";
import { __ } from "../utils/i18n";

const store = useStore();
const presentation_settings = store.presentation_settings;
const STORAGE_KEY = "crispy-print:format-builder-layout:v1";
const MIN_SPLIT = 30;
const MAX_SPLIT = 70;

type PreviewMode = "normal" | "half" | "full";
type PreviewZoomMode = "fit" | "manual";
interface BuilderLayoutState {
	fieldsCollapsed: boolean;
	settingsCollapsed: boolean;
	middleSplitPercent: number;
	previewMode: PreviewMode;
}

const defaultLayoutState: BuilderLayoutState = {
	fieldsCollapsed: true,
	settingsCollapsed: true,
	middleSplitPercent: 50,
	previewMode: "normal",
};

const fieldsCollapsed = ref(defaultLayoutState.fieldsCollapsed);
const settingsCollapsed = ref(defaultLayoutState.settingsCollapsed);
const middleSplitPercent = ref(defaultLayoutState.middleSplitPercent);
const previewMode = ref<PreviewMode>(defaultLayoutState.previewMode);
const previewZoomMode = ref<PreviewZoomMode>("fit");
const previewZoomPercent = ref(100);
const isResizing = ref(false);
const publishDialogOpen = ref(false);
const publishPreviewLoading = ref(false);
const publishSubmitting = ref(false);
const publishPreview = ref<CrispyTemplatePublishPreview | null>(null);
const isDiagnosticsExpanded = ref(false);
let resizeCleanup: (() => void) | null = null;

const effectiveFieldsCollapsed = computed(
	() => fieldsCollapsed.value || previewMode.value !== "normal"
);
const effectiveSettingsCollapsed = computed(
	() => settingsCollapsed.value || previewMode.value !== "normal"
);
const effectiveMiddleSplit = computed(() => {
	if (previewMode.value === "full") return 30;
	if (previewMode.value === "half") return 40;
	return middleSplitPercent.value;
});

const layoutStyle = computed(() => {
	const fieldsWidth = effectiveFieldsCollapsed.value ? "44px" : "280px";
	const settingsWidth = effectiveSettingsCollapsed.value ? "44px" : "280px";
	const split = effectiveMiddleSplit.value;
	const layoutWidth = `minmax(320px, ${split}fr)`;
	const previewWidth = `minmax(360px, ${100 - split}fr)`;

	return {
		gridTemplateColumns: `${fieldsWidth} ${layoutWidth} 10px ${previewWidth} ${settingsWidth}`,
	};
});

const allowedPdfStandards = new Set(["PDF/A-2u", "PDF/A-3u", "PDF/A-4", "PDF 1.7", "PDF 2.0"]);
const formatHealthItems = computed<FormatHealthItem[]>(() => {
	const items: FormatHealthItem[] = [];
	const format = store.crispyFormat.value;
	const settings = store.presentation_settings.value;
	const pdfStandard = format?.pdf_standard || "PDF/A-2u";

	if (!format) return items;
	if (!format.name) {
		items.push({ level: "error", message: __("Format name is missing.") });
	}
	if (store.formatType.value === "DocType" && !format.doc_type) {
		items.push({ level: "error", message: __("DocType formats need a target DocType.") });
	}
	if (!settings?.branding?.company && !format.company) {
		items.push({
			level: "warning",
			message: __(
				"Set a company so company-scoped formats, templates, and assets resolve predictably."
			),
		});
	}
	if (store.formatType.value === "DocType" && !format.is_default) {
		items.push({
			level: "warning",
			message: __(
				"This format is not marked as the default, so the Typst button may not use it automatically."
			),
		});
	}
	if (!allowedPdfStandards.has(pdfStandard)) {
		items.push({
			level: "error",
			message: __("Unsupported PDF standard: {0}", [pdfStandard]),
		});
	}
	if (settings?.source !== "branding_profile" && !settings?.branding?.profile) {
		items.push({
			level: "info",
			message: __(
				"No Branding Profile is attached; this format uses custom presentation settings."
			),
		});
	}
	if (store.rawTypst.value && !store.typstCode.value.trim()) {
		items.push({ level: "error", message: __("Raw Typst mode has no Typst source.") });
	}
	if (store.isReportMode.value && !store.typstCode.value.trim()) {
		items.push({
			level: "warning",
			message: __("Report format has no generated Typst source yet."),
		});
	}
	if (store.dirty.value) {
		items.push({
			level: "info",
			message: __(
				"Unsaved changes are present; published templates and previews from saved records may be stale."
			),
		});
	}
	if (findUnresolvedTypstBlocks(store.layout.value).length) {
		items.push({
			level: "warning",
			message: __(
				"One or more Typst Block fields are not resolved for the current company/DocType."
			),
		});
	}
	return items;
});

onMounted(async () => {
	loadLayoutState();
	const formatName = getCrispyBuilderFormatName();
	if (formatName) await store.fetch(formatName);
	window.addEventListener("keydown", handleHistoryShortcuts);
});

onBeforeUnmount(() => {
	window.removeEventListener("keydown", handleHistoryShortcuts);
	resizeCleanup?.();
});

watch([fieldsCollapsed, settingsCollapsed, middleSplitPercent, previewMode], saveLayoutState);

function handleHistoryShortcuts(event: KeyboardEvent) {
	if (!(event.ctrlKey || event.metaKey) || event.altKey) return;
	const key = event.key.toLowerCase();
	if (key === "z" && !event.shiftKey) {
		event.preventDefault();
		store.undo();
		return;
	}
	if (key === "y" || (key === "z" && event.shiftKey)) {
		event.preventDefault();
		store.redo();
	}
}

function clamp(value: number, min: number, max: number) {
	return Math.min(max, Math.max(min, value));
}

function isPreviewMode(value: unknown): value is PreviewMode {
	return value === "normal" || value === "half" || value === "full";
}

function findUnresolvedTypstBlocks(layout: any): any[] {
	const unresolved: any[] = [];
	(layout?.sections || []).forEach((section: any) => {
		(section?.columns || []).forEach((column: any) => {
			(column?.fields || []).forEach((field: any) => {
				if (
					field?.fieldtype === "Crispy Typst Block" &&
					field?.crispy_typst_block &&
					!field?.crispy_typst_block_code
				) {
					unresolved.push(field);
				}
			});
		});
	});
	return unresolved;
}

function loadLayoutState() {
	if (typeof window === "undefined") return;
	try {
		const raw = window.localStorage.getItem(STORAGE_KEY);
		if (!raw) return;
		const parsed = JSON.parse(raw) as Partial<BuilderLayoutState>;
		fieldsCollapsed.value =
			typeof parsed.fieldsCollapsed === "boolean"
				? parsed.fieldsCollapsed
				: defaultLayoutState.fieldsCollapsed;
		settingsCollapsed.value =
			typeof parsed.settingsCollapsed === "boolean"
				? parsed.settingsCollapsed
				: defaultLayoutState.settingsCollapsed;
		middleSplitPercent.value = Number.isFinite(parsed.middleSplitPercent)
			? clamp(Number(parsed.middleSplitPercent), MIN_SPLIT, MAX_SPLIT)
			: defaultLayoutState.middleSplitPercent;
		previewMode.value = isPreviewMode(parsed.previewMode)
			? parsed.previewMode
			: defaultLayoutState.previewMode;
	} catch {
		fieldsCollapsed.value = defaultLayoutState.fieldsCollapsed;
		settingsCollapsed.value = defaultLayoutState.settingsCollapsed;
		middleSplitPercent.value = defaultLayoutState.middleSplitPercent;
		previewMode.value = defaultLayoutState.previewMode;
	}
	previewZoomMode.value = "fit";
	previewZoomPercent.value = 100;
}

function saveLayoutState() {
	if (typeof window === "undefined") return;
	try {
		const payload: BuilderLayoutState = {
			fieldsCollapsed: fieldsCollapsed.value,
			settingsCollapsed: settingsCollapsed.value,
			middleSplitPercent: middleSplitPercent.value,
			previewMode: previewMode.value,
		};
		window.localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
	} catch {
		// Layout persistence is best-effort; editing should continue without storage.
	}
}

function toggleFieldsPane() {
	fieldsCollapsed.value = !effectiveFieldsCollapsed.value;
	if (previewMode.value !== "normal") previewMode.value = "normal";
}

function toggleSettingsPane() {
	settingsCollapsed.value = !effectiveSettingsCollapsed.value;
	if (previewMode.value !== "normal") previewMode.value = "normal";
}

function setPreviewMode(value: PreviewMode) {
	previewMode.value = value;
}

function setPreviewZoomMode(value: PreviewZoomMode) {
	previewZoomMode.value = value;
}

function setPreviewZoomPercent(value: number) {
	previewZoomPercent.value = clamp(value, 25, 200);
}

async function openPublishDialog() {
	publishDialogOpen.value = true;
	await loadPublishPreview("minor");
}

async function loadPublishPreview(versionBump: "minor" | "major") {
	if (!publishDialogOpen.value) return;
	publishPreviewLoading.value = true;
	try {
		publishPreview.value = await store.getTemplatePublishPreview(versionBump);
	} finally {
		publishPreviewLoading.value = false;
	}
}

async function publishTemplate(args: {
	version_bump: "minor" | "major";
	make_active: boolean;
	effective_from?: string | null;
	notes?: string | null;
}) {
	publishSubmitting.value = true;
	try {
		await store.publishTemplate(args);
		publishDialogOpen.value = false;
		publishPreview.value = null;
	} finally {
		publishSubmitting.value = false;
	}
}

function resetMiddleSplit() {
	middleSplitPercent.value = defaultLayoutState.middleSplitPercent;
	if (previewMode.value !== "normal") previewMode.value = "normal";
}

function onResizePointerDown(event: PointerEvent) {
	const root = (event.currentTarget as HTMLElement | null)?.closest("#crispy-print-root");
	if (!root) return;
	event.preventDefault();
	previewMode.value = "normal";
	isResizing.value = true;
	const middlePanes = root.querySelectorAll<HTMLElement>(".pane--layout, .pane--preview");
	const layoutPane = middlePanes[0];
	const previewPane = middlePanes[1];
	const layoutRect = layoutPane?.getBoundingClientRect();
	const previewRect = previewPane?.getBoundingClientRect();
	if (!layoutRect || !previewRect) {
		isResizing.value = false;
		return;
	}
	const start = layoutRect.left;
	const total = previewRect.right - layoutRect.left;
	if (total <= 0) {
		isResizing.value = false;
		return;
	}

	const onMove = (moveEvent: PointerEvent) => {
		const next = ((moveEvent.clientX - start) / total) * 100;
		middleSplitPercent.value = clamp(next, MIN_SPLIT, MAX_SPLIT);
	};
	const onUp = () => {
		isResizing.value = false;
		resizeCleanup?.();
		resizeCleanup = null;
	};
	resizeCleanup?.();
	window.addEventListener("pointermove", onMove);
	window.addEventListener("pointerup", onUp, { once: true });
	resizeCleanup = () => {
		window.removeEventListener("pointermove", onMove);
		window.removeEventListener("pointerup", onUp);
	};
}

// Watch for route changes
if (typeof frappe !== "undefined" && frappe?.router?.on) {
	frappe.router.on("change", async () => {
		const formatName = getCrispyBuilderFormatName();
		if (formatName) await store.fetch(formatName);
	});
}
</script>

<style scoped>
/* CrispyPFB.vue */
.crispy-layout {
	display: grid;
	gap: 12px;
	background: #fff;
	padding: 16px;
	align-items: stretch;
	min-height: 0;
	height: calc(100vh - 60px);
}

.crispy-layout--resizing {
	user-select: none;
	cursor: col-resize;
}

.pane-shell {
	position: relative;
	min-width: 0;
	min-height: 0;
	display: flex;
}

.pane-shell--collapsed {
	border: 1px solid #e2e8f0;
	background: #f8fafc;
	overflow: hidden;
}

.pane {
	min-height: 0;
	background: #fff;
	min-width: 0;
}

.pane--fields {
	width: 100%;
}

.pane--layout {
	grid-column-start: 2;
	overflow: hidden;
}

.pane--preview {
	grid-column-start: 4;
	overflow: hidden;
}

.pane--settings {
	width: 100%;
}

.pane-toggle {
	width: 28px;
	height: 28px;
	display: inline-flex;
	align-items: center;
	justify-content: center;
	border: 1px solid transparent;
	background: transparent;
	color: #4b5563;
	border-radius: 6px;
	line-height: 1;
	cursor: pointer;
	box-shadow: none;
	transition: background-color 0.15s ease, border-color 0.15s ease, color 0.15s ease;
}

.pane-toggle--inline {
	position: static;
	flex: 0 0 auto;
	margin-left: 2px;
}

.pane-toggle--settings.pane-toggle--inline {
	margin-left: 0;
	margin-right: 2px;
}

.pane-toggle:hover {
	background: transparent;
	border-color: transparent;
	color: #0f172a;
}

.pane-toggle:focus-visible {
	outline: 2px solid #2563eb;
	outline-offset: 2px;
}

.pane-toggle__icon {
	display: none;
	align-items: center;
	justify-content: center;
}

.pane-toggle .es-icon {
	flex: 0 0 auto;
	--icon-stroke: currentColor;
	--icon-fill: transparent;
}

.pane-toggle:hover .pane-toggle__placeholder,
.pane-toggle:focus-visible .pane-toggle__placeholder {
	display: none;
}

.pane-toggle:hover .pane-toggle__icon,
.pane-toggle:focus-visible .pane-toggle__icon {
	display: inline-flex;
}

.pane-rail {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: flex-start;
	gap: 14px;
	padding: 10px 0;
	color: #475569;
	font-size: 12px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.04em;
}

.pane-rail__label {
	display: inline-flex;
	writing-mode: vertical-rl;
	transform: rotate(180deg);
	line-height: 1;
	margin-top: 2px;
}

.pane-toggle--rail {
	position: static;
	flex: 0 0 auto;
}

.middle-resize-handle {
	grid-column-start: 3;
	border: 0;
	padding: 0;
	width: 10px;
	min-width: 10px;
	height: 100%;
	background: transparent;
	cursor: col-resize;
	position: relative;
}

.middle-resize-handle::before {
	content: "";
	position: absolute;
	top: 8px;
	bottom: 8px;
	left: 4px;
	width: 2px;
	border-radius: 9999px;
	background: #cbd5e1;
}

.middle-resize-handle:hover::before,
.middle-resize-handle:focus-visible::before,
.crispy-layout--resizing .middle-resize-handle::before {
	background: #64748b;
}

.middle-resize-handle:focus-visible {
	outline: 2px solid #2563eb;
	outline-offset: 2px;
}
</style>
