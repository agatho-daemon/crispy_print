import type { CrispyLayout, LayoutField } from "./layout"

export interface FrappeFormattingEnv {
	format: (value: any, df: any, opts: any, doc: any) => any
	getDocfield: (doctype: string, fieldname: string) => any
	stripHtml?: (value: string) => string
	noValueType?: string[]
}

function fallbackStripHtml(value: string) {
	return value
		.replace(/(<br\s*\/?>\s*)+/gi, "\n") // Consecutive <br> tags → single \n
		.replace(/<[^>]+>/g, "")
		.replace(/\n{2,}/g, "\n") // Collapse multiple consecutive newlines to single \n
}

export function applyFrappeFormattingToDoc(opts: {
	layout: CrispyLayout | null | undefined
	doctype: string | null | undefined
	fullDoc: Record<string, any> | null | undefined
	filteredDoc: Record<string, any> | null | undefined
	env: FrappeFormattingEnv | null | undefined
}): void {
	const { layout, doctype, fullDoc, filteredDoc, env } = opts

	if (!layout || !doctype || !fullDoc || !filteredDoc || !env) {
		return
	}

	const normalizeFieldtype = (df: any) => String(df?.fieldtype || "").replace(/\s+/g, "")
	const shouldFormatFieldtype = (fieldtype: string) =>
		["Currency", "Int", "Float", "Percent", "Date", "Datetime", "Time"].includes(fieldtype)

	const shouldCleanupText = (fieldtype: string) =>
		[
			"SmallText",
			"Text",
			"TextEditor",
			"LongText",
			"HTML",
			"HTMLEditor",
			"ReadOnly",
			"Data",
		].includes(fieldtype)

	const stripHtml = (value: any) => {
		if (typeof value !== "string") return value
		return env.stripHtml ? env.stripHtml(value) : fallbackStripHtml(value)
	}

	const formatValue = (value: any, df: any) => {
		// `only_value` avoids HTML wrappers (right-align spans, etc.)
		const formatted = stripHtml(env.format(value, df, { only_value: 1 }, fullDoc))
		// Additional cleanup: collapse consecutive newlines
		return typeof formatted === "string" ? formatted.replace(/\n{2,}/g, "\n").trim() : formatted
	}

	const walkFields = (): LayoutField[] => {
		const out: LayoutField[] = []
		for (const section of layout.sections || []) {
			for (const col of (section as any).columns || []) {
				for (const field of (col as any).fields || []) {
					if (field && field.fieldname) out.push(field as LayoutField)
				}
			}
		}
		return out
	}

	for (const field of walkFields()) {
		if (!field.fieldname) continue

		// Table fields: format each selected column value per row.
		if (field.fieldtype === "Table") {
			const tableFieldname = field.fieldname
			const df = env.getDocfield(doctype, tableFieldname)
			const childDoctype = df?.options || field.options
			if (!childDoctype) continue

			const rows = filteredDoc[tableFieldname]
			if (!Array.isArray(rows) || !rows.length) continue

			const columns = field.table_columns || []
			for (const row of rows) {
				if (!row || typeof row !== "object") continue
				for (const col of columns) {
					if (!col?.fieldname) continue
					const childDf = env.getDocfield(childDoctype, col.fieldname)
					if (!childDf) continue
					if (!(col.fieldname in row)) continue
					const ft = normalizeFieldtype(childDf)
					if (!shouldFormatFieldtype(ft)) continue
					row[col.fieldname] = formatValue(row[col.fieldname], childDf)
				}
			}
			continue
		}

		// Non-table fields: format based on DocType docfield.
		const df = env.getDocfield(doctype, field.fieldname)
		if (!df) continue
		if (!(field.fieldname in filteredDoc)) continue

		const ft = normalizeFieldtype(df)

		// Format numeric/date fields
		if (shouldFormatFieldtype(ft)) {
			filteredDoc[field.fieldname] = formatValue(filteredDoc[field.fieldname], df)
			continue
		}

		// Clean up text fields (strip HTML, collapse newlines)
		if (shouldCleanupText(ft)) {
			const value = filteredDoc[field.fieldname]
			if (typeof value === "string") {
				filteredDoc[field.fieldname] = stripHtml(value)
					.replace(/\n{2,}/g, "\n")
					.trim()
			}
		}
	}
}
