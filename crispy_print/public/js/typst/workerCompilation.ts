import {
	default_presentation_settings,
	ensure_table_settings,
	ensure_typography,
	merge_presentation_settings,
} from "../utils/presentation_settings"
import { deepClone } from "../utils/json"
import {
	buildForegroundPlacements,
	getLetterheadFilename,
	resolveBrandingMode,
} from "./branding"
import { typstColor, typstLength, typstQuoted } from "./typstEscaping"
import { fontWeightToNumber } from "../utils/typstTextStyle"

const IMAGE_EXTENSIONS = new Set([
	"png",
	"jpg",
	"jpeg",
	"svg",
	"gif",
	"webp",
	"bmp",
	"tif",
	"tiff",
	"avif",
])

/**
 * Parse and format Typst error messages from server responses.
 * Handles nested JSON, escaped strings, and Unicode box drawing characters.
 */
export function parseTypstError(error: any): string {
	try {
		let errorStr = String(error?.message || error || "Typst compilation failed")

		errorStr = errorStr.replace(/\\n/g, "\n")
		errorStr = errorStr.replace(/\\"/g, '"')
		errorStr = errorStr.replace(/\\\\/g, "\\")
		errorStr = errorStr.replace(/\\u250c/g, "┌")
		errorStr = errorStr.replace(/\\u2500/g, "─")
		errorStr = errorStr.replace(/\\u2502/g, "│")

		const typstErrorMatch = errorStr.match(
			/Typst compilation failed:\s*(.+?)(?=\n\nDuring handling|$)/s
		)
		if (typstErrorMatch) {
			errorStr = typstErrorMatch[1].trim()
		}

		const errorMatch = errorStr.match(/error:\s*(.+?)(?=\n|$)/)
		const errorMessage = errorMatch ? errorMatch[1].trim() : "Compilation error"
		const locationMatch = errorStr.match(/document\.typ:(\d+):(\d+)/)
		const location = locationMatch ? `Line ${locationMatch[1]}, Column ${locationMatch[2]}` : ""
		const snippetMatch = errorStr.match(/(\d+)\s*│\s*(.+?)(?=\n|$)/m)
		const snippet = snippetMatch ? snippetMatch[2].trim() : ""
		const parts: string[] = []

		parts.push(`Error: ${errorMessage}`)
		if (location) {
			parts.push(`Location: ${location}`)
		}
		if (snippet) {
			parts.push("")
			parts.push("Code:")
			parts.push(`  ${snippet}`)
		}

		return parts.join("\n")
	} catch (e) {
		return String(error?.message || error || "Compilation failed")
	}
}

export function buildDefaultStyleDefs(presentation_settings: any) {
	const safePresentationSettings = merge_presentation_settings(
		default_presentation_settings,
		presentation_settings ? deepClone(presentation_settings) : {}
	)
	const typography = ensure_typography(safePresentationSettings)
	const fieldLabel = typography.fieldLabel
	const fieldValue = typography.fieldValue
	const sectionLabel = typography.sectionLabel
	const tableSettings = ensure_table_settings(safePresentationSettings)
	const tableHeader = tableSettings.typography.header
	const tableBody = tableSettings.typography.body
	const tableInset = tableSettings.inset
	const tableStrokeWidth = Number.isFinite(tableSettings.stroke.width)
		? tableSettings.stroke.width
		: 0
	const formatColor = (color: string, fallback = "none") => typstColor(color, fallback)
	const tableStrokeColor = formatColor(tableSettings.stroke.color, "black")
	const tableHeaderFill = formatColor(tableSettings.header.backgroundColor, "none")
	const tableStripeFill = formatColor(tableSettings.stripe.color, "none")
	const tableStripeEnabled = Boolean(tableSettings.stripe.enabled)

	const lines: string[] = []
	lines.push("// Typography styles (auto-injected for raw Typst)")
	lines.push("#let fieldLabelStyle = (")
	lines.push(`  font: ${typstQuoted(fieldLabel.fontFamily)},`)
	lines.push(`  size: ${typstLength(fieldLabel.fontSize, 8)},`)
	lines.push(`  style: ${typstQuoted(fieldLabel.fontStyle)},`)
	lines.push(`  weight: ${fontWeightToNumber(fieldLabel.fontWeight)},`)
	lines.push(`  fill: ${formatColor(fieldLabel.color, "black")}`)
	lines.push(")")
	lines.push("")
	lines.push("#let fieldValueStyle = (")
	lines.push(`  font: ${typstQuoted(fieldValue.fontFamily)},`)
	lines.push(`  size: ${typstLength(fieldValue.fontSize, 10)},`)
	lines.push(`  style: ${typstQuoted(fieldValue.fontStyle)},`)
	lines.push(`  weight: ${fontWeightToNumber(fieldValue.fontWeight)},`)
	lines.push(`  fill: ${formatColor(fieldValue.color, "black")}`)
	lines.push(")")
	lines.push("")
	lines.push("#let sectionLabelStyle = (")
	lines.push(`  font: ${typstQuoted(sectionLabel.fontFamily)},`)
	lines.push(`  size: ${typstLength(sectionLabel.fontSize, 14)},`)
	lines.push(`  style: ${typstQuoted(sectionLabel.fontStyle)},`)
	lines.push(`  weight: ${fontWeightToNumber(sectionLabel.fontWeight)},`)
	lines.push(`  fill: ${formatColor(sectionLabel.color, "black")}`)
	lines.push(")")
	lines.push("")
	lines.push("// Table styles (auto-injected for raw Typst)")
	lines.push("#let tableHeaderStyle = (")
	lines.push(`  font: ${typstQuoted(tableHeader.fontFamily)},`)
	lines.push(`  size: ${typstLength(tableHeader.fontSize, 9)},`)
	lines.push(`  style: ${typstQuoted(tableHeader.fontStyle)},`)
	lines.push(`  weight: ${fontWeightToNumber(tableHeader.fontWeight)},`)
	lines.push(`  fill: ${formatColor(tableHeader.color, "black")}`)
	lines.push(")")
	lines.push("")
	lines.push("#let tableBodyStyle = (")
	lines.push(`  font: ${typstQuoted(tableBody.fontFamily)},`)
	lines.push(`  size: ${typstLength(tableBody.fontSize, 9)},`)
	lines.push(`  style: ${typstQuoted(tableBody.fontStyle)},`)
	lines.push(`  weight: ${fontWeightToNumber(tableBody.fontWeight)},`)
	lines.push(`  fill: ${formatColor(tableBody.color, "black")}`)
	lines.push(")")
	lines.push("")
	lines.push(
		`#let tableCellInset = (top: ${tableInset.top}pt, right: ${tableInset.right}pt, bottom: ${tableInset.bottom}pt, left: ${tableInset.left}pt)`
	)
	lines.push(
		`#let tableStroke = ${
			tableStrokeWidth > 0 ? `${tableStrokeWidth}pt + ${tableStrokeColor}` : "none"
		}`
	)
	lines.push(`#let tableHeaderFill = ${tableHeaderFill}`)
	lines.push(`#let tableStripeFill = ${tableStripeFill}`)
	lines.push(`#let tableStripeEnabled = ${tableStripeEnabled ? "true" : "false"}`)
	lines.push("")
	return lines.join("\n")
}

export function buildPresentationSettingsBlock(options: {
	presentation_settings?: Record<string, any> | null
	letterheadData?: Record<string, any> | null
	qrEnabled?: boolean
	qrData?: string | null
	qrFilename?: string | null
	qrSettings?: Record<string, any> | null
}) {
	const lines: string[] = []
	const presentation_settings = merge_presentation_settings(
		default_presentation_settings,
		options.presentation_settings || {}
	)
	const margins = presentation_settings.page.margins || {}
	const page_size = String(presentation_settings.page.size || "A4").toLowerCase()
	const orientation = String(presentation_settings.page.orientation || "portrait")
	const marginValue = (value: any, fallback: number) => {
		const num = Number(value)
		return Number.isFinite(num) ? num : fallback
	}
	const marginTop = marginValue(margins.top, 25)
	const marginBottom = marginValue(margins.bottom, 20)
	const marginLeft = marginValue(margins.left, 20)
	const marginRight = marginValue(margins.right, 20)
	const branding_mode = resolveBrandingMode(presentation_settings, options.letterheadData)
	const letterheadFilename = getLetterheadFilename(presentation_settings, options.letterheadData)
	const foregroundLines = buildForegroundPlacements({
		presentation_settings,
		branding_mode,
		qrEnabled: options.qrEnabled,
		qrData: options.qrData,
		qrFilename: options.qrFilename,
		qrSettings: options.qrSettings,
	})

	lines.push("// Presentation settings (from Settings pane)")
	lines.push("#set page(")
	lines.push(`  paper: ${typstQuoted(page_size)},`)
	if (orientation === "landscape") {
		lines.push("  flipped: true,")
	}
	lines.push(
		`  margin: (top: ${marginTop}mm, bottom: ${marginBottom}mm, left: ${marginLeft}mm, right: ${marginRight}mm),`
	)
	lines.push("  header: header_block,")
	lines.push("  footer: footer_block,")
	if (letterheadFilename) {
		lines.push(`  background: image("${letterheadFilename}", width: 100%)`)
	}
	if (foregroundLines.length) {
		lines.push("  foreground: [")
		foregroundLines.forEach((line) => {
			lines.push(`    ${line}`)
		})
		lines.push("  ]")
	}
	lines.push(")")
	lines.push("")

	return lines.join("\n").trim()
}

export function buildHeaderFooterBlock(options: { docHeader?: string; docFooter?: string }) {
	const lines: string[] = []

	lines.push("#let header_block = []")
	lines.push("#let footer_block = []")
	lines.push("")

	if (options.docHeader && options.docHeader.trim()) {
		lines.push("// Document Header")
		lines.push(options.docHeader.trim())
		lines.push("")
	}
	if (options.docFooter && options.docFooter.trim()) {
		lines.push("// Document Footer")
		lines.push(options.docFooter.trim())
		lines.push("")
	}
	return lines.join("\n").trim()
}

function isImageAssetValue(value: string): boolean {
	const raw = String(value || "").trim()
	if (!raw) return false
	const match = raw.match(/\.([a-zA-Z0-9]+)(?:[#?].*)?$/)
	if (!match) return false
	return IMAGE_EXTENSIONS.has(String(match[1] || "").toLowerCase())
}

export function normalizeDocImageAssets(value: any, collector: Set<string>): any {
	if (Array.isArray(value)) {
		return value.map((item) => normalizeDocImageAssets(item, collector))
	}
	if (value && typeof value === "object") {
		const out: Record<string, any> = {}
		Object.entries(value as Record<string, any>).forEach(([key, item]) => {
			out[key] = normalizeDocImageAssets(item, collector)
		})
		return out
	}
	if (typeof value !== "string") {
		return value
	}

	const raw = value.trim()
	if (!isImageAssetValue(raw)) {
		return value
	}
	collector.add(raw)
	const filename = raw.split("/").pop()
	return filename || value
}
