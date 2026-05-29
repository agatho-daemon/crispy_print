import { describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: vi.fn(),
	saveCrispyFormat: vi.fn(),
	compileReportPreview: vi.fn(async (args) => {
		const response = await (globalThis as any).frappe.call({
			method: "crispy_print.api.v1.compile_report_preview",
			args,
		})
		return response.message
	}),
	compileTypst: vi.fn(),
	compileTypstSvg: vi.fn(),
}))

describe("useStore report preview", () => {
	it("compileReportPreview builds and compiles source in one request", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi
				.fn()
				.mockResolvedValueOnce({ message: { success: true, typst_source: "#typst" } }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any
		store.presentation_settings.value = {
			page: { size: "A4", orientation: "landscape", margins: { top: 25, bottom: 20, left: 20, right: 20 } },
			branding: {
				mode: "letterhead",
				letterhead: "LH-1",
				letterhead_image: "",
				logo: { company: "", image: "/files/logo.png", size: 25, dx: 0, dy: 0 },
			},
		} as any
		store.letterhead.value = { image: "/files/letterhead.png" } as any
		store.reportBuilderConfig.value = {
			...store.reportBuilderConfig.value,
			show_filters: true,
			font_family: "Inter 18pt",
			font_size_pt: 10,
		}
		store.typstCode.value = "#show heading: it => it"
		store.layout.value = {
			sections: [
				{
					columns: [
						{
							fields: [
								{
									fieldname: "data.table",
									table_columns: [
										{ fieldname: "item", width: "1fr" },
										{ fieldname: "qty", width: "auto" },
									],
								},
							],
						},
					],
				},
			],
		} as any

		const result = await store.compileReportPreview("Sales Order")

		expect(result).toEqual({ success: true, typst_source: "#typst" })
		expect((globalThis as any).frappe.call).toHaveBeenCalledTimes(1)
		const first = (globalThis as any).frappe.call.mock.calls[0][0]
		expect(first.method).toBe("crispy_print.api.v1.compile_report_preview")
		expect(first.args.report).toBe("Sales Order")
		expect(first.args.format_name).toBe("Format-1")
		expect(first.args.filters).toEqual({})
		expect(first.args.column_config).toEqual([
			{ fieldname: "item", width: "1fr" },
			{ fieldname: "qty", width: "auto" },
		])
		expect(first.args.include_filters).toBe(1)
		expect(first.args.orientation).toBe("landscape")
		expect(first.args.presentation_settings).toMatchObject({
			page: { orientation: "landscape" },
		})
		expect(first.args.typst_preamble_override).toContain('#set text(font: "Inter 18pt"')
		expect(first.args.typst_code_override).toBe("#show heading: it => it")
		expect(first.args.preview_data?.title).toBe("Sales Order")
		expect(Array.isArray(first.args.preview_data?.columns)).toBe(true)
		expect(Array.isArray(first.args.preview_data?.rows)).toBe(true)
		expect(first.args.preview_data?.chart_svg).toBe("report_chart.svg")
		expect(first.args.presentation_settings?.branding?.letterhead_image).toBe(
			"/files/letterhead.png"
		)
		expect(first.args.limit).toBe(50)
		expect(first.args.asset_files).toContain("/files/letterhead.png")
		expect(first.args.chart_svg).toContain("Placeholder Chart")
	})

	it("compileReportPreview throws when source is missing", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi.fn().mockResolvedValueOnce({ message: { success: true } }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any

		await expect(store.compileReportPreview("Sales Order")).rejects.toThrow(
			"No Typst source returned"
		)
		expect((globalThis as any).frappe.call).toHaveBeenCalledTimes(1)
	})

	it("compileReportPreview prefers explicit columnConfig override", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi
				.fn()
				.mockResolvedValueOnce({ message: { success: true, typst_source: "#typst" } }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any
		store.layout.value = {
			sections: [
				{
					columns: [
						{
							fields: [
								{
									fieldname: "data.table",
									table_columns: [{ fieldname: "from_layout", width: "auto" }],
								},
							],
						},
					],
				},
			],
		} as any

		await store.compileReportPreview("Sales Order", [
			{ fieldname: "from_override", width: "2fr" },
		])

		const first = (globalThis as any).frappe.call.mock.calls[0][0]
		expect(first.args.column_config).toEqual([
			{ fieldname: "from_override", width: "2fr" },
		])
	})

	it("compileReportPreview accepts structured source payload", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi
				.fn()
				.mockResolvedValueOnce({
					message: {
						success: true,
						typst_source: "#typst",
						asset_files: ["/private/files/logo.svg"],
						truncation: { is_truncated: true, returned_rows: 50, original_rows: 120 },
					},
				})
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any

		const result = await store.compileReportPreview("Sales Order")

		expect(result).toMatchObject({ success: true, typst_source: "#typst" })
		expect((globalThis as any).frappe.call).toHaveBeenCalledTimes(1)
	})

	it("compileReportPreview normalizes unitless widths to pt", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi
				.fn()
				.mockResolvedValueOnce({ message: { success: true, typst_source: "#typst" } }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any
		store.layout.value = {
			sections: [
				{
					columns: [
						{
							fields: [
								{
									fieldname: "data.table",
									table_columns: [
										{ fieldname: "item", width: 120 },
										{ fieldname: "qty", width: "80" },
										{ fieldname: "invalid", width: "wide-ish" },
									],
								},
							],
						},
					],
				},
			],
		} as any

		await store.compileReportPreview("Sales Order")

		const first = (globalThis as any).frappe.call.mock.calls[0][0]
		expect(first.args.column_config).toEqual([
			{ fieldname: "item", width: "120pt" },
			{ fieldname: "qty", width: "80pt" },
			{ fieldname: "invalid", width: "auto" },
		])
	})

	it("compileReportPreview honors branding mode in payload images", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi
				.fn()
				.mockResolvedValueOnce({ message: { success: true, typst_source: "#typst" } })
				.mockResolvedValueOnce({ message: { success: true, typst_source: "#typst" } }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any
		store.letterhead.value = { image: "/files/lh.png" } as any
		store.presentation_settings.value = {
			page: { size: "A4", orientation: "landscape", margins: { top: 25, bottom: 20, left: 20, right: 20 } },
			branding: {
				mode: "logo",
				letterhead: "",
				letterhead_image: "",
				logo: { company: "", image: "/files/logo.png", size: 25, dx: 0, dy: 0 },
			},
		} as any

		await store.compileReportPreview("Sales Order")

		const firstSource = (globalThis as any).frappe.call.mock.calls[0][0]
		expect(firstSource.args.presentation_settings?.branding?.letterhead_image).toBe("")
		expect(firstSource.args.asset_files).toContain("/files/logo.png")

		store.presentation_settings.value = {
			page: { size: "A4", orientation: "landscape", margins: { top: 25, bottom: 20, left: 20, right: 20 } },
			branding: {
				mode: "letterhead",
				letterhead: "LH-1",
				letterhead_image: "",
				logo: { company: "", image: "/files/logo.png", size: 25, dx: 0, dy: 0 },
			},
		} as any
		store.letterhead.value = { image: "/files/lh.png" } as any

		await store.compileReportPreview("Sales Order")

		const secondSource = (globalThis as any).frappe.call.mock.calls[1][0]
		expect(secondSource.args.presentation_settings?.branding?.letterhead_image).toBe(
			"/files/lh.png"
		)
		expect(secondSource.args.asset_files).toContain("/files/lh.png")
	})
})
