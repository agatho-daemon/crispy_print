import { describe, expect, it, vi } from "vitest"
import { pickFormatName } from "../../utils/formatSelection"
import { getCrispyBuilderFormatName, getRouteSafe } from "../../utils/routes"

describe("formatSelection", () => {
	it("picks requested format when available", () => {
		const formats = [{ name: "A" }, { name: "B" }]
		expect(pickFormatName(formats, "B")).toBe("B")
	})

	it("picks default format when flagged", () => {
		const formats = [{ name: "A" }, { name: "B", is_default: 1 }]
		expect(pickFormatName(formats)).toBe("B")
	})

	it("falls back to first format", () => {
		const formats = [{ name: "A" }, { name: "B" }]
		expect(pickFormatName(formats)).toBe("A")
	})

	it("returns null when no formats", () => {
		expect(pickFormatName([], null)).toBeNull()
	})
})

describe("routes helpers", () => {
	it("returns empty route when frappe is unavailable", () => {
		const original = (globalThis as any).frappe
		delete (globalThis as any).frappe
		expect(getRouteSafe()).toEqual([])
		;(globalThis as any).frappe = original
	})

	it("returns crispy format name from route", () => {
		const original = (globalThis as any).frappe
		;(globalThis as any).frappe = {
			get_route: vi.fn(() => ["crispy-format-builder", "My Format"]),
		}

		expect(getRouteSafe()).toEqual(["crispy-format-builder", "My Format"])
		expect(getCrispyBuilderFormatName()).toBe("My Format")
		;(globalThis as any).frappe = original
	})
})
