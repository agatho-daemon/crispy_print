import { describe, expect, it, vi } from "vitest"
import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"

function loadReportButtonBundle() {
	const currentDir = dirname(fileURLToPath(import.meta.url))
	const bundlePath = resolve(currentDir, "../../report_button.bundle.js")
	const bundleCode = readFileSync(bundlePath, "utf8")
	;(0, eval)(bundleCode)
}

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
		query_report: null as unknown,
		router: { on: vi.fn() },
	}
	;(globalThis as any).frappe = frappe
	;(globalThis as any).window = globalThis
	;(globalThis as any).window.frappe = frappe
	;(globalThis as any).__ = (value: string) => value
	;(globalThis as any).$ = () => ({ on: vi.fn() })
}

describe("report_button", () => {
	it("stores report state and routes on click", async () => {
		vi.resetModules()
		setupGlobals()
		delete (globalThis as any).__crispy_qr_patched__

		loadReportButtonBundle()

		const report = {
				report_name: "Sales Register",
				get_filter_values: () => ({ company: "ACME" }),
				columns: [{ fieldname: "item" }],
				page: {
					btn_typst_print: null,
					inner_toolbar: [{ querySelector: (): null => null }],
					add_inner_button: (label: string, handler: () => void): any[] => {
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
		expect((globalThis as any).frappe.set_route).toHaveBeenCalledWith(
			"crispy-print-preview",
			"report",
			"Sales Register"
		)
	})

	it("preserves ERPNext filter value shapes and route options", () => {
		vi.resetModules()
		setupGlobals()
		delete (globalThis as any).__crispy_qr_patched__
		loadReportButtonBundle()

		const filters = {
			company: "ACME",
			from_date: "2026-01-01",
			to_date: "2026-01-31",
			accounts: ["1100 - Receivables", "1200 - Bank"],
			party_type: "Customer",
			party: ["CUST-001", "CUST-002"],
			cost_center: ["Main - ACME", "North - ACME"],
			project: "PROJ-001",
			accounting_dimensions: { branch: "Kuwait", region: ["North", "South"] },
			include_dimensions: 1,
			group_by_party: 0,
			optional_link: "",
			custom_filter: null,
		}
		const report = {
			report_name: "General Ledger",
			get_filter_values: () => filters,
			columns: [
				{ fieldname: "posting_date", fieldtype: "Date" },
				{ fieldname: "account", fieldtype: "Link", options: "Account" },
			],
			page: {
				btn_typst_print: null,
				inner_toolbar: [{ querySelector: (): null => null }],
				add_inner_button: (_label: string, handler: () => void): any[] =>
					Object.assign([{ setAttribute: vi.fn() }], { length: 1, _handler: handler }),
			},
		} as any

		;(globalThis as any).crispy_print.add_print_button(report)
		report.page.btn_typst_print._handler()

		expect((globalThis as any).frappe.route_options.filters).toEqual(filters)
		expect((globalThis as any).frappe.route_options.columns).toEqual(report.columns)
	})

	it("rebinds a restored report button to the current Query Report instance", () => {
		vi.resetModules()
		setupGlobals()
		delete (globalThis as any).__crispy_qr_patched__
		loadReportButtonBundle()

		const page: any = {
			btn_typst_print: null,
			inner_toolbar: [{ querySelector: (): null => null }],
			add_inner_button: (_label: string, handler: () => void) => {
				const element = document.createElement("button") as HTMLButtonElement & {
					_handler?: () => void
				}
				document.body.appendChild(element)
				element._handler = handler
				const button: any = [element]
				button.length = 1
				button.remove = () => element.remove()
				button._handler = handler
				return button
			},
		}
		const firstReport = {
			report_name: "Salary Register",
			get_filter_values: () => ({ from_date: "2025-12-01" }),
			columns: [{ fieldname: "basic_salary" }],
			page,
		} as any
		;(globalThis as any).crispy_print.add_print_button(firstReport)
		const firstElement = page.btn_typst_print[0]

		const restoredReport = {
			report_name: "Salary Register",
			get_filter_values: () => ({ from_date: "2026-01-01" }),
			columns: [
				{ fieldname: "basic_salary" },
				{ fieldname: "_test_allowance" },
			],
			page,
		} as any
		;(globalThis as any).crispy_print.add_print_button(restoredReport)

		expect(firstElement.isConnected).toBe(false)
		page.btn_typst_print._handler()
		expect((globalThis as any).frappe.route_options.filters).toEqual({
			from_date: "2026-01-01",
		})
		expect((globalThis as any).frappe.route_options.columns).toHaveLength(2)
		document.body.innerHTML = ""
	})
})
