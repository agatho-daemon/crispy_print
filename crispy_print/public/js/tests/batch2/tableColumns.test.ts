import { describe, expect, it } from "vitest"
import { getDefaultAlignment } from "../../utils/tableColumns"

describe("table column helpers", () => {
	it("defaults numeric field types to right alignment", () => {
		expect(getDefaultAlignment("Int")).toBe("right")
		expect(getDefaultAlignment("Float")).toBe("right")
		expect(getDefaultAlignment("Currency")).toBe("right")
		expect(getDefaultAlignment("Percent")).toBe("right")
	})

	it("defaults non-numeric field types to left alignment", () => {
		expect(getDefaultAlignment("Data")).toBe("left")
		expect(getDefaultAlignment("Text")).toBe("left")
		expect(getDefaultAlignment(undefined)).toBe("left")
	})
})
