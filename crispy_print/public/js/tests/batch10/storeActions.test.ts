import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getApplicableTypstBlocks: vi.fn(async () => []),
	getCrispyFormat: vi.fn(),
	getCrispyTemplatePublishPreview: vi.fn(async () => ({ template_name: "Template", next_version: "1.0" })),
	duplicateCrispyFormatForCompany: vi.fn(async () => ({ name: "Format ACME", source_name: "Format-1", company: "ACME" })),
	duplicateCrispyTemplateForCompany: vi.fn(async () => ({
		cloned_format: "Format ACME",
		clone_mode: "snapshot",
		source_template: "Template-1",
		template: { name: "Template ACME", version: "1.0", status: "Approved", is_active: false },
	})),
	publishTemplateFromCrispyFormat: vi.fn(async () => ({ name: "Template v1" })),
	saveCrispyFormat: vi.fn(),
}))

vi.mock("../../api/frappe", () => ({
	withDoctype: vi.fn(),
}))

describe("useStore actions", () => {
	beforeEach(() => {
		vi.resetModules()
		vi.clearAllMocks()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			show_alert: vi.fn(),
		}
	})

	it("saves changes with serialized layout", async () => {
		const { useStore } = await import("../../composables/useStore")
		const { saveCrispyFormat } = await import("../../api/crispy")

		const store = useStore()
		store.crispyFormat.value = { name: "Format-1", doc_type: "Invoice" } as any
		store.layout.value = { sections: [] } as any
		store.presentation_settings.value = { page: { size: "A4", orientation: "portrait", margins: { top: 25, bottom: 20, left: 20, right: 20 } }, branding: { mode: "none", letterhead: "", letterhead_image: "", logo: { company: "", image: "", size: 25, dx: 0, dy: 0 } } } as any
		store.typstCode.value = ""
		store.rawTypst.value = false
		store.dirty.value = true

		await store.saveChanges()

		expect(saveCrispyFormat).toHaveBeenCalledTimes(1)
		const args = (saveCrispyFormat as any).mock.calls[0]
		expect(args[0]).toBe("Format-1")
		expect(args[1].layout_json).toContain("sections")
		expect(args[1].raw_typst).toBe(0)
		expect(store.dirty.value).toBe(false)
	})

	it("resetLayout uses default and marks dirty", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()

		store.layout.value = { sections: [{ label: "Old", columns: [] }] } as any
		store.dirty.value = false

		store.resetLayout()

		expect(store.layout.value?.sections?.length).toBe(0)
		expect(store.dirty.value).toBe(true)
	})

	it("passes effective company to template publish APIs", async () => {
		const { useStore } = await import("../../composables/useStore")
		const {
			getCrispyTemplatePublishPreview,
			publishTemplateFromCrispyFormat,
		} = await import("../../api/crispy")

		const store = useStore()
		store.crispyFormat.value = { name: "Format-1", doc_type: "Invoice", company: "ACME" } as any
		store.presentation_settings.value = {
			page: { size: "A4", orientation: "portrait", margins: { top: 25, bottom: 20, left: 20, right: 20 } },
			branding: { mode: "none", company: "ACME", letterhead: "", letterhead_image: "", logo: { company: "ACME", image: "", size: 25, dx: 0, dy: 0 } },
		} as any

		await store.getTemplatePublishPreview("minor")
		await store.publishTemplate({ version_bump: "minor", make_active: true })

		expect(getCrispyTemplatePublishPreview).toHaveBeenCalledWith({
			source_crispy_format: "Format-1",
			version_bump: "minor",
			company: "ACME",
		})
		expect(publishTemplateFromCrispyFormat).toHaveBeenCalledWith({
			source_crispy_format: "Format-1",
			version_bump: "minor",
			make_active: true,
			effective_from: null,
			notes: null,
			company: "ACME",
		})
	})

	it("saves dirty format before duplicating current format for company", async () => {
		const { useStore } = await import("../../composables/useStore")
		const { duplicateCrispyFormatForCompany, saveCrispyFormat } = await import("../../api/crispy")

		const store = useStore()
		store.crispyFormat.value = { name: "Format-1", doc_type: "Invoice", company: "Source Co" } as any
		store.layout.value = { sections: [] } as any
		store.presentation_settings.value = { page: { size: "A4", orientation: "portrait", margins: { top: 25, bottom: 20, left: 20, right: 20 } }, branding: { mode: "none", letterhead: "", letterhead_image: "", logo: { company: "Source Co", image: "", size: 25, dx: 0, dy: 0 } } } as any
		store.dirty.value = true

		await store.duplicateFormatForCompany({ target_company: "ACME", set_default: true })

		expect(saveCrispyFormat).toHaveBeenCalledTimes(1)
		expect(duplicateCrispyFormatForCompany).toHaveBeenCalledWith({
			source_name: "Format-1",
			target_company: "ACME",
			set_default: true,
			name: null,
			name_strategy: "copy",
		})
	})

	it("duplicates a template snapshot for another company", async () => {
		const { useStore } = await import("../../composables/useStore")
		const { duplicateCrispyTemplateForCompany } = await import("../../api/crispy")

		const store = useStore()
		await store.duplicateTemplateForCompany({
			source_template: "Template-1",
			target_company: "ACME",
			clone_mode: "snapshot",
			make_active: false,
		})

		expect(duplicateCrispyTemplateForCompany).toHaveBeenCalledWith({
			source_template: "Template-1",
			target_company: "ACME",
			clone_mode: "snapshot",
			make_active: false,
			version_bump: "minor",
		})
	})
})
