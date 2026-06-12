import { describe, expect, it, vi } from "vitest"
import { useBrandingData } from "../../composables/useBrandingData"

const getLetterheads = vi.fn(async (_args?: Record<string, unknown>) => [
	"Letterhead A",
	"Letterhead B",
])
const getCompanies = vi.fn(async (_args?: Record<string, unknown>) => [
	{ name: "Alpha Co", abbr: "ALP", company_logo: "/files/alpha.png" },
])

vi.mock("../../api/crispy", () => ({
	getLetterheads: (args?: Record<string, unknown>) => getLetterheads(args),
	getCompanies: (args?: Record<string, unknown>) => getCompanies(args),
}))

describe("useBrandingData", () => {
	it("fetches letterheads", async () => {
		const { fetchLetterheads, availableLetterheads, loadingLetterheads } = useBrandingData()
		const pending = fetchLetterheads({ company: "Alpha Co", include_current: "Letterhead B" })
		expect(loadingLetterheads.value).toBe(true)
		await pending
		expect(availableLetterheads.value.length).toBe(2)
		expect(loadingLetterheads.value).toBe(false)
		expect(getLetterheads).toHaveBeenCalledWith({
			company: "Alpha Co",
			include_current: "Letterhead B",
		})
	})

	it("fetches companies and resolves logo", async () => {
		;(globalThis as any).frappe = {}
		const { fetchCompanies, resolveCompanyLogo, availableCompanies } = useBrandingData()
		await fetchCompanies({ include_current: "Alpha Co" })
		expect(availableCompanies.value.length).toBe(1)
		expect(resolveCompanyLogo("Alpha Co")).toBe("/files/alpha.png")
		expect(getCompanies).toHaveBeenCalledWith({ include_current: "Alpha Co" })
	})
})
