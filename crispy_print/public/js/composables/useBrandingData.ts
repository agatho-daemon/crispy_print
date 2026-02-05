import { ref } from "vue"
import { getCompanies, getLetterheads, type CompanyOption } from "../api/crispy"
import { getLogger } from "../logger"

const logger = getLogger({ module: "BrandingData" })

export function useBrandingData() {
	const availableLetterheads = ref<string[]>([])
	const loadingLetterheads = ref(false)
	const availableCompanies = ref<CompanyOption[]>([])
	const loadingCompanies = ref(false)

	function resolveCompanyLogo(companyName: string): string {
		if (!companyName) return ""
		const match = availableCompanies.value.find((company) => company.name === companyName)
		return match?.company_logo || ""
	}

	async function fetchLetterheads() {
		loadingLetterheads.value = true
		try {
			availableLetterheads.value = await getLetterheads()
		} catch (error) {
			logger.error("Failed to fetch letterheads", error)
			availableLetterheads.value = []
		} finally {
			loadingLetterheads.value = false
		}
	}

	async function fetchCompanies() {
		if (typeof frappe === "undefined") {
			availableCompanies.value = []
			return
		}

		loadingCompanies.value = true
		try {
			availableCompanies.value = await getCompanies()
		} catch (error) {
			logger.error("Failed to fetch companies", error)
			availableCompanies.value = []
		} finally {
			loadingCompanies.value = false
		}
	}

	return {
		availableLetterheads,
		loadingLetterheads,
		availableCompanies,
		loadingCompanies,
		resolveCompanyLogo,
		fetchLetterheads,
		fetchCompanies,
	}
}
