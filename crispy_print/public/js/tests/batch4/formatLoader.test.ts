import { beforeEach, describe, expect, it, vi } from "vitest"

const getLetterheadDoc = vi.fn(async (name: string) => ({ name, image: `/files/${name}.png` }))

vi.mock("../../api/crispy", () => ({
	getLetterheadDoc: (name: string) => getLetterheadDoc(name),
}))

describe("formatLoader letterhead cache", async () => {
	const { clearLetterheadCache, resolveLetterheadDoc } = await import("../../utils/formatLoader")

	beforeEach(() => {
		getLetterheadDoc.mockClear()
		clearLetterheadCache()
	})

	it("returns null for empty names", async () => {
		await expect(resolveLetterheadDoc("")).resolves.toBeNull()
		await expect(resolveLetterheadDoc(null)).resolves.toBeNull()
		await expect(resolveLetterheadDoc(undefined)).resolves.toBeNull()
	})

	it("caches letterhead docs", async () => {
		const first = await resolveLetterheadDoc("Letterhead A")
		const second = await resolveLetterheadDoc("Letterhead A")
		expect(first).toEqual(second)
		expect(getLetterheadDoc).toHaveBeenCalledTimes(1)
	})
})
