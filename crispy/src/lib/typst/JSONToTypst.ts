// Print Format Builder JSON → Typst Translator
// Translates layout from Crispy builder + optional letterhead into Typst source

import type { CrispyLayout, LayoutSection, LayoutField, TableColumn } from "@/utils/layout"

export type LayoutWithOptionalSections = Omit<CrispyLayout, "sections"> & {
	sections?: (LayoutSection & { has_fields?: boolean })[]
}

export type RealDocData = Record<string, any> | null

export function translateJSONToTypst(
	layoutData: LayoutWithOptionalSections | null | undefined,
	letterheadData: any = null,
	doctype = "Document",
	realDocData: RealDocData = null,
	options: Record<string, any> = {}
) {
	const translator = new JSONTypstTranslator(layoutData || {}, letterheadData || {}, doctype, realDocData, options)
	return translator.translate()
}

class JSONTypstTranslator {
	layout: LayoutWithOptionalSections
	letterhead: any
	doctype: string
	realDocData: RealDocData
	sections: LayoutWithOptionalSections["sections"]
	header: string | undefined
	options: Record<string, any>

	constructor(layoutData: LayoutWithOptionalSections, letterheadData: any, doctype: string, realDocData: RealDocData, options: Record<string, any>) {
		this.layout = layoutData || {}
		this.letterhead = letterheadData || {}
		this.doctype = doctype
		this.realDocData = realDocData
		this.sections = this.layout.sections || []
		this.header = this.layout.header || ""
		this.options = options || {}
	}

	translate() {
		console.log("[Typst] Starting translation...")
		console.log("[Typst] Sections:", this.sections?.length || 0)

		const parts: string[] = []

		parts.push(this.generateUserSection())
		parts.push(this.generateAutoSection())

		return parts.join("\n\n")
	}

	generateUserSection() {
		const lines = [
			"// ========================================",
			"// USER CUSTOM SECTION",
			"// ✏️ Document formatting, branding, and styling",
			"// ========================================",
			"",
			"// Page setup",
		]

		// Get page settings from options
		const pageSize = this.options.pageSize || "A4"
		const orientation = this.options.orientation || "portrait"
		const fontFamily = this.options.fontFamily || "Arial"
		const fontSize = this.options.fontSize || 10
		
		// Use margins from options or fall back to pageMargins
		const margins = this.options.margins 
			? this.resolveMargins(this.options.margins)
			: this.resolveMargins(this.options.pageMargins)

		if (this.letterhead && (this.letterhead as any).image) {
			const imagePath = (this.letterhead as any).image as string
			const filename = imagePath.split("/").pop()

			if ((this.letterhead as any).letter_head_name) {
				lines.push(`// Letterhead: ${(this.letterhead as any).letter_head_name}`)
			}
			lines.push("#set page(")
			lines.push(`  paper: "${pageSize.toLowerCase()}",`)
			if (orientation === "landscape") {
				lines.push("  flipped: true,")
			}
			lines.push(`  margin: (top: ${margins.top}, bottom: ${margins.bottom}, left: ${margins.left}, right: ${margins.right}),`)
			if (filename) {
				lines.push(`  background: image("${filename}", width: 100%)`)
			}
			lines.push(")")
			console.log("[Typst Translator] Added letterhead as page background:", filename)
		} else {
			lines.push("#set page(")
			lines.push(`  paper: "${pageSize.toLowerCase()}",`)
			if (orientation === "landscape") {
				lines.push("  flipped: true,")
			}
			lines.push(`  margin: (top: ${margins.top}, bottom: ${margins.bottom}, left: ${margins.left}, right: ${margins.right})`)
			lines.push(")")
			console.log("[Typst Translator] No letterhead found:", this.letterhead)
		}

		lines.push("")
		lines.push("// Typography")
		lines.push("#set text(")
		lines.push(`  font: "${fontFamily}",`)
		lines.push(`  size: ${fontSize}pt`)
		lines.push(")")
		lines.push("")

		lines.push("// Add your custom styling below")
		lines.push("")
		lines.push("// ========================================")
		lines.push("// END USER CUSTOM SECTION")
		lines.push("// ========================================")

		return lines.join("\n")
	}

	resolveMargins(margins: Record<string, any> | null | undefined) {
		const defaults = { top: 30, bottom: 20, left: 7, right: 7 }
		const values = { ...defaults, ...(margins || {}) }
		const asMm = (val: any, fallback: number) => {
			const num = parseFloat(val)
			if (Number.isFinite(num) && num >= 0) {
				return `${num}mm`
			}
			return `${fallback}mm`
		}
		return {
			top: asMm(values.top, defaults.top),
			bottom: asMm(values.bottom, defaults.bottom),
			left: asMm(values.left, defaults.left),
			right: asMm(values.right, defaults.right),
		}
	}

	generateAutoSection() {
		const lines: string[] = [
			"// ========================================",
			"// AUTO-GENERATED SECTION",
			"// ⚠️ WARNING: This section is regenerated from Print Format Builder",
			"// ⚠️ Do not edit below - changes will be overwritten!",
			"// ========================================",
			"",
		]

		const allFields: string[] = []
		const tableFields: { fieldname: string; columns: TableColumn[] }[] = []

		this.sections?.forEach((section) => {
			;(section.columns || []).forEach((column) => {
				;(column.fields || []).forEach((field: LayoutField) => {
					if (field && field.fieldname) {
						if (field.fieldtype === "Table") {
							tableFields.push({
								fieldname: field.fieldname,
								columns: field.table_columns || [],
							})
						} else if (
							field.fieldtype !== "Section Break" &&
							field.fieldtype !== "Column Break" &&
							field.fieldtype !== "Custom HTML"
						) {
							allFields.push(field.fieldname)
						}
					}
				})
			})
		})

		if (allFields.length > 0 || tableFields.length > 0) {
			if (this.realDocData) {
				lines.push("// Document data dictionary (real document data)")
				lines.push("#let doc = (")

				Object.keys(this.realDocData).forEach((key, idx, arr) => {
					const value = (this.realDocData as Record<string, any>)[key]
					const isLast = idx === arr.length - 1

					if (value === null || value === undefined) {
						lines.push(`  ${key}: ""${isLast ? "" : ","}`)
					} else if (Array.isArray(value)) {
						lines.push(`  ${key}: (`)
						value.forEach((row: any, rowIdx: number) => {
							if (typeof row === "object" && row !== null) {
								lines.push(`    (`)
								Object.entries(row).forEach(([colKey, colVal], colIdx, colArr) => {
									const isLastCol = colIdx === colArr.length - 1
									const escapedVal = String(colVal || "").replace(/"/g, '\\"')
									lines.push(`      ${colKey}: "${escapedVal}"${isLastCol ? "" : ","}`)
								})
								const isLastRow = rowIdx === value.length - 1
								lines.push(`    )${isLastRow ? "" : ","}`)
							}
						})
						lines.push(`  )${isLast ? "" : ","}`)
					} else if (typeof value === "string") {
						let cleanValue = value
							.replace(/<br\s*\/?>\s*\n/gi, "\n")
							.replace(/<br\s*\/?>/gi, "\n")
							.replace(/<[^>]+>/g, "")
							.replace(/"/g, '\\"')
							.replace(/\n/g, "\\n")
						lines.push(`  ${key}: "${cleanValue}"${isLast ? "" : ","}`)
					} else if (typeof value === "number") {
						lines.push(`  ${key}: ${value}${isLast ? "" : ","}`)
					} else if (typeof value === "boolean") {
						lines.push(`  ${key}: ${value ? "true" : "false"}${isLast ? "" : ","}`)
					} else {
						lines.push(`  ${key}: "${String(value)}"${isLast ? "" : ","}`)
					}
				})

				lines.push(")")
				lines.push("")
			} else {
				lines.push("// Document data dictionary (mock preview data)")
				lines.push("#let doc = (")
				lines.push(`  name: "DOC-00001",`)
				lines.push(`  doctype: "${this.doctype}",`)
				lines.push(`  title: "Document Title",`)

				allFields.forEach((fieldname) => {
					lines.push(`  ${fieldname}: "${fieldname}",`)
				})

				tableFields.forEach((table, idx) => {
					const isLast = idx === tableFields.length - 1
					lines.push(`  ${table.fieldname}: (`)
					for (let rowIdx = 0; rowIdx < 2; rowIdx++) {
						lines.push(`    (`)
						table.columns.forEach((col, colIdx) => {
							const isLastCol = colIdx === table.columns.length - 1
							const colName = col.fieldname || "col"
							lines.push(`      ${colName}: "Row ${rowIdx + 1} ${colName}"${isLastCol ? "" : ","}`)
						})
						lines.push(`    )${rowIdx === 1 ? "" : ","}`)
					}
					lines.push(`  )${isLast ? "" : ","}`)
				})

				lines.push(")")
				lines.push("")
			}
		}

		if (this.header) {
			lines.push("// Document Header")
			lines.push(this.convertHTMLToTypst(this.header))
			lines.push("")
		}

		this.sections?.forEach((section, idx) => {
			lines.push(this.translateSection(section, idx))
		})

		lines.push("")
		lines.push("// ========================================")
		lines.push("// END AUTO-GENERATED SECTION")
		lines.push("// ========================================")

		return lines.join("\n")
	}

	translateSection(section: LayoutSection & { has_fields?: boolean }, index: number) {
		const lines: string[] = []
		const label = section.label || `Section ${index + 1}`

		lines.push(`// Section: ${label}`)

		if (!section.columns || section.columns.length === 0) {
			lines.push("// (empty section)")
			return lines.join("\n")
		}

		if (!section.has_fields) {
			lines.push("// (no fields)")
			return lines.join("\n")
		}

		if (section.label) {
			lines.push(`=== ${section.label}`)
			lines.push("")
		}

		if (section.columns.length === 1) {
			const column = section.columns[0]
			if (column.fields && column.fields.length > 0) {
				column.fields.forEach((field) => {
					lines.push(this.translateField(field))
				})
			}
		} else {
			lines.push(`#grid(`)
			lines.push(`  columns: (${section.columns.map(() => "1fr").join(", ")}),`)
			lines.push(`  gutter: 1cm,`)

			section.columns.forEach((column, colIdx) => {
				lines.push(`  [`)
				if (column.fields && column.fields.length > 0) {
					column.fields.forEach((field) => {
						lines.push(`    ${this.translateField(field)}`)
					})
				}
				lines.push(`  ]${colIdx < section.columns.length - 1 ? "," : ""}`)
			})

			lines.push(`)`)
		}

		lines.push("")
		return lines.join("\n")
	}

	translateField(field?: LayoutField) {
		if (!field) return "// (null field)"

		const fieldtype = field.fieldtype || "Data"
		const fieldname = field.fieldname || "unknown"
		const label = field.label || fieldname

		switch (fieldtype) {
			case "Section Break":
				return `// Section Break: ${label}`
			case "Column Break":
				return `// Column Break`
			case "Custom HTML":
				if ((field as any).html || field.options) {
					return this.convertHTMLToTypst((field as any).html || field.options || "")
				}
				return `// Custom HTML (empty)`
			case "Table":
				return this.translateTable(field)
			case "HTML":
				return `// HTML field: ${fieldname}`
			default:
				if ((field as any).print_hide) {
					return `// ${label} (hidden)`
				}

				if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
					return `// ${label} (field not in document)`
				}

				return `#text(size: 8pt, fill: rgb("#888"))[${label}]#linebreak()#text(size: 10pt)[#doc.${fieldname}]#parbreak()`
		}
	}

	translateTable(field: LayoutField) {
		const lines: string[] = []
		const fieldname = field.fieldname || "items"
		const label = field.label || "Table"

		lines.push(`// Table: ${label}`)

		if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
			lines.push(`// Table field "${fieldname}" not in document`)
			return lines.join("\n")
		}

		if (field.table_columns && field.table_columns.length > 0) {
			const columns = field.table_columns

			lines.push(`#if type(doc.${fieldname}) == array and doc.${fieldname}.len() > 0 [`)
			lines.push(`  #table(`)
			lines.push(`    columns: (${columns.map(() => "1fr").join(", ")}),`)
			lines.push(`    align: (${columns.map(() => "left").join(", ")}),`)

			const headerCells = columns
				.map((col) => {
					const headerLabel = (col.label || col.fieldname || "Column").replace(/#/g, "\\#")
					return `[*${headerLabel}*]`
				})
				.join(", ")
			lines.push(`    ${headerCells},`)

			lines.push(`    ..doc.${fieldname}.map(item => (`)
			lines.push(`      ${columns.map((col) => `[#item.at("${col.fieldname}", default: "")]`).join(", ")}`)
			lines.push(`    )).flatten()`)
			lines.push(`  )`)
			lines.push(`] else [`)
			lines.push(`  // Table "${label}" is empty or not an array`)
			lines.push(`]`)
		} else {
			lines.push(`// TODO: Table ${fieldname} has no columns defined`)
		}

		return lines.join("\n")
	}

	convertHTMLToTypst(html: string) {
			if (!html || !html.trim()) return "// (empty HTML)"

			let typst = html
				.replace(/<h1[^>]*>(.*?)<\/h1>/gi, "= $1")
				.replace(/<h2[^>]*>(.*?)<\/h2>/gi, "== $1")
				.replace(/<h3[^>]*>(.*?)<\/h3>/gi, "=== $1")
				.replace(/<strong[^>]*>(.*?)<\/strong>/gi, "*$1*")
				.replace(/<b[^>]*>(.*?)<\/b>/gi, "*$1*")
				.replace(/<em[^>]*>(.*?)<\/em>/gi, "_$1_")
				.replace(/<i[^>]*>(.*?)<\/i>/gi, "_$1_")
				.replace(/<br\s*\/?>/gi, " \\\n")
				.replace(/<p[^>]*>(.*?)<\/p>/gi, "$1\n\n")
				.replace(/<div[^>]*>(.*?)<\/div>/gi, "$1\n")
				.replace(/<[^>]+>/g, "")

			typst = typst
				.replace(/\{\{\s*doc\.(\w+)\s*\}\}/g, "#doc.$1")
				.replace(/\{%.*?%\}/g, "")

		return typst.trim()
	}
}

export { JSONTypstTranslator }
