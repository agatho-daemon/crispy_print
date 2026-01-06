import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { nextTick, reactive, ref } from "vue"
import SettingsPane from "../../components/SettingsPane.vue"

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
	useStore: () => ({
		fields: ref([]),
		removeQr: ref(false),
	}),
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
		const brandingHeader = headers.find((btn) => btn.text().includes("Letterhead / Logo"))
		expect(brandingHeader).toBeTruthy()
		await brandingHeader!.trigger("click")

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
})
