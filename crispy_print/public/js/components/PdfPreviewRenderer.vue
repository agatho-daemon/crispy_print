<template>
	<div ref="rootEl" class="pdf-preview" :aria-busy="busy">
		<div class="pdf-preview__pages">
			<div
				v-for="page in pages"
				:key="`${revision}-${page.number}`"
				ref="pageEls"
				class="typst-page pdf-preview__page"
				:data-page-number="page.number"
				:style="{ width: `${page.width}px`, height: `${page.height}px` }"
			>
				<canvas :ref="(element) => setCanvas(page.number, element)" />
				<div
					:ref="(element) => setTextLayer(page.number, element)"
					class="pdf-preview__text-layer"
				></div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import type { PDFDocumentProxy, RenderTask, TextLayer } from "pdfjs-dist/legacy/build/pdf.mjs";
import { loadPdfJs } from "../utils/pdfJs";

type PdfLoadingTask = ReturnType<typeof import("pdfjs-dist/legacy/build/pdf.mjs").getDocument>;

interface PageDescriptor {
	number: number;
	width: number;
	height: number;
}

const props = defineProps<{
	data: Uint8Array | null;
	revision: number;
	viewportRoot?: HTMLElement | null;
}>();
const emit = defineEmits<{
	(event: "state", value: "loading-pdf" | "rendering" | "ready" | "error", detail?: any): void;
	(event: "page-count", value: number): void;
}>();

const rootEl = ref<HTMLElement | null>(null);
const pageEls = ref<HTMLElement[]>([]);
const pages = ref<PageDescriptor[]>([]);
const canvases = new Map<number, HTMLCanvasElement>();
const textLayers = new Map<number, HTMLElement>();
const renderTasks = new Map<number, RenderTask>();
const textLayerTasks = new Map<number, TextLayer>();
const renderRequests = new Map<number, symbol>();
const renderedPages = new Set<number>();
const intersectingPages = new Set<number>();
let wantedPages = new Set<number>();
const busy = computed(() => Boolean(props.data?.byteLength) && renderedPages.size === 0);
const MAX_RENDERED_PAGES = 5;
let documentProxy: PDFDocumentProxy | null = null;
let loadingTask: PdfLoadingTask | null = null;
let observer: IntersectionObserver | null = null;
let generation = 0;

function setCanvas(pageNumber: number, element: any) {
	if (!(element instanceof HTMLCanvasElement)) return;
	if (!canvases.has(pageNumber)) {
		// HTML canvases otherwise allocate a default 300×150 backing store for
		// every PDF placeholder, which becomes material on very large reports.
		element.width = 0;
		element.height = 0;
	}
	canvases.set(pageNumber, element);
}

function setTextLayer(pageNumber: number, element: any) {
	if (!(element instanceof HTMLElement)) return;
	textLayers.set(pageNumber, element);
}

async function cleanupDocument(invalidate = true) {
	if (invalidate) generation += 1;
	observer?.disconnect();
	observer = null;
	renderTasks.forEach((task) => task.cancel());
	renderTasks.clear();
	textLayerTasks.forEach((task) => task.cancel());
	textLayerTasks.clear();
	renderRequests.clear();
	renderedPages.clear();
	intersectingPages.clear();
	wantedPages.clear();
	canvases.clear();
	textLayers.clear();
	pageEls.value = [];
	pages.value = [];
	const previousLoadingTask = loadingTask;
	const previousDocument = documentProxy;
	loadingTask = null;
	documentProxy = null;
	if (previousLoadingTask) {
		await previousLoadingTask.destroy().catch(() => undefined);
	} else if (previousDocument) {
		await previousDocument.destroy().catch(() => undefined);
	}
}

async function renderPage(pageNumber: number, expectedGeneration: number) {
	if (
		!documentProxy ||
		renderedPages.has(pageNumber) ||
		renderTasks.has(pageNumber) ||
		renderRequests.has(pageNumber)
	)
		return;
	const canvas = canvases.get(pageNumber);
	const textLayer = textLayers.get(pageNumber);
	if (!canvas || !textLayer) return;
	const request = Symbol(`pdf-page-${pageNumber}`);
	renderRequests.set(pageNumber, request);

	try {
		emit("state", "rendering");
		const page = await documentProxy.getPage(pageNumber);
		if (
			expectedGeneration !== generation ||
			renderRequests.get(pageNumber) !== request ||
			!wantedPages.has(pageNumber)
		)
			return;
		const viewport = page.getViewport({ scale: 96 / 72 });
		const descriptor = pages.value[pageNumber - 1];
		if (descriptor) {
			descriptor.width = viewport.width;
			descriptor.height = viewport.height;
		}
		const ratio = Math.min(window.devicePixelRatio || 1, 2);
		canvas.width = Math.ceil(viewport.width * ratio);
		canvas.height = Math.ceil(viewport.height * ratio);
		canvas.style.width = `${viewport.width}px`;
		canvas.style.height = `${viewport.height}px`;
		const context = canvas.getContext("2d");
		if (!context) throw new Error("Canvas rendering is unavailable");
		const task = page.render({
			canvas,
			viewport,
			transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
		});
		renderTasks.set(pageNumber, task);
		textLayer.replaceChildren();
		const textPromise = (async () => {
			const textContent = await page.getTextContent({ includeMarkedContent: true });
			if (
				expectedGeneration !== generation ||
				renderRequests.get(pageNumber) !== request ||
				!wantedPages.has(pageNumber)
			)
				return;
			textLayer.style.setProperty("--scale-factor", String(viewport.scale));
			const { TextLayer } = await loadPdfJs();
			const textTask = new TextLayer({
				textContentSource: textContent,
				container: textLayer,
				viewport,
			});
			textLayerTasks.set(pageNumber, textTask);
			await textTask.render();
		})();
		await Promise.all([task.promise, textPromise]);
		renderTasks.delete(pageNumber);
		textLayerTasks.delete(pageNumber);
		if (
			expectedGeneration !== generation ||
			renderRequests.get(pageNumber) !== request ||
			!wantedPages.has(pageNumber)
		)
			return;
		renderRequests.delete(pageNumber);
		renderedPages.add(pageNumber);
		emit("state", "ready", { pageCount: pages.value.length });
	} catch (error: any) {
		renderTasks.delete(pageNumber);
		textLayerTasks.delete(pageNumber);
		if (renderRequests.get(pageNumber) === request) renderRequests.delete(pageNumber);
		if (
			error?.name === "RenderingCancelledException" ||
			expectedGeneration !== generation ||
			!wantedPages.has(pageNumber)
		)
			return;
		emit("state", "error", error);
	}
}

function releasePage(pageNumber: number) {
	renderRequests.delete(pageNumber);
	const task = renderTasks.get(pageNumber);
	if (task) {
		task.cancel();
		renderTasks.delete(pageNumber);
	}
	const textTask = textLayerTasks.get(pageNumber);
	if (textTask) {
		textTask.cancel();
		textLayerTasks.delete(pageNumber);
	}
	const canvas = canvases.get(pageNumber);
	if (canvas) {
		canvas.width = 0;
		canvas.height = 0;
		canvas.style.width = "";
		canvas.style.height = "";
	}
	textLayers.get(pageNumber)?.replaceChildren();
	renderedPages.delete(pageNumber);
}

function updateRenderWindow(pageNumber: number, expectedGeneration: number) {
	const halfWindow = Math.floor(MAX_RENDERED_PAGES / 2);
	let firstPage = Math.max(1, pageNumber - halfWindow);
	const lastPage = Math.min(pages.value.length, firstPage + MAX_RENDERED_PAGES - 1);
	firstPage = Math.max(1, lastPage - MAX_RENDERED_PAGES + 1);
	wantedPages = new Set<number>();
	for (let number = firstPage; number <= lastPage; number += 1) wantedPages.add(number);

	for (const number of new Set([
		...renderedPages,
		...renderTasks.keys(),
		...renderRequests.keys(),
	])) {
		if (!wantedPages.has(number)) releasePage(number);
	}
	for (const number of wantedPages) void renderPage(number, expectedGeneration);
}

function closestIntersectingPage(): number | null {
	if (!intersectingPages.size) return null;
	const rootRect = props.viewportRoot?.getBoundingClientRect();
	const viewportCenter = rootRect ? rootRect.top + rootRect.height / 2 : window.innerHeight / 2;
	let closestPage: number | null = null;
	let closestDistance = Number.POSITIVE_INFINITY;
	for (const pageNumber of intersectingPages) {
		const element = pageEls.value.find(
			(pageElement) => Number(pageElement.dataset.pageNumber) === pageNumber
		);
		if (!element) continue;
		const rect = element.getBoundingClientRect();
		const distance = Math.abs(rect.top + rect.height / 2 - viewportCenter);
		if (distance < closestDistance) {
			closestPage = pageNumber;
			closestDistance = distance;
		}
	}
	return closestPage;
}

function observePages(expectedGeneration: number) {
	observer?.disconnect();
	if (typeof IntersectionObserver === "undefined") {
		void renderPage(1, expectedGeneration);
		return;
	}
	observer = new IntersectionObserver(
		(entries) => {
			for (const entry of entries) {
				const pageNumber = Number((entry.target as HTMLElement).dataset.pageNumber);
				if (entry.isIntersecting) {
					intersectingPages.add(pageNumber);
				} else {
					intersectingPages.delete(pageNumber);
				}
			}
			const closestPage = closestIntersectingPage();
			if (closestPage !== null) updateRenderWindow(closestPage, expectedGeneration);
		},
		{ root: props.viewportRoot || null, rootMargin: "800px 0px", threshold: 0.01 }
	);
	pageEls.value.forEach((element) => observer?.observe(element));
	wantedPages = new Set([1]);
	void renderPage(1, expectedGeneration);
}

async function loadPdf(data: Uint8Array | null) {
	const expectedGeneration = ++generation;
	await cleanupDocument(false);
	if (expectedGeneration !== generation) return;
	if (!data?.byteLength) return;
	emit("state", "loading-pdf");
	try {
		const { getDocument } = await loadPdfJs();
		if (expectedGeneration !== generation) return;
		loadingTask = getDocument({ data: data.slice() });
		const loaded = await loadingTask.promise;
		if (expectedGeneration !== generation) {
			await loaded.destroy();
			return;
		}
		documentProxy = loaded;
		const firstPage = await loaded.getPage(1);
		const firstViewport = firstPage.getViewport({ scale: 96 / 72 });
		pages.value = Array.from({ length: loaded.numPages }, (_, index) => ({
			number: index + 1,
			width: firstViewport.width,
			height: firstViewport.height,
		}));
		emit("page-count", loaded.numPages);
		await nextTick();
		observePages(expectedGeneration);
	} catch (error) {
		if (expectedGeneration === generation) emit("state", "error", error);
	}
}

watch(
	() => [props.data, props.revision] as const,
	([data]) => void loadPdf(data),
	{ immediate: true }
);
onBeforeUnmount(() => void cleanupDocument());
</script>

<style scoped>
.pdf-preview__pages {
	display: grid;
	gap: 16px;
}

.pdf-preview__page {
	position: relative;
	background: #fff;
	box-shadow: 0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2);
}

.pdf-preview__page canvas {
	display: block;
}

.pdf-preview__text-layer {
	position: absolute;
	inset: 0;
	z-index: 2;
	overflow: hidden;
	line-height: 1;
	text-align: initial;
	-webkit-text-size-adjust: none;
	-moz-text-size-adjust: none;
	text-size-adjust: none;
	forced-color-adjust: none;
	transform-origin: 0 0;
}

.pdf-preview__text-layer :deep(:is(span, br)) {
	position: absolute;
	color: transparent;
	white-space: pre;
	cursor: text;
	transform-origin: 0% 0%;
}

.pdf-preview__text-layer :deep(span.markedContent) {
	top: 0;
	height: 0;
}

.pdf-preview__text-layer :deep(::selection) {
	background: blue;
	background: AccentColor;
	color: transparent;
}
</style>
