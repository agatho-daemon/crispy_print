import { describe, expect, it } from "vitest"
import { translateJSONToTypst } from "../../typst/JSONToTypst"

describe("JSONToTypst translator", () => {
	it("emits page setup and header/footer bindings", () => {
		const typst = translateJSONToTypst(
			{ sections: [] },
			null,
			"Sales Invoice",
			{ name: "INV-0001" },
			{
				pageSize: "A4",
				margins: { top: 10, bottom: 10, left: 10, right: 10 },
				docHeader: "#let header_block = []",
				docFooter: "#let footer_block = []",
			}
		)
		expect(typst).toContain("#set page(")
		expect(typst).toContain("header: header_block")
		expect(typst).toContain("footer: footer_block")
	})
})
