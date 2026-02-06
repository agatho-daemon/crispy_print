import { describe, expect, it, vi } from "vitest"

import { deepClone } from "../../utils/json"

describe("deepClone", () => {
	it("falls back when structuredClone throws", () => {
		const original = { a: 1, b: { c: 2 } }
		const prev = (globalThis as any).structuredClone
		;(globalThis as any).structuredClone = vi.fn(() => {
			throw new Error("nope")
		})
		const cloned = deepClone(original)
		expect(cloned).not.toBe(original)
		expect(cloned).toEqual(original)
		;(globalThis as any).structuredClone = prev
	})

	it("returns original when JSON clone fails", () => {
		const prev = (globalThis as any).structuredClone
		;(globalThis as any).structuredClone = undefined
		const circular: any = { a: 1 }
		circular.self = circular
		const cloned = deepClone(circular)
		expect(cloned).toBe(circular)
		;(globalThis as any).structuredClone = prev
	})
})
