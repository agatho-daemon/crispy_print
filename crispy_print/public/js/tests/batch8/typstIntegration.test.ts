import { describe, expect, it } from "vitest"
import { translateJSONToTypst } from "../../typst/JSONToTypst"

describe("Typst integration", () => {
	it("renders letterhead background and QR foreground", () => {
		const typst = translateJSONToTypst(
			{
				sections: [
					{
						label: "Header",
						columns: [
							{
								label: "",
								fields: [{ fieldname: "title", fieldtype: "Data", label: "Title" }],
							},
						],
					},
				],
			},
			{ image: "/files/letterhead.png", letter_head_name: "Default LH" },
			"Invoice",
			{ name: "INV-0001", title: "Test" },
			{
				brandingMode: "letterhead",
				pageSize: "A4",
				margins: { top: 10, bottom: 10, left: 10, right: 10 },
				qrEnabled: true,
				qrFilename: "INV-0001-qr.svg",
			}
		)

		expect(typst).toContain('background: image("letterhead.png", width: 100%)')
		expect(typst).toContain("foreground: [")
		expect(typst).toContain('image("INV-0001-qr.svg"')
		expect(typst).not.toContain('image("logo.png"')
	})

	it("renders logo and QR in foreground for logo mode", () => {
		const typst = translateJSONToTypst(
			{
				sections: [
					{
						label: "Main",
						columns: [
							{
								label: "",
								fields: [{ fieldname: "name", fieldtype: "Data", label: "Name" }],
							},
						],
					},
				],
			},
			null,
			"Document",
			{ name: "DOC-1" },
			{
				brandingMode: "logo",
				logo: { image: "/files/logo.png", size: 30, dx: 2, dy: 3 },
				qrEnabled: true,
				qrFilename: "DOC-1-qr.svg",
			}
		)

		expect(typst).toContain("foreground: [")
		expect(typst).toContain('image("logo.png"')
		expect(typst).toContain('image("DOC-1-qr.svg"')
		expect(typst).not.toContain("background: image(")
	})
})
