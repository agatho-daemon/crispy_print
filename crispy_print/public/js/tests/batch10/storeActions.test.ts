import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: vi.fn(),
	saveCrispyFormat: vi.fn(),
}))

vi.mock("../../api/frappe", () => ({
	withDoctype: vi.fn(),
}))

describe("useStore actions", () => {
	beforeEach(() => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			show_alert: vi.fn(),
		}
	})

	it("saves changes with serialized layout", async () => {
		const { useStore } = await import("../../composables/useStore")
		const { saveCrispyFormat } = await import("../../api/crispy")

		const store = useStore()
		store.crispyFormat.value = { name: "Format-1", doc_type: "Invoice" } as any
		store.layout.value = { sections: [] } as any
		store.presentation_settings.value = { page: { size: "A4", orientation: "portrait", margins: { top: 25, bottom: 20, left: 20, right: 20 } }, branding: { mode: "none", letterhead: "", letterhead_image: "", logo: { company: "", image: "", size: 25, dx: 0, dy: 0 } } } as any
		store.typstCode.value = ""
		store.rawTypst.value = false
		store.dirty.value = true

		await store.saveChanges()

		expect(saveCrispyFormat).toHaveBeenCalledTimes(1)
		const args = (saveCrispyFormat as any).mock.calls[0]
		expect(args[0]).toBe("Format-1")
		expect(args[1].layout_json).toContain("sections")
		expect(args[1].raw_typst).toBe(0)
		expect(store.dirty.value).toBe(false)
	})

	it("resetLayout uses default and marks dirty", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()

		store.layout.value = { sections: [{ label: "Old", columns: [] }] } as any
		store.dirty.value = false

		store.resetLayout()

		expect(store.layout.value?.sections?.length).toBe(0)
		expect(store.dirty.value).toBe(true)
	})
})
