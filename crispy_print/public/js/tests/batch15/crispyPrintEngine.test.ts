import { readFileSync } from "node:fs"
import { dirname, resolve } from "node:path"
import { fileURLToPath } from "node:url"
import { beforeEach, describe, expect, it, vi } from "vitest"

function loadCrispyPrintEngine() {
	const currentDir = dirname(fileURLToPath(import.meta.url))
	const bundlePath = resolve(currentDir, "../../crispy_print_engine.js")
	const bundleCode = readFileSync(bundlePath, "utf8")
	;(0, eval)(bundleCode)
}

function setupGlobals(call = vi.fn()) {
	const frappe = {
		call,
		set_route: vi.fn(),
		route_options: {},
		ui: {
			form: {
				print_engines: {},
				register_print_engine(name: string, renderer: unknown) {
					this.print_engines[name] = renderer
				},
			},
		},
	}
	;(globalThis as any).frappe = frappe
	;(globalThis as any).window = globalThis
	;(globalThis as any).window.frappe = frappe
	return frappe
}

describe("crispy_print_engine", () => {
	beforeEach(() => {
		vi.restoreAllMocks()
	})

	it("registers the crispy_print renderer", () => {
		const frappe = setupGlobals()

		loadCrispyPrintEngine()

		expect(frappe.ui.form.print_engines.crispy_print).toBeTruthy()
	})

	it("allows printing when an active Crispy Template resolves", async () => {
		const call = vi.fn(async () => ({ message: true }))
		const frappe = setupGlobals(call)
		loadCrispyPrintEngine()

		const renderer = frappe.ui.form.print_engines.crispy_print as any
		await expect(renderer.can_print({ doctype: "Sales Invoice", name: "SINV-1" })).resolves.toBe(
			true
		)
		expect(call).toHaveBeenCalledWith({
			method: "crispy_print.api.v1.can_resolve_crispy_template_for_document",
			args: {
				source_doctype: "Sales Invoice",
				source_docname: "SINV-1",
			},
		})
	})

	it("falls back when no active Crispy Template resolves", async () => {
		const call = vi.fn(async () => ({ message: false }))
		const frappe = setupGlobals(call)
		loadCrispyPrintEngine()

		const renderer = frappe.ui.form.print_engines.crispy_print as any
		await expect(renderer.can_print({ doctype: "Sales Invoice", name: "SINV-1" })).resolves.toBe(
			false
		)
	})

	it("falls back when template resolution fails", async () => {
		vi.spyOn(console, "warn").mockImplementation(() => {})
		const call = vi.fn(async () => {
			throw new Error("permission denied")
		})
		const frappe = setupGlobals(call)
		loadCrispyPrintEngine()

		const renderer = frappe.ui.form.print_engines.crispy_print as any
		await expect(renderer.can_print({ doctype: "Sales Invoice", name: "SINV-1" })).resolves.toBe(
			false
		)
	})

	it("opens the Crispy preview route with form context", () => {
		const frappe = setupGlobals()
		loadCrispyPrintEngine()

		const renderer = frappe.ui.form.print_engines.crispy_print as any
		const frm = { doctype: "Sales Invoice", docname: "SINV-1" }
		renderer.open({ frm, doctype: "Sales Invoice", name: "SINV-1" })

		expect(frappe.route_options).toMatchObject({
			frm,
			doctype: "Sales Invoice",
			name: "SINV-1",
			docname: "SINV-1",
			source: "print_doc",
			print_engine: "crispy_print",
		})
		expect(frappe.set_route).toHaveBeenCalledWith(
			"crispy-print-preview",
			"Sales Invoice",
			"SINV-1"
		)
	})
})
