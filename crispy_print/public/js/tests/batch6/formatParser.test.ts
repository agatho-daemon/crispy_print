import { describe, expect, it } from "vitest"
import { default_presentation_settings, type PresentationSettings } from "../../utils/presentation_settings"
import { parseCrispyFormatDoc } from "../../utils/formatLoader"

describe("formatLoader.parseCrispyFormatDoc", () => {
	it("parses presentation settings JSON and merges defaults", () => {
		const input = {
			presentation_settings: JSON.stringify({
				page: { size: "A5", margins: { top: 10 } },
				qr: { size: 20 },
			}),
		}
		const parsed = parseCrispyFormatDoc(input as any)
		const settings = parsed.presentation_settings as PresentationSettings
		expect(settings.page.size).toBe("A5")
		expect(settings.page.margins.top).toBe(10)
		expect(settings.page.margins.left).toBe(default_presentation_settings.page.margins.left)
		expect(settings.qr?.size).toBe(20)
	})

	it("falls back to defaults for invalid JSON", () => {
		const parsed = parseCrispyFormatDoc({ presentation_settings: "{bad json" } as any)
		expect(parsed.presentation_settings.page.size).toBe(default_presentation_settings.page.size)
	})
})
