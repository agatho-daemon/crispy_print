import { describe, expect, it } from "vitest"
import { typstColor, typstLength, typstQuoted } from "../../typst/typstEscaping"

describe("typst escaping helpers", () => {
	it("escapes strings before embedding in Typst literals", () => {
		expect(typstQuoted('Inter"; #panic() //')).toBe('"Inter\\"; #panic() //"')
		expect(typstQuoted("Line\nBreak\\")).toBe('"Line\\nBreak\\\\"')
	})

	it("only accepts strict hex colors", () => {
		expect(typstColor("#abc")).toBe('rgb("abc")')
		expect(typstColor("#aabbccdd")).toBe('rgb("aabbccdd")')
		expect(typstColor('#fff"); #panic()')).toBe("none")
		expect(typstColor("red")).toBe("none")
	})

	it("normalizes safe Typst lengths and rejects injected values", () => {
		expect(typstLength("12", 9)).toBe("12pt")
		expect(typstLength("10mm", 9)).toBe("10mm")
		expect(typstLength('10pt); #panic() //', 9)).toBe("9pt")
	})
})
