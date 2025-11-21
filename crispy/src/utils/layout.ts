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
}

export interface LayoutField {
	fieldname: string
	label: string
	fieldtype: string
	table_columns?: TableColumn[]
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
 * Similar to Frappe's print builder but for Typst output
 */
export function createDefaultLayout(meta: any, crispyFormat: any): CrispyLayout {
	if (!meta?.fields) {
		return { sections: [] }
	}

	const sections: LayoutSection[] = []
	let currentSection: LayoutSection | null = null
	let currentColumn: LayoutColumn | null = null

	// Filter out print_hide and break fields
	const printableFields = meta.fields.filter(
		(f: DocField) => !f.print_hide && f.fieldname && f.label
	)

	for (const field of printableFields) {
		if (field.fieldtype === "Section Break") {
			// Start a new section
			if (currentSection && currentSection.columns.length > 0) {
				sections.push(currentSection)
			}
			currentSection = {
				label: field.label || "Details",
				columns: [],
			}
			currentColumn = null
		} else if (field.fieldtype === "Column Break") {
			// Start a new column in current section
			if (currentSection) {
				currentColumn = {
					label: field.label || "",
					fields: [],
				}
				currentSection.columns.push(currentColumn)
			}
		} else {
			// Regular field
			if (!currentSection) {
				// No section yet, create default one
				currentSection = {
					label: "Details",
					columns: [],
				}
			}

			if (!currentColumn) {
				// No column yet, create default one
				currentColumn = {
					label: "",
					fields: [],
				}
				currentSection.columns.push(currentColumn)
			}

			// Add field to current column
			const layoutField: LayoutField = {
				fieldname: field.fieldname,
				label: field.label,
				fieldtype: field.fieldtype,
			}

			// Handle table fields with child columns
			if (field.fieldtype === "Table" && field.options) {
				layoutField.table_columns = getTableColumns(field.options)
			}

			currentColumn.fields.push(layoutField)
		}
	}

	// Push last section if exists
	if (currentSection && currentSection.columns.length > 0) {
		sections.push(currentSection)
	}

	// If no sections were created, create a default one with all fields
	if (sections.length === 0 && printableFields.length > 0) {
		const defaultColumn: LayoutColumn = {
			label: "",
			fields: printableFields
				.filter((f: DocField) => f.fieldtype && !["Section Break", "Column Break"].includes(f.fieldtype))
				.map((f: DocField) => ({
					fieldname: f.fieldname,
					label: f.label,
					fieldtype: f.fieldtype,
				})),
		}

		sections.push({
			label: "Details",
			columns: [defaultColumn],
		})
	}

	return { sections }
}

/**
 * Get table columns for a child table field
 */
function getTableColumns(childDoctype: string): TableColumn[] {
	if (typeof frappe === "undefined") {
		return []
	}

	const childMeta = frappe.get_meta(childDoctype)
	if (!childMeta?.fields) {
		return []
	}

	return childMeta.fields
		.filter((f: DocField) => !f.print_hide && f.fieldname && f.label)
		.filter((f: DocField) => f.fieldtype && !["Section Break", "Column Break"].includes(f.fieldtype))
		.map((f: DocField) => ({
			fieldname: f.fieldname,
			label: f.label,
			fieldtype: f.fieldtype,
			width: "auto",
		}))
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
