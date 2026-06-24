import { describe, expect, it } from "vitest"
import {
	default_presentation_settings,
	ensure_logo_settings,
	ensure_qr_settings,
	ensure_table_settings,
	ensure_typography,
	merge_presentation_settings,
} from "../../utils/presentation_settings"

describe("presentation_settings helpers", () => {
	it("ensures QR settings defaults", () => {
		const settings: any = { page: { size: "A4", orientation: "portrait", margins: {} }, branding: {} }
		const qr = ensure_qr_settings(settings)
		expect(qr.size).toBe(15)
		expect(qr.dx).toBe(0)
		expect(qr.dy).toBe(0)
		expect(Array.isArray(qr.fields)).toBe(true)
		expect(qr.sourceMode).toBe("")
	})

	it("ensures logo settings defaults", () => {
		const settings: any = { page: { size: "A4", orientation: "portrait", margins: {} }, branding: {} }
		const logo = ensure_logo_settings(settings)
		expect(logo.company).toBe("")
		expect(logo.image).toBe("")
		expect(logo.size).toBe(25)
		expect(logo.dx).toBe(0)
		expect(logo.dy).toBe(0)
	})

	it("ensures typography defaults", () => {
		const settings: any = { page: { size: "A4", orientation: "portrait", margins: {} }, branding: {} }
		const typography = ensure_typography(settings)
		expect(typography.fieldLabel).toBeDefined()
		expect(typography.fieldValue).toBeDefined()
		expect(typography.sectionLabel).toBeDefined()
	})

	it("ensures table settings defaults", () => {
		const settings: any = { page: { size: "A4", orientation: "portrait", margins: {} }, branding: {} }
		const table = ensure_table_settings(settings)
		expect(table.inset.top).toBeDefined()
		expect(table.stroke.width).toBeDefined()
		expect(table.header.backgroundColor).toBeDefined()
		expect(table.stripe.enabled).toBeDefined()
		expect(table.cellLabel.enabled).toBe(true)
		expect(table.cellLabel.color).toBe("#475569")
		expect(table.typography.header).toBeDefined()
		expect(table.typography.body).toBeDefined()
	})

	it("merges overrides with defaults", () => {
		const merged = merge_presentation_settings(default_presentation_settings, {
			page: { margins: { top: 10, bottom: 20, left: 30, right: 40 } } as any,
			qr: { size: 20, dx: 0, dy: 0, fields: [], enabled: true, sourceMode: "basic" },
			branding: { logo: { company: "Acme", image: "", size: 25, dx: 0, dy: 0 } } as any,
			table: {
				stroke: { width: 1, color: "#000000" },
				cellLabel: { enabled: false, baselineShift: 1, color: "#334155" },
			} as any,
		})
		expect(merged.page.margins.top).toBe(10)
		expect(merged.page.margins.left).toBe(30)
		expect(merged.qr?.size).toBe(20)
		expect(merged.qr?.sourceMode).toBe("basic")
		expect(merged.branding.logo?.company).toBe("Acme")
		expect(merged.table?.stroke.width).toBe(1)
		expect(merged.table?.cellLabel.enabled).toBe(false)
		expect(merged.table?.cellLabel.baselineShift).toBe(1)
		expect(merged.table?.cellLabel.color).toBe("#334155")
	})

	it("preserves inherited qr source mode when override is blank", () => {
		const merged = merge_presentation_settings(default_presentation_settings, {
			qr: { sourceMode: "" },
		} as any)
		expect(merged.qr?.sourceMode).toBe("")

		const inherited = merge_presentation_settings(
			{
				...default_presentation_settings,
				qr: { ...(default_presentation_settings.qr || {}), sourceMode: "document_code_profile" },
			} as any,
			{ qr: { sourceMode: "" } } as any
		)
		expect(inherited.qr?.sourceMode).toBe("document_code_profile")
	})

	it("does not expose legacy presentation aliases", () => {
		expect("pageSize" in default_presentation_settings).toBe(false)
		expect("branding_mode" in default_presentation_settings).toBe(false)
		expect("letterheadImage" in default_presentation_settings).toBe(false)
		expect("report_builder" in default_presentation_settings).toBe(false)
	})
})
