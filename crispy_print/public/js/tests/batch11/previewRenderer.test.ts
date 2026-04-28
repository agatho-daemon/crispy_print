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

	it("emits zoom changes from the preview toolbar", async () => {
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
				zoomMode: "fit",
				zoomPercent: 100,
			},
		})

		await wrapper.findAll(".preview-zoom-toolbar button")[1].trigger("click")
		expect(wrapper.emitted("update:zoomMode")?.[0]).toEqual(["manual"])
		expect(wrapper.emitted("update:zoomPercent")?.[0]).toEqual([100])

		await wrapper.findAll(".preview-zoom-toolbar button")[0].trigger("click")
		expect(wrapper.emitted("update:zoomMode")?.[1]).toEqual(["fit"])
	})

	it("allows typing an exact zoom percentage", async () => {
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
				zoomMode: "fit",
				zoomPercent: 100,
			},
		})

		await wrapper.find(".preview-zoom-toolbar__value").trigger("click")
		const input = wrapper.find(".preview-zoom-toolbar__input")
		expect(input.exists()).toBe(true)
		await input.setValue("83%")
		await input.trigger("keydown.enter")

		expect(wrapper.emitted("update:zoomMode")?.[0]).toEqual(["manual"])
		expect(wrapper.emitted("update:zoomPercent")?.[0]).toEqual([83])
	})

	it("cancels exact zoom editing with Escape", async () => {
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
				zoomMode: "manual",
				zoomPercent: 100,
			},
		})

		await wrapper.find(".preview-zoom-toolbar__value").trigger("click")
		await wrapper.find(".preview-zoom-toolbar__input").setValue("140")
		await wrapper.find(".preview-zoom-toolbar__input").trigger("keydown.escape")

		expect(wrapper.emitted("update:zoomMode")).toBeUndefined()
		expect(wrapper.emitted("update:zoomPercent")).toBeUndefined()
		expect(wrapper.find(".preview-zoom-toolbar__input").exists()).toBe(false)
	})

	it("increments from the displayed fit percentage to the next 10 percent boundary", async () => {
		const descriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "clientWidth")
		Object.defineProperty(HTMLElement.prototype, "clientWidth", {
			configurable: true,
			get() {
				return 900
			},
		})
		try {
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
					zoomMode: "fit",
					zoomPercent: 100,
				},
			})

			await new Promise((resolve) => requestAnimationFrame(resolve))
			await nextTick()
			await wrapper.findAll(".preview-zoom-toolbar__icon")[1].trigger("click")

			expect(wrapper.emitted("update:zoomMode")?.[0]).toEqual(["manual"])
			expect(wrapper.emitted("update:zoomPercent")?.[0]).toEqual([120])
		} finally {
			if (descriptor) {
				Object.defineProperty(HTMLElement.prototype, "clientWidth", descriptor)
			} else {
				delete (HTMLElement.prototype as any).clientWidth
			}
		}
	})

	it("decrements from the displayed fit percentage to the previous 10 percent boundary", async () => {
		const descriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, "clientWidth")
		Object.defineProperty(HTMLElement.prototype, "clientWidth", {
			configurable: true,
			get() {
				return 900
			},
		})
		try {
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
					zoomMode: "fit",
					zoomPercent: 100,
				},
			})

			await new Promise((resolve) => requestAnimationFrame(resolve))
			await nextTick()
			await wrapper.findAll(".preview-zoom-toolbar__icon")[0].trigger("click")

			expect(wrapper.emitted("update:zoomMode")?.[0]).toEqual(["manual"])
			expect(wrapper.emitted("update:zoomPercent")?.[0]).toEqual([110])
		} finally {
			if (descriptor) {
				Object.defineProperty(HTMLElement.prototype, "clientWidth", descriptor)
			} else {
				delete (HTMLElement.prototype as any).clientWidth
			}
		}
	})

	it("renders report SVG pages inside the zoomable stage", async () => {
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
			new CustomEvent("crispy-report-preview", {
				detail: {
					svg_pages: ['<svg viewBox="0 0 100 100"></svg>'],
					page_count: 1,
				},
			})
		)
		await nextTick()

		expect(wrapper.find(".preview-stage #typst-svg-container").exists()).toBe(true)
		expect(wrapper.find(".typst-page").exists()).toBe(true)
		expect(wrapper.find("#typst-svg-container").classes()).toContain("has-pages")
	})
})
