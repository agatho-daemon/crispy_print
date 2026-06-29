import { describe, expect, it } from "vitest"
import { buildForegroundPlacements, resolveBrandingMode } from "../../typst/branding"
import { resolveTypstPaper } from "../../typst/page"

describe("typst page helpers", () => {
	it("uses explicit branding mode when provided", () => {
		const mode = resolveBrandingMode({ branding: { mode: "logo" } }, { image: "/files/lh.png" })
		expect(mode).toBe("logo")
	})

	it("builds QR placement without logo", () => {
		const lines = buildForegroundPlacements({
			presentation_settings: {},
			branding_mode: "none",
			qrEnabled: true,
			qrFilename: "qr.svg",
			qrSettings: { size: 10, dx: 0, dy: 0 },
		})
		expect(lines.length).toBe(1)
		expect(lines[0]).toContain('image("qr.svg"')
	})

	it("builds logo placement without QR", () => {
		const lines = buildForegroundPlacements({
			presentation_settings: {
				branding: { logo: { image: "/files/logo.png", size: 20, dx: 1, dy: 2 } },
			},
			branding_mode: "logo",
			qrEnabled: false,
			qrFilename: null,
			qrSettings: null,
		})
		expect(lines.length).toBe(1)
		expect(lines[0]).toContain('image("logo.png"')
	})

	it("maps UI page size labels to Typst paper identifiers", () => {
		expect(resolveTypstPaper("A4")).toBe("a4")
		expect(resolveTypstPaper("Letter")).toBe("us-letter")
		expect(resolveTypstPaper("Legal")).toBe("us-legal")
		expect(resolveTypstPaper("Tabloid")).toBe("us-tabloid")
		expect(resolveTypstPaper("Executive")).toBe("us-executive")
		expect(resolveTypstPaper("Foolscap Folio")).toBe("us-foolscap-folio")
		expect(resolveTypstPaper("Statement")).toBe("us-statement")
		expect(resolveTypstPaper("Ledger")).toBe("us-ledger")
		expect(resolveTypstPaper("Oficio")).toBe("us-oficio")
		expect(resolveTypstPaper("Gov Letter")).toBe("us-gov-letter")
		expect(resolveTypstPaper("Government Legal")).toBe("us-gov-legal")
		expect(resolveTypstPaper("Business Card")).toBe("us-business-card")
		expect(resolveTypstPaper("Digest")).toBe("us-digest")
		expect(resolveTypstPaper("Trade")).toBe("us-trade")
		expect(resolveTypstPaper("us-letter")).toBe("us-letter")
		expect(resolveTypstPaper("us-legal")).toBe("us-legal")
		expect(resolveTypstPaper("us-tabloid")).toBe("us-tabloid")
		expect(resolveTypstPaper("us-executive")).toBe("us-executive")
		expect(resolveTypstPaper("us-foolscap-folio")).toBe("us-foolscap-folio")
		expect(resolveTypstPaper("us-statement")).toBe("us-statement")
		expect(resolveTypstPaper("us-ledger")).toBe("us-ledger")
		expect(resolveTypstPaper("us-oficio")).toBe("us-oficio")
		expect(resolveTypstPaper("us-gov-letter")).toBe("us-gov-letter")
		expect(resolveTypstPaper("us-gov-legal")).toBe("us-gov-legal")
		expect(resolveTypstPaper("us-business-card")).toBe("us-business-card")
		expect(resolveTypstPaper("us-digest")).toBe("us-digest")
		expect(resolveTypstPaper("us-trade")).toBe("us-trade")
	})
})
