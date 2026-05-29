import { beforeEach, describe, expect, it, vi } from "vitest"

const getLetterheadDoc = vi.fn(async (name: string) => ({ name, image: `/files/${name}.png` }))
const getApplicableTypstBlocks = vi.fn(async (_args: any) => [
	{
		name: "invoice_header",
		block_key: "invoice_header",
		block_name: "Invoice Header",
		typst_code: "#text[#doc.customer_name]",
	},
])
const getCrispyFormat = vi.fn(async (_name: string) => ({
	name: "Block Format",
	doc_type: "Sales Invoice",
	layout_json: JSON.stringify({
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
	}),
	presentation_settings: "{}",
}))

vi.mock("../../api/crispy", () => ({
	getApplicableTypstBlocks: (args: any) => getApplicableTypstBlocks(args),
	getCrispyFormat: (name: string) => getCrispyFormat(name),
	getLetterheadDoc: (name: string) => getLetterheadDoc(name),
}))

describe("formatLoader letterhead cache", async () => {
	const { clearLetterheadCache, loadFormatData, resolveLetterheadDoc } = await import(
		"../../utils/formatLoader"
	)

	beforeEach(() => {
		getLetterheadDoc.mockClear()
		getApplicableTypstBlocks.mockClear()
		getCrispyFormat.mockClear()
		clearLetterheadCache()
	})

	it("returns null for empty names", async () => {
		await expect(resolveLetterheadDoc("")).resolves.toBeNull()
		await expect(resolveLetterheadDoc(null)).resolves.toBeNull()
		await expect(resolveLetterheadDoc(undefined)).resolves.toBeNull()
	})

	it("caches letterhead docs", async () => {
		const first = await resolveLetterheadDoc("Letterhead A")
		const second = await resolveLetterheadDoc("Letterhead A")
		expect(first).toEqual(second)
		expect(getLetterheadDoc).toHaveBeenCalledTimes(1)
	})

	it("hydrates Crispy Typst Block references while loading format data", async () => {
		const data = await loadFormatData("Block Format")
		const field = data?.layout?.sections?.[0]?.columns?.[0]?.fields?.[0] as any

		expect(getApplicableTypstBlocks).toHaveBeenCalledWith({ doctype: "Sales Invoice" })
		expect(field.crispy_typst_block_name).toBe("Invoice Header")
		expect(field.crispy_typst_block_code).toContain("#doc.customer_name")
	})
})
