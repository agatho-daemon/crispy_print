import { describe, expect, it } from "vitest"
import {
	defaultPageSettings,
	ensureLogoSettings,
	ensureQrSettings,
	ensureTableSettings,
	ensureTypography,
	mergePageSettings,
} from "../../utils/pageSettings"

describe("pageSettings helpers", () => {
	it("ensures QR settings defaults", () => {
		const settings: any = { pageSize: "A4", orientation: "portrait", margins: {} }
		const qr = ensureQrSettings(settings)
		expect(qr.size).toBe(15)
		expect(qr.dx).toBe(0)
		expect(qr.dy).toBe(0)
		expect(Array.isArray(qr.fields)).toBe(true)
	})

	it("ensures logo settings defaults", () => {
		const settings: any = { pageSize: "A4", orientation: "portrait", margins: {} }
		const logo = ensureLogoSettings(settings)
		expect(logo.company).toBe("")
		expect(logo.image).toBe("")
		expect(logo.size).toBe(25)
		expect(logo.dx).toBe(0)
		expect(logo.dy).toBe(0)
	})

	it("ensures typography defaults", () => {
		const settings: any = { pageSize: "A4", orientation: "portrait", margins: {} }
		const typography = ensureTypography(settings)
		expect(typography.fieldLabel).toBeDefined()
		expect(typography.fieldValue).toBeDefined()
		expect(typography.sectionLabel).toBeDefined()
	})

	it("ensures table settings defaults", () => {
		const settings: any = { pageSize: "A4", orientation: "portrait", margins: {} }
		const table = ensureTableSettings(settings)
		expect(table.inset.top).toBeDefined()
		expect(table.stroke.width).toBeDefined()
		expect(table.header.backgroundColor).toBeDefined()
		expect(table.stripe.enabled).toBeDefined()
		expect(table.typography.header).toBeDefined()
		expect(table.typography.body).toBeDefined()
	})

	it("merges overrides with defaults", () => {
		const merged = mergePageSettings(defaultPageSettings, {
			margins: { top: 10 },
			qr: { size: 20 },
			logo: { company: "Acme" },
			table: { stroke: { width: 1 } },
		})
		expect(merged.margins.top).toBe(10)
		expect(merged.margins.left).toBe(defaultPageSettings.margins.left)
		expect(merged.qr?.size).toBe(20)
		expect(merged.logo?.company).toBe("Acme")
		expect(merged.table?.stroke.width).toBe(1)
	})
})
