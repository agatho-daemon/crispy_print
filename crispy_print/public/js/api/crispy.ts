// Crispy Print API wrappers (typed).

import { call, getDoc, getList, setValue } from "./frappe"
import type { PageSettings } from "../utils/pageSettings"
import type { CrispyLayout } from "../utils/layout"

export interface CrispyFormatDoc {
	name: string
	doc_type?: string
	crispy_format_type?: string
	report?: string
	contract?: string
	is_default?: number
	is_generic?: number
	generic_report_type?: string
	doc_header?: string
	doc_footer?: string
	qrcode?: number
	raw_typst?: number
	layout_json?: string
	page_settings?: string
	typst_code?: string
	typst_preamble?: string
	__onload?: any
}

export interface CompanyOption {
	name: string
	abbr?: string
	company_logo?: string
}

export async function getCrispyFormat(name: string): Promise<CrispyFormatDoc> {
	return await getDoc<CrispyFormatDoc>("Crispy Format", name)
}

export async function saveCrispyFormat(
	name: string,
	values: {
		layout_json?: string
		page_settings?: string
		doc_header?: string
		doc_footer?: string
		typst_code?: string
		typst_preamble?: string
		raw_typst?: number
	}
): Promise<void> {
	await setValue("Crispy Format", name, values)
}

export async function getCrispyFormatsForDoctype(
	doctype: string
): Promise<Array<{ name: string; doc_type: string; is_default?: number }>> {
	const res = await call<Array<{ name: string; doc_type: string; is_default?: number }>>({
		method: "crispy_print.api.get_crispy_formats_for_doctype",
		args: { doctype },
	})
	return res.message || []
}

export async function getDefaultCrispyFormatForDoctype(doctype: string): Promise<string | null> {
	const rows = await getList<{ name: string }>("Crispy Format", {
		filters: { doc_type: doctype, is_default: 1 },
		fields: ["name"],
		limit: 1,
	})
	return rows.length ? rows[0].name : null
}

export async function getLetterheads(): Promise<string[]> {
	const rows = await getList<{ name: string }>("Letter Head", {
		fields: ["name"],
		order_by: "name asc",
	})
	return rows.map((r) => r.name)
}

export async function getLetterheadDoc(name: string): Promise<any> {
	return await getDoc<any>("Letter Head", name)
}

export async function getCompanies(): Promise<CompanyOption[]> {
	return await getList<CompanyOption>("Company", {
		fields: ["name", "abbr", "company_logo"],
		order_by: "name asc",
	})
}

export async function getTypstLocalFonts(): Promise<string[]> {
	const res = await call<string[]>({
		method: "crispy_print.api.get_typst_local_fonts",
	})
	return res.message || []
}

export function encodePageSettings(settings: PageSettings): string {
	return JSON.stringify(settings)
}

export function encodeLayout(layoutJson: CrispyLayout): string {
	return JSON.stringify(layoutJson)
}
