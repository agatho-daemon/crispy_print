// utils/layout.ts
// Utility functions for creating and manipulating Typst print layouts

declare const frappe: any
declare const __: any
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
	width?: number
}

export interface LayoutField {
	fieldname: string
	label: string
	fieldtype: string
	options?: string
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
}

export interface CrispyLayout {
	header?: string
	sections: LayoutSection[]
}

/**
 * Creates a default Typst-based layout from DocType metadata
 * Mirrors Frappe's beta print builder behavior
 */
export function createDefaultLayout(meta: any, crispyFormat: any): CrispyLayout {
	if (!meta?.fields) {
		return { sections: [] }
	}

	type SectionWithFields = LayoutSection & { has_fields?: boolean }

	const layout: CrispyLayout & { sections: SectionWithFields[] } = {
		header: getDefaultHeader(meta),
		sections: [],
	}

	const sections = layout.sections

	let currentSection: SectionWithFields | null = null
	let currentColumn: LayoutColumn | null = null

	const setSection = (df?: DocField) => {
		const source = df || { label: "" }
		currentSection = {
			label: source.label || "",
			columns: [],
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
				const field: LayoutField = {
					label: df.label,
					fieldname: df.fieldname,
					fieldtype: df.fieldtype || "Data",
					options: df.options,
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
				currentSection!.has_fields = true
			}
		}
	}

	const filteredSections = (sections as SectionWithFields[]).filter(
		(section: SectionWithFields) => Boolean(section.has_fields)
	)
	layout.sections = filteredSections

	return layout
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
	let totalWidth = 0

	const candidates = childMeta.fields
		.filter((f: DocField) => !f.print_hide && f.fieldname && f.label)
		.filter(
			(f: DocField) =>
				f.fieldtype && !["Section Break", "Column Break"].includes(f.fieldtype)
		)

	for (const f of candidates) {
		if (!parentHasLabel) break
		if (totalWidth >= 100) break
		const rawWidth = (f as any).width
		const width =
			typeof rawWidth === "number" && rawWidth < 100 ? rawWidth : rawWidth ? 20 : 10

		tableColumns.push({
			fieldname: f.fieldname,
			label: f.label,
			fieldtype: f.fieldtype,
			width,
		})
		totalWidth += width
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
	return `<div class="document-header">
\t<h3>${meta?.name || ""}</h3>
\t<p>{{ doc.name }}</p>
</div>`
}

/**
 * Pick specific keys from an object (for serialization)
 */
export function pluck<T extends Record<string, any>>(
	obj: T,
	keys: (keyof T)[]
): Partial<T> {
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
	return JSON.stringify(layout, null, 2)
}

/**
 * Parse layout from JSON string
 */
export function deserializeLayout(json: string): CrispyLayout | null {
	try {
		return JSON.parse(json)
	} catch (e) {
		console.error("[Layout] Failed to parse layout JSON:", e)
		return null
	}
}
