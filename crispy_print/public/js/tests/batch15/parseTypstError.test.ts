import { describe, expect, it, vi } from "vitest"

import { parseTypstError } from "../../typst/setupWorker"

describe("parseTypstError", () => {
	it("extracts error message and location", () => {
		const raw =
			'Typst compilation failed: error: unknown variable: foo\\n  ┌─ document.typ:12:5\\n  │\\n12 │ foo\\n  │'
		const result = parseTypstError(raw)
		expect(result).toContain("Error: unknown variable: foo")
		expect(result).toContain("Location: Line 12, Column 5")
		expect(result).toContain("Code:")
	})
})


describe("classified preview errors", () => {
	it.each([
		[413, "request-size limit"],
		[500, "application and reverse-proxy logs"],
		[502, "valid backend response"],
		[503, "service is unavailable"],
		[504, "gateway timed out"],
	])("preserves HTTP %s and its neutral hint", (status, hint) => {
		vi.stubGlobal("__", (text: string) => text)
		try {
			const text = parseTypstError({ kind: "request", status, message: "raw HTML must not appear" })
			expect(text).toContain(`HTTP ${status}`)
			expect(text.toLowerCase()).toContain(hint.toLowerCase())
			expect(text).not.toContain("raw HTML")
		} finally { vi.unstubAllGlobals() }
	})

	it("preserves a safe application message", () => {
		expect(parseTypstError({ kind: "application", message: "Typst compilation failed. Check the server error log for details." }))
			.toBe("Typst compilation failed. Check the server error log for details.")
	})
})
