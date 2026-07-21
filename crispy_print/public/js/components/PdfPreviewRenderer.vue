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
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import {
	GlobalWorkerOptions,
	getDocument,
	type PDFDocumentProxy,
	type RenderTask,
} from "pdfjs-dist/legacy/build/pdf.js";

GlobalWorkerOptions.workerSrc = "/assets/crispy_print/vendor/pdfjs/pdf.worker.min.js";

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
const renderTasks = new Map<number, RenderTask>();
const renderedPages = new Set<number>();
const busy = computed(() => Boolean(props.data?.byteLength) && renderedPages.size === 0);
let documentProxy: PDFDocumentProxy | null = null;
let loadingTask: ReturnType<typeof getDocument> | null = null;
let observer: IntersectionObserver | null = null;
let generation = 0;

function setCanvas(pageNumber: number, element: any) {
	if (element instanceof HTMLCanvasElement) canvases.set(pageNumber, element);
}

async function cleanupDocument(invalidate = true) {
	if (invalidate) generation += 1;
	observer?.disconnect();
	observer = null;
	renderTasks.forEach((task) => task.cancel());
	renderTasks.clear();
	renderedPages.clear();
	canvases.clear();
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
	if (!documentProxy || renderedPages.has(pageNumber) || renderTasks.has(pageNumber)) return;
	const canvas = canvases.get(pageNumber);
	if (!canvas) return;

	try {
		emit("state", "rendering");
		const page = await documentProxy.getPage(pageNumber);
		if (expectedGeneration !== generation) return;
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
			canvasContext: context,
			viewport,
			transform: ratio === 1 ? undefined : [ratio, 0, 0, ratio, 0, 0],
		});
		renderTasks.set(pageNumber, task);
		await task.promise;
		renderTasks.delete(pageNumber);
		if (expectedGeneration !== generation) return;
		renderedPages.add(pageNumber);
		emit("state", "ready", { pageCount: pages.value.length });
	} catch (error: any) {
		renderTasks.delete(pageNumber);
		if (error?.name === "RenderingCancelledException" || expectedGeneration !== generation)
			return;
		emit("state", "error", error);
	}
}

function releasePage(pageNumber: number) {
	const task = renderTasks.get(pageNumber);
	if (task) {
		task.cancel();
		renderTasks.delete(pageNumber);
	}
	const canvas = canvases.get(pageNumber);
	if (canvas) {
		canvas.width = 0;
		canvas.height = 0;
		canvas.style.width = "";
		canvas.style.height = "";
	}
	renderedPages.delete(pageNumber);
}

function observePages(expectedGeneration: number) {
	observer?.disconnect();
	if (typeof IntersectionObserver === "undefined") {
		void renderPage(1, expectedGeneration);
		return;
	}
	observer = new IntersectionObserver(
		(entries) => {
			entries.forEach((entry) => {
				const pageNumber = Number((entry.target as HTMLElement).dataset.pageNumber);
				if (entry.isIntersecting) {
					void renderPage(pageNumber, expectedGeneration);
				} else {
					releasePage(pageNumber);
				}
			});
		},
		{ root: props.viewportRoot || null, rootMargin: "800px 0px", threshold: 0.01 }
	);
	pageEls.value.forEach((element) => observer?.observe(element));
	void renderPage(1, expectedGeneration);
}

async function loadPdf(data: Uint8Array | null) {
	const expectedGeneration = ++generation;
	await cleanupDocument(false);
	if (expectedGeneration !== generation) return;
	if (!data?.byteLength) return;
	emit("state", "loading-pdf");
	try {
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
	background: #fff;
	box-shadow: 0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2);
}

.pdf-preview__page canvas {
	display: block;
}
</style>
