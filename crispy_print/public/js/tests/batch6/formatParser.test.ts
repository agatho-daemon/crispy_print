import { describe, expect, it } from "vitest"
import { defaultPageSettings, type PageSettings } from "../../utils/pageSettings"
import { parseCrispyFormatDoc } from "../../utils/formatLoader"

describe("formatLoader.parseCrispyFormatDoc", () => {
	it("parses page settings JSON and merges defaults", () => {
		const input = {
			page_settings: JSON.stringify({
				pageSize: "A5",
				margins: { top: 10 },
				qr: { size: 20 },
			}),
		}
		const parsed = parseCrispyFormatDoc(input as any)
		const settings = parsed.pageSettings as PageSettings
		expect(settings.pageSize).toBe("A5")
		expect(settings.margins.top).toBe(10)
		expect(settings.margins.left).toBe(defaultPageSettings.margins.left)
		expect(settings.qr?.size).toBe(20)
	})

	it("falls back to defaults for invalid JSON", () => {
		const parsed = parseCrispyFormatDoc({ page_settings: "{bad json" } as any)
		expect(parsed.pageSettings.pageSize).toBe(defaultPageSettings.pageSize)
	})
})
