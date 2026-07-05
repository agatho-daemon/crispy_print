import { describe, expect, it } from "vitest"
import { getRawTypstInsertText } from "../../utils/rawTypstInsert"

describe("raw Typst insert helper", () => {
	it("inserts document fields through doc accessors", () => {
		expect(
			getRawTypstInsertText({
				fieldname: "customer",
				label: "Customer",
				fieldtype: "Data",
			})
		).toBe("#doc.customer")
	})

	it("inserts empty Crispy Typst Block helper calls for the author to fill", () => {
		expect(
			getRawTypstInsertText({
				fieldname: "_crispy_typst_block",
				label: "Crispy Typst Block",
				fieldtype: "Crispy Typst Block",
			})
		).toBe('#crispy_block("")')
	})

	it("inserts empty Crispy Image helper calls for the author to fill", () => {
		expect(
			getRawTypstInsertText({
				fieldname: "_crispy_image",
				label: "Crispy Image",
				fieldtype: "Crispy Image",
			})
		).toBe('#crispy_image("")')
	})

	it("does not treat builder-only fields as document fields", () => {
		expect(
			getRawTypstInsertText({
				fieldname: "_typst_snippet",
				label: "Custom Typst",
				fieldtype: "Typst",
				raw_typst_field: "#text[custom]",
			})
		).toBe("#text[custom]")
		expect(
			getRawTypstInsertText({
				fieldname: "empty",
				label: "Empty",
				fieldtype: "Empty",
			})
		).toBe("[]")
		expect(
			getRawTypstInsertText({
				fieldname: "spacer",
				label: "Spacer",
				fieldtype: "Spacer",
			})
		).toBe("#v(1em)")
		expect(
			getRawTypstInsertText({
				fieldname: "divider",
				label: "Divider",
				fieldtype: "Divider",
			})
		).toBe("#line(length: 100%, stroke: 0.5pt + gray)")
	})
})
