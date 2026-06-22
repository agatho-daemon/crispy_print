// utils/layoutFieldExtractor.ts
// Extract and filter fields actually used in a layout

import type { CrispyLayout, LayoutSection, LayoutColumn } from "./layout"
import { extractUsedFieldsFromTypstSource } from "./typstFieldExtractor"

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
		if (field.fieldname && field.fieldname !== "_template" && !isBuilderOnlyField(field)) {
			usedFields.add(field.fieldname)
		}

		// Table field - add parent field and all columns
		if (field.fieldtype === "Table" && field.table_columns) {
			// Add the parent table field
			if (field.fieldname) {
				usedFields.add(field.fieldname)
			}

			// Add all columns from table (both namespaced and bare)
				field.table_columns.forEach((col) => {
					if (col.fieldname) {
						// Add bare column name for table rendering
						usedFields.add(col.fieldname)
						// Add namespaced column for filtering
						if (field.fieldname) {
							usedFields.add(`${field.fieldname}.${col.fieldname}`)
							getDependentTableFields(col.fieldname).forEach((dependentField) => {
								usedFields.add(dependentField)
								usedFields.add(`${field.fieldname}.${dependentField}`)
							})
						}
					}
				})
		}

		// Custom Typst field - extract field references from Typst code
		if (field.fieldtype === "Typst" && field.raw_typst_field) {
			const typstCode = String(field.raw_typst_field)
			const extractedFields = extractUsedFieldsFromTypstSource(typstCode)
			extractedFields.forEach((fieldname) => usedFields.add(fieldname))
		}

		if (field.fieldtype === "Crispy Typst Block" && field.crispy_typst_block_code) {
			const typstCode = String(field.crispy_typst_block_code)
			const extractedFields = extractUsedFieldsFromTypstSource(typstCode)
			extractedFields.forEach((fieldname) => usedFields.add(fieldname))
		}
	})
}

function isBuilderOnlyField(field: { fieldname?: string; fieldtype?: string }): boolean {
	if (field.fieldname?.startsWith("_")) return true
	return ["Typst", "Spacer", "Divider", "Empty", "Crispy Typst Block"].includes(
		field.fieldtype || ""
	)
}

function getDependentTableFields(fieldname: string): string[] {
	if (["qty", "quantity", "stock_qty"].includes(fieldname)) {
		return ["uom", "stock_uom"]
	}
	return []
}

/**
 * Filter document data to only include used fields
 * This creates a minimal doc object for Typst compilation
 */
export function filterDocumentFields(
	doc: any,
	usedFields: Set<string>,
	options: { includeAllChildFieldsIfUnspecified?: boolean } = {}
): any {
	if (!doc || typeof doc !== "object") return doc

	const filtered: any = {}
	const directFields = new Set<string>()
	const tableFieldMap = new Map<string, Set<string>>()

	usedFields.forEach((fieldname) => {
		if (!fieldname) return
		const dotIndex = fieldname.indexOf(".")
		if (dotIndex > 0) {
			const parent = fieldname.slice(0, dotIndex)
			const child = fieldname.slice(dotIndex + 1)
			if (parent) {
				directFields.add(parent)
				if (child) {
					if (!tableFieldMap.has(parent)) {
						tableFieldMap.set(parent, new Set<string>())
					}
					tableFieldMap.get(parent)?.add(child)
				}
			}
			return
		}
		directFields.add(fieldname)
	})

	// Always include essential top-level fields (used by `doc_header` and other helpers)
	const essentialFields = ["name", "doctype", "title"]
	essentialFields.forEach((field) => {
		if (field in doc) {
			filtered[field] = doc[field]
		}
	})

	// Copy only used fields
	directFields.forEach((fieldname) => {
		if (fieldname in doc) {
			const value = doc[fieldname]

			// Handle child tables
			if (Array.isArray(value)) {
				const tableFields = tableFieldMap.get(fieldname)
				const includeAllChildFields =
					Boolean(options.includeAllChildFieldsIfUnspecified) &&
					(!tableFields || tableFields.size === 0)

				// For child tables, recursively filter child doc fields
				filtered[fieldname] = value.map((childDoc) => {
					if (!childDoc || typeof childDoc !== "object") return childDoc

					// Extract fields used in table columns
					const childFiltered: any = {}
					if (includeAllChildFields) {
						Object.keys(childDoc).forEach((childField) => {
							childFiltered[childField] = childDoc[childField]
						})
					} else if (tableFields && tableFields.size) {
						// Only copy the child-table columns referenced in the layout.
						// (Previously this loop iterated `directFields` — the PARENT
						// field set — which leaked unrelated parent-level field names
						// into child rows.)
						tableFields.forEach((childField) => {
							if (childField in childDoc) {
								childFiltered[childField] = childDoc[childField]
							} else {
								childFiltered[childField] = ""
							}
						})
					}

					// Always include essential child table fields
					const essentialChildFields = [
						"name",
						"idx",
						"doctype",
						"parent",
						"parentfield",
						"parenttype",
					]
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
