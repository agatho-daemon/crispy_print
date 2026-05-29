import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { ref } from "vue"
import FieldsPane from "../../components/FieldsPane.vue"
import SettingsPane from "../../components/SettingsPane.vue"
import TypstCodePane from "../../components/TypstCodePane.vue"
import PreviewPane from "../../components/PreviewPane.vue"

vi.mock("../../api/crispy", () => ({
	getTypstLocalFonts: vi.fn(async () => ["Inter 18pt", "Serif"]),
}))

vi.mock("../../composables/useBrandingData", () => ({
	useBrandingData: () => ({
		availableLetterheads: ref([]),
		loadingLetterheads: ref(false),
		availableCompanies: ref([]),
		loadingCompanies: ref(false),
		resolveCompanyLogo: () => "",
		fetchLetterheads: vi.fn(),
		fetchCompanies: vi.fn(),
	}),
}))

vi.mock("../../composables/useStore", () => ({
	useStore: () => ({
		fields: ref([]),
		loading: ref(false),
		initializing: ref(false),
		formatName: ref("Format-1"),
		layout: ref({ sections: [] }),
		docHeader: ref(""),
		docFooter: ref(""),
		typstPreamble: ref(""),
		typstCode: ref(""),
		rawTypst: ref(false),
		qrEnabled: ref(false),
		letterhead: ref(null),
		docType: ref("Invoice"),
		changeKey: ref(0),
		sampleReports: ref([]),
		crispyFormat: ref({ crispy_format_type: "DocType", is_generic: 0 }),
		presentation_settings: ref({
			page: {
				size: "A4",
				orientation: "portrait",
				margins: { top: 10, bottom: 10, left: 10, right: 10 },
			},
			branding: {
				mode: "none",
				letterhead: "",
				letterhead_image: "",
				logo: { company: "", image: "", size: 25, dx: 0, dy: 0 },
			},
			language: "en",
		}),
	}),
}))

describe("Help button accessibility", () => {
	it("adds ARIA attributes for help popovers", () => {
		const fields = mount(FieldsPane, {
			props: { fields: [], isReportMode: false },
		})
		const fieldsHelp = fields.find("button.fields-pane__help-btn")
		expect(fieldsHelp.attributes("aria-haspopup")).toBe("dialog")
		expect(fieldsHelp.attributes("aria-controls")).toBe("fields-help")

		const settings = mount(SettingsPane, {
			props: {
				presentation_settings: {
					page: {
						size: "A4",
						orientation: "portrait",
						margins: { top: 10, bottom: 10, left: 10, right: 10 },
					},
					branding: {
						mode: "none",
						letterhead: "",
						letterhead_image: "",
						logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
					},
					typography: {},
					qr: {},
				},
				markDirty: vi.fn(),
			},
			global: {
				stubs: {
					ColorInput: true,
					QrFieldsDialog: true,
				},
			},
		})
		const settingsHelp = settings.find("button.settings-pane__help-btn")
		expect(settingsHelp.attributes("aria-haspopup")).toBe("dialog")
		expect(settingsHelp.attributes("aria-controls")).toBe("settings-help")

		const typst = mount(TypstCodePane)
		const typstHelp = typst.find("button.typst-code-pane__help-btn")
		expect(typstHelp.attributes("aria-haspopup")).toBe("dialog")
		expect(typstHelp.attributes("aria-controls")).toBe("typst-code-help")

		const preview = mount(PreviewPane, {
			global: {
				stubs: {
					PreviewRenderer: {
						template: "<div><slot name=\"menu\"></slot></div>",
					},
				},
			},
		})
		const previewHelp = preview.find("button.preview-pane__help-btn")
		expect(previewHelp.attributes("aria-haspopup")).toBe("dialog")
		expect(previewHelp.attributes("aria-controls")).toBe("preview-help")
	})
})
