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
const getCrispyFormatsForDoctype = vi.fn(async (_doctype: string, _args?: any) => [
	{ name: "Company Format", doc_type: "Sales Invoice", company: "ACME" },
])
const getCrispyFormat = vi.fn(async (_name: string, _context?: any) => ({
	name: "Block Format",
	doc_type: "Sales Invoice",
	company: "ACME",
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
	getCrispyFormat: (name: string, context?: any) => getCrispyFormat(name, context),
	getCrispyFormatsForDoctype: (doctype: string, args?: any) =>
		getCrispyFormatsForDoctype(doctype, args),
	getLetterheadDoc: (name: string) => getLetterheadDoc(name),
}))

describe("formatLoader letterhead cache", async () => {
	const { clearLetterheadCache, loadFormatData, resolveLetterheadDoc } = await import(
		"../../utils/formatLoader"
	)

	beforeEach(() => {
		getLetterheadDoc.mockClear()
		getApplicableTypstBlocks.mockClear()
		getCrispyFormatsForDoctype.mockClear()
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
		const data = await loadFormatData("Block Format", { company: "ACME" })
		const field = data?.layout?.sections?.[0]?.columns?.[0]?.fields?.[0] as any

		expect(getCrispyFormat).toHaveBeenCalledWith("Block Format", { company: "ACME" })
		expect(getApplicableTypstBlocks).toHaveBeenCalledWith({ doctype: "Sales Invoice", company: "ACME" })
		expect(field.crispy_typst_block_name).toBe("Invoice Header")
		expect(field.crispy_typst_block_code).toContain("#doc.customer_name")
	})

	it("passes company when loading formats for a DocType", async () => {
		const { getFormatsForDoctype } = await import("../../utils/formatLoader")

		const rows = await getFormatsForDoctype("Sales Invoice", "ACME")

		expect(rows[0].name).toBe("Company Format")
		expect(getCrispyFormatsForDoctype).toHaveBeenCalledWith("Sales Invoice", { company: "ACME" })
	})
})
