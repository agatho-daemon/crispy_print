import { afterEach, describe, expect, it, vi } from "vitest"
import { readFileSync } from "node:fs"
import { resolve, dirname } from "node:path"
import { fileURLToPath } from "node:url"

const sourceDir = resolve(dirname(fileURLToPath(import.meta.url)), "../..")
const load = (file: string) => (0, eval)(readFileSync(resolve(sourceDir, file), "utf8"))

afterEach(() => {
	vi.unstubAllGlobals()
	document.body.replaceChildren()
})

describe.each([
	["en", "Crispy Print", "Open Crispy Print Preview"],
	["zh", "脆皮打印", "打开 Crispy Print 预览"],
])("print toolbar (%s)", (_language, label, title) => {
	function setup() {
		vi.stubGlobal("__", (text: string) => text === "Open Crispy Print Preview" ? title : label)
		vi.stubGlobal("crispy_print", {})
		const frappe = {
			provide: vi.fn(),
			set_route: vi.fn(),
			call: vi.fn(),
			ui: { form: { on: vi.fn() } },
		}
		vi.stubGlobal("frappe", frappe)
		vi.stubGlobal("$", () => ({ on: vi.fn() }))
		delete (window as any).__crispy_qr_patched__
		load("report_button.bundle.js")
		return frappe
	}

	it.each(["legacy", "escaped-label"])("renders the image with the %s button structure", (structure) => {
		setup()
		const element = document.createElement("button")
		if (structure === "escaped-label") {
			element.innerHTML = '<span class="es-spinner"></span><span class="es-button__loading-label">Busy</span><span class="es-button__label"></span>'
			element.querySelector(".es-button__label")!.textContent = label
		} else {
			element.textContent = label
		}
		const spinner = element.querySelector(".es-spinner")
		const loadingLabel = element.querySelector(".es-button__loading-label")
		const onClick = vi.fn()
		element.addEventListener("click", onClick)
		;(globalThis as any).crispy_print.decorate_print_button([element])
		;(globalThis as any).crispy_print.decorate_print_button([element])
		expect(element.querySelectorAll("img")).toHaveLength(1)
		const image = element.querySelector("img")!
		expect(image.getAttribute("src")).toBe("/assets/crispy_print/icons/typst.svg")
		expect(image.alt).toBe(label)
		expect(element.title).toBe(title)
		expect(element.getAttribute("aria-label")).toBe(label)
		expect(element.textContent).not.toContain("<img")
		element.click()
		expect(onClick).toHaveBeenCalledOnce()
		image.dispatchEvent(new Event("error"))
		expect(element.textContent).toContain(label)
		if (structure === "escaped-label") {
			expect(element.querySelector(".es-spinner")).toBe(spinner)
			expect(element.querySelector(".es-button__loading-label")).toBe(loadingLabel)
		}
	})

	it("passes plain text to the form API and retains preview routing", () => {
		const frappe = setup()
		load("crispy_print_button.js")
		;(window as any).typstPrint.registerButtonsFor(["Sales Invoice"])
		const refresh = frappe.ui.form.on.mock.calls[0][1].refresh
		const element = document.createElement("button")
		const addButton = vi.fn((text: string) => {
			element.textContent = text
			return [element]
		})
		refresh({ is_new: () => false, add_custom_button: addButton, doctype: "Sales Invoice", docname: "TEST-001" })
		expect(addButton.mock.calls[0][0]).toBe(label)
		expect(element.querySelector("img")).not.toBeNull()
		const callback = (addButton.mock.calls[0] as any)[1]
		callback()
		expect(frappe.set_route).toHaveBeenCalledWith("crispy-print-preview", "Sales Invoice", "TEST-001")
		addButton.mockClear()
		refresh({ is_new: () => true, add_custom_button: addButton })
		expect(addButton).not.toHaveBeenCalled()
	})

	it("passes plain text to the report API for toolbar and mobile menu labels", () => {
		const frappe = setup()
		vi.stubGlobal("$", () => ({ on: vi.fn() }))
		delete (window as any).__crispy_qr_patched__
		load("report_button.bundle.js")
		const element = document.createElement("button")
		const addButton = vi.fn((text: string) => {
			element.textContent = text
			return [element]
		})
		const report = {
			report_name: "Stock Balance",
			page: { add_inner_button: addButton },
			get_filter_values: () => ({ company: "Example" }),
			columns: [{ fieldname: "item_code" }],
		}
		;(globalThis as any).crispy_print.add_print_button(report)
		expect(addButton.mock.calls[0][0]).toBe(label)
		expect(element.querySelector("img")!.alt).toBe(label)
		expect(element.title).toBe(title)
		const callback = (addButton.mock.calls[0] as any)[1]
		callback()
		expect(frappe.set_route).toHaveBeenCalledWith("crispy-print-preview", "report", "Stock Balance")
	})
})
