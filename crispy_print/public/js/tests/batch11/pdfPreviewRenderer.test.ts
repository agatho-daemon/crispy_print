import { flushPromises, mount } from "@vue/test-utils"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import PdfPreviewRenderer from "../../components/PdfPreviewRenderer.vue"
import { decodePdfData } from "../../utils/pdfBytes"

const mocks = vi.hoisted(() => {
	const render = vi.fn(() => ({ promise: Promise.resolve(), cancel: vi.fn() }))
	const destroyDocument = vi.fn(() => Promise.resolve())
	const destroyLoading = vi.fn(() => Promise.resolve())
	const getPage = vi.fn(async (number: number) => ({
		getViewport: () => ({ width: 800, height: 1100 }),
		render: () => render(number),
	}))
	const getDocument = vi.fn(() => ({
		promise: Promise.resolve({ numPages: 20, getPage, destroy: destroyDocument }),
		destroy: destroyLoading,
	}))
	return { render, destroyDocument, destroyLoading, getPage, getDocument }
})

vi.mock("pdfjs-dist/legacy/build/pdf.js", () => ({
	GlobalWorkerOptions: {},
	getDocument: mocks.getDocument,
}))

let observerCallback: IntersectionObserverCallback | null = null

class ObserverStub {
	observe = vi.fn()
	disconnect = vi.fn()
	constructor(callback: IntersectionObserverCallback) {
		observerCallback = callback
	}
}

describe("PDF preview renderer", () => {
	beforeEach(() => {
		vi.clearAllMocks()
		observerCallback = null
		;(globalThis as any).IntersectionObserver = ObserverStub
		vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockReturnValue({} as any)
	})

	afterEach(() => {
		vi.restoreAllMocks()
	})

	it("decodes report PDF data at the boundary", () => {
		expect(Array.from(decodePdfData("JVBERg=="))).toEqual([37, 80, 68, 70])
		expect(decodePdfData("").byteLength).toBe(0)
	})

	it("creates placeholders for all pages but initially paints only the first page", async () => {
		const wrapper = mount(PdfPreviewRenderer, {
			props: { data: new Uint8Array([37, 80, 68, 70]), revision: 1 },
		})
		await flushPromises()

		expect(wrapper.findAll(".pdf-preview__page")).toHaveLength(20)
		expect(mocks.render).toHaveBeenCalledTimes(1)
		expect(mocks.render).toHaveBeenCalledWith(1)
		expect(wrapper.emitted("ready")).toBeUndefined()
		expect(wrapper.emitted("state")?.some(([state]) => state === "ready")).toBe(true)

		const firstPage = wrapper.find<HTMLElement>(".pdf-preview__page").element
		const firstCanvas = wrapper.find<HTMLCanvasElement>("canvas").element
		expect(firstCanvas.width).toBeGreaterThan(0)
		observerCallback?.(
			[{ target: firstPage, isIntersecting: false } as IntersectionObserverEntry],
			{} as IntersectionObserver
		)
		expect(firstCanvas.width).toBe(0)

		wrapper.unmount()
		await flushPromises()
		expect(mocks.destroyLoading).toHaveBeenCalled()
		expect(mocks.destroyDocument).not.toHaveBeenCalled()
	})
})
