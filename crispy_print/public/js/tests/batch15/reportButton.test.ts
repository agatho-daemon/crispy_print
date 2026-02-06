import { describe, expect, it, vi } from "vitest"

function setupGlobals() {
	const frappe = {
		provide: (path: string) => {
			const parts = path.split(".")
			let ctx: any = globalThis
			parts.forEach((part) => {
				ctx[part] = ctx[part] || {}
				ctx = ctx[part]
			})
			return ctx
		},
		set_route: vi.fn(),
		route_options: {},
		query_report: null,
		router: { on: vi.fn() },
	}
	;(globalThis as any).frappe = frappe
	;(globalThis as any).window = globalThis
	;(globalThis as any).window.frappe = frappe
	;(globalThis as any).$ = () => ({ on: vi.fn() })
}

describe("report_button", () => {
	it("stores report state and routes on click", async () => {
		vi.resetModules()
		setupGlobals()
		delete (globalThis as any).__crispy_qr_patched__

		await import("../../report_button.bundle.js")

		const report = {
			report_name: "Sales Register",
			get_filter_values: () => ({ company: "ACME" }),
			columns: [{ fieldname: "item" }],
			page: {
				btn_typst_print: null,
				inner_toolbar: [{ querySelector: () => null }],
				add_inner_button: (label: string, handler: () => void) => {
					return Object.assign([{
						setAttribute: vi.fn(),
					}], { length: 1, _handler: handler })
				},
			},
		} as any

		const crispy_print = (globalThis as any).crispy_print
		crispy_print.add_print_button(report)

		const btn = report.page.btn_typst_print
		expect(btn).toBeTruthy()
		btn._handler()

		const stored = window.sessionStorage.getItem("crispy-print:report:Sales Register")
		expect(stored).toContain("Sales Register")
		expect((globalThis as any).window.frappe.route_options).toBeDefined()
		expect((globalThis as any).window.frappe.route_options.source).toBe("report")
		expect((globalThis as any).window.frappe.route_options.columns).toBeTruthy()
		expect((globalThis as any).frappe.set_route).toHaveBeenCalled()
	})
})
