import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("../../api/frappe", () => ({
	call: vi.fn(),
	getDoc: vi.fn(),
	getList: vi.fn(),
	setValue: vi.fn(),
}))

describe("crispy format import/export api wrappers", () => {
	beforeEach(() => {
		vi.resetModules()
		vi.clearAllMocks()
	})

	it("exports a format payload", async () => {
		const { call } = await import("../../api/frappe")
		;(call as any).mockResolvedValueOnce({
			message: {
				schema_version: 1,
				exported_at: "2026-02-07T10:00:00",
				app: "crispy_print",
				format: { name: "My Format" },
			},
		})

		const { exportCrispyFormat } = await import("../../api/crispy")
		const payload = await exportCrispyFormat("My Format")

		expect(payload.schema_version).toBe(1)
		expect((call as any).mock.calls[0][0]).toMatchObject({
			method: "crispy_print.api.v1.export_crispy_format",
			args: { name: "My Format" },
		})
	})

	it("checks conflicts with serialized payload", async () => {
		const { call } = await import("../../api/frappe")
		;(call as any).mockResolvedValueOnce({
			message: {
				schema_version: 1,
				name: "My Format",
				exists: true,
				conflict: true,
			},
		})

		const { checkImportConflicts } = await import("../../api/crispy")
		const payload = { schema_version: 1, format: { name: "My Format" } }
		const res = await checkImportConflicts(payload)

		expect(res.exists).toBe(true)
		expect((call as any).mock.calls[0][0]).toMatchObject({
			method: "crispy_print.api.v1.check_import_conflicts",
		})
		expect(typeof (call as any).mock.calls[0][0].args.payload).toBe("string")
	})

	it("imports with selected conflict action", async () => {
		const { call } = await import("../../api/frappe")
		;(call as any).mockResolvedValueOnce({
			message: {
				success: true,
				name: "My Format (Imported)",
				warnings: ["Missing reference: Letter Head 'X'"],
				conflict_action: "copy",
			},
		})

		const { importCrispyFormat } = await import("../../api/crispy")
		const result = await importCrispyFormat('{"schema_version":1}', "copy")

		expect(result.success).toBe(true)
		expect(result.warnings.length).toBe(1)
		expect((call as any).mock.calls[0][0]).toMatchObject({
			method: "crispy_print.api.v1.import_crispy_format",
			args: {
				payload: '{"schema_version":1}',
				on_conflict: "copy",
			},
		})
	})
})
