import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { ref } from "vue"
import PreviewPane from "../../components/PreviewPane.vue"

const compileReportPreview = vi.fn(async () => ({
	success: true,
	pdf_data: "JVBERi0xLjQK",
	page_count: 1,
}))
const requestPreviewRefresh = vi.fn()
const crispyFormat = ref({ crispy_format_type: "Report", pdf_standard: "PDF/A-2u" })

vi.mock("../../composables/useStore", () => ({
	useStore: () => ({
		formatName: ref("Format-1"),
		layout: ref({ sections: [] }),
		docHeader: ref(""),
		docFooter: ref(""),
		typstPreamble: ref(""),
		typstCode: ref(""),
		typstBlocks: ref([]),
		rawTypst: ref(false),
		qrEnabled: ref(false),
		letterhead: ref(null),
		docType: ref("Report"),
		previewRevision: ref(0),
		reportPreviewReady: ref(true),
		selectedReportName: ref("Accounts Receivable"),
		crispyFormat,
		effective_presentation_settings: ref({
			page: {
				size: "A4",
				orientation: "portrait",
				margins: { top: 10, bottom: 10, left: 10, right: 10 },
			},
			branding: { mode: "none", letterhead: "", logo: {} },
		}),
		presentation_settings: ref({}),
		reportBuilderConfig: ref({
			show_filters: true,
			show_summary: true,
			include_total_row: true,
		}),
		compileReportPreview,
		requestPreviewRefresh,
	}),
}))

describe("PreviewPane refresh shortcut", () => {
	it("clicks refresh on Ctrl/Cmd Enter", async () => {
		crispyFormat.value = { crispy_format_type: "Report", pdf_standard: "PDF/A-2u" }
		compileReportPreview.mockClear()
		requestPreviewRefresh.mockClear()
		;(globalThis as any).frappe = { show_alert: vi.fn() }
		const target = document.createElement("div")
		document.body.appendChild(target)

		const wrapper = mount(PreviewPane, {
			attachTo: target,
			global: {
				stubs: {
					ReportPreviewVariables: true,
					PreviewRenderer: {
						template: '<div><slot name="menu" /></div>',
					},
				},
			},
		})
		compileReportPreview.mockClear()

		window.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", ctrlKey: true }))
		await Promise.resolve()

		expect(compileReportPreview).toHaveBeenCalledWith("Accounts Receivable", [])
		expect(requestPreviewRefresh).not.toHaveBeenCalled()

		wrapper.unmount()
		target.remove()
	})

	it("requests DocType preview refresh on button click and Ctrl/Cmd Enter", async () => {
		crispyFormat.value = { crispy_format_type: "DocType", pdf_standard: "PDF/A-2u" }
		compileReportPreview.mockClear()
		requestPreviewRefresh.mockClear()
		const target = document.createElement("div")
		document.body.appendChild(target)

		const wrapper = mount(PreviewPane, {
			attachTo: target,
			global: {
				stubs: {
					ReportPreviewVariables: true,
					PreviewRenderer: {
						template: '<div><slot name="menu" /></div>',
					},
				},
			},
		})
		requestPreviewRefresh.mockClear()

		await wrapper.find("#typst-refresh").trigger("click")
		window.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", metaKey: true }))
		await Promise.resolve()

		expect(requestPreviewRefresh).toHaveBeenCalledTimes(2)
		expect(compileReportPreview).not.toHaveBeenCalled()

		wrapper.unmount()
		target.remove()
	})
})
