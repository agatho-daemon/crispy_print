// utils/layout.ts
// Utility functions for creating and manipulating Typst print layouts

export interface DocField {
	fieldname: string
	label: string
	fieldtype?: string
	options?: string
	print_hide?: number
}

export interface TableColumn {
	fieldname: string
	label: string
	fieldtype: string
	width?: string
	align?: "left" | "center" | "right"
}

export interface LayoutField {
	fieldname: string
	label: string
	fieldtype: string
	options?: string
	align?: "left" | "center" | "right"
	table_columns?: TableColumn[]
	field_template?: string
}

export interface LayoutColumn {
	label: string
	fields: LayoutField[]
}

export interface LayoutSection {
	label: string
	columns: LayoutColumn[]
	id?: number
	page_break?: boolean
}

export interface CrispyLayout {
	header?: string
	sections: LayoutSection[]
}

function generateLayoutId(): number {
	return Date.now() + Math.random()
}

/**
 * Normalize layout structure for consistent UI + serialization.
 * - Ensures arrays exist (`sections`, `columns`, `fields`)
 * - Ensures every section has a stable `id`
 * - Strips legacy/derived keys (e.g. `has_fields`)
 * - Leaves layout empty if it's empty (no auto-seeding)
 */
export function normalizeLayout(layout: CrispyLayout | null | undefined): CrispyLayout {
	const base: CrispyLayout = {
		header: layout?.header || "",
		sections: Array.isArray(layout?.sections) ? layout!.sections : [],
	}

	const normalizedSections: LayoutSection[] = base.sections.map((rawSection) => {
		const { has_fields: _ignoredHasFields, ...section } = (rawSection || {}) as any

		const columns = Array.isArray(section.columns) ? section.columns : []
		const normalizedColumns: LayoutColumn[] = columns.map((rawColumn: any) => {
			const column: LayoutColumn = {
				label: typeof rawColumn?.label === "string" ? rawColumn.label : "",
				fields: Array.isArray(rawColumn?.fields) ? rawColumn.fields : [],
			}

			column.fields = column.fields
				.filter(Boolean)
				.map((rawField: any) => {
					const fieldtype = rawField?.fieldtype || "Data"
					return {
						...rawField,
						fieldtype,
						label: typeof rawField?.label === "string" ? rawField.label : "",
						fieldname: typeof rawField?.fieldname === "string" ? rawField.fieldname : "",
						align: rawField?.align || getDefaultFieldAlignment(fieldtype),
					} as LayoutField
				})
				.filter((f) => Boolean(f.fieldname))

			return column
		})

		return {
			label: typeof section.label === "string" ? section.label : "",
			columns: normalizedColumns,
			id: typeof section.id === "number" ? section.id : generateLayoutId(),
		}
	})

	return {
		...base,
		sections: normalizedSections,
	}
}

/**
 * Creates a default Typst-based layout from DocType metadata
 * Mirrors Frappe's print format builder behavior
 */
export function createDefaultLayout(meta: any, crispyFormat: any): CrispyLayout {
	if (!meta?.fields) {
		return { sections: [] }
	}

	const layout: CrispyLayout & { sections: LayoutSection[] } = {
		header: getDefaultHeader(meta),
		sections: [],
	}

	const sections = layout.sections

	let currentSection: LayoutSection | null = null
	let currentColumn: LayoutColumn | null = null

	const setSection = (df?: DocField) => {
		const source = df || { label: "" }
		currentSection = {
			label: source.label || "",
			columns: [],
			id: generateLayoutId(),
		}
		currentColumn = null
		sections.push(currentSection)
	}

	const setColumn = (df?: DocField) => {
		if (!currentSection) {
			setSection()
		}
		const source = df || { label: "" }
		currentColumn = {
			label: source.label || "",
			fields: [],
		}
		currentSection!.columns.push(currentColumn)
	}

	for (let dfRaw of meta.fields as DocField[]) {
		let df = dfRaw.fieldname ? (JSON.parse(JSON.stringify(dfRaw)) as DocField) : null
		if (!df) continue

		if (df.fieldtype === "Section Break") {
			setSection(df)
		} else if (df.fieldtype === "Column Break") {
			setColumn(df)
		} else if (df.label) {
			if (!currentColumn) setColumn()

			if (!df.print_hide) {
				const fieldtype = df.fieldtype || "Data"

				const field: LayoutField = {
					label: df.label,
					fieldname: df.fieldname,
					fieldtype: fieldtype,
					options: df.options,
					align: getDefaultFieldAlignment(fieldtype),
				}

				const fieldTemplate = getFieldTemplate(crispyFormat, df.fieldname, df)
				if (fieldTemplate) {
					field.label = `${__(df.label, null, (df as any).parent)} (${__("Field Template")})`
					field.fieldtype = "Field Template"
					field.field_template = (fieldTemplate as any).name
					field.fieldname = "_template"
				}

				if (df.fieldtype === "Table") {
					field.table_columns = getTableColumns(df)
				}

				currentColumn!.fields.push(field)
			}
		}
	}

	const filteredSections = sections.filter((section: LayoutSection) =>
		section.columns?.some((col: LayoutColumn) => col.fields?.length)
	)
	layout.sections = filteredSections

	return normalizeLayout(layout)
}

/**
 * Get table columns for a child table field
 */
export function getTableColumns(dfOrDoctype: DocField | string): TableColumn[] {
	const childDoctype = typeof dfOrDoctype === "string" ? dfOrDoctype : dfOrDoctype.options
	const parentHasLabel =
		typeof dfOrDoctype === "string" ? true : Boolean((dfOrDoctype as DocField).label)

	if (typeof frappe === "undefined") {
		return []
	}

	if (!childDoctype) {
		return []
	}

	const childMeta = frappe.get_meta(childDoctype)
	if (!childMeta?.fields) {
		return []
	}

	const tableColumns: TableColumn[] = []

	const candidates = childMeta.fields
		.filter((f: DocField) => !f.print_hide && f.fieldname && f.label)
		.filter(
			(f: DocField) => f.fieldtype && !["Section Break", "Column Break"].includes(f.fieldtype)
		)

	for (const f of candidates) {
		if (!parentHasLabel) break

		// Use Typst width values
		const width = "auto" // Default to auto width

		tableColumns.push({
			fieldname: f.fieldname,
			label: f.label,
			fieldtype: f.fieldtype,
			width,
			align: getDefaultFieldAlignment(f.fieldtype),
		})
	}

	return tableColumns
}

function getFieldTemplate(crispyFormat: any, fieldname: string, df: DocField) {
	const templates = crispyFormat?.__onload?.print_templates || []
	for (const template of templates) {
		if (template.field === fieldname) {
			return template
		}
	}
	return null
}

function getDefaultHeader(meta: any) {
	// Header rendering is handled via Typst `doc_header` on the Crispy Format doctype.
	// Keep layout.header empty for legacy compatibility.
	return ""
}

/**
 * Pick specific keys from an object (for serialization)
 */
export function pluck<T extends Record<string, any>>(obj: T, keys: (keyof T)[]): Partial<T> {
	const result: Partial<T> = {}
	for (const key of keys) {
		if (key in obj) {
			result[key] = obj[key]
		}
	}
	return result
}

/**
 * Convert layout to JSON string for storage
 */
export function serializeLayout(layout: CrispyLayout): string {
	const normalized = normalizeLayout(layout)

	const cleanedSections = (normalized.sections || []).map((section) => {
		const { has_fields: _ignored, ...restSection } = section as any
		return {
			...restSection,
			columns: (restSection.columns || []).map((column: any) => ({ ...column })),
		}
	})

	return JSON.stringify(
		{
			...normalized,
			sections: cleanedSections,
		}
		// null,
		// 2
	)
}

/**
 * Parse layout from JSON string
 */
export function deserializeLayout(json: string): CrispyLayout | null {
	try {
		const parsed = JSON.parse(json) as CrispyLayout
		return normalizeLayout(parsed)
	} catch (e) {
		console.error("[Layout] Failed to parse layout JSON:", e)
		return null
	}
}

/**
 * Get default alignment for a field based on its fieldtype
 * Numeric fields default to right alignment, like Frappe
 */
export function getDefaultFieldAlignment(fieldtype: string): "left" | "center" | "right" {
	const numericTypes = ["Int", "Float", "Currency", "Percent"]
	return numericTypes.includes(fieldtype) ? "right" : "left"
}
