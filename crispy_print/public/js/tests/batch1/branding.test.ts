import { describe, expect, it } from "vitest"
import {
	buildForegroundPlacements,
	getLetterheadFilename,
	resolveBrandingImage,
	resolveBrandingMode,
} from "../../typst/branding"

describe("branding helpers", () => {
	it("defaults to none when no branding is set", () => {
		expect(resolveBrandingMode({}, null)).toBe("none")
		expect(getLetterheadFilename({}, null)).toBe("")
		expect(resolveBrandingImage({}, null)).toBeNull()
	})

	it("detects letterhead mode and filename", () => {
		const letterhead = { image: "/files/letterhead.png" }
		expect(resolveBrandingMode({}, letterhead)).toBe("letterhead")
		expect(getLetterheadFilename({}, letterhead)).toBe("letterhead.png")
		expect(resolveBrandingImage({}, letterhead)).toBe("/files/letterhead.png")
	})

	it("detects logo mode and ignores letterhead", () => {
		const presentation_settings = {
			branding: { mode: "logo", logo: { image: "/files/logo.png" } },
		}
		const letterhead = { image: "/files/letterhead.png" }
		expect(resolveBrandingMode(presentation_settings, letterhead)).toBe("logo")
		expect(getLetterheadFilename(presentation_settings, letterhead)).toBe("")
		expect(resolveBrandingImage(presentation_settings, letterhead)).toBe("/files/logo.png")
	})

	it("builds foreground placements for logo and QR", () => {
		const lines = buildForegroundPlacements({
			presentation_settings: {
				branding: { logo: { image: "/files/logo.png", size: 20, dx: 1, dy: 2 } },
			},
			branding_mode: "logo",
			qrEnabled: true,
			qrFilename: "doc-qr.svg",
			qrSettings: { size: 15, dx: 0, dy: 5 },
		})
		expect(lines.length).toBe(2)
		expect(lines[0]).toContain('image("logo.png"')
		expect(lines[1]).toContain('image("doc-qr.svg"')
	})
})
