import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { nextTick, reactive, ref } from "vue"
import SettingsPane from "../../components/SettingsPane.vue"

const hoisted = vi.hoisted(() => ({
	storeMock: {
		fields: { value: [] },
		loading: { value: false },
		initializing: { value: false },
		isReportMode: { value: false },
		reportBuilderConfig: {
			value: {
				preset: "grid",
				font_family: "Inter 18pt",
				font_size_pt: 9,
				show_filters: true,
				show_summary: true,
				include_total_row: true,
				chart_enabled: true,
				chart_card_border: true,
				chart_width_percent: 100,
				chart_max_height_pt: 220,
				chart_spacing_top_pt: 0,
				chart_spacing_bottom_pt: 12,
			},
		},
		reportBasicReadOnly: { value: false },
	},
}))

vi.mock("../../api/crispy", () => ({
	getTypstLocalFonts: vi.fn(async () => ["Inter 18pt", "Serif"]),
}))

vi.mock("../../composables/useBrandingData", () => ({
	useBrandingData: () => ({
		availableLetterheads: ref(["LH-1"]),
		loadingLetterheads: ref(false),
		availableCompanies: ref([{ name: "ACME", abbr: "AC" }]),
		loadingCompanies: ref(false),
		resolveCompanyLogo: (company: string) => (company === "ACME" ? "/files/acme.png" : ""),
		fetchLetterheads: vi.fn(),
		fetchCompanies: vi.fn(),
	}),
}))

vi.mock("../../composables/useStore", () => ({
	useStore: () => hoisted.storeMock,
}))

describe("SettingsPane", () => {
	it("updates logo image when company changes", async () => {
		const pageSettings = reactive({
			brandingMode: "none",
			logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
			margins: { top: 10, bottom: 10, left: 10, right: 10 },
			typography: {},
			letterhead: "",
			qr: {},
		}) as any

		const markDirty = vi.fn()

		const wrapper = mount(SettingsPane, {
			props: { pageSettings, markDirty },
			global: {
				stubs: {
					ColorInput: true,
					QrFieldsDialog: true,
				},
			},
		})

		const headers = wrapper.findAll("button.settings-pane__section-header")
		const brandingHeader = headers.find((btn) => btn.text().includes("Branding"))
		expect(brandingHeader).toBeTruthy()
		await brandingHeader!.trigger("click")
		await nextTick()

		const selects = wrapper.findAll("select")
		const brandingSelect = selects.find((select) => select.find('option[value="logo"]').exists())
		expect(brandingSelect).toBeTruthy()
		await brandingSelect!.setValue("logo")
		await nextTick()

		const companySelect = wrapper
			.findAll("select")
			.find((select) => select.find('option[value="ACME"]').exists())
		expect(companySelect).toBeTruthy()
		await companySelect!.setValue("ACME")
		await nextTick()

		expect(pageSettings.logo.image).toBe("/files/acme.png")
	})

	it("keeps chart controls under Chart Settings in report mode", async () => {
		hoisted.storeMock.isReportMode.value = true
		const pageSettings = reactive({
			brandingMode: "none",
			logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
			margins: { top: 10, bottom: 10, left: 10, right: 10 },
			typography: {},
			letterhead: "",
			qr: {},
			table: {
				inset: { top: 2, right: 2, bottom: 2, left: 2 },
				stroke: { width: 0.5, color: "#e2e8f0" },
				header: { backgroundColor: "#f1f5f9" },
				stripe: { enabled: false, color: "#f8fafc" },
				typography: {
					header: {
						fontFamily: "Inter 18pt",
						fontSize: "9pt",
						fontStyle: "normal",
						fontWeight: "semibold",
						color: "#0f172a",
					},
					body: {
						fontFamily: "Inter 18pt",
						fontSize: "9pt",
						fontStyle: "normal",
						fontWeight: "regular",
						color: "#0f172a",
					},
				},
			},
		}) as any

		const wrapper = mount(SettingsPane, {
			props: { pageSettings, markDirty: vi.fn() },
			global: {
				stubs: {
					ColorInput: true,
					QrFieldsDialog: true,
				},
			},
		})

		const headers = wrapper.findAll("button.settings-pane__section-header")
		const reportTemplateHeader = headers.find((btn) =>
			btn.text().includes("Report Template")
		)
		expect(reportTemplateHeader).toBeTruthy()
		await reportTemplateHeader!.trigger("click")
		await nextTick()

		const reportTemplateCardText = wrapper.text()
		expect(reportTemplateCardText).not.toContain("Header Fill")
		expect(reportTemplateCardText).not.toContain("Row Stripe Fill")
		expect(reportTemplateCardText).not.toContain("Chart Block")

		const chartHeader = wrapper
			.findAll("button.settings-pane__section-header")
			.find((btn) => btn.text().includes("Chart Settings"))
		expect(chartHeader).toBeTruthy()
		await chartHeader!.trigger("click")
		await nextTick()
		expect(wrapper.text()).toContain("Enable Chart")
		expect(wrapper.text()).toContain("Show Summary")

		hoisted.storeMock.isReportMode.value = false
	})
})
