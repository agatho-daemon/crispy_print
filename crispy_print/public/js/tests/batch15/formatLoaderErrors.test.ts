import { describe, expect, it } from "vitest"

import { parseCrispyFormatDoc } from "../../utils/formatLoader"
import { defaultPageSettings } from "../../utils/pageSettings"

describe("formatLoader error handling", () => {
	it("falls back to default page settings on invalid page_settings JSON", () => {
		const parsed = parseCrispyFormatDoc({
			name: "Bad Settings",
			page_settings: "{bad json",
		} as any)
		expect(parsed.pageSettings.pageSize).toBe(defaultPageSettings.pageSize)
	})

	it("returns null layout when layout_json is invalid", () => {
		const parsed = parseCrispyFormatDoc({
			name: "Bad Layout",
			layout_json: "{bad json",
		} as any)
		expect(parsed.layout).toBeNull()
	})
})
