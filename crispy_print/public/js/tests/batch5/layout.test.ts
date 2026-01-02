import { describe, expect, it } from "vitest"
import { serializeLayout, type CrispyLayout } from "../../utils/layout"

describe("layout serialization", () => {
	it("serializes layout with sections and columns", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section 1",
					columns: [{ label: "Col 1", fields: [] }],
				},
			],
		}
		const json = serializeLayout(layout)
		expect(json).toContain('"sections"')
		expect(json).toContain('"columns"')
	})

	it("drops has_fields from sections", () => {
		const layout: CrispyLayout = {
			sections: [
				{
					label: "Section 1",
					columns: [{ label: "Col 1", fields: [] }],
					has_fields: true as any,
				},
			],
		}
		const json = serializeLayout(layout)
		expect(json).not.toContain("has_fields")
	})
})
