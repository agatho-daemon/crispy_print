<template>
	<div ref="previewPaneEl" class="preview-pane">
		<!-- Optional controls/menu (used by builder) -->
		<slot name="menu"></slot>

		<div class="preview-pane__body">
			<div class="preview-zoom-toolbar" role="group" :aria-label="__('Preview zoom')">
				<button
					type="button"
					class="btn btn-default btn-xs"
					:class="{ 'is-active': zoomMode === 'fit' }"
					:aria-pressed="zoomMode === 'fit'"
					@click.stop.prevent="fitPreview"
				>
					{{ __("Fit") }}
				</button>
				<button
					type="button"
					class="btn btn-default btn-xs"
					:class="{ 'is-active': zoomMode === 'manual' && zoomPercent === 100 }"
					:aria-pressed="zoomMode === 'manual' && zoomPercent === 100"
					@click.stop.prevent="setZoom(100)"
				>
					{{ __("100%") }}
				</button>
				<button
					type="button"
					class="btn btn-default btn-xs preview-zoom-toolbar__icon"
					:title="__('Zoom out')"
					:aria-label="__('Zoom out')"
					@click.stop.prevent="changeZoom(-10)"
				>
					-
				</button>
				<input
					v-if="isEditingZoom"
					ref="zoomInputEl"
					v-model="zoomDraft"
					type="text"
					class="preview-zoom-toolbar__input"
					inputmode="numeric"
					:aria-label="__('Zoom percentage')"
					@keydown.enter.stop.prevent="applyZoomDraft"
					@keydown.escape.stop.prevent="cancelZoomEdit"
					@blur="applyZoomDraft"
				/>
				<button
					v-else
					type="button"
					class="preview-zoom-toolbar__value"
					:title="__('Edit zoom percentage')"
					:aria-label="__('Edit zoom percentage')"
					@click.stop.prevent="startZoomEdit"
				>
					{{ displayZoom }}
				</button>
				<button
					type="button"
					class="btn btn-default btn-xs preview-zoom-toolbar__icon"
					:title="__('Zoom in')"
					:aria-label="__('Zoom in')"
					@click.stop.prevent="changeZoom(10)"
				>
					+
				</button>
			</div>
			<div
				ref="viewportEl"
				class="preview-viewport"
				:class="{
					'preview-viewport--pannable': canPan,
					'preview-viewport--panning': isPanning,
				}"
				@pointerdown="onPanPointerDown"
			>
				<div class="preview-stage-sizer" :style="stageSizerStyle">
					<div ref="stageEl" class="preview-stage" :style="stageStyle">
						<div id="typst-svg-container">
							<div id="typst-preview-placeholder" class="preview-placeholder">
								{{ __("Preview output will render here.") }}
							</div>
						</div>
					</div>
				</div>
			</div>
			<div v-if="errorPanel" class="preview-error">
				<div class="preview-error__header">
					<span class="preview-error__title">{{ __("Typst Error") }}</span>
					<button class="preview-error__copy" type="button" @click="copyError">
						{{ __("Copy") }}
					</button>
				</div>
				<pre class="preview-error__body">{{ errorPanel }}</pre>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { setupWorker } from "../typst/setupWorker";
import { CrispyPreviewEvents, type CrispyPreviewStatusDetail } from "../utils/events";
import { sanitizeSvg } from "../utils/safeSvg";
import { getLogger } from "../logger";
import { __ } from "../utils/i18n";

interface Props {
	formatName: string | null;
	layout: any;
	docHeader: string;
	docFooter: string;
	typstPreamble: string;
	typstCode?: string;
	pdfStandard?: string | null;
	rawTypst?: boolean;
	qrEnabled: boolean;
	presentation_settings: any;
	letterhead: any;
	docType: string | null;
	docName?: string | null;
	changeKey?: number;
	watchDataChanges?: boolean;
	zoomMode?: "fit" | "manual";
	zoomPercent?: number;
}

const props = withDefaults(defineProps<Props>(), {
	zoomMode: "fit",
	zoomPercent: 100,
});
const emit = defineEmits<{
	(event: "update:zoomMode", value: "fit" | "manual"): void;
	(event: "update:zoomPercent", value: number): void;
}>();
const logger = getLogger({ component: "PreviewRenderer" });

const previewPaneEl = ref<HTMLElement | null>(null);
const viewportEl = ref<HTMLElement | null>(null);
const stageEl = ref<HTMLElement | null>(null);
const zoomInputEl = ref<HTMLInputElement | null>(null);
const errorPanel = ref<string | null>(null);
const panX = ref(0);
const panY = ref(0);
const isPanning = ref(false);
const viewportWidth = ref(0);
const stageHeight = ref(0);
const isEditingZoom = ref(false);
const zoomDraft = ref("");
let teardown: (() => void) | null = null;
let panCleanup: (() => void) | null = null;
let contentObserver: MutationObserver | null = null;
let stageResizeObserver: ResizeObserver | null = null;
let stageMetricsFrame: number | null = null;
let stageMetricsReadFrame: number | null = null;

const zoomPercent = computed(() => clamp(Number(props.zoomPercent) || 100, 25, 200));
const zoomMode = computed(() => props.zoomMode);
const pageWidthPx = computed(() => getPageWidthPx(props.presentation_settings));
const fitScale = computed(() => {
	if (!viewportWidth.value || !pageWidthPx.value) return 1;
	return viewportWidth.value / pageWidthPx.value;
});
const zoomScale = computed(() =>
	zoomMode.value === "fit" ? fitScale.value : zoomPercent.value / 100
);
const canPan = computed(() => zoomMode.value === "manual");
const displayZoom = computed(() => `${Math.round(zoomScale.value * 100)}%`);
const stageStyle = computed(() => ({
	width: `${pageWidthPx.value}px`,
	"--preview-page-width": `${pageWidthPx.value}px`,
	transform: `translate(${panX.value}px, ${panY.value}px) scale(${zoomScale.value})`,
}));
const stageSizerStyle = computed(() => {
	if (!pageWidthPx.value || !stageHeight.value) return {};
	return {
		width: `${pageWidthPx.value * zoomScale.value}px`,
		height: `${stageHeight.value * zoomScale.value}px`,
	};
});

function createAdapter() {
	const enableDataWatch = props.watchDataChanges !== false;
	return {
		getLayout: () => props.layout,
		getDocHeader: () => props.docHeader,
		getDocFooter: () => props.docFooter,
		getTypstPreamble: () => props.typstPreamble,
		getTypstCode: () => props.typstCode || "",
		getPdfStandard: () => props.pdfStandard || "PDF/A-2u",
		getRawTypst: () => Boolean(props.rawTypst),
		getQrEnabled: () => props.qrEnabled,
		getLetterhead: () => props.letterhead,
		getDoctype: () => props.docType,
		getDocname: () => props.docName,
		get_presentation_settings: () => props.presentation_settings,
		hookDataChanges: enableDataWatch
			? (callback: () => void) => {
					// Prefer explicit invalidation via changeKey to avoid expensive deep watches.
					if (props.changeKey !== undefined) {
						const stop = watch(
							() => [
								props.changeKey,
								props.presentation_settings,
								props.letterhead,
								props.qrEnabled,
							],
							(_newVal, oldVal) => {
								if (oldVal !== undefined) {
									callback();
								}
							}
						);
						return () => stop();
					}

					// Fallback for callers that don't provide changeKey.
					const stop = watch(
						() => [
							props.layout,
							props.presentation_settings,
							props.letterhead,
							props.docHeader,
							props.docFooter,
							props.typstPreamble,
							props.typstCode,
							props.rawTypst,
						],
						() => callback(),
						{ deep: true }
					);
					return () => stop();
			  }
			: undefined,
		hookDoctypeChanges: (callback: (doctype: string | null | undefined) => void) => {
			const stop = watch(
				() => props.docType,
				(next) => callback(next),
				{ immediate: true }
			);
			return () => stop();
		},
	};
}

watch(
	() => [props.formatName, previewPaneEl.value] as const,
	([formatName, element]) => {
		if (!formatName || !element) return;

		teardown?.();
		teardown = setupWorker(formatName, element, createAdapter());
	},
	{ immediate: true }
);

watch(
	() =>
		[
			props.presentation_settings?.page?.size,
			props.presentation_settings?.page?.orientation,
		] as const,
	() => scheduleStageMetricsUpdate()
);

function onPreviewStatus(event: Event) {
	const detail = (event as CustomEvent<CrispyPreviewStatusDetail>).detail;
	if (!detail) return;
	if (detail.status === "error") {
		errorPanel.value = detail.message || "Typst compilation failed.";
	} else if (detail.status === "ready" || detail.status === "compiling") {
		errorPanel.value = null;
	}
}

function clamp(value: number, min: number, max: number) {
	return Math.min(max, Math.max(min, value));
}

function getPageWidthPx(presentation_settings: any): number {
	const page_size = String(presentation_settings?.page?.size || "A4").toLowerCase();
	const orientation = String(
		presentation_settings?.page?.orientation || "portrait"
	).toLowerCase();
	const sizes: Record<string, { width: number; height: number; unit: "mm" | "in" }> = {
		a3: { width: 297, height: 420, unit: "mm" },
		a4: { width: 210, height: 297, unit: "mm" },
		a5: { width: 148, height: 210, unit: "mm" },
		letter: { width: 8.5, height: 11, unit: "in" },
		legal: { width: 8.5, height: 14, unit: "in" },
		tabloid: { width: 11, height: 17, unit: "in" },
		executive: { width: 7.25, height: 10.5, unit: "in" },
	};
	const size = sizes[page_size] || sizes.a4;
	const width = orientation === "landscape" ? size.height : size.width;
	return size.unit === "mm" ? (width / 25.4) * 96 : width * 96;
}

function resetPan() {
	panX.value = 0;
	panY.value = 0;
	if (viewportEl.value) {
		viewportEl.value.scrollLeft = 0;
		viewportEl.value.scrollTop = 0;
	}
}

function applyStageMetrics(nextViewportWidth?: number, nextStageHeight?: number) {
	if (Number.isFinite(nextViewportWidth) && nextViewportWidth! > 0) {
		viewportWidth.value = Math.round(nextViewportWidth!);
	}
	if (Number.isFinite(nextStageHeight) && nextStageHeight! > 0) {
		stageHeight.value = Math.round(nextStageHeight!);
	}
}

function updateStageMetricsFromDom() {
	const stage = stageEl.value;
	const viewport = viewportEl.value;
	if (!stage) return;
	applyStageMetrics(
		viewport?.clientWidth || stage.offsetWidth,
		stage.scrollHeight || stage.offsetHeight
	);
}

function scheduleStageMetricsUpdate() {
	if (stageMetricsFrame !== null) cancelAnimationFrame(stageMetricsFrame);
	if (stageMetricsReadFrame !== null) cancelAnimationFrame(stageMetricsReadFrame);
	void nextTick(() => {
		stageMetricsFrame = requestAnimationFrame(() => {
			stageMetricsFrame = null;
			stageMetricsReadFrame = requestAnimationFrame(() => {
				stageMetricsReadFrame = null;
				updateStageMetricsFromDom();
			});
		});
	});
}

function fitPreview() {
	emit("update:zoomMode", "fit");
	resetPan();
}

function setZoom(value: number) {
	emit("update:zoomMode", "manual");
	emit("update:zoomPercent", clamp(value, 25, 200));
	if (value === 100) resetPan();
}

function changeZoom(delta: number) {
	const current = Math.round(zoomScale.value * 100);
	if (delta > 0) {
		setZoom(Math.floor(current / 10) * 10 + 10);
		return;
	}
	if (delta < 0) {
		setZoom(Math.ceil(current / 10) * 10 - 10);
	}
}

function startZoomEdit() {
	zoomDraft.value = String(Math.round(zoomScale.value * 100));
	isEditingZoom.value = true;
	void nextTick(() => {
		zoomInputEl.value?.focus();
		zoomInputEl.value?.select();
	});
}

function parseZoomDraft(value: string): number | null {
	const normalized = value.trim().replace(/%$/, "").trim();
	if (!normalized) return null;
	const parsed = Number(normalized);
	if (!Number.isFinite(parsed)) return null;
	return clamp(parsed, 25, 200);
}

function applyZoomDraft() {
	if (!isEditingZoom.value) return;
	const parsed = parseZoomDraft(zoomDraft.value);
	isEditingZoom.value = false;
	if (parsed === null) return;
	setZoom(parsed);
}

function cancelZoomEdit() {
	isEditingZoom.value = false;
	zoomDraft.value = "";
}

function onPanPointerDown(event: PointerEvent) {
	if (!canPan.value) return;
	if (event.button !== 0) return;
	const target = event.target as HTMLElement | null;
	if (target?.closest("button, input, select, textarea, a")) return;
	event.preventDefault();
	isPanning.value = true;
	const startX = event.clientX;
	const startY = event.clientY;
	const initialX = panX.value;
	const initialY = panY.value;

	const onMove = (moveEvent: PointerEvent) => {
		panX.value = initialX + moveEvent.clientX - startX;
		panY.value = initialY + moveEvent.clientY - startY;
	};
	const onUp = () => {
		isPanning.value = false;
		panCleanup?.();
		panCleanup = null;
	};
	panCleanup?.();
	window.addEventListener("pointermove", onMove);
	window.addEventListener("pointerup", onUp, { once: true });
	panCleanup = () => {
		window.removeEventListener("pointermove", onMove);
		window.removeEventListener("pointerup", onUp);
	};
}

/**
 * Handle report preview custom event with SVG data
 */
function onReportPreview(event: Event) {
	const detail = (event as CustomEvent).detail;
	if (!detail || !detail.svg_pages) return;

	logger.info("Received report preview", detail);

	// Clear error panel
	errorPanel.value = null;

	// Get container
	const container = previewPaneEl.value?.querySelector<HTMLElement>("#typst-svg-container");
	if (!container) return;

	// Clear existing content
	container.innerHTML = "";
	container.classList.add("has-pages");

	// Render SVG pages
	const svgPages = detail.svg_pages as string[];
	svgPages.forEach((svgContent: string, index: number) => {
		const pageDiv = document.createElement("div");
		pageDiv.className = "typst-page";
		pageDiv.setAttribute("data-page-number", String(index + 1));
		pageDiv.innerHTML = sanitizeSvg(svgContent);
		container.appendChild(pageDiv);
	});
	resetPan();
	scheduleStageMetricsUpdate();

	logger.info(`Rendered ${svgPages.length} page(s)`);
}

function copyError() {
	if (!errorPanel.value) return;
	if (navigator?.clipboard?.writeText) {
		navigator.clipboard.writeText(errorPanel.value);
		return;
	}
	const textarea = document.createElement("textarea");
	textarea.value = errorPanel.value;
	document.body.appendChild(textarea);
	textarea.select();
	document.execCommand("copy");
	document.body.removeChild(textarea);
}

onMounted(() => {
	window.addEventListener(CrispyPreviewEvents.Status, onPreviewStatus);
	window.addEventListener("crispy-report-preview", onReportPreview);
	const container = previewPaneEl.value?.querySelector<HTMLElement>("#typst-svg-container");
	if (container) {
		contentObserver = new MutationObserver(() => {
			resetPan();
			if (!stageResizeObserver) scheduleStageMetricsUpdate();
		});
		contentObserver.observe(container, { childList: true });
	}
	if (typeof ResizeObserver !== "undefined" && stageEl.value) {
		stageResizeObserver = new ResizeObserver((entries) => {
			let nextViewportWidth: number | undefined;
			let nextStageHeight: number | undefined;
			for (const entry of entries) {
				if (entry.target === viewportEl.value) {
					nextViewportWidth = entry.contentRect.width;
				}
				if (entry.target === stageEl.value) {
					nextStageHeight = entry.contentRect.height;
				}
			}
			applyStageMetrics(nextViewportWidth, nextStageHeight);
		});
		stageResizeObserver.observe(stageEl.value);
		if (viewportEl.value) stageResizeObserver.observe(viewportEl.value);
	}
	scheduleStageMetricsUpdate();
});

onBeforeUnmount(() => {
	if (teardown) teardown();
	panCleanup?.();
	contentObserver?.disconnect();
	stageResizeObserver?.disconnect();
	if (stageMetricsFrame !== null) cancelAnimationFrame(stageMetricsFrame);
	if (stageMetricsReadFrame !== null) cancelAnimationFrame(stageMetricsReadFrame);
	window.removeEventListener(CrispyPreviewEvents.Status, onPreviewStatus);
	window.removeEventListener("crispy-report-preview", onReportPreview);
});
</script>

<style scoped>
.preview-pane {
	background: #fff;
	border: 1px solid #e2e8f0;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.preview-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 16px;
	background: #f8fafc;
	margin-top: 8px;
}

.preview-zoom-toolbar {
	position: sticky;
	top: 0;
	z-index: 2;
	display: flex;
	align-items: center;
	gap: 6px;
	padding: 8px;
	margin-bottom: 12px;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	background: rgba(255, 255, 255, 0.94);
	box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

.preview-zoom-toolbar .is-active {
	background: #0f172a;
	color: #fff;
}

.preview-zoom-toolbar__icon {
	width: 28px;
	padding-left: 0;
	padding-right: 0;
}

.preview-zoom-toolbar__value {
	min-width: 44px;
	border: 1px solid transparent;
	background: transparent;
	padding: 2px 6px;
	text-align: center;
	font-size: 12px;
	font-weight: 600;
	color: #475569;
	border-radius: 6px;
	line-height: 1.4;
	cursor: text;
}

.preview-zoom-toolbar__value:hover,
.preview-zoom-toolbar__value:focus-visible {
	border-color: #cbd5e1;
	background: #fff;
	color: #0f172a;
	outline: none;
}

.preview-zoom-toolbar__input {
	width: 56px;
	height: 24px;
	border: 1px solid #cbd5e1;
	border-radius: 6px;
	padding: 2px 6px;
	background: #fff;
	color: #0f172a;
	font-size: 12px;
	font-weight: 600;
	text-align: center;
	outline: none;
}

.preview-zoom-toolbar__input:focus {
	border-color: #64748b;
	box-shadow: 0 0 0 2px rgba(100, 116, 139, 0.14);
}

.preview-viewport {
	min-height: 240px;
	overflow: auto;
}

.preview-viewport--pannable {
	cursor: grab;
}

.preview-viewport--panning {
	cursor: grabbing;
	user-select: none;
}

.preview-stage-sizer {
	position: relative;
	min-width: 100%;
}

.preview-stage {
	position: absolute;
	top: 0;
	left: 0;
	transform-origin: top left;
	will-change: transform;
}

.preview-stage :deep(.typst-page) {
	width: var(--preview-page-width);
	max-width: none;
}

.preview-stage :deep(.typst-page svg) {
	width: 100%;
	height: auto;
	display: block;
}

.preview-placeholder {
	padding: 20px;
	border: 1px dashed #cbd5e1;
	border-radius: 6px;
	text-align: center;
	color: #94a3b8;
	font-size: 14px;
	background: #fff;
}

/* When Typst pages render, we add .has-pages class; keep the same styles as current flow */
#typst-svg-container.has-pages {
	display: grid;
	gap: 16px;
}

.preview-error {
	margin-top: 16px;
	border: 1px solid #fecaca;
	background: #fff1f2;
	border-radius: 8px;
	overflow: hidden;
	box-shadow: 0 6px 16px rgba(239, 68, 68, 0.15);
}

.preview-error__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 10px 12px;
	background: #fee2e2;
	border-bottom: 1px solid #fecaca;
}

.preview-error__title {
	font-size: 12px;
	font-weight: 700;
	color: #991b1b;
	letter-spacing: 0.02em;
	text-transform: uppercase;
}

.preview-error__copy {
	border: 1px solid #fca5a5;
	background: #fff;
	color: #b91c1c;
	border-radius: 6px;
	padding: 4px 8px;
	font-size: 12px;
	cursor: pointer;
}

.preview-error__body {
	margin: 0;
	padding: 12px;
	font-size: 12px;
	line-height: 1.5;
	color: #7f1d1d;
	white-space: pre-wrap;
	font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
		monospace;
}
</style>
