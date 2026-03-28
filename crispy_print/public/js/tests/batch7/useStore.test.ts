import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: async () => ({
		name: "Test Format",
		doc_type: "Sales Invoice",
		layout_json: JSON.stringify({ sections: [] }),
		page_settings: JSON.stringify({ pageSize: "A4" }),
		raw_typst: 0,
	}),
	saveCrispyFormat: async () => {},
}))

vi.mock("../../api/frappe", () => ({
	withDoctype: async () => {},
}))

vi.mock("../../utils/formatLoader", async (orig) => {
	const actual = (await orig()) as Record<string, any>
	return {
			...actual,
			parseCrispyFormatDoc: () => ({
				layout: { sections: [] as unknown[] },
				pageSettings: {
				pageSize: "A4",
				orientation: "portrait",
				margins: { top: 1, bottom: 1, left: 1, right: 1 },
				language: "en",
			},
			docHeader: "",
			formatDoc: {},
		}),
	}
})

describe("useStore", () => {
	beforeEach(() => {
		(globalThis as any).__ = (msg: string): string => msg;
		(globalThis as any).frappe = {
			call: vi.fn(async () => ({ message: {} })),
			get_meta: vi.fn(() => ({ fields: [] as unknown[] })),
			show_alert: vi.fn(),
			throw: vi.fn((message: string) => {
				throw new Error(message)
			}),
		};
	})

	it("marks dirty when markDirty is called", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		expect(store.dirty.value).toBe(false)
		store.markDirty()
		expect(store.dirty.value).toBe(true)
	})

	it("supports undo/redo history for layout changes", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.layout.value = { sections: [] } as any
		store.markDirty()
		const before = JSON.stringify(store.layout.value)

		store.layout.value = {
			sections: [
				{
					id: "s1",
					label: "Section",
					columns: [{ id: "c1", label: "", fields: [] }],
				},
			],
		} as any
		store.markDirty()
		const after = JSON.stringify(store.layout.value)
		expect(after).not.toBe(before)
		expect(store.canUndo.value).toBe(true)

		store.undo()
		expect(JSON.stringify(store.layout.value)).toBe(before)
		expect(store.canRedo.value).toBe(true)

		store.redo()
		expect(JSON.stringify(store.layout.value)).toBe(after)
	})
})
