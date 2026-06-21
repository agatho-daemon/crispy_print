import type { TableSettings } from "./presentation_settings"
import { typstTextStyle } from "../typst/textStyles"
import { escapeTypstString } from "./typstEscape"

export const REPORT_BASIC_SIGNATURE_PREFIX = "CRISPY_REPORT_BASIC_SIGNATURE:"

export type ReportBuilderMode = "basic" | "advanced"
export type ReportBuilderPreset = "grid" | "tree" | "summary" | "minimal"
export type ColumnAlignStrategy = "auto" | "left" | "center" | "right"

export interface ReportBuilderConfig {
	mode: ReportBuilderMode
	preset: ReportBuilderPreset
	show_filters: boolean
	show_summary: boolean
	include_total_row: boolean
	show_footer_total: boolean
	chart_enabled: boolean
	chart_width_percent: number
	chart_max_height_pt: number
	chart_card_border: boolean
	chart_spacing_top_pt: number
	chart_spacing_bottom_pt: number
	header_fill: string
	header_text_weight: string
	font_family: string
	font_size_pt: number
	row_striping: boolean
	row_stripe_fill: string
	column_align_strategy: ColumnAlignStrategy
	table_inset_x_pt: number
	table_inset_y_pt: number
	table_stroke_top_pt: number
	table_stroke_body_pt: number
	raw_signature: string | null
	report_table_sync_signature: string | null
}

interface ReportTypstBuildOptions {
	tableSettings?: TableSettings | null
}

export function getDefaultReportBuilderConfig(
	genericReportType?: string | null
): ReportBuilderConfig {
	const type = String(genericReportType || "").toLowerCase()
	const preset: ReportBuilderPreset =
		type === "tree"
			? "tree"
			: type === "summary"
				? "summary"
				: type === "minimal"
					? "minimal"
					: "grid"

	return {
		mode: "basic",
		preset,
		show_filters: true,
		show_summary: true,
		include_total_row: true,
		show_footer_total: true,
		chart_enabled: true,
		chart_width_percent: 100,
		chart_max_height_pt: 220,
		chart_card_border: true,
		chart_spacing_top_pt: 0,
		chart_spacing_bottom_pt: 12,
		header_fill: "#B3D7FF",
		header_text_weight: "bold",
		font_family: "Inter 18pt",
		font_size_pt: 9,
		row_striping: false,
		row_stripe_fill: "#F8FBFF",
		column_align_strategy: "auto",
		table_inset_x_pt: 8,
		table_inset_y_pt: 6,
		table_stroke_top_pt: 1,
		table_stroke_body_pt: 0.5,
		raw_signature: null,
		report_table_sync_signature: null,
	}
}

export function normalizeReportBuilderConfig(
	input: unknown,
	genericReportType?: string | null
): ReportBuilderConfig {
	const defaults = getDefaultReportBuilderConfig(genericReportType)
	const raw = (input && typeof input === "object" ? input : {}) as Record<string, unknown>

	const mode = raw.mode === "advanced" ? "advanced" : "basic"
	const presetCandidate = String(raw.preset || defaults.preset).toLowerCase()
	const preset: ReportBuilderPreset =
		presetCandidate === "tree" || presetCandidate === "summary" || presetCandidate === "minimal"
			? (presetCandidate as ReportBuilderPreset)
			: "grid"

	const alignCandidate = String(raw.column_align_strategy || defaults.column_align_strategy)
	const column_align_strategy: ColumnAlignStrategy =
		alignCandidate === "left" ||
		alignCandidate === "center" ||
		alignCandidate === "right" ||
		alignCandidate === "auto"
			? (alignCandidate as ColumnAlignStrategy)
			: "auto"

	const includeTotalRow = toBool(
		raw.include_total_row,
		toBool(raw.show_footer_total, defaults.include_total_row)
	)

	return {
		...defaults,
		mode,
		preset,
		show_filters: toBool(raw.show_filters, defaults.show_filters),
		show_summary: toBool(raw.show_summary, defaults.show_summary),
		include_total_row: includeTotalRow,
		show_footer_total: includeTotalRow,
		chart_enabled: toBool(raw.chart_enabled, defaults.chart_enabled),
		chart_width_percent: clamp(toNumber(raw.chart_width_percent, defaults.chart_width_percent), 10, 100),
		chart_max_height_pt: clamp(toNumber(raw.chart_max_height_pt, defaults.chart_max_height_pt), 60, 600),
		chart_card_border: toBool(raw.chart_card_border, defaults.chart_card_border),
		chart_spacing_top_pt: clamp(toNumber(raw.chart_spacing_top_pt, defaults.chart_spacing_top_pt), 0, 120),
		chart_spacing_bottom_pt: clamp(
			toNumber(raw.chart_spacing_bottom_pt, defaults.chart_spacing_bottom_pt),
			0,
			120
		),
		header_fill: asString(raw.header_fill, defaults.header_fill),
		header_text_weight: asString(raw.header_text_weight, defaults.header_text_weight),
		font_family: asString(raw.font_family, defaults.font_family),
		font_size_pt: clamp(toNumber(raw.font_size_pt, defaults.font_size_pt), 4, 96),
		row_striping: toBool(raw.row_striping, defaults.row_striping),
		row_stripe_fill: asString(raw.row_stripe_fill, defaults.row_stripe_fill),
		column_align_strategy,
		table_inset_x_pt: toNumber(raw.table_inset_x_pt, defaults.table_inset_x_pt),
		table_inset_y_pt: toNumber(raw.table_inset_y_pt, defaults.table_inset_y_pt),
		table_stroke_top_pt: toNumber(raw.table_stroke_top_pt, defaults.table_stroke_top_pt),
		table_stroke_body_pt: toNumber(raw.table_stroke_body_pt, defaults.table_stroke_body_pt),
		raw_signature:
			typeof raw.raw_signature === "string" && raw.raw_signature.trim()
				? raw.raw_signature.trim()
				: null,
		report_table_sync_signature:
			typeof raw.report_table_sync_signature === "string" && raw.report_table_sync_signature.trim()
				? raw.report_table_sync_signature.trim()
				: null,
	}
}

export function buildReportTypstFromConfig(
	config: ReportBuilderConfig,
	options: ReportTypstBuildOptions = {}
): string {
	const fontSize = Math.max(1, Number(config.font_size_pt) || 9)
	const tableHeaderAlign = resolveHeaderAlign(config.column_align_strategy)
	const tableBodyAlign = resolveBodyAlign(config.column_align_strategy)
	const tableSettings = options.tableSettings || null
	const stripeEnabled = tableSettings ? Boolean(tableSettings.stripe.enabled) : config.row_striping
	const stripeFill = asHexColor(
		tableSettings?.stripe?.color || config.row_stripe_fill,
		"#F8FBFF"
	)
	const headerFill = asHexColor(
		tableSettings?.header?.backgroundColor || config.header_fill,
		"#B3D7FF"
	)
	const tableStrokeTopPt = tableSettings
		? toNumber(tableSettings.stroke?.width, config.table_stroke_top_pt)
		: config.table_stroke_top_pt
	const tableStrokeBodyPt = tableSettings
		? toNumber(tableSettings.stroke?.width, config.table_stroke_body_pt)
		: config.table_stroke_body_pt
	const tableInsetTopPt = tableSettings
		? toNumber(tableSettings.inset?.top, config.table_inset_y_pt)
		: config.table_inset_y_pt
	const tableInsetRightPt = tableSettings
		? toNumber(tableSettings.inset?.right, config.table_inset_x_pt)
		: config.table_inset_x_pt
	const tableInsetBottomPt = tableSettings
		? toNumber(tableSettings.inset?.bottom, config.table_inset_y_pt)
		: config.table_inset_y_pt
	const tableInsetLeftPt = tableSettings
		? toNumber(tableSettings.inset?.left, config.table_inset_x_pt)
		: config.table_inset_x_pt
	const headerFontFamily = asString(
		tableSettings?.typography?.header?.fontFamily,
		config.font_family
	)
	const headerFontSize = formatPt(
		toPointNumber(tableSettings?.typography?.header?.fontSize, fontSize)
	)
	const headerFontStyle = asString(tableSettings?.typography?.header?.fontStyle, "normal")
	const headerFontWeight = asString(
		tableSettings?.typography?.header?.fontWeight,
		config.header_text_weight
	)
	const headerFontColor = asHexColor(
		tableSettings?.typography?.header?.color || "#0f172a",
		"#0f172a"
	)
	const headerTextStyle = typstTextStyle(
		{
			fontFamily: headerFontFamily,
			fontSize: headerFontSize,
			fontStyle: headerFontStyle,
			fontWeight: headerFontWeight,
			color: `#${headerFontColor}`,
		},
		fontSize
	)
	const bodyFontFamily = asString(
		tableSettings?.typography?.body?.fontFamily,
		config.font_family
	)
	const bodyFontSize = formatPt(
		toPointNumber(tableSettings?.typography?.body?.fontSize, fontSize)
	)
	const bodyFontStyle = asString(tableSettings?.typography?.body?.fontStyle, "normal")
	const bodyFontWeight = asString(tableSettings?.typography?.body?.fontWeight, "regular")
	const bodyFontColor = asHexColor(
		tableSettings?.typography?.body?.color || "#0f172a",
		"#0f172a"
	)
	const bodyTextStyle = typstTextStyle(
		{
			fontFamily: bodyFontFamily,
			fontSize: bodyFontSize,
			fontStyle: bodyFontStyle,
			fontWeight: bodyFontWeight,
			color: `#${bodyFontColor}`,
		},
		fontSize
	)
	const boldBodyTextStyle = typstTextStyle(
		{
			fontFamily: bodyFontFamily,
			fontSize: bodyFontSize,
			fontStyle: bodyFontStyle,
			fontWeight: "bold",
			color: `#${bodyFontColor}`,
		},
		fontSize
	)

	const lines: string[] = []
	lines.push("// Generated by Crispy Report Basic Mode")
	lines.push("// Edit in Advanced mode for full control.")
	lines.push(`#set text(font: "${escapeTypstString(config.font_family)}", size: ${formatPt(fontSize)})`)
	lines.push("")
	lines.push("#align(center)[")
	lines.push('  #text(size: 16pt, weight: "bold")[#data.title]')
	lines.push("  #v(0.3em)")
	lines.push('  #text(size: 9pt, fill: rgb("#666"))[#data.subtitle]')
	lines.push("]")
	lines.push("")
	lines.push("#v(1em)")
	lines.push("")

	if (config.show_filters) {
		lines.push('#if "filters" in data and data.filters.len() > 0 [')
		lines.push("  #block(")
		lines.push('    fill: rgb("f5f5f5"),')
		lines.push("    inset: 10pt,")
		lines.push("    radius: 4pt,")
		lines.push("    width: 100%,")
		lines.push("  )[")
		lines.push('    #text(size: 9pt, weight: "semibold")[Filters:]')
		lines.push("    #v(0.5em)")
		lines.push("    #grid(")
		lines.push("      columns: (auto, 1fr) * 2,")
		lines.push("      column-gutter: 12pt,")
		lines.push("      row-gutter: 6pt,")
		lines.push("      ..data")
		lines.push("        .filters")
		lines.push("        .map(f => (")
		lines.push('          text(size: 8pt, weight: "medium")[#f.label:],')
		lines.push("          text(size: 8pt)[#f.value],")
		lines.push("        ))")
		lines.push("        .flatten()")
		lines.push("    )")
		lines.push("  ]")
		lines.push("  #v(1em)")
		lines.push("]")
		lines.push("")
	}

	if (config.chart_enabled) {
		lines.push('#if "chart_svg" in data and data.chart_svg != "" [')
		if (config.chart_spacing_top_pt > 0) {
			lines.push(`  #v(${formatPt(config.chart_spacing_top_pt)})`)
		}
		lines.push("  #block(")
		lines.push(
			`    stroke: ${
				config.chart_card_border
					? '(paint: rgb("E5E7EB"), thickness: 0.5pt)'
					: "none"
			},`
		)
		lines.push("    inset: (x: 8pt, y: 8pt),")
		lines.push("    radius: 2pt,")
		lines.push("  )[")
		lines.push("    #align(center)[")
		lines.push(
			`      #image(data.chart_svg, width: ${Math.round(
				config.chart_width_percent
			)}%, height: ${formatPt(config.chart_max_height_pt)}, fit: "contain")`
		)
		lines.push("    ]")
		lines.push("  ]")
		if (config.chart_spacing_bottom_pt > 0) {
			lines.push(`  #v(${formatPt(config.chart_spacing_bottom_pt)})`)
		}
		lines.push("]")
		lines.push("")
	}

	if (config.show_summary) {
		lines.push('#if "report_summary" in data and data.report_summary.len() > 0 [')
		lines.push("  #block(")
		lines.push("    inset: (x: 8pt, y: 6pt),")
		lines.push("    width: 100%,")
		lines.push("  )[")
		lines.push("    #grid(")
		lines.push("      columns: (1fr, auto),")
		lines.push("      column-gutter: 12pt,")
		lines.push("      row-gutter: 4pt,")
		lines.push("      ..data")
		lines.push("        .report_summary")
		lines.push("        .map(item => (")
		lines.push('          text(size: 8pt, weight: "medium")[#item.label],')
		lines.push(
			'          text(size: 8pt, fill: if "color_class" in item and item.color_class == "green" { rgb("#22C55E") } else if "color_class" in item and item.color_class == "red" { rgb("#EF4444") } else if "color_class" in item and item.color_class == "blue" { rgb("#3B82F6") } else { rgb("#0f172a") })['
		)
		lines.push(
			'            #if "formatted_value" in item and item.formatted_value != "" { item.formatted_value } else { item.value }'
		)
		lines.push("          ],")
		lines.push("        ))")
		lines.push("        .flatten()")
		lines.push("    )")
		lines.push("  ]")
		lines.push("  #v(0.8em)")
		lines.push("]")
		lines.push("")
	}

	lines.push("#let cp_column_width(col) = {")
	lines.push('  if "width_kind" in col {')
	lines.push('    if col.width_kind == "auto" { auto }')
	lines.push('    else if col.width_kind == "fr" { col.width_value * 1fr }')
	lines.push('    else if col.width_kind == "pt" { col.width_value * 1pt }')
	lines.push('    else if col.width_kind == "em" { col.width_value * 1em }')
	lines.push('    else if col.width_kind == "rem" { col.width_value * 1em }')
	lines.push('    else if col.width_kind == "%" { col.width_value * 1% }')
	lines.push('    else if col.width_kind == "cm" { col.width_value * 1cm }')
	lines.push('    else if col.width_kind == "mm" { col.width_value * 1mm }')
	lines.push('    else if col.width_kind == "in" { col.width_value * 1in }')
	lines.push("    else { auto }")
	lines.push("  } else { auto }")
	lines.push("}")
	lines.push("")
	lines.push("#table(")
	lines.push("  columns: data.columns.map(cp_column_width),")
	lines.push("")
	lines.push("  stroke: (x, y) => (")
	lines.push(`    top: if y == 0 { ${formatPt(tableStrokeTopPt)} } else { ${formatPt(tableStrokeBodyPt)} },`)
	lines.push(`    bottom: ${formatPt(tableStrokeBodyPt)},`)
	lines.push("    left: 0pt,")
	lines.push("    right: 0pt,")
	lines.push("  ),")
	lines.push("")
	lines.push("  align: (x, y) => {")
	lines.push("    if y == 0 {")
	lines.push(`      ${tableHeaderAlign} + horizon`)
	lines.push("    } else if data.columns.at(x).is_numeric {")
	lines.push(`      ${tableBodyAlign}`)
	lines.push("    } else {")
	lines.push(`      ${tableBodyAlign === "right + horizon" ? "left + horizon" : tableBodyAlign}`)
	lines.push("    }")
	lines.push("  },")
	lines.push("")
	lines.push("  fill: (x, y) => {")
	lines.push('    if y == 0 { rgb("' + headerFill + '") }')
	if (stripeEnabled) {
		lines.push(`    else if calc.even(y) { rgb("${stripeFill}") }`)
	}
	lines.push("  },")
	lines.push("")
	lines.push(
		`  inset: (top: ${formatPt(tableInsetTopPt)}, right: ${formatPt(tableInsetRightPt)}, bottom: ${formatPt(tableInsetBottomPt)}, left: ${formatPt(tableInsetLeftPt)}),`
	)
	lines.push("")
	lines.push("  table.header(")
	lines.push(
		`    ..data.columns.map(col => text(..${headerTextStyle})[#col.label])`
	)
	lines.push("  ),")
	lines.push("")
	lines.push("  ..data")
	lines.push("    .rows")
	if (!config.include_total_row) {
		lines.push("    .filter(row => row.is_total_row != true)")
	}
	lines.push("    .map(row => {")
	lines.push("      row.cells.enumerate().map(cell_entry => {")
	lines.push("        let idx = cell_entry.at(0)")
	lines.push("        let cell = cell_entry.at(1)")
	lines.push("        let content = if row.is_bold {")
	lines.push(
		`          text(..${boldBodyTextStyle})[#cell.value]`
	)
	lines.push("        } else {")
	lines.push(
		`          text(..${bodyTextStyle})[#cell.value]`
	)
	lines.push("        }")
	lines.push('        if idx == 0 and "indent" in row and row.indent != none and row.indent > 0 {')
	lines.push("          box(inset: (left: row.indent * 2em))[#content]")
	lines.push("        } else {")
	lines.push("          content")
	lines.push("        }")
	lines.push("      })")
	lines.push("    })")
	lines.push("    .flatten()")
	lines.push(")")

	if (config.show_footer_total) {
		lines.push("")
		lines.push("#v(1em)")
		lines.push("#align(right)[")
		lines.push('  #text(size: 8pt, fill: rgb("#666"))[')
		lines.push("    Total Records: #data.total_rows")
		lines.push("  ]")
		lines.push("]")
	}

	const body = lines.join("\n").trim()
	const signature = computeReportBasicSignature(body)
	return `// ${REPORT_BASIC_SIGNATURE_PREFIX}${signature}\n${body}\n`
}

export function computeReportBasicSignature(source: string): string {
	const normalized = stripSignature(source)
	let hash = 5381
	for (let i = 0; i < normalized.length; i += 1) {
		hash = (hash * 33) ^ normalized.charCodeAt(i)
	}
	return (hash >>> 0).toString(16)
}

export function extractReportBasicSignature(source: string): string | null {
	if (!source) return null
	const firstLine = source.split("\n", 1)[0] || ""
	const marker = `// ${REPORT_BASIC_SIGNATURE_PREFIX}`
	if (!firstLine.startsWith(marker)) return null
	const value = firstLine.replace(marker, "").trim()
	return value || null
}

export function isBasicManagedTypst(source: string, signature?: string | null): boolean {
	if (!source || !source.trim()) return false
	const embedded = extractReportBasicSignature(source)
	if (!embedded) return false
	const expected = signature || embedded
	const actual = computeReportBasicSignature(source)
	return expected === actual
}

function stripSignature(source: string): string {
	const lines = (source || "").replace(/\r\n/g, "\n").split("\n")
	if (!lines.length) return ""
	const marker = `// ${REPORT_BASIC_SIGNATURE_PREFIX}`
	const filtered = lines[0].startsWith(marker) ? lines.slice(1) : lines
	return filtered.join("\n").trim()
}

function toBool(value: unknown, fallback: boolean): boolean {
	return typeof value === "boolean" ? value : fallback
}

function toNumber(value: unknown, fallback: number): number {
	const num = Number(value)
	return Number.isFinite(num) ? num : fallback
}

function toPointNumber(value: unknown, fallback: number): number {
	if (typeof value === "string") {
		const match = value.trim().match(/^(-?\d+(?:\.\d+)?)pt$/i)
		if (match) {
			const parsed = Number(match[1])
			return Number.isFinite(parsed) ? parsed : fallback
		}
	}
	return toNumber(value, fallback)
}

function asString(value: unknown, fallback: string): string {
	return typeof value === "string" && value.trim() ? value.trim() : fallback
}

function formatPt(value: number): string {
	const num = Number.isFinite(value) ? value : 0
	return `${Math.max(0, num)}pt`
}

function asHexColor(value: string, fallback: string): string {
	const raw = String(value || "").trim()
	const withHash = raw.startsWith("#") ? raw : `#${raw}`
	return /^#[0-9a-fA-F]{6}$/.test(withHash) ? withHash.slice(1) : fallback.replace("#", "")
}

function clamp(value: number, min: number, max: number): number {
	return Math.min(Math.max(value, min), max)
}

function resolveHeaderAlign(strategy: ColumnAlignStrategy): string {
	switch (strategy) {
		case "left":
			return "left"
		case "right":
			return "right"
		case "center":
			return "center"
		default:
			return "center"
	}
}

function resolveBodyAlign(strategy: ColumnAlignStrategy): string {
	switch (strategy) {
		case "left":
			return "left + horizon"
		case "center":
			return "center + horizon"
		case "right":
			return "right + horizon"
		default:
			return "right + horizon"
	}
}
