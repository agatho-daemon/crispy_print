import { describe, expect, it, vi } from "vitest"
import { createTypstWorker } from "../../typst/createTypstWorker"

describe("createTypstWorker", () => {
	it("creates worker and cleans up blob url", () => {
		const terminate = vi.fn()
		const workerCtor = vi.fn(() => ({ terminate }))
		const originalCreate = (URL as any).createObjectURL
		const originalRevoke = (URL as any).revokeObjectURL
		if (!originalCreate) {
			;(URL as any).createObjectURL = () => ""
		}
		if (!originalRevoke) {
			;(URL as any).revokeObjectURL = () => {}
		}
		const createUrl = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock")
		const revokeUrl = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {})

		const originalWorker = (globalThis as any).Worker
		;(globalThis as any).Worker = workerCtor as any

		const handle = createTypstWorker()
		expect(workerCtor).toHaveBeenCalledWith("blob:mock")
		expect(handle.worker).toBeDefined()

		handle.cleanup()
		expect(terminate).toHaveBeenCalledTimes(1)
		expect(revokeUrl).toHaveBeenCalledWith("blob:mock")
		;(globalThis as any).Worker = originalWorker
		createUrl.mockRestore()
		revokeUrl.mockRestore()
		if (!originalCreate) {
			delete (URL as any).createObjectURL
		} else {
			;(URL as any).createObjectURL = originalCreate
		}
		if (!originalRevoke) {
			delete (URL as any).revokeObjectURL
		} else {
			;(URL as any).revokeObjectURL = originalRevoke
		}
	})
})
