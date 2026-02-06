import { describe, expect, it } from "vitest"
import { deserializeLayout, normalizeLayout, serializeLayout } from "../../utils/layout"

describe("layout round trip", () => {
	it("normalizes and preserves core structure", () => {
		const layout = {
			header: "",
			sections: [
				{
					label: "Section",
					columns: [
						{
							label: "",
							fields: [
								{ fieldname: "amount", fieldtype: "Currency", label: "Amount" },
								{ fieldname: "", fieldtype: "Data", label: "Empty" },
							],
						},
					],
					has_fields: true,
				},
			],
		}

		const serialized = serializeLayout(layout as any)
		const parsed = deserializeLayout(serialized)
		const normalized = normalizeLayout(layout as any)

		expect(serialized).not.toContain("has_fields")
		expect(parsed?.sections?.length).toBe(1)
	const sectionId = parsed?.sections?.[0]?.id
	expect(typeof sectionId === "string" || typeof sectionId === "number").toBe(true)
		expect(parsed?.sections?.[0]?.columns?.[0]?.fields?.length).toBe(1)
		expect(normalized.sections[0].columns[0].fields[0].align).toBe("right")
	})
})
