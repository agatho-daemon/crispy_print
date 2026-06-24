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
											{ fieldname: "item_code", label: "Item Code", fieldtype: "Data" },
											{ fieldname: "description", label: "Description", fieldtype: "Data", width: "1fr" },
											{ fieldname: "qty", label: "Qty", fieldtype: "Float" },
											{ fieldname: "discount_amount", label: "Discount Amount", fieldtype: "Currency" },
											{ fieldname: "rate", label: "Rate", fieldtype: "Currency" },
											{ fieldname: "amount", label: "Amount", fieldtype: "Currency" },
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
				items: [{
					item_code: "STO-0001",
					description: "Wireless Keyboard",
					qty: "1",
					uom: "Nos",
					discount_amount: "KWD -1.000",
					rate: "KWD 10.000",
					amount: "KWD 10.000",
				}],
				taxes: [{ tax_amount: "0.00" }],
			},
			{
				printBehavior: {
					compact_item_print: 1,
					print_uom_after_quantity: 0,
					print_taxes_with_zero_amount: 0,
				},
			},
		)

		expect(typst).toContain("inset: tableCellInset")
		expect(typst).toContain("[#if \"description\" in row and row.description != \"\"")
		expect(typst).toContain("[Item Code:]")
		expect(typst).toContain("[Discount Amount:]")
		expect(typst).not.toContain("[#text(..tableHeaderStyle)[Item Code]]")
		expect(typst).not.toContain("[#text(..tableHeaderStyle)[Discount Amount]]")
		expect(typst).toContain("#let tableCellLabelEnabled = true")
		expect(typst).toContain("fill: rgb(\"475569\")")
		expect(typst).toContain("table.cell(colspan: 2)[#text(..tableHeaderStyle)[Qty]]")
		expect(typst).toContain("cp_measure_label_table_cell(cp_quantity_parts(row, row.qty).label)")
		expect(typst).toContain("cp_measure_value_table_cell(cp_quantity_parts(row, row.qty).value)")
		expect(typst).toContain("#let cp_print_uom_after_quantity = false")
		expect(typst).toContain("baseline: -2pt")
		expect(typst).toContain("cp_measure_label_table_cell(cp_currency_parts(row.rate).label)")
		expect(typst).toContain("cp_measure_value_table_cell(cp_currency_parts(row.rate).value)")
		expect(typst).toContain("cp_currency_parts(value)")
		expect(typst).toContain("doc.taxes.filter(row => not cp_is_zero_tax_row(row))")
	})

	it("can disable split table cell labels while preserving custom label style constants", () => {
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
											{ fieldname: "rate", label: "Rate", fieldtype: "Currency" },
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
				items: [{ qty: "1", uom: "Nos", rate: "KWD 10.000" }],
			},
			{
				table: {
					cellLabel: {
						enabled: false,
						fontSize: "7pt",
						fontWeight: "medium",
						baselineShift: 1.5,
						color: "#334155",
					},
				},
				printBehavior: {
					print_uom_after_quantity: 1,
				},
			},
		)

		expect(typst).toContain("#let tableCellLabelEnabled = false")
		expect(typst).toContain("size: 7pt")
		expect(typst).toContain("baseline: 1.5pt")
		expect(typst).toContain("fill: rgb(\"334155\")")
		expect(typst).not.toContain("table.cell(colspan: 2)[#text(..tableHeaderStyle)[Qty]]")
		expect(typst).not.toContain("cp_measure_label_table_cell(cp_quantity_parts(row, row.qty).label)")
		expect(typst).toContain("[#text(..tableBodyStyle)[#cp_quantity_inline(row, row.qty)]]")
		expect(typst).toContain("if cp_print_uom_after_quantity and uom != \"\"")
		expect(typst).toContain("uom + \" \" + str(value)")
		expect(typst).toContain("[#text(..tableBodyStyle)[#row.rate]]")
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
