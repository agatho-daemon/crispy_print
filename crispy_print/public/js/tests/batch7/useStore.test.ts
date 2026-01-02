import { describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: async () => ({
		name: "Test Format",
		doc_type: "Sales Invoice",
		layout_json: JSON.stringify({ sections: [] }),
		page_settings: JSON.stringify({ pageSize: "A4" }),
		raw_typst: 0,
		qrcode: 0,
	}),
	saveCrispyFormat: async () => {},
}))

vi.mock("../../api/frappe", () => ({
	withDoctype: async () => {},
}))

vi.mock("../../utils/formatLoader", async (orig) => {
	const actual = await orig()
	return {
		...actual,
		parseCrispyFormatDoc: () => ({
			layout: { sections: [] },
			pageSettings: {
				pageSize: "A4",
				orientation: "portrait",
				margins: { top: 1, bottom: 1, left: 1, right: 1 },
			},
			docHeader: "",
			formatDoc: {},
		}),
	}
})

describe("useStore", () => {
	it("marks dirty when markDirty is called", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		expect(store.dirty.value).toBe(false)
		store.markDirty()
		expect(store.dirty.value).toBe(true)
	})
})
