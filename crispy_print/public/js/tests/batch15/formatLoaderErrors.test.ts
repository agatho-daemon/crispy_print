import { describe, expect, it } from "vitest"

import { parseCrispyFormatDoc } from "../../utils/formatLoader"
import { default_presentation_settings } from "../../utils/presentation_settings"

describe("formatLoader error handling", () => {
	it("falls back to default presentation settings on invalid presentation_settings JSON", () => {
		const parsed = parseCrispyFormatDoc({
			name: "Bad Settings",
			presentation_settings: "{bad json",
		} as any)
		expect(parsed.presentation_settings.page.size).toBe(default_presentation_settings.page.size)
	})

	it("returns null layout when layout_json is invalid", () => {
		const parsed = parseCrispyFormatDoc({
			name: "Bad Layout",
			layout_json: "{bad json",
		} as any)
		expect(parsed.layout).toBeNull()
	})
})
