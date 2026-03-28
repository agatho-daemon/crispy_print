import { describe, expect, it, vi } from "vitest"
import {
	getDefaultFormat,
	getFormatsForDoctype,
	loadFormatData,
	loadLetterheadDoc,
} from "../../utils/formatLoader"

vi.mock("../../api/crispy", () => ({
	getCrispyFormat: vi.fn(async () => {
		throw new Error("nope")
	}),
	getCrispyFormatsForDoctype: vi.fn(async () => {
		throw new Error("nope")
	}),
	getDefaultCrispyFormatForDoctype: vi.fn(async () => {
		throw new Error("nope")
	}),
	getLetterheadDoc: vi.fn(async () => {
		throw new Error("nope")
	}),
	getLetterheads: vi.fn(async (): Promise<unknown[]> => []),
}))

describe("formatLoader error paths", () => {
	it("returns null when format load fails", async () => {
		const spy = vi.spyOn(console, "error").mockImplementation(() => {})
		const result = await loadFormatData("Broken")
		expect(result).toBeNull()
		spy.mockRestore()
	})

	it("returns empty formats list on error", async () => {
		const spy = vi.spyOn(console, "error").mockImplementation(() => {})
		const result = await getFormatsForDoctype("Invoice")
		expect(result).toEqual([])
		spy.mockRestore()
	})

	it("returns null default format on error", async () => {
		const spy = vi.spyOn(console, "error").mockImplementation(() => {})
		const result = await getDefaultFormat("Invoice")
		expect(result).toBeNull()
		spy.mockRestore()
	})

	it("returns null when letterhead fetch fails", async () => {
		const spy = vi.spyOn(console, "error").mockImplementation(() => {})
		const result = await loadLetterheadDoc("Letterhead 1")
		expect(result).toBeNull()
		spy.mockRestore()
	})
})
