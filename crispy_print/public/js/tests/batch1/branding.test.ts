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
		const pageSettings = { brandingMode: "logo", logo: { image: "/files/logo.png" } }
		const letterhead = { image: "/files/letterhead.png" }
		expect(resolveBrandingMode(pageSettings, letterhead)).toBe("logo")
		expect(getLetterheadFilename(pageSettings, letterhead)).toBe("")
		expect(resolveBrandingImage(pageSettings, letterhead)).toBe("/files/logo.png")
	})

	it("builds foreground placements for logo and QR", () => {
		const lines = buildForegroundPlacements({
			pageSettings: { logo: { image: "/files/logo.png", size: 20, dx: 1, dy: 2 } },
			brandingMode: "logo",
			qrEnabled: true,
			qrFilename: "doc-qr.svg",
			qrSettings: { size: 15, dx: 0, dy: 5 },
		})
		expect(lines.length).toBe(2)
		expect(lines[0]).toContain('image("logo.png"')
		expect(lines[1]).toContain('image("doc-qr.svg"')
	})
})
