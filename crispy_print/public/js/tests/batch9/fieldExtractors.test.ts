import { describe, expect, it } from "vitest"
import { extractUsedFields, filterDocumentFields } from "../../utils/layoutFieldExtractor"
import { extractUsedFieldsFromTypstSource } from "../../utils/typstFieldExtractor"

describe("layout field extractor", () => {
	it("extracts fieldnames and table columns", () => {
		const used = extractUsedFields({
			sections: [
				{
					label: "Main",
					columns: [
						{
							label: "",
							fields: [
								{ fieldname: "customer", fieldtype: "Data", label: "Customer" },
								{
									fieldname: "items",
									fieldtype: "Table",
									label: "Items",
									table_columns: [
										{ fieldname: "item_code", label: "Item Code", fieldtype: "Data" },
									],
								},
							],
						},
					],
				},
			],
		})

		expect(used.has("customer")).toBe(true)
		expect(used.has("items")).toBe(true)
		expect(used.has("item_code")).toBe(true)
		expect(used.has("doctype")).toBe(true)
	})

	it("filters document fields with child table rules", () => {
		const used = new Set(["customer", "items.item_code"])
		const doc = {
			name: "INV-1",
			doctype: "Sales Invoice",
			customer: "Alice",
			items: [
				{ item_code: "A-1", qty: 2, name: "row1" },
				{ item_code: "B-2", qty: 3, name: "row2" },
			],
		}

		const filtered = filterDocumentFields(doc, used)
		expect(filtered.customer).toBe("Alice")
		expect(filtered.items[0].item_code).toBe("A-1")
		expect(filtered.items[0].qty).toBeUndefined()
		expect(filtered.items[0].name).toBe("row1")
	})

	it("includes all child fields when flag is set", () => {
		const used = new Set(["items"])
		const doc = { items: [{ item_code: "A-1", qty: 2 }] }
		const filtered = filterDocumentFields(doc, used, { includeAllChildFieldsIfUnspecified: true })
		expect(filtered.items[0].item_code).toBe("A-1")
		expect(filtered.items[0].qty).toBe(2)
	})

	it("extracts document fields from Crispy Typst Block code", () => {
		const used = extractUsedFields({
			sections: [
				{
					label: "Blocks",
					columns: [
						{
							label: "",
							fields: [
								{
									fieldname: "_crispy_typst_block",
									fieldtype: "Crispy Typst Block",
									label: "Crispy Typst Block",
									crispy_typst_block: "invoice_totals",
									crispy_typst_block_code: "#text[#doc.grand_total #doc.customer_name]",
								},
							],
						},
					],
				},
			],
		} as any)

		expect(used.has("grand_total")).toBe(true)
		expect(used.has("customer_name")).toBe(true)
		expect(used.has("_crispy_typst_block")).toBe(false)
	})
})

describe("typst field extractor", () => {
	it("extracts fields from hints and doc references", () => {
		const source = `
// fields: name, items.item_code
#text(doc.name)
#text(doc["customer"])
`
		const fields = extractUsedFieldsFromTypstSource(source)
		expect(fields.has("name")).toBe(true)
		expect(fields.has("items.item_code")).toBe(true)
		expect(fields.has("customer")).toBe(true)
	})
})
