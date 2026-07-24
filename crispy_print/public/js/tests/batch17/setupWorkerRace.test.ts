import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { setupWorker } from "../../typst/setupWorker"
import { CrispyPreviewEvents } from "../../utils/events"

class MockWorker extends EventTarget {
	messages: any[] = []
	postMessage = vi.fn((message: any) => {
		this.messages.push(message)
	})
	terminate = vi.fn()
	emit(message: any) {
		this.dispatchEvent(new MessageEvent("message", { data: message }))
	}
}

function makePane() {
	const pane = document.createElement("div")
	pane.innerHTML = `
		<div id="typst-status"></div>
		<div id="typst-svg-container"></div>
		<button id="typst-download"></button>
		<button id="typst-view-pdf"></button>
		<button id="typst-refresh"></button>
		<button id="typst-view-code"></button>
		<input id="typst-sample-doc-input" />
	`
	document.body.appendChild(pane)
	return pane
}

function makeAdapter() {
	return {
		getLayout: () => ({ sections: [] }) as any,
		getRawTypst: () => true,
		getTypstCode: () => "#text[#doc.name]",
		get_presentation_settings: () => ({}),
	}
}

async function flushCompileTimers() {
	await Promise.resolve()
	await vi.runOnlyPendingTimersAsync()
	await Promise.resolve()
	await vi.runOnlyPendingTimersAsync()
	await Promise.resolve()
}

describe("setupWorker race guards", () => {
	let worker: MockWorker
	let callbacks: Record<string, (r: any) => void>

	beforeEach(() => {
		vi.useFakeTimers()
		vi.stubGlobal("__", (value: string) => value)
		vi.stubGlobal("requestAnimationFrame", (callback: FrameRequestCallback) => {
			callback(0)
			return 1
		})
		vi.stubGlobal("cancelAnimationFrame", vi.fn())
		callbacks = {}
		worker = new MockWorker()
		;(globalThis as any).frappe = {
			csrf_token: "token",
			call: vi.fn((options: any) => {
				callbacks[options.args.name] = options.callback
			}),
			show_alert: vi.fn(),
			utils: { debounce: (fn: any) => fn },
		}
	})

	afterEach(() => {
		document.body.innerHTML = ""
		vi.useRealTimers()
		vi.unstubAllGlobals()
	})

	it("ignores out-of-order document loads", async () => {
		const pane = makePane()
		setupWorker("Test Format", pane, makeAdapter(), {
			createWorker: () => ({ worker: worker as any, cleanup: vi.fn() }),
			instanceId: "pane-a",
		})

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "A", instanceId: "pane-a" },
			})
		)
		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "B", instanceId: "pane-a" },
			})
		)

		callbacks.B({ message: { name: "B" } })
		await flushCompileTimers()
		callbacks.A({ message: { name: "A" } })
		await flushCompileTimers()

		const previewMessages = worker.messages.filter((message) => message.requestId === "preview")
		expect(previewMessages).toHaveLength(1)
		expect(previewMessages[0].typstSrc).toContain('name: "B"')
		expect(previewMessages[0].typstSrc).not.toContain('name: "A"')
	})

	it("invalidates stale pdf responses after document switch", async () => {
		const pane = makePane()
		setupWorker("Test Format", pane, makeAdapter(), {
			createWorker: () => ({ worker: worker as any, cleanup: vi.fn() }),
			instanceId: "pane-a",
		})

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "A", instanceId: "pane-a" },
			})
		)
		callbacks.A({ message: { name: "A" } })
		await flushCompileTimers()
		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.RequestPdf, {
				detail: { action: "download", instanceId: "pane-a" },
			})
		)
		const oldPdfRequest = worker.messages.find((message) => message.requestId === "download")
		expect(oldPdfRequest).toBeTruthy()

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "B", instanceId: "pane-a" },
			})
		)
		callbacks.B({ message: { name: "B" } })
		await flushCompileTimers()
		worker.emit({
			type: "compile",
			ok: true,
			format: "pdf",
			requestId: "download",
			seq: oldPdfRequest.seq,
			pdfBytes: [37, 80, 68, 70],
		})

		const postCountBefore = worker.messages.length
		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.RequestPdf, {
				detail: { action: "download", instanceId: "pane-a" },
			})
		)

		expect(worker.messages.length).toBe(postCountBefore + 1)
		expect(worker.messages[worker.messages.length - 1].requestId).toBe("download")
	})

	it("cancels pending compile timers on cleanup", async () => {
		const pane = makePane()
		const cleanupWorker = vi.fn()
		const teardown = setupWorker("Test Format", pane, makeAdapter(), {
			createWorker: () => ({ worker: worker as any, cleanup: cleanupWorker }),
			instanceId: "pane-a",
		})

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "A", instanceId: "pane-a" },
			})
		)
		callbacks.A({ message: { name: "A" } })
		await Promise.resolve()
		teardown()
		vi.advanceTimersByTime(500)

		expect(worker.postMessage).not.toHaveBeenCalled()
		expect(cleanupWorker).toHaveBeenCalledTimes(1)
	})

	it("prints the cached DocType preview PDF", async () => {
		const loadHandlers: Array<() => void> = []
		const printWindow = {
			addEventListener: vi.fn((event: string, callback: () => void) => {
				if (event === "load") loadHandlers.push(callback)
			}),
			focus: vi.fn(),
			print: vi.fn(),
		}
		vi.spyOn(window, "open").mockReturnValue(printWindow as unknown as Window)
		Object.defineProperty(URL, "createObjectURL", {
			configurable: true,
			value: vi.fn(() => "blob:doctype-preview"),
		})
		Object.defineProperty(URL, "revokeObjectURL", {
			configurable: true,
			value: vi.fn(),
		})
		const pane = makePane()
		const teardown = setupWorker("Test Format", pane, makeAdapter(), {
			createWorker: () => ({ worker: worker as any, cleanup: vi.fn() }),
			instanceId: "pane-a",
		})
		worker.emit({
			type: "compile",
			ok: true,
			format: "pdf",
			requestId: "preview",
			pdfBytes: [37, 80, 68, 70],
		})
		await Promise.resolve()

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.RequestPdf, {
				detail: { action: "print", instanceId: "pane-a" },
			})
		)
		await Promise.resolve()

		expect(window.open).toHaveBeenCalledWith("blob:doctype-preview", "_blank")
		expect(loadHandlers).toHaveLength(1)
		loadHandlers[0]()
		expect(printWindow.focus).toHaveBeenCalledOnce()
		expect(printWindow.print).toHaveBeenCalledOnce()
		expect((globalThis as any).frappe.show_alert).toHaveBeenCalledWith({
			message: "Print dialog opened.",
			indicator: "green",
		})
		teardown()
	})

	it("recovers from a missing-layout dead end after a later valid document refresh", async () => {
		const pane = makePane()
		let hasLayout = false
		const teardown = setupWorker(
			"Test Format",
			pane,
			{
				getLayout: () => (hasLayout ? ({ sections: [] } as any) : null),
				getRawTypst: () => false,
				getTypstCode: () => "#text[#doc.name]",
				get_presentation_settings: () => ({}),
			},
			{
				createWorker: () => ({ worker: worker as any, cleanup: vi.fn() }),
				instanceId: "pane-a",
			}
		)

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "A", instanceId: "pane-a" },
			})
		)
		callbacks.A({ message: { name: "A" } })
		await Promise.resolve()
		vi.advanceTimersByTime(150 + 500 + 1000 + 1500 + 2000 + 2500)

		expect(worker.messages.filter((message) => message.requestId === "preview")).toHaveLength(0)

		hasLayout = true
		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.Refresh, {
				detail: { instanceId: "pane-a" },
			})
		)
		callbacks.A({ message: { name: "A" } })
		await flushCompileTimers()

		expect(worker.messages.some((message) => message.requestId === "preview")).toBe(true)
		teardown()
	})

	it("prefers server-generated document code payload for QR compilation", async () => {
		const pane = makePane()
		setupWorker(
			"Test Format",
			pane,
			{
				...makeAdapter(),
				getQrEnabled: () => true,
				get_presentation_settings: () => ({
					qr: { sourceMode: "document_code_profile" },
				}),
			},
			{
				createWorker: () => ({ worker: worker as any, cleanup: vi.fn() }),
				instanceId: "pane-a",
			}
		)

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "A", instanceId: "pane-a" },
			})
		)
		callbacks.A({
			message: {
				name: "A",
				__crispy_document_code: { encoded_value: "SERVER-QR-CODE" },
			},
		})
		await flushCompileTimers()

		const previewMessage = worker.messages.find((message) => message.requestId === "preview")
		expect(previewMessage).toBeTruthy()
		expect(previewMessage.qrData).toBe("SERVER-QR-CODE")
		expect(previewMessage.barcodeOptions?.symbology).toBe("QR Code")
		expect(previewMessage.typstSrc).toContain("@local/crispy-print:0.1.0")
		expect(previewMessage.typstSrc).toContain("crispy-qrcode")
		expect(previewMessage.typstSrc).toContain("SERVER-QR-CODE")
		expect(previewMessage.typstSrc).toContain("#text[#doc.name]")
	})

	it("sends selected-field payload for basic QR compilation", async () => {
		const pane = makePane()
		setupWorker(
			"Test Format",
			pane,
			{
				...makeAdapter(),
				getQrEnabled: () => true,
				get_presentation_settings: () => ({
					qr: { sourceMode: "basic", fields: ["name", "customer"] },
				}),
			},
			{
				createWorker: () => ({ worker: worker as any, cleanup: vi.fn() }),
				instanceId: "pane-a",
			}
		)

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.SetDoc, {
				detail: { doctype: "Sales Invoice", docname: "A", instanceId: "pane-a" },
			})
		)
		callbacks.A({
			message: {
				name: "A",
				customer: "Customer A",
			},
		})
		await flushCompileTimers()

		const previewMessage = worker.messages.find((message) => message.requestId === "preview")
		expect(previewMessage).toBeTruthy()
		expect(previewMessage.qrFilename).toBe("A-qr.svg")
		expect(previewMessage.qrData).toBe("name: A\ncustomer: Customer A")
		expect(previewMessage.typstSrc).toContain("crispy-qrcode")
		expect(previewMessage.typstSrc).toContain("name: A\\ncustomer: Customer A")
		expect(previewMessage.typstSrc).toContain("#text[#doc.name]")
	})
})
