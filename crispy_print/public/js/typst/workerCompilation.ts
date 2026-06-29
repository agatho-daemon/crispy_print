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
import { resolveTypstPaper } from "./page"
import { typstQuoted } from "./typstEscaping"
import { buildTableStyleConstants, buildTypographyStyleDefs } from "./textStyles"

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

	const lines: string[] = []
	lines.push(
		buildTypographyStyleDefs(
			{ fieldLabel, fieldValue, sectionLabel },
			tableSettings,
			{
				typographyComment: "// Typography styles (auto-injected for raw Typst)",
				tableComment: "// Table styles (auto-injected for raw Typst)",
			}
		)
	)
	lines.push(buildTableStyleConstants(tableSettings))
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
	const page_size = resolveTypstPaper(presentation_settings.page.size || "A4")
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
