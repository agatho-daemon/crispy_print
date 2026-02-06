import { describe, expect, it, vi } from "vitest"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: vi.fn(),
	saveCrispyFormat: vi.fn(),
}))

describe("useStore report preview", () => {
	it("compileReportPreview builds source then compiles", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi
				.fn()
				.mockResolvedValueOnce({ message: "#typst" })
				.mockResolvedValueOnce({ message: { success: true } }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any
		store.reportFilters.value = { company: "ACME" }

		const result = await store.compileReportPreview("Sales Order", [
			{ fieldname: "item", width: "1fr" },
		])

		expect(result).toEqual({ success: true })
		expect((globalThis as any).frappe.call).toHaveBeenCalledTimes(2)
		const first = (globalThis as any).frappe.call.mock.calls[0][0]
		expect(first.method).toBe("crispy_print.api.v1.get_report_typst_source")
		expect(first.args.report).toBe("Sales Order")
		expect(first.args.format_name).toBe("Format-1")
		const second = (globalThis as any).frappe.call.mock.calls[1][0]
		expect(second.method).toBe("crispy_print.api.v1.compile_typst")
	})

	it("compileReportPreview throws when source is missing", async () => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string) => msg
		;(globalThis as any).frappe = {
			call: vi.fn().mockResolvedValueOnce({ message: "" }),
		}

		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.crispyFormat.value = { name: "Format-1" } as any

		await expect(store.compileReportPreview("Sales Order")).rejects.toThrow(
			"No Typst source returned"
		)
		expect((globalThis as any).frappe.call).toHaveBeenCalledTimes(1)
	})
})
