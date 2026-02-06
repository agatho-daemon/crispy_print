import { describe, expect, it } from "vitest"

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
