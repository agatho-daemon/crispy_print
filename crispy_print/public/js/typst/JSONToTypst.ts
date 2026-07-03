// Print Format Builder JSON → Typst Translator
// Translates layout from Crispy builder + optional letterhead into Typst source

import type { CrispyLayout, LayoutSection, LayoutField, TableColumn } from "../utils/layout"
import { buildForegroundPlacements, getLetterheadFilename, resolveBrandingMode } from "./branding"
import { resolveTypstPaper } from "./page"
import { typstLength, typstQuoted } from "./typstEscaping"
import { buildTableStyleConstants, buildTypographyStyleDefs } from "./textStyles"
import {
	default_presentation_settings,
	ensure_table_settings,
	ensure_typography,
	merge_presentation_settings,
	type PresentationSettings,
} from "../utils/presentation_settings"
import { deepClone } from "../utils/json"
import { normalizeHtmlText } from "../utils/htmlText"
import { escapeTypstString } from "../utils/typstEscape"

export type LayoutWithOptionalSections = Omit<CrispyLayout, "sections"> & {
	sections?: LayoutSection[]
}

export type RealDocData = Record<string, any> | null

function typstStringLiteral(value: unknown): string {
	return `"${escapeTypstString(normalizeHtmlText(value))}"`
}

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

		Object.keys(realDocData).forEach((key) => {
			const value = (realDocData as Record<string, any>)[key]

			if (value === null || value === undefined) {
				lines.push(`  ${key}: "",`)
			} else if (Array.isArray(value)) {
				lines.push(`  ${key}: (`)
				value.forEach((row: any) => {
					if (typeof row === "object" && row !== null) {
						lines.push(`    (`)
						Object.entries(row).forEach(([colKey, colVal]) => {
							lines.push(`      ${colKey}: ${typstStringLiteral(colVal)},`)
						})
						lines.push(`    ),`)
					}
				})
				lines.push(`  ),`)
			} else if (typeof value === "string") {
				lines.push(`  ${key}: ${typstStringLiteral(value)},`)
			} else if (typeof value === "number") {
				lines.push(`  ${key}: ${value},`)
			} else if (typeof value === "boolean") {
				lines.push(`  ${key}: ${value ? "true" : "false"},`)
			} else {
				lines.push(`  ${key}: ${typstStringLiteral(value)},`)
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
	private _presentation_settings: PresentationSettings | null = null

	private get_print_behavior(): Record<string, any> {
		return ((this.options.printBehavior || {}) as Record<string, any>) || {}
	}

	private is_enabled_behavior(key: string): boolean {
		return Boolean(this.get_print_behavior()[key])
	}

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
		const presentation_settings = merge_presentation_settings(
			default_presentation_settings,
			options || {}
		)
		this.options = {
			...(options || {}),
			...presentation_settings,
		}
	}

	translate() {
		const parts: string[] = []

		parts.push(this.generateUserSection())
		parts.push(this.generateAutoSection())

		return parts.join("\n\n")
	}

	private get_presentation_settings(): PresentationSettings {
		if (!this._presentation_settings) {
			const overrides = (this.options ? deepClone(this.options) : {}) as Partial<PresentationSettings>
			this._presentation_settings = merge_presentation_settings(default_presentation_settings, overrides)
		}
		return this._presentation_settings
	}

	escapeTypstText(value: string) {
		return String(value || "")
			.replace(/\\/g, "\\\\")
			.replace(/\[/g, "\\[")
			.replace(/\]/g, "\\]")
			.replace(/#/g, "\\#")
			.replace(/\*/g, "\\*")
	}

	generateUserSection() {
		const lines = [
			"// ========================================",
			"// USER CUSTOM SECTION",
			"// ✏️ Document formatting, branding, and styling",
			"// ========================================",
			"",
		]

		const presentationSettings = this.get_presentation_settings()
		const typography = ensure_typography(presentationSettings)
		const tableSettings = ensure_table_settings(presentationSettings)
		lines.push(
			buildTypographyStyleDefs(typography, tableSettings, {
				typographyComment: "// Typography styles",
				tableComment: "// Table styles",
			})
		)
		lines.push(buildTableStyleConstants(tableSettings))
		lines.push("#let cp_is_zero_tax_value(value) = value == 0 or value == \"0\" or value == \"0.0\" or value == \"0.00\" or value == \"\"")
		lines.push("#let cp_is_zero_tax_row(row) = {")
		lines.push("  if \"tax_amount\" in row { cp_is_zero_tax_value(row.tax_amount) }")
		lines.push("  else if \"base_tax_amount\" in row { cp_is_zero_tax_value(row.base_tax_amount) }")
		lines.push("  else if \"amount\" in row { cp_is_zero_tax_value(row.amount) }")
		lines.push("  else { false }")
		lines.push("}")
		lines.push("#let cp_row_uom(row) = {")
		lines.push("  if \"uom\" in row and row.uom != \"\" { row.uom }")
		lines.push("  else if \"stock_uom\" in row and row.stock_uom != \"\" { row.stock_uom }")
		lines.push("  else { \"\" }")
		lines.push("}")
		lines.push("#let cp_measure_label_cell(label) = {")
		lines.push("  if tableCellLabelEnabled and label != \"\" {")
		lines.push("    text(..tableCellLabelStyle)[#label]")
		lines.push("  }")
		lines.push("}")
		lines.push("#let cp_measure_label_table_cell(label) = table.cell(stroke: (right: none))[#cp_measure_label_cell(label)]")
		lines.push("#let cp_measure_value_table_cell(value) = table.cell(stroke: (left: none))[#text(..tableBodyStyle)[#value]]")
		lines.push("#let cp_currency_parts(value) = {")
		lines.push("  let text = str(value)")
		lines.push("  let parts = text.split(\" \")")
		lines.push("  if parts.len() > 1 and parts.at(0).len() <= 4 {")
		lines.push("    (label: parts.at(0), value: parts.slice(1).join(\" \"))")
		lines.push("  } else {")
		lines.push("    (label: \"\", value: text)")
		lines.push("  }")
		lines.push("}")
		lines.push(
			`#let cp_print_uom_after_quantity = ${
				this.is_enabled_behavior("print_uom_after_quantity") ? "true" : "false"
			}`
		)
		lines.push("#let cp_quantity_parts(row, value) = {")
		lines.push("  let uom = cp_row_uom(row)")
		lines.push("  if cp_print_uom_after_quantity and uom != \"\" {")
		lines.push("    (label: \"\", value: str(value) + \" \" + uom)")
		lines.push("  } else {")
		lines.push("    (label: uom, value: str(value))")
		lines.push("  }")
		lines.push("}")
		lines.push("#let cp_quantity_inline(row, value) = {")
		lines.push("  let uom = cp_row_uom(row)")
		lines.push("  if cp_print_uom_after_quantity and uom != \"\" {")
		lines.push("    str(value) + \" \" + uom")
		lines.push("  } else if uom != \"\" {")
		lines.push("    uom + \" \" + str(value)")
		lines.push("  } else {")
		lines.push("    str(value)")
		lines.push("  }")
		lines.push("}")
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
		const presentation_settings = this.get_presentation_settings()
		const page_size = presentation_settings.page.size || "A4"
		const orientation = presentation_settings.page.orientation || "portrait"
		const margins = this.resolveMargins(presentation_settings.page.margins)

		const branding_mode = resolveBrandingMode(presentation_settings, this.letterhead)
		const letterheadFilename = getLetterheadFilename(presentation_settings, this.letterhead)
		const qrEnabled = Boolean(this.options.qrEnabled)
		const qrData = (this.options.qrData as string | undefined) || ""
		const qrFilename = (this.options.qrFilename as string | undefined) || ""
		const qrSettings = presentation_settings.qr || {}
		const foregroundLines = buildForegroundPlacements({
			presentation_settings,
			branding_mode,
			qrEnabled,
			qrData,
			qrFilename,
			qrSettings,
		})

		lines.push("// Page setup")
		lines.push("#set page(")
		lines.push(`  paper: ${typstQuoted(resolveTypstPaper(page_size))},`)
		if (orientation === "landscape") {
			lines.push("  flipped: true,")
		}
		lines.push(
			`  margin: (top: ${margins.top}, bottom: ${margins.bottom}, left: ${margins.left}, right: ${margins.right}),`
		)
		lines.push("  header: header_block,")
		lines.push("  footer: footer_block,")
		if ((branding_mode === "letterhead" || branding_mode === "logo_letterhead") && letterheadFilename) {
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
						} else if (field.fieldtype !== "Section Break" && field.fieldtype !== "Column Break") {
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

				Object.keys(this.realDocData).forEach((key) => {
					const value = (this.realDocData as Record<string, any>)[key]

					if (value === null || value === undefined) {
						lines.push(`  ${key}: "",`)
					} else if (Array.isArray(value)) {
						lines.push(`  ${key}: (`)
						// Keep arrays as arrays even when only one row exists; trailing comma is allowed in Typst tuples
						value.forEach((row: any) => {
							if (typeof row === "object" && row !== null) {
								lines.push(`    (`)
								Object.entries(row).forEach(([colKey, colVal]) => {
									lines.push(`      ${colKey}: ${typstStringLiteral(colVal)},`)
								})
								lines.push(`    ),`)
							}
						})
						lines.push(`  ),`)
					} else if (typeof value === "string") {
						lines.push(`  ${key}: ${typstStringLiteral(value)},`)
					} else if (typeof value === "number") {
						lines.push(`  ${key}: ${value},`)
					} else if (typeof value === "boolean") {
						lines.push(`  ${key}: ${value ? "true" : "false"},`)
					} else {
						lines.push(`  ${key}: ${typstStringLiteral(value)},`)
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

				tableFields.forEach((table) => {
					lines.push(`  ${table.fieldname}: (`)
					for (let rowIdx = 0; rowIdx < 2; rowIdx++) {
						lines.push(`    (`)
						table.columns.forEach((col) => {
							const colName = col.fieldname || "col"
							lines.push(`      ${colName}: "Row ${rowIdx + 1} ${colName}",`)
						})
						lines.push(`    ),`)
					}
					lines.push(`  ),`)
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

		const printContext = (this.realDocData as any)?.__crispy_print_context || {}
		if (printContext.show_draft_heading) {
			lines.push('#align(center)[#text(size: 18pt, weight: "bold", fill: rgb("#b91c1c"))[Draft]]')
			lines.push("#v(1em)")
			lines.push("")
		}

		const lastSectionIndex = (this.sections?.length || 1) - 1
		this.sections?.forEach((section, idx) => {
			lines.push(this.translateSection(section, idx, idx === lastSectionIndex))
		})

		lines.push("")
		lines.push("// ========================================")
		lines.push("// END AUTO-GENERATED SECTION")
		lines.push("// ========================================")

		return lines.join("\n")
	}

	translateSection(section: LayoutSection, index: number, isLastSection: boolean) {
		const lines: string[] = []
		const label = section.label || `Section ${index + 1}`
		const safeLabel = this.escapeTypstText(label)

		const appendPageBreak = () => {
			if (section.page_break && !isLastSection) {
				lines.push("")
				lines.push("#pagebreak()")
			}
		}

		lines.push(`// Section: ${label}`)

		if (!section.columns || section.columns.length === 0) {
			lines.push("// (empty section)")
			appendPageBreak()
			return lines.join("\n")
		}

		const hasFields = section.columns?.some((col) => col.fields && col.fields.length > 0) || false
		if (!hasFields) {
			lines.push("// (no fields)")
			appendPageBreak()
			return lines.join("\n")
		}

		const isRawTypstSection = section.columns.every((col) =>
			(col.fields || []).every((field) => field.fieldtype === "Typst")
		)

		if (section.label) {
			lines.push(`#block(spacing: 0.6em)[#text(..sectionLabelStyle)[${safeLabel}]]`)
			lines.push("")
		}

		// lines.push(`#v(8pt) // Spacing after section`)
		lines.push("")

		if (isRawTypstSection) {
			const maxRows = Math.max(...section.columns.map((col) => col.fields?.length || 0))
			const numCols = section.columns.length

			for (let rowIdx = 0; rowIdx < maxRows; rowIdx++) {
				for (let colIdx = 0; colIdx < numCols; colIdx++) {
					const column = section.columns[colIdx]
					const field = column.fields?.[rowIdx]
					if (!field) continue
					const code = String(field.raw_typst_field || "").trim()
					if (code) {
						lines.push(code)
					}
				}
			}
			appendPageBreak()
			return lines.join("\n")
		}

		// All sections use grid (unified approach for consistent spacing)
		const maxRows = Math.max(...section.columns.map((col) => col.fields?.length || 0))
		const numCols = section.columns.length

		// Only create grid if there are rows
		if (maxRows > 0) {
			lines.push(`#grid(`)
			const columnWidths = section.columns.map((col) => col.width || "1fr")
			lines.push(`  columns: (${columnWidths.join(", ")}),`)

			// Iterate row by row (row-major order)
			for (let rowIdx = 0; rowIdx < maxRows; rowIdx++) {
				for (let colIdx = 0; colIdx < numCols; colIdx++) {
					const column = section.columns[colIdx]
					const field = column.fields?.[rowIdx]

					if (field) {
						if (field.fieldtype === "Table") {
							const fieldname = field.fieldname || "items"
							const label = field.label || "Table"

							lines.push(`  // Table: ${label}`)

							if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
								lines.push(`  // Table field "${fieldname}" not in document`)
							}

							if (!field.table_columns || field.table_columns.length === 0) {
								lines.push(`  // TODO: Table ${fieldname} has no columns defined`)
							}
						}

						const cellContent = this.translateFieldAsCell(field)
						lines.push(this.formatGridCellLine(cellContent))
					} else {
						// Empty cell for alignment
						lines.push(this.formatGridCellLine("[#none]"))
					}
				}
			}

			lines.push(`)`)
		} else {
			lines.push("// (no fields in columns)")
		}
		appendPageBreak()
		return lines.join("\n")
	}

	translateFieldAsCell(field: LayoutField): string {
		// Translate field as a grid cell (wrapped in [], no #parbreak())
		const fieldtype = field.fieldtype || "Data"
		const fieldname = field.fieldname || "unknown"
		const label = this.escapeTypstText((field.label ?? "").trim())

		switch (fieldtype) {
			case "Section Break":
				return `[] // Section Break: ${label || fieldname}`
			case "Column Break":
				return `[] // Column Break`
			case "Typst": {
				const code = String(field.raw_typst_field || "").trim()
				return code ? this.formatContentCell(code) : `[] // Custom Typst (empty)`
			}
			case "Crispy Typst Block": {
				const code = String(field.crispy_typst_block_code || "").trim()
				const blockKey = field.crispy_typst_block || fieldname
				return code ? this.formatContentCell(code) : `[] // Missing Crispy Typst Block: ${blockKey}`
			}
			case "Spacer": {
				const value = field.spacer_value || "1em"
				return `[#v(${value})]`
			}
			case "Divider": {
				const length = field.divider_length || "100%"
				const stroke = field.divider_stroke || "0.5pt"
				const color = field.divider_color || "gray"
				const colorValue = color.startsWith("#") ? `rgb("${color.substring(1)}")` : color
				return `[#line(length: ${length}, stroke: ${stroke} + ${colorValue})]`
			}
			case "Empty":
				return `[#none]`
			case "Table":
				return `[${this.translateTable(field, { includeComment: false })}]`
			case "HTML":
				return `[] // HTML field: ${fieldname}`
			default:
				if ((field as any).print_hide) {
					return `[] // ${label || fieldname} (hidden)`
				}

				if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
					return `[] // ${label || fieldname} (field not in document)`
				}

				const align = field.align || this.getDefaultAlignment(fieldtype)

				if (!label) {
					if (align === "left") {
						return `[#text(..fieldValueStyle)[#doc.${fieldname}]]`
					}
					return `[#align(${align})[#text(..fieldValueStyle)[#doc.${fieldname}]]]`
				}

				if (align === "left") {
					return `[#text(..fieldLabelStyle)[${label}]#linebreak()#text(..fieldValueStyle)[#doc.${fieldname}]]`
				}
				return `[#text(..fieldLabelStyle)[${label}]#linebreak()#align(${align})[#text(..fieldValueStyle)[#doc.${fieldname}]]]`
		}
	}

	private formatGridCellLine(cellContent: string): string {
		if (cellContent.includes("\n")) {
			const indented = cellContent
				.split("\n")
				.map((line) => `  ${line}`)
				.join("\n")
			return `${indented},`
		}

		const placeholderComment = cellContent.match(/^(\[\])\s*(\/\/.*)$/)
		if (placeholderComment) {
			return `  ${placeholderComment[1]}, ${placeholderComment[2]}`
		}

		return `  ${cellContent},`
	}

	private formatContentCell(code: string): string {
		if (code.includes("\n")) {
			return `[\n${code}\n]`
		}
		return `[${code}]`
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
			case "Crispy Typst Block": {
				const code = String(field.crispy_typst_block_code || "").trim()
				const blockKey = field.crispy_typst_block || fieldname
				return code ? code : `// Missing Crispy Typst Block: ${blockKey}`
			}
			case "Spacer": {
				const value = field.spacer_value || "1em"
				return `#v(${value})`
			}
			case "Divider": {
				const length = field.divider_length || "100%"
				const stroke = field.divider_stroke || "0.5pt"
				const color = field.divider_color || "gray"
				// Use rgb() only for hex colors, named colors go directly
				const colorValue = color.startsWith("#") ? `rgb("${color.substring(1)}")` : color
				return `#line(length: ${length}, stroke: ${stroke} + ${colorValue})`
			}
			case "Empty":
				return `[#none]`
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

	translateTable(field: LayoutField, options: { includeComment?: boolean } = {}) {
		const lines: string[] = []
		const fieldname = field.fieldname || "items"
		const label = field.label || "Table"
		const includeComment = options.includeComment !== false
		ensure_table_settings(this.get_presentation_settings())

		if (includeComment) {
			lines.push(`// Table: ${label}`)
		}

		if (this.realDocData && !(fieldname in (this.realDocData as Record<string, any>))) {
			if (includeComment) {
				lines.push(`// Table field "${fieldname}" not in document`)
			}
			return lines.join("\n")
		}

		if (field.table_columns && field.table_columns.length > 0) {
			const columns = field.table_columns
			const itemTable = this.is_item_table(fieldname)
			const compactItems = this.is_enabled_behavior("compact_item_print") && itemTable
			const compactColumns = compactItems
				? this.getCompactItemColumns(columns)
				: { visible: columns, folded: [] as TableColumn[] }
			const effectiveColumns = compactColumns.visible
			const tableSettings = ensure_table_settings(this.get_presentation_settings())
			const splitCellLabels = Boolean(tableSettings.cellLabel?.enabled)
			const rowSource = this.getTableRowSource(fieldname)

			lines.push(`#if type(doc.${fieldname}) == array and doc.${fieldname}.len() > 0 [`)
			lines.push(`  #table(`)
			// Use column widths from layout (auto, 1fr, 2fr, 100pt, etc.)
			const widths = effectiveColumns.flatMap((col) =>
				this.shouldSplitTableCellLabel(col, { itemTable, splitCellLabels })
					? ["auto", col.width || "auto"]
					: [col.width || "auto"]
			)
			lines.push(`    columns: (${widths.join(", ")}),`)
			const alignments = effectiveColumns.flatMap((col) => {
				const align = col.align || this.getDefaultAlignment(col.fieldtype)
				return this.shouldSplitTableCellLabel(col, { itemTable, splitCellLabels })
					? [align, align]
					: [align]
			})
			lines.push(`    align: (${alignments.join(", ")}),`)
			lines.push(`    inset: tableCellInset,`)
			lines.push(`    stroke: tableStroke,`)
			lines.push(
				`    fill: (x, y) => if y == 0 { tableHeaderFill } else { if tableStripeEnabled and calc.even(y) { tableStripeFill } else { none } },`
			)

			const headerCells = effectiveColumns
				.map((col) => {
					const label = this.escapeTypstText(col.label || "")
					return this.shouldSplitTableCellLabel(col, { itemTable, splitCellLabels })
						? `table.cell(colspan: 2)[#text(..tableHeaderStyle)[${label}]]`
						: `[#text(..tableHeaderStyle)[${label}]]`
				})
				.join(", ")
			lines.push(`    table.header(${headerCells}),`)

			// Row data - map each row to all its column values and flatten
			const rowCells = effectiveColumns
				.map((col) =>
					this.renderTableCell(col, {
						itemTable,
						splitCellLabels,
						compactItems,
						foldedColumns: compactColumns.folded,
					})
				)
				.join(", ")
			lines.push(`    ..${rowSource}.map(row => {`)
			lines.push(`      (${rowCells})`)
			lines.push(`    }).flatten(),`)

			lines.push(`  )`)
			lines.push(`]`)
		} else {
			if (includeComment) {
				lines.push(`// TODO: Table ${fieldname} has no columns defined`)
			}
		}

		return lines.join("\n")
	}

	private is_item_table(fieldname: string): boolean {
		return ["items", "packed_items"].includes(String(fieldname || "").toLowerCase())
	}

	private is_tax_table(fieldname: string): boolean {
		return ["taxes", "taxes_and_charges"].includes(String(fieldname || "").toLowerCase())
	}

	private getTableRowSource(fieldname: string): string {
		if (
			!this.is_enabled_behavior("print_taxes_with_zero_amount") &&
			this.is_tax_table(fieldname)
		) {
			return `doc.${fieldname}.filter(row => not cp_is_zero_tax_row(row))`
		}
		return `doc.${fieldname}`
	}

	private renderTableCell(
		col: TableColumn,
		options: {
			itemTable?: boolean
			splitCellLabels?: boolean
			compactItems?: boolean
			foldedColumns?: TableColumn[]
		} = {}
	): string {
		const fieldname = col.fieldname || ""
		if (options.itemTable && options.compactItems && fieldname === "description") {
			return this.renderCompactDescriptionCell(options.foldedColumns || [])
		}
		if (
			options.itemTable &&
			["qty", "quantity", "stock_qty"].includes(fieldname)
		) {
			if (options.splitCellLabels) {
				return `cp_measure_label_table_cell(cp_quantity_parts(row, row.${fieldname}).label), cp_measure_value_table_cell(cp_quantity_parts(row, row.${fieldname}).value)`
			}
			return `[#text(..tableBodyStyle)[#cp_quantity_inline(row, row.${fieldname})]]`
		}
		if (options.itemTable && col.fieldtype === "Currency") {
			if (options.splitCellLabels) {
				return `cp_measure_label_table_cell(cp_currency_parts(row.${fieldname}).label), cp_measure_value_table_cell(cp_currency_parts(row.${fieldname}).value)`
			}
			return `[#text(..tableBodyStyle)[#row.${fieldname}]]`
		}
		return `[#text(..tableBodyStyle)[#row.${fieldname}]]`
	}

	private getCompactItemColumns(columns: TableColumn[]): {
		visible: TableColumn[]
		folded: TableColumn[]
	} {
		const compactFieldnames = new Set(["description", "qty", "rate", "amount"])
		const visible = columns.filter((col) => compactFieldnames.has(col.fieldname || ""))
		const folded = columns.filter((col) => !compactFieldnames.has(col.fieldname || ""))

		if (folded.length && !visible.some((col) => col.fieldname === "description")) {
			visible.unshift({
				fieldname: "description",
				label: "Description",
				fieldtype: "Data",
				width: "1fr",
				align: "left",
			})
		}

		return { visible, folded }
	}

	private renderCompactDescriptionCell(foldedColumns: TableColumn[]): string {
		const lines = [
			"[#if \"description\" in row and row.description != \"\" [#text(..tableBodyStyle)[#row.description]]",
		]
		foldedColumns.forEach((col) => {
			const fieldname = col.fieldname || ""
			if (!fieldname || fieldname === "image") return
			const label = this.escapeTypstText(col.label || fieldname)
			lines.push(
				`#if "${fieldname}" in row and row.${fieldname} != "" [#linebreak()#text(size: tableBodyStyle.size * 0.85, weight: "semibold")[${label}:] #text(..tableBodyStyle)[#row.${fieldname}]]`
			)
		})
		lines.push("]")
		return lines.join("")
	}

	private shouldSplitTableCellLabel(
		col: TableColumn,
		options: { itemTable?: boolean; splitCellLabels?: boolean } = {}
	): boolean {
		if (!options.itemTable || !options.splitCellLabels) return false
		const fieldname = col.fieldname || ""
		return ["qty", "quantity", "stock_qty"].includes(fieldname) || col.fieldtype === "Currency"
	}
}

export { JSONTypstTranslator }
