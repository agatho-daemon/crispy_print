// utils/formatLoader.ts
// Modular utilities for loading and managing Crispy Format data

declare const frappe: any

export interface FormatInfo {
	name: string
	doc_type: string
	is_default?: number
}

export interface PageSettings {
	pageSize: string
	orientation: string
	margins: {
		top: number
		bottom: number
		left: number
		right: number
	}
	fontFamily?: string
	fontSize?: number
	letterhead: string
}

export interface FormatData {
	name: string
	doc_type: string
	layout_json: string
	page_settings: string
	is_default?: number
}

/**
 * Get all Crispy Formats for a specific DocType
 */
export async function getFormatsForDoctype(doctype: string): Promise<FormatInfo[]> {
	try {
		const response = await frappe.call({
			method: "crispy_print.api.get_crispy_formats_for_doctype",
			args: { doctype }
		})
		return response.message || []
	} catch (error) {
		console.error("[FormatLoader] Error fetching formats:", error)
		return []
	}
}

/**
 * Get the default format for a DocType
 */
export async function getDefaultFormat(doctype: string): Promise<string | null> {
	try {
		const formats = await frappe.db.get_list("Crispy Format", {
			filters: {
				doc_type: doctype,
				is_default: 1
			},
			fields: ["name"],
			limit: 1
		})
		return formats.length > 0 ? formats[0].name : null
	} catch (error) {
		console.error("[FormatLoader] Error fetching default format:", error)
		return null
	}
}

/**
 * Load complete format data including layout and page settings
 */
export async function loadFormatData(formatName: string): Promise<{
	layout: any
	pageSettings: PageSettings
	formatDoc: FormatData
} | null> {
	try {
		const doc = await frappe.db.get_doc("Crispy Format", formatName) as FormatData

		let layout = null
		let pageSettings: PageSettings = {
			pageSize: "A4",
			orientation: "portrait",
			margins: { top: 25, bottom: 20, left: 20, right: 20 },
			letterhead: ""
		}

		// Parse layout JSON
		if (doc.layout_json) {
			try {
				layout = JSON.parse(doc.layout_json)
			} catch (e) {
				console.error("[FormatLoader] Failed to parse layout_json:", e)
			}
		}

		// Parse page settings
		if (doc.page_settings) {
			try {
				const settings = JSON.parse(doc.page_settings)
				pageSettings = {
					pageSize: settings.pageSize || "A4",
					orientation: settings.orientation || "portrait",
					margins: settings.margins || { top: 25, bottom: 20, left: 20, right: 20 },
					fontFamily: settings.fontFamily,
					fontSize: settings.fontSize,
					letterhead: settings.letterhead || ""
				}
			} catch (e) {
				console.error("[FormatLoader] Failed to parse page_settings:", e)
			}
		}

		return { layout, pageSettings, formatDoc: doc }
	} catch (error) {
		console.error("[FormatLoader] Error loading format data:", error)
		return null
	}
}

/**
 * Get all available Letter Heads
 */
export async function getLetterheads(): Promise<string[]> {
	try {
		const letterheads = await frappe.db.get_list("Letter Head", {
			fields: ["name"],
			order_by: "name asc"
		})
		return letterheads.map((lh: any) => lh.name)
	} catch (error) {
		console.error("[FormatLoader] Error fetching letterheads:", error)
		return []
	}
}

/**
 * Get full Letter Head document with image
 */
export async function getLetterheadData(letterheadName: string): Promise<any | null> {
	if (!letterheadName) return null
	
	try {
		const doc = await frappe.db.get_doc("Letter Head", letterheadName)
		console.log("[FormatLoader] Letterhead data fetched:", letterheadName, doc)
		return doc
	} catch (error) {
		console.error("[FormatLoader] Error fetching letterhead data:", error)
		return null
	}
}
