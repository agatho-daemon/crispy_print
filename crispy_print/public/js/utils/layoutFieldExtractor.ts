// utils/layoutFieldExtractor.ts
// Extract and filter fields actually used in a layout

import type { CrispyLayout, LayoutSection, LayoutColumn, LayoutField } from "./layout"

/**
 * Extract all field names referenced in a layout
 * This includes fields in sections and table columns
 */
export function extractUsedFields(layout: CrispyLayout): Set<string> {
	const usedFields = new Set<string>()

	if (!layout?.sections) return usedFields

	// Always include essential fields for document identification
	const essentialFields = ["name", "doctype", "docstatus", "owner", "modified"]
	essentialFields.forEach((field) => usedFields.add(field))

	// Extract fields from sections
	layout.sections.forEach((section) => {
		extractFieldsFromSection(section, usedFields)
	})

	return usedFields
}

/**
 * Recursively extract fields from a section
 */
function extractFieldsFromSection(section: LayoutSection, usedFields: Set<string>): void {
	if (!section.columns) return

	section.columns.forEach((column) => {
		extractFieldsFromColumn(column, usedFields)
	})
}

/**
 * Extract fields from a column
 */
function extractFieldsFromColumn(column: LayoutColumn, usedFields: Set<string>): void {
	if (!column.fields) return

	column.fields.forEach((field) => {
		// Regular field
		if (field.fieldname && field.fieldname !== "_template") {
			usedFields.add(field.fieldname)
		}

		// Table field - add parent field and all columns
		if (field.fieldtype === "Table" && field.table_columns) {
			// Add the parent table field
			if (field.fieldname) {
				usedFields.add(field.fieldname)
			}

			// Add all columns from table
			field.table_columns.forEach((col) => {
				if (col.fieldname) {
					usedFields.add(col.fieldname)
				}
			})
		}
	})
}

/**
 * Filter document data to only include used fields
 * This creates a minimal doc object for Typst compilation
 */
export function filterDocumentFields(doc: any, usedFields: Set<string>): any {
	if (!doc || typeof doc !== "object") return doc

	const filtered: any = {}

	// Always include essential top-level fields (used by `doc_header` and other helpers)
	const essentialFields = ["name", "doctype", "title"]
	essentialFields.forEach((field) => {
		if (field in doc) {
			filtered[field] = doc[field]
		}
	})

	// Copy only used fields
	usedFields.forEach((fieldname) => {
		if (fieldname in doc) {
			const value = doc[fieldname]

			// Handle child tables
			if (Array.isArray(value)) {
				// For child tables, recursively filter child doc fields
				filtered[fieldname] = value.map((childDoc) => {
					if (!childDoc || typeof childDoc !== "object") return childDoc

					// Extract fields used in table columns
					const childFiltered: any = {}
					usedFields.forEach((childField) => {
						if (childField in childDoc) {
							childFiltered[childField] = childDoc[childField]
						}
					})

					// Always include essential child table fields
					const essentialChildFields = ["name", "idx", "doctype", "parent", "parentfield", "parenttype"]
					essentialChildFields.forEach((field) => {
						if (field in childDoc) {
							childFiltered[field] = childDoc[field]
						}
					})

					return childFiltered
				})
			} else {
				filtered[fieldname] = value
			}
		}
	})

	return filtered
}
