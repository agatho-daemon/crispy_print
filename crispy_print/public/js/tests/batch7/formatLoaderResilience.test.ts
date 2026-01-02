import { describe, expect, it } from "vitest"
import { parseCrispyFormatDoc } from "../../utils/formatLoader"
import { defaultPageSettings } from "../../utils/pageSettings"

describe("format loader resilience", () => {
	it("falls back when layout_json is invalid", () => {
		const parsed = parseCrispyFormatDoc({
			layout_json: "{bad json",
			page_settings: JSON.stringify({ pageSize: "A4" }),
		} as any)
		expect(parsed.layout).toBeNull()
		expect(parsed.pageSettings.pageSize).toBe("A4")
	})

	it("keeps defaults when page_settings missing", () => {
		const parsed = parseCrispyFormatDoc({} as any)
		expect(parsed.pageSettings.pageSize).toBe(defaultPageSettings.pageSize)
	})
})
