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
										table_columns: [{ fieldname: "item_code", label: "Item Code" }],
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
								fields: [{ fieldname: "intro", fieldtype: "Data" }],
							},
						],
					},
					{
						label: "One",
						columns: [
							{
								label: "",
								fields: [{ fieldname: "title", fieldtype: "Data" }],
							},
						],
						page_break: true,
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
})
