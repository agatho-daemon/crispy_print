import { describe, expect, it } from "vitest"
import { parseCrispyFormatDoc } from "../../utils/formatLoader"
import { default_presentation_settings } from "../../utils/presentation_settings"

describe("format loader resilience", () => {
	it("falls back when layout_json is invalid", () => {
		const parsed = parseCrispyFormatDoc({
			layout_json: "{bad json",
			presentation_settings: JSON.stringify({
				page: { size: "A4", orientation: "portrait", margins: { top: 25, bottom: 20, left: 20, right: 20 } },
			}),
		} as any)
		expect(parsed.layout).toBeNull()
		expect(parsed.presentation_settings.page.size).toBe("A4")
	})

	it("keeps defaults when presentation_settings missing", () => {
		const parsed = parseCrispyFormatDoc({} as any)
		expect(parsed.presentation_settings.page.size).toBe(default_presentation_settings.page.size)
	})
})
