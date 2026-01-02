import { describe, expect, it } from "vitest"
import { buildForegroundPlacements, resolveBrandingMode } from "../../typst/branding"

describe("typst page helpers", () => {
	it("uses explicit branding mode when provided", () => {
		const mode = resolveBrandingMode({ brandingMode: "logo" }, { image: "/files/lh.png" })
		expect(mode).toBe("logo")
	})

	it("builds QR placement without logo", () => {
		const lines = buildForegroundPlacements({
			pageSettings: {},
			brandingMode: "none",
			qrEnabled: true,
			qrFilename: "qr.svg",
			qrSettings: { size: 10, dx: 0, dy: 0 },
		})
		expect(lines.length).toBe(1)
		expect(lines[0]).toContain('image("qr.svg"')
	})

	it("builds logo placement without QR", () => {
		const lines = buildForegroundPlacements({
			pageSettings: { logo: { image: "/files/logo.png", size: 20, dx: 1, dy: 2 } },
			brandingMode: "logo",
			qrEnabled: false,
			qrFilename: null,
			qrSettings: null,
		})
		expect(lines.length).toBe(1)
		expect(lines[0]).toContain('image("logo.png"')
	})
})
