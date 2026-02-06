// Test that raw_typst_field content is rendered in Typst output
import { describe, it, expect } from "vitest"
import { translateJSONToTypst } from "../../typst/JSONToTypst"
import type { CrispyLayout } from "../../utils/layout"

describe("Raw Typst Field Rendering", () => {
	it("should render raw_typst_field content in Typst output", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section 1",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "custom_header",
									fieldtype: "Typst",
									label: "Custom Header",
									raw_typst_field: `#text(weight: 700, size: 14pt)[My Custom Header]`,
								},
								{
									fieldname: "customer_name",
									fieldtype: "Data",
									label: "Customer",
								},
							],
						},
					],
				},
			],
		}

		const typst = translateJSONToTypst(layout, null, "Sales Invoice", null, {})

		// Should contain the raw Typst code
		expect(typst).toContain("#text(weight: 700, size: 14pt)[My Custom Header]")
		// Should NOT contain the empty comment
		expect(typst).not.toContain("// Custom Typst (empty)")
	})

	it("should render comment when raw_typst_field is empty", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section 1",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "custom_empty",
									fieldtype: "Typst",
									label: "Empty Custom",
									raw_typst_field: "",
								},
							],
						},
					],
				},
			],
		}

		const typst = translateJSONToTypst(layout, null, "Sales Invoice", null, {})

		expect(typst).toContain("// USER CUSTOM SECTION")
		expect(typst).toContain("// Add your custom styling below")
	})

	it("should render comment when raw_typst_field is missing", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section 1",
					columns: [
						{
							label: "Column",
							fields: [
								{
									fieldname: "custom_missing",
									fieldtype: "Typst",
									label: "Missing Custom",
									// No raw_typst_field property
								},
							],
						},
					],
				},
			],
		}

		const typst = translateJSONToTypst(layout, null, "Sales Invoice", null, {})

		expect(typst).toContain("// USER CUSTOM SECTION")
		expect(typst).toContain("// Add your custom styling below")
	})
})
