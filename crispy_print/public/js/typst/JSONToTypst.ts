// Print Format Builder JSON → Typst Translator
// Translates layout from Crispy builder + optional letterhead into Typst source

import type { CrispyLayout, LayoutSection, LayoutField, TableColumn } from "../utils/layout"
import { buildForegroundPlacements, getLetterheadFilename, resolveBrandingMode } from "./branding"

export type LayoutWithOptionalSections = Omit<CrispyLayout, "sections"> & {
	sections?: LayoutSection[]
}

export type RealDocData = Record<string, any> | null

export function translateJSONToTypst(
	layoutData: LayoutWithOptionalSections | null | undefined,
	letterheadData: any = null,
	doctype = "Document",
	realDocData: RealDocData = null,
	options: Record<string, any> = {}
) {
	const translator = new JSONTypstTranslator(
		layoutData || {},
		letterheadData || {},
		doctype,
		realDocData,
		options
	)
	return translator.translate()
}

export function buildDocDictionary(realDocData: RealDocData, doctype = "Document") {
	const lines: string[] = []

	if (realDocData) {
		lines.push("// Document data dictionary (real document data)")
		lines.push("#let doc = (")

		Object.keys(realDocData).forEach((key, idx, arr) => {
			const value = (realDocData as Record<string, any>)[key]
			const isLast = idx === arr.length - 1

			if (value === null || value === undefined) {
				lines.push(`  ${key}: ""${isLast ? "" : ","}`)
			} else if (Array.isArray(value)) {
				lines.push(`  ${key}: (`)
				value.forEach((row: any) => {
					if (typeof row === "object" && row !== null) {
						lines.push(`    (`)
						Object.entries(row).forEach(([colKey, colVal], colIdx, colArr) => {
							const isLastCol = colIdx === colArr.length - 1
							const escapedVal = String(colVal || "").replace(/"/g, '\\"')
							lines.push(`      ${colKey}: "${escapedVal}"${isLastCol ? "" : ","}`)
						})
						lines.push(`    ),`)
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
		return lines.join("\n")
	}

	lines.push("// Document data dictionary (mock preview data)")
	lines.push("#let doc = (")
	lines.push(`  name: "DOC-00001",`)
	lines.push(`  doctype: "${doctype}",`)
	lines.push(`  title: "Document Title",`)
	lines.push(")")
	lines.push("")
	return lines.join("\n")
}

class JSONTypstTranslator {
	layout: LayoutWithOptionalSections
	letterhead: any
	doctype: string
	realDocData: RealDocData
	sections: LayoutWithOptionalSections["sections"]
	options: Record<string, any>

	constructor(
		layoutData: LayoutWithOptionalSections,
		letterheadData: any,
		doctype: string,
		realDocData: RealDocData,
		options: Record<string, any>
	) {
		this.layout = layoutData || {}
		this.letterhead = letterheadData || {}
		this.doctype = doctype
		this.realDocData = realDocData
		this.sections = this.layout.sections || []
		this.options = options || {}
	}

	translate() {
		const parts: string[] = []

		parts.push(this.generateUserSection())
		parts.push(this.generateAutoSection())

		return parts.join("\n\n")
	}

	escapeTypstText(value: string) {
		return String(value || "")
			.replace(/\\/g, "\\\\")
			.replace(/\[/g, "\\[")
			.replace(/\]/g, "\\]")
			.replace(/#/g, "\\#")
			.replace(/\*/g, "\\*")
	}

	// Convert font weight name to numeric value for Typst
	fontWeightToNumber(weight: string): number {
		const weightMap: Record<string, number> = {
			thin: 100,
			extralight: 200,
			light: 300,
			normal: 400,
			regular: 400,
			medium: 500,
			semibold: 600,
			bold: 700,
			extrabold: 800,
			black: 900,
		}
		const normalized = weight.toLowerCase()
		return weightMap[normalized] || 400
	}

	generateUserSection() {
		const lines = [
			"// ========================================",
			"// USER CUSTOM SECTION",
			"// ✏️ Document formatting, branding, and styling",
			"// ========================================",
			"",
		]

		// Typography styles for labels and values
		const typography = this.options.typography || {}
		const fieldLabel = typography.fieldLabel || {
			fontFamily: "Inter 18pt",
			fontSize: "8pt",
			fontStyle: "normal",
			fontWeight: "semibold",
			color: "#64748b",
		}
		const fieldValue = typography.fieldValue || {
			fontFamily: "Inter 18pt",
			fontSize: "10pt",
			fontStyle: "normal",
			fontWeight: "regular",
			color: "#0f172a",
		}
		const sectionLabel = typography.sectionLabel || {
			fontFamily: "Inter 18pt",
			fontSize: "14pt",
			fontStyle: "normal",
			fontWeight: "bold",
			color: "#1e293b",
		}

		lines.push("// Typography styles")
		lines.push("#let fieldLabelStyle = (")
		lines.push(`  font: "${fieldLabel.fontFamily}",`)
		lines.push(`  size: ${fieldLabel.fontSize},`)
		lines.push(`  style: "${fieldLabel.fontStyle}",`)
		lines.push(`  weight: ${this.fontWeightToNumber(fieldLabel.fontWeight)},`)
		lines.push(`  fill: rgb("${fieldLabel.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("#let fieldValueStyle = (")
		lines.push(`  font: "${fieldValue.fontFamily}",`)
		lines.push(`  size: ${fieldValue.fontSize},`)
		lines.push(`  style: "${fieldValue.fontStyle}",`)
		lines.push(`  weight: ${this.fontWeightToNumber(fieldValue.fontWeight)},`)
		lines.push(`  fill: rgb("${fieldValue.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("#let sectionLabelStyle = (")
		lines.push(`  font: "${sectionLabel.fontFamily}",`)
		lines.push(`  size: ${sectionLabel.fontSize},`)
		lines.push(`  style: "${sectionLabel.fontStyle}",`)
		lines.push(`  weight: ${this.fontWeightToNumber(sectionLabel.fontWeight)},`)
		lines.push(`  fill: rgb("${sectionLabel.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("#let header_block = []")
		lines.push("#let footer_block = []")
		lines.push("")

		lines.push("// Add your custom styling below")
		lines.push("")
		const typstPreamble = (this.options.typstPreamble as string | undefined) || ""
		if (typstPreamble && typstPreamble.trim()) {
			lines.push(typstPreamble.trim())
			lines.push("")
		}
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

	buildPageSetupBlock() {
		const lines: string[] = []
		const pageSize = this.options.pageSize || "A4"
		const orientation = this.options.orientation || "portrait"
		const margins = this.options.margins
			? this.resolveMargins(this.options.margins)
			: this.resolveMargins(this.options.pageMargins)

		const brandingMode = resolveBrandingMode(this.options, this.letterhead)
		const letterheadFilename = getLetterheadFilename(this.options, this.letterhead)
		const qrEnabled = Boolean(this.options.qrEnabled)
		const qrFilename = (this.options.qrFilename as string | undefined) || ""
		const qrSettings = (this.options.qrSettings as Record<string, any> | undefined) || {}
		const foregroundLines = buildForegroundPlacements({
			pageSettings: this.options,
			brandingMode,
			qrEnabled,
			qrFilename,
			qrSettings,
		})

		lines.push("// Page setup")
		lines.push("#set page(")
		lines.push(`  paper: "${pageSize.toLowerCase()}",`)
		if (orientation === "landscape") {
			lines.push("  flipped: true,")
		}
		lines.push(
			`  margin: (top: ${margins.top}, bottom: ${margins.bottom}, left: ${margins.left}, right: ${margins.right}),`
		)
		lines.push("  header: header_block,")
		lines.push("  footer: footer_block,")
		if (brandingMode === "letterhead" && letterheadFilename) {
			if ((this.letterhead as any).letter_head_name) {
				lines.push(`  // Letterhead: ${(this.letterhead as any).letter_head_name}`)
			}
			lines.push(`  background: image("${letterheadFilename}", width: 100%),`)
		}
		if (foregroundLines.length) {
			lines.push("  foreground: [")
			foregroundLines.forEach((line) => {
				lines.push(`    ${line}`)
			})
			lines.push("  ],")
		}
		lines.push(")")
		lines.push("")

		return lines.join("\n")
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
						// Keep arrays as arrays even when only one row exists; trailing comma is allowed in Typst tuples
						value.forEach((row: any) => {
							if (typeof row === "object" && row !== null) {
								lines.push(`    (`)
								Object.entries(row).forEach(([colKey, colVal], colIdx, colArr) => {
									const isLastCol = colIdx === colArr.length - 1
									const escapedVal = String(colVal || "").replace(/"/g, '\\"')
									lines.push(`      ${colKey}: "${escapedVal}"${isLastCol ? "" : ","}`)
								})
								lines.push(`    ),`)
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

		const docFooter = (this.options.docFooter as string | undefined) || ""
		const docHeader = (this.options.docHeader as string | undefined) || ""
		if (docHeader && docHeader.trim()) {
			lines.push("// Document Header")
			lines.push(docHeader.trim())
			lines.push("")
		}

		if (docFooter && docFooter.trim()) {
			lines.push("// Document Footer")
			lines.push(docFooter.trim())
			lines.push("")
		}

		lines.push(this.buildPageSetupBlock())

		this.sections?.forEach((section, idx) => {
			lines.push(this.translateSection(section, idx))
		})

		lines.push("")
		lines.push("// ========================================")
		lines.push("// END AUTO-GENERATED SECTION")
		lines.push("// ========================================")

		return lines.join("\n")
	}

	translateSection(section: LayoutSection, index: number) {
		const lines: string[] = []
		const label = section.label || `Section ${index + 1}`
		const safeLabel = this.escapeTypstText(label)

		if (section.page_break && index > 0) {
			lines.push("#pagebreak()")
			lines.push("")
		}

		lines.push(`// Section: ${label}`)

		if (!section.columns || section.columns.length === 0) {
			lines.push("// (empty section)")
			return lines.join("\n")
		}

		const hasFields = section.columns?.some((col) => col.fields && col.fields.length > 0) || false
		if (!hasFields) {
			lines.push("// (no fields)")
			return lines.join("\n")
		}

		if (section.label) {
			lines.push(`#block(spacing: 0.6em)[#text(..sectionLabelStyle)[${safeLabel}]]`)
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
		const label = this.escapeTypstText((field.label ?? "").trim())

		switch (fieldtype) {
			case "Section Break":
				return `// Section Break: ${label || fieldname}`
			case "Column Break":
				return `// Column Break`
			case "Typst": {
				const code = String(field.raw_typst_field || "").trim()
				return code ? code : `// Custom Typst (empty)`
			}
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
					return `// ${label || fieldname} (hidden)`
				}

				if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
					return `// ${label || fieldname} (field not in document)`
				}

				// Determine alignment
				const align = field.align || this.getDefaultAlignment(fieldtype)

				// If label is empty, render only the value (common for "display" fields like address_display).
				if (!label) {
					if (align === "left") {
						return `#text(..fieldValueStyle)[#doc.${fieldname}]#parbreak()`
					}
					return `#align(${align})[#text(..fieldValueStyle)[#doc.${fieldname}]]#parbreak()`
				}

				// Label always left-aligned, value respects field alignment
				if (align === "left") {
					// Both left-aligned - simple format
					return `#text(..fieldLabelStyle)[${label}]#linebreak()#text(..fieldValueStyle)[#doc.${fieldname}]#parbreak()`
				}
				// Label left, value aligned separately
				return `#text(..fieldLabelStyle)[${label}]#linebreak()#align(${align})[#text(..fieldValueStyle)[#doc.${fieldname}]]#parbreak()`
		}
	}

	getDefaultAlignment(fieldtype: string): "left" | "center" | "right" {
		// Numeric fields default to right alignment, like Frappe
		const numericTypes = ["Int", "Float", "Currency", "Percent"]
		return numericTypes.includes(fieldtype) ? "right" : "left"
	}

	translateTable(field: LayoutField) {
		const lines: string[] = []
		const fieldname = field.fieldname || "items"
		const label = field.label || "Table"
		const safeLabel = this.escapeTypstText(label)

		lines.push(`// Table: ${label}`)

		if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
			lines.push(`// Table field "${fieldname}" not in document`)
			return lines.join("\n")
		}

		if (field.table_columns && field.table_columns.length > 0) {
			const columns = field.table_columns

			lines.push(`#if type(doc.${fieldname}) == array and doc.${fieldname}.len() > 0 [`)
			lines.push(`  #table(`)
			// Use column widths from layout (auto, 1fr, 2fr, 100pt, etc.)
			const widths = columns.map((col) => col.width || "auto")
			lines.push(`    columns: (${widths.join(", ")}),`)
			const alignments = columns.map((col) => {
				const align = col.align || this.getDefaultAlignment(col.fieldtype)
				return align
			})
			lines.push(`    align: (${alignments.join(", ")}),`)

			const headerCells = columns
				.map((col) => `[*${this.escapeTypstText(col.label || "")}*]`)
				.join(", ")
			lines.push(`    ${headerCells},`)

			// Row data - map each row to all its column values and flatten
			const rowCells = columns.map((col) => `[#row.${col.fieldname}]`).join(", ")
			lines.push(`    ..doc.${fieldname}.map(row => (${rowCells})).flatten(),`)

			lines.push(`  )`)
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

		typst = typst.replace(/\{\{\s*doc\.(\w+)\s*\}\}/g, "#doc.$1").replace(/\{%.*?%\}/g, "")

		return typst.trim()
	}
}

export { JSONTypstTranslator }
