import { flushPromises, mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"
import CrispyImageDialog from "../../components/CrispyImageDialog.vue"
import { getPrivateImageFiles } from "../../api/crispy"

vi.mock("../../api/crispy", () => ({
	getPrivateImageFiles: vi.fn(async () => [
		{
			name: "FILE-1",
			filename: "logo.svg",
			file_name: "logo.svg",
			file_url: "/private/files/logo.svg",
		},
		{
			name: "FILE-2",
			filename: "seal.png",
			file_name: "seal.png",
			file_url: "/private/files/seal.png",
		},
	]),
}))

describe("CrispyImageDialog", () => {
	beforeEach(() => {
		vi.mocked(getPrivateImageFiles).mockClear()
		;(globalThis as any).frappe = {
			show_alert: vi.fn(),
			ui: {
				FileUploader: vi.fn(function FileUploader(this: any, options: any) {
					this.options = options
					this.dialog = { set_value: vi.fn() }
					this.show = vi.fn()
				}),
			},
		}
	})

	it("lists private images and emits the selected image settings", async () => {
		const wrapper = mount(CrispyImageDialog)
		await flushPromises()

		expect(wrapper.text()).toContain("logo.svg")
		expect(wrapper.text()).toContain("seal.png")

		await wrapper.findAll(".crispy-image-dialog__item")[1].trigger("click")
		await wrapper.find(".crispy-image-dialog__footer .btn-primary").trigger("click")

		expect(wrapper.emitted("select")?.[0]).toEqual([
			{
				filename: "seal.png",
				width: "100%",
				height: "",
				fit: "",
			},
		])
	})

	it("forces uploads to private files and selects uploaded filename", async () => {
		const wrapper = mount(CrispyImageDialog)
		await flushPromises()

		await wrapper.find(".crispy-image-dialog__toolbar .btn-primary").trigger("click")

		const Uploader = (globalThis as any).frappe.ui.FileUploader
		const instance = Uploader.mock.instances[0]
		expect(instance.dialog.set_value).toHaveBeenCalledWith("is_private", 1)

		await instance.options.on_success({ file_url: "/private/files/uploaded.svg" })
		await flushPromises()

		await wrapper.find(".crispy-image-dialog__footer .btn-primary").trigger("click")
		expect(wrapper.emitted("select")?.[0]?.[0]).toMatchObject({
			filename: "uploaded.svg",
		})
	})

	it("edits size settings", async () => {
		const wrapper = mount(CrispyImageDialog, {
			props: {
				selectedFilename: "logo.svg",
				settings: {
					width: "28.5mm",
					height: "12mm",
					fit: "contain",
				},
			},
		})
		await flushPromises()

		await wrapper.find(".crispy-image-dialog__footer .btn-primary").trigger("click")

		expect(wrapper.emitted("select")?.[0]?.[0]).toMatchObject({
			filename: "logo.svg",
			width: "28.5mm",
			height: "12mm",
			fit: "contain",
		})
	})
})
