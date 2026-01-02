import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: vi.fn(),
	saveCrispyFormat: vi.fn(),
}))

vi.mock("../../api/frappe", () => ({
	withDoctype: vi.fn(),
}))

describe("raw typst mode", () => {
	beforeEach(() => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			show_alert: vi.fn(),
		}
	})

	it("saves when layout is missing but rawTypst is enabled", async () => {
		const { useStore } = await import("../../composables/useStore")
		const { saveCrispyFormat } = await import("../../api/crispy")

		const store = useStore()
		store.crispyFormat.value = { name: "Raw-1", doc_type: "Invoice" } as any
		store.layout.value = null
		store.pageSettings.value = { pageSize: "A4" } as any
		store.typstCode.value = "#set page()"
		store.rawTypst.value = true
		store.dirty.value = true

		await store.saveChanges()

		expect(saveCrispyFormat).toHaveBeenCalledTimes(1)
		const args = (saveCrispyFormat as any).mock.calls[0]
		expect(args[0]).toBe("Raw-1")
		expect(args[1].layout_json).toBe("")
		expect(args[1].typst_code).toBe("#set page()")
		expect(args[1].raw_typst).toBe(1)
	})
})
