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
})
