import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: async () => ({
		name: "Test Format",
		doc_type: "Sales Invoice",
		layout_json: JSON.stringify({ sections: [] }),
		presentation_settings: JSON.stringify({
			page: { size: "A4", orientation: "portrait", margins: { top: 1, bottom: 1, left: 1, right: 1 } },
			branding: { mode: "none", letterhead: "", letterhead_image: "", logo: { company: "", image: "", size: 25, dx: 0, dy: 0 } },
		}),
		raw_typst: 0,
	}),
	getApplicableTypstBlocks: async () => [
		{
			name: "invoice_header",
			block_key: "invoice_header",
			block_name: "Invoice Header",
			category: "Header",
			description: "Header block",
			typst_code: "#text[#doc.customer_name]",
			version: "1.0.0",
		},
	],
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
				presentation_settings: {
				page: { size: "A4", orientation: "portrait", margins: { top: 1, bottom: 1, left: 1, right: 1 } },
				branding: { mode: "none", letterhead: "", letterhead_image: "", logo: { company: "", image: "", size: 25, dx: 0, dy: 0 } },
				language: "en",
			},
			docHeader: "",
			formatDoc: {},
		}),
	}
})

describe("useStore", () => {
	beforeEach(() => {
		vi.resetModules();
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

	it("adds Crispy Typst Block to fields and resolves block references", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		;(globalThis as any).frappe.get_meta = vi.fn(() => ({
			fields: [
				{
					fieldname: "customer_name",
					label: "Customer Name",
					fieldtype: "Data",
				},
			],
		}))

		await store.fetch("Test Format")

		expect(
			store.fields.value.some(
				(field: any) =>
					field.fieldname === "_crispy_typst_block" &&
					field.fieldtype === "Crispy Typst Block"
			)
		).toBe(true)

		store.layout.value = {
			sections: [
				{
					label: "",
					columns: [
						{
							label: "",
							fields: [
								{
									fieldname: "_crispy_typst_block",
									fieldtype: "Crispy Typst Block",
									label: "Crispy Typst Block",
									crispy_typst_block: "invoice_header",
								},
							],
						},
					],
				},
			],
		} as any

		store.resolveLayoutTypstBlocks()

		const field = store.layout.value?.sections[0].columns[0].fields[0] as any
		expect(field.crispy_typst_block_name).toBe("Invoice Header")
		expect(field.crispy_typst_block_code).toContain("#doc.customer_name")
	})
})
