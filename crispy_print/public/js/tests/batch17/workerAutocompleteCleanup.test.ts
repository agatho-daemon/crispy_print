import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"
import { createSampleDocAutocomplete } from "../../typst/workerAutocomplete"

function makeAutocomplete(input: HTMLInputElement) {
	return createSampleDocAutocomplete({
		previewPane: document.body,
		getInput: () => input,
		getCurrentDoctype: () => "Sales Invoice",
		setCurrentDoctype: vi.fn(),
		setCurrentDocname: vi.fn(),
		clearSelectedDocument: vi.fn(),
		onSelect: vi.fn(),
		setFetchingStatus: vi.fn(),
	})
}

describe("worker autocomplete cleanup", () => {
	beforeEach(() => {
		vi.useFakeTimers()
		document.body.innerHTML = '<input id="typst-sample-doc-input" />'
		;(globalThis as any).__ = (value: string) => value
		;(globalThis as any).frappe = {
			call: vi.fn(),
		}
	})

	afterEach(() => {
		vi.useRealTimers()
		vi.unstubAllGlobals()
		document.body.innerHTML = ""
	})

	it("does not require awesomplete.destroy during cleanup", () => {
		const input = document.querySelector<HTMLInputElement>("#typst-sample-doc-input")!
		;(globalThis as any).Awesomplete = vi.fn(function (this: any) {
			this.list = []
		})

		const autocomplete = makeAutocomplete(input)
		autocomplete.setup("Sales Invoice")

		expect(() => autocomplete.cleanup()).not.toThrow()
	})

	it("cancels pending debounced searches on cleanup", () => {
		const input = document.querySelector<HTMLInputElement>("#typst-sample-doc-input")!
		;(globalThis as any).Awesomplete = vi.fn(function (this: any) {
			this.list = []
			this.destroy = vi.fn()
		})

		const autocomplete = makeAutocomplete(input)
		autocomplete.setup("Sales Invoice")
		input.value = "INV"
		input.dispatchEvent(new Event("input"))
		autocomplete.cleanup()

		vi.advanceTimersByTime(300)
		expect((globalThis as any).frappe.call).not.toHaveBeenCalled()
	})

	it("localizes the document search placeholder", () => {
		const input = document.querySelector<HTMLInputElement>("#typst-sample-doc-input")!
		;(globalThis as any).__ = (value: string, replacements?: string[]) => {
			if (value === "Sales Invoice") return "فاتورة مبيعات"
			if (value === "Search {0}...") return `البحث عن ${replacements?.[0]}...`
			return value
		}
		;(globalThis as any).Awesomplete = vi.fn(function (this: any) {
			this.list = []
		})

		const autocomplete = makeAutocomplete(input)
		autocomplete.setup("Sales Invoice")

		expect(input.placeholder).toBe("البحث عن فاتورة مبيعات...")
	})
})
