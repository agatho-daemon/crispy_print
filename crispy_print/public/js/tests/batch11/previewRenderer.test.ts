import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { nextTick } from "vue"
import PreviewRenderer from "../../components/PreviewRenderer.vue"
import { CrispyPreviewEvents } from "../../utils/events"

vi.mock("../../typst/setupWorker", () => ({
	setupWorker: vi.fn(() => () => {}),
}))

describe("PreviewRenderer", () => {
	it("invokes setupWorker when format is ready", async () => {
		const { setupWorker } = await import("../../typst/setupWorker")

		const wrapper = mount(PreviewRenderer, {
			props: {
				formatName: "Format-1",
				layout: { sections: [] },
				docHeader: "",
				docFooter: "",
				typstPreamble: "",
				qrEnabled: false,
				pageSettings: {
					pageSize: "A4",
					orientation: "portrait",
					margins: { top: 10, bottom: 10, left: 10, right: 10 },
					language: "en",
				},
				letterhead: null,
				docType: "Invoice",
			},
		})

		await nextTick()
		expect(setupWorker).toHaveBeenCalledTimes(1)
		const args = (setupWorker as any).mock.calls[0]
		expect(args[0]).toBe("Format-1")
		expect(args[1]).toBe(wrapper.element)
	})

	it("shows error panel on error status", async () => {
		const wrapper = mount(PreviewRenderer, {
			props: {
				formatName: "Format-1",
				layout: { sections: [] },
				docHeader: "",
				docFooter: "",
				typstPreamble: "",
				qrEnabled: false,
				pageSettings: {
					pageSize: "A4",
					orientation: "portrait",
					margins: { top: 10, bottom: 10, left: 10, right: 10 },
					language: "en",
				},
				letterhead: null,
				docType: "Invoice",
			},
		})

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.Status, {
				detail: { status: "error", message: "Boom" },
			})
		)
		await nextTick()
		expect(wrapper.find(".preview-error").exists()).toBe(true)
		expect(wrapper.find(".preview-error__body").text()).toContain("Boom")

		window.dispatchEvent(
			new CustomEvent(CrispyPreviewEvents.Status, {
				detail: { status: "ready" },
			})
		)
		await nextTick()
		expect(wrapper.find(".preview-error").exists()).toBe(false)
	})
})
