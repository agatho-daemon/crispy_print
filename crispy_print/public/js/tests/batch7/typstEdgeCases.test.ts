import { describe, expect, it } from "vitest"
import { translateJSONToTypst } from "../../typst/JSONToTypst"

describe("Typst edge cases", () => {
	it("emits table layout when a table field is present", () => {
		const typst = translateJSONToTypst(
			{
				sections: [
					{
						label: "Items",
						columns: [
							{
								label: "Col 1",
								fields: [
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
			},
			null,
			"Sales Invoice",
			{ name: "INV-0001", items: [] },
			{}
		)
		expect(typst).toContain("table(")
	})

	it("emits page break when section has page_break", () => {
		const typst = translateJSONToTypst(
			{
				sections: [
					{
						label: "Intro",
						columns: [
							{
									label: "",
									fields: [{ fieldname: "intro", fieldtype: "Data", label: "Intro" }],
								},
							],
							page_break: true,
					},
					{
						label: "One",
						columns: [
							{
								label: "",
								fields: [{ fieldname: "title", fieldtype: "Data", label: "Title" }],
							},
						],
					},
				],
			},
			null,
			"Document",
			{ name: "DOC-1" },
			{}
		)
		expect(typst).toContain("#pagebreak()")
	})

	it("escapes special characters in labels", () => {
		const typst = translateJSONToTypst(
			{
				sections: [
					{
						label: "Section [A]",
						columns: [
							{
								label: "",
								fields: [
									{
										fieldname: "title",
										fieldtype: "Data",
										label: "Consider Tax or Charge for [X]",
									},
									{
										fieldname: "items",
										fieldtype: "Table",
										label: "Items",
										table_columns: [
											{ fieldname: "col_a", label: "Add or Deduct [Y]", fieldtype: "Data" },
										],
									},
								],
							},
						],
					},
				],
			},
			null,
			"Document",
			{ name: "DOC-1", title: "Doc", items: [{ col_a: "A" }] },
			{}
		)
		expect(typst).toContain("Section \\[A\\]")
		expect(typst).toContain("Consider Tax or Charge for \\[X\\]")
		expect(typst).toContain("Add or Deduct \\[Y\\]")
	})

	it("honors print behavior options for item quantity and zero tax rows", () => {
		const typst = translateJSONToTypst(
			{
				sections: [
					{
						label: "Lines",
						columns: [
							{
								label: "",
								fields: [
									{
										fieldname: "items",
										fieldtype: "Table",
										label: "Items",
										table_columns: [
											{ fieldname: "qty", label: "Qty", fieldtype: "Float" },
										],
									},
									{
										fieldname: "taxes",
										fieldtype: "Table",
										label: "Taxes",
										table_columns: [
											{ fieldname: "tax_amount", label: "Tax Amount", fieldtype: "Currency" },
										],
									},
								],
							},
						],
					},
				],
			},
			null,
			"Sales Invoice",
			{
				name: "INV-0001",
				items: [{ qty: "1", uom: "Nos" }],
				taxes: [{ tax_amount: "0.00" }],
			},
			{
				printBehavior: {
					compact_item_print: 1,
					print_uom_after_quantity: 1,
					print_taxes_with_zero_amount: 0,
				},
			},
		)

		expect(typst).toContain("inset: (x: 1pt, y: 1pt)")
		expect(typst).toContain('row.uom != ""')
		expect(typst).toContain("doc.taxes.filter(row => not cp_is_zero_tax_row(row))")
	})

	it("adds a draft heading when the document print context requests it", () => {
		const typst = translateJSONToTypst(
			{ sections: [] },
			null,
			"Sales Invoice",
			{
				name: "INV-DRAFT",
				__crispy_print_context: { show_draft_heading: true },
			},
			{},
		)

		expect(typst).toContain("[Draft]")
	})
})
