import { describe, expect, it, vi } from "vitest"
import { createTypstWorker } from "../../typst/createTypstWorker"

describe("createTypstWorker", () => {
	it("creates same-origin static worker by default", () => {
		const terminate = vi.fn()
		const workerCtor = vi.fn(() => ({ terminate }))
		const originalWorker = (globalThis as any).Worker
		;(globalThis as any).Worker = workerCtor as any

		const handle = createTypstWorker()
		expect(workerCtor).toHaveBeenCalledWith("/assets/crispy_print/js/typst/typstCliWorker.js")
		expect(handle.worker).toBeDefined()

		handle.cleanup()
		expect(terminate).toHaveBeenCalledTimes(1)
		;(globalThis as any).Worker = originalWorker
	})

	it("does not attempt a blob fallback when static worker construction fails", () => {
		const workerCtor = vi.fn(() => {
			throw new Error("blocked")
		})
		const originalWorker = (globalThis as any).Worker
		;(globalThis as any).Worker = workerCtor as any

		expect(() => createTypstWorker()).toThrow("blocked")
		expect(workerCtor).toHaveBeenCalledTimes(1)
		expect(workerCtor).toHaveBeenCalledWith("/assets/crispy_print/js/typst/typstCliWorker.js")
		;(globalThis as any).Worker = originalWorker
	})
})
