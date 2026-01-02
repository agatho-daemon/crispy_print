import { describe, expect, it, vi } from "vitest"
import { useBrandingData } from "../../composables/useBrandingData"

const getLetterheads = vi.fn(async () => ["Letterhead A", "Letterhead B"])
const getCompanies = vi.fn(async () => [
	{ name: "Alpha Co", abbr: "ALP", company_logo: "/files/alpha.png" },
])

vi.mock("../../api/crispy", () => ({
	getLetterheads: () => getLetterheads(),
	getCompanies: () => getCompanies(),
}))

describe("useBrandingData", () => {
	it("fetches letterheads", async () => {
		const { fetchLetterheads, availableLetterheads, loadingLetterheads } = useBrandingData()
		const pending = fetchLetterheads()
		expect(loadingLetterheads.value).toBe(true)
		await pending
		expect(availableLetterheads.value.length).toBe(2)
		expect(loadingLetterheads.value).toBe(false)
	})

	it("fetches companies and resolves logo", async () => {
		;(globalThis as any).frappe = {}
		const { fetchCompanies, resolveCompanyLogo, availableCompanies } = useBrandingData()
		await fetchCompanies()
		expect(availableCompanies.value.length).toBe(1)
		expect(resolveCompanyLogo("Alpha Co")).toBe("/files/alpha.png")
	})
})
