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
	is_advanced?: number
	generic_report_type?: string
	doc_header?: string
	doc_footer?: string
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

export interface ExportPayload {
	schema_version: number
	exported_at: string
	app: string
	format: CrispyFormatDoc
}

export interface ConflictResult {
	schema_version: number
	name: string
	exists: boolean
	conflict: boolean
}

export interface ImportResult {
	success: boolean
	name: string
	warnings: string[]
	conflict_action: "copy" | "overwrite"
}

export interface ReportBuilderDefaults {
	mode: "basic" | "advanced"
	preset: "grid" | "tree" | "summary" | "minimal"
	show_filters: boolean
	show_summary: boolean
	include_total_row: boolean
	show_footer_total: boolean
	chart_enabled: boolean
	chart_width_percent: number
	chart_max_height_pt: number
	chart_card_border: boolean
	chart_spacing_top_pt: number
	chart_spacing_bottom_pt: number
	header_fill: string
	header_text_weight: string
	font_family: string
	font_size_pt: number
	row_striping: boolean
	row_stripe_fill: string
	column_align_strategy: "auto" | "left" | "center" | "right"
	table_inset_x_pt: number
	table_inset_y_pt: number
	table_stroke_top_pt: number
	table_stroke_body_pt: number
	raw_signature: string | null
	report_table_sync_signature: string | null
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
		is_advanced?: number
	}
): Promise<void> {
	await setValue("Crispy Format", name, values)
}

export async function getCrispyFormatsForDoctype(
	doctype: string
): Promise<Array<{ name: string; doc_type: string; is_default?: number }>> {
	const res = await call<Array<{ name: string; doc_type: string; is_default?: number }>>({
		method: "crispy_print.api.v1.get_crispy_formats_for_doctype",
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
		method: "crispy_print.api.v1.get_typst_local_fonts",
	})
	return res.message || []
}

export async function getDefaultReportBuilderConfig(
	genericReportType?: string | null
): Promise<ReportBuilderDefaults> {
	const res = await call<ReportBuilderDefaults>({
		method: "crispy_print.api.v1.get_default_report_builder_config",
		args: { generic_report_type: genericReportType || null },
	})
	if (!res.message) {
		throw new Error("Missing report builder defaults")
	}
	return res.message
}

export function encodePageSettings(settings: PageSettings): string {
	return JSON.stringify(settings)
}

export function encodeLayout(layoutJson: CrispyLayout): string {
	return JSON.stringify(layoutJson)
}

export async function exportCrispyFormat(name: string): Promise<ExportPayload> {
	const res = await call<ExportPayload>({
		method: "crispy_print.api.v1.export_crispy_format",
		args: { name },
	})
	if (!res.message) {
		throw new Error("Missing export payload")
	}
	return res.message
}

export async function checkImportConflicts(payload: unknown): Promise<ConflictResult> {
	const res = await call<ConflictResult>({
		method: "crispy_print.api.v1.check_import_conflicts",
		args: { payload: typeof payload === "string" ? payload : JSON.stringify(payload) },
	})
	if (!res.message) {
		throw new Error("Missing conflict response")
	}
	return res.message
}

export async function importCrispyFormat(
	payload: unknown,
	onConflict: "copy" | "overwrite"
): Promise<ImportResult> {
	const res = await call<ImportResult>({
		method: "crispy_print.api.v1.import_crispy_format",
		args: {
			payload: typeof payload === "string" ? payload : JSON.stringify(payload),
			on_conflict: onConflict,
		},
	})
	if (!res.message) {
		throw new Error("Missing import response")
	}
	return res.message
}
