import { ref } from "vue"
import {
	getCompanies,
	getLetterheads,
	type CompanyListArgs,
	type CompanyOption,
} from "../api/crispy"
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

	async function fetchLetterheads(args: {
		company?: string | null
		include_current?: string | null
	} = {}) {
		loadingLetterheads.value = true
		try {
			availableLetterheads.value = await getLetterheads(args)
		} catch (error) {
			logger.error("Failed to fetch letterheads", error)
			availableLetterheads.value = []
		} finally {
			loadingLetterheads.value = false
		}
	}

	async function fetchCompanies(args: CompanyListArgs = {}) {
		if (typeof frappe === "undefined") {
			availableCompanies.value = []
			return
		}

		loadingCompanies.value = true
		try {
			availableCompanies.value = await getCompanies(args)
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
