import { describe, expect, it } from "vitest"
import { deserializeLayout } from "../../utils/layout"

describe("layout utils", () => {
	it("deserializes a basic layout JSON", () => {
		const json = JSON.stringify({ sections: [{ label: "A", columns: [] }] })
		const layout = deserializeLayout(json)
		expect(layout).not.toBeNull()
		if (!layout) throw new Error("Expected deserialized layout")
		expect(layout.sections.length).toBe(1)
	})
})
