import { mount } from "@vue/test-utils"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { nextTick } from "vue"
import SampleFormatsDialog from "../../components/SampleFormatsDialog.vue"

const listSampleFormats = vi.fn(async () => [
	{
		id: "sales-invoice-basic",
		title: "Sales Invoice Starter",
		description: "A compact invoice layout.",
		target_type: "DocType",
		doc_type: "Sales Invoice",
		tags: ["invoice", "starter"],
		recommended_use: "Use as a first invoice format.",
		format_name: "Sample Sales Invoice Starter",
	},
])
const getCompanies = vi.fn(async () => [{ name: "ACME", abbr: "AC" }])

vi.mock("../../api/crispy", () => ({
	listSampleFormats: () => listSampleFormats(),
	getCompanies: () => getCompanies(),
}))

async function flushPromises() {
	await Promise.resolve()
	await Promise.resolve()
	await nextTick()
}

describe("SampleFormatsDialog", () => {
	beforeEach(() => {
		vi.clearAllMocks()
	})

	it("loads examples and creates a selected sample", async () => {
		const wrapper = mount(SampleFormatsDialog, {
			props: {
				open: true,
				submitting: false,
			},
		})

		await flushPromises()

		expect(listSampleFormats).toHaveBeenCalled()
		expect(getCompanies).toHaveBeenCalled()
		expect(wrapper.text()).toContain("Sales Invoice Starter")

		await wrapper.find("select").setValue("ACME")
		await wrapper.find("input.form-control").setValue("My Invoice Example")
		await wrapper.find("input[type='checkbox']").setValue(true)
		await wrapper.find(".btn-primary").trigger("click")

		expect(wrapper.emitted("confirm")?.[0]?.[0]).toEqual({
			sample_id: "sales-invoice-basic",
			company: "ACME",
			name: "My Invoice Example",
			set_default: true,
		})
	})
})
