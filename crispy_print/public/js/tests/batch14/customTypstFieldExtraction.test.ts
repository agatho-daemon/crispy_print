// Test custom Typst field extraction
import { describe, it, expect } from "vitest"
import { extractUsedFields } from "../../utils/layoutFieldExtractor"
import type { CrispyLayout } from "../../utils/layout"

describe("Custom Typst Field Extraction", () => {
	it("should extract fields from custom Typst code", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "customer",
									fieldtype: "Link",
									label: "Customer",
								},
								{
									fieldname: "custom_typst_field",
									fieldtype: "Typst",
									label: "Custom",
									raw_typst_field: `
										#text(weight: 700)[Grand Total: #doc.grand_total]
										#text[Paid Amount: #doc.paid_amount]
										#text[Balance: #{doc.outstanding_amount}]
									`,
								},
							],
						},
					],
				},
			],
		}

		const used = extractUsedFields(layout)

		// Should include regular fields
		expect(used.has("customer")).toBe(true)

		// Should include fields from custom Typst code
		expect(used.has("grand_total")).toBe(true)
		expect(used.has("paid_amount")).toBe(true)
		expect(used.has("outstanding_amount")).toBe(true)
	})

	it("should handle multiple custom Typst fields", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "typst1",
									fieldtype: "Typst",
									label: "Header",
									raw_typst_field: "#doc.supplier_name",
								},
								{
									fieldname: "typst2",
									fieldtype: "Typst",
									label: "Footer",
									raw_typst_field: "#doc.total_qty items",
								},
							],
						},
					],
				},
			],
		}

		const used = extractUsedFields(layout)

		expect(used.has("supplier_name")).toBe(true)
		expect(used.has("total_qty")).toBe(true)
	})

	it("should handle custom Typst with table field references", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "custom_table_summary",
									fieldtype: "Typst",
									label: "Table Summary",
									raw_typst_field: `
										#for item in doc.items [
											#text[#item.item_name: #item.qty]
										]
									`,
								},
							],
						},
					],
				},
			],
		}

		const used = extractUsedFields(layout)

		// Should extract the items array field
		expect(used.has("items")).toBe(true)
	})

	it("should handle empty or missing raw_typst_field", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "empty_typst",
									fieldtype: "Typst",
									label: "Empty",
									raw_typst_field: "",
								},
								{
									fieldname: "no_code",
									fieldtype: "Typst",
									label: "No Code",
									// No raw_typst_field property
								},
							],
						},
					],
				},
			],
		}

		const used = extractUsedFields(layout)

		// Should not throw errors
		expect(used.size).toBeGreaterThanOrEqual(5) // At least essential fields
	})
})
