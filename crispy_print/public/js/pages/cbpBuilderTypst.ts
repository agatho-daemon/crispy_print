import type { CrispyBrandingProfileDoc } from "../api/crispy"
import { num, pageDimensions, specimenRows } from "./cbpBuilderSupport"

export interface CbpPreviewTypstContext {
	model: CrispyBrandingProfileDoc
	profileName: string
	isDefault: boolean
	effectiveCodeOnly: boolean
	tableStriping: boolean
	qrEnabled: boolean
	usesLogo: boolean
	logoImage: string
	letterheadImage: string
	letterheadLabel: string
	letterheadSourceLabel: string
}

export function buildCodePreviewTypst(source: string, context: CbpPreviewTypstContext) {
	return `${buildSpecimenDictionary(context)}\n\n${source}`
}

export function buildVisualPreviewTypst(context: CbpPreviewTypstContext) {
	const { model } = context
	const page = pageDimensions(model.page_size || "A4", model.orientation || "portrait")
	const letterhead = assetFilename(context.letterheadImage)
	const logo = context.usesLogo ? assetFilename(context.logoImage) : ""
	const pageBackground = letterhead
		? `\n  background: image(${toTypstValue(letterhead)}, width: 100%),`
		: ""
	const logoPlacement = logo
		? `\n    #place(top + left, dx: ${num(model.branding_logo_offset_x_mm)}mm, dy: ${num(model.branding_logo_offset_y_mm)}mm, image(${toTypstValue(logo)}, width: ${num(model.branding_logo_width_mm)}mm))`
		: ""
	const qrPlacement = context.qrEnabled
		? `\n    #place(bottom + left, dx: ${num(model.qr_dx_mm)}mm, dy: ${num(model.qr_dy_mm)}mm)[#box(width: ${num(model.qr_code_size_mm)}mm, height: ${num(model.qr_code_size_mm)}mm, stroke: (paint: black, thickness: 0.7pt))[#align(center + horizon)[#text(size: 8pt, weight: "bold")[QR]]]]`
		: ""
	const pageForeground =
		logoPlacement || qrPlacement
			? `\n  foreground: [${logoPlacement}${qrPlacement}\n  ],`
			: ""
	const tableFill = context.tableStriping
		? `(x, y) => if y == 0 { rgb(${toTypstValue(model.table_header_background_color || "#F1F5F9")}) } else if y == 2 { rgb(${toTypstValue(model.table_stripe_color || "#F8FAFC")}) }`
		: `(x, y) => if y == 0 { rgb(${toTypstValue(model.table_header_background_color || "#F1F5F9")}) }`

	return `#set page(
  width: ${page.width}mm,
  height: ${page.height}mm,
  margin: (
    top: ${num(model.margin_top_mm)}mm,
    right: ${num(model.margin_right_mm)}mm,
    bottom: ${num(model.margin_bottom_mm)}mm,
    left: ${num(model.margin_left_mm)}mm,
  ),${pageBackground}${pageForeground}
)

#set text(font: ${toTypstValue(model.field_value_font_family || "Arial")}, size: ${num(model.field_value_font_size_pt)}pt)

#let sectionStyle = ${typstTextStyle(model, "section_label")}
#let fieldLabelStyle = ${typstTextStyle(model, "field_label")}
#let fieldValueStyle = ${typstTextStyle(model, "field_value")}
#let tableHeaderStyle = ${typstTextStyle(model, "table_header")}
#let tableBodyStyle = ${typstTextStyle(model, "table_body")}
#let specimenSectionStyle = (size: 14pt, weight: "bold", fill: black)
#let specimenSampleHeadingStyle = (size: 10pt, weight: "bold", fill: rgb("#334155"))

#let section(title) = [
  #v(1.75em)
  #text(..specimenSectionStyle)[#title]
  #v(-1.00em)
  #line(length: 100%, stroke: 0.45pt + rgb("#E5E7EB"))
  #v(0.20em)
]

#let field(label, value) = [
  #text(..fieldLabelStyle)[#label]#linebreak()#text(..fieldValueStyle)[#value]
]

#section[Page Settings]
#grid(
  columns: (1fr,) * 4,
  column-gutter: 12pt,
  row-gutter: 8pt,
  field[Profile Name][${typstContent(model.profile_name || context.profileName)}],
  field[Company][${typstContent(model.company || "Not selected")}],
  field[Default][${typstContent(context.isDefault ? "Yes" : "No")}],
  field[Page Size][${typstContent(model.page_size || "A4")}],
  field[Orientation][${typstContent(titleCase(model.orientation || "portrait"))}],
  field[Margin Top][${typstContent(mmValue(model.margin_top_mm))}],
  field[Margin Right][${typstContent(mmValue(model.margin_right_mm))}],
  field[Margin Bottom][${typstContent(mmValue(model.margin_bottom_mm))}],
  field[Margin Left][${typstContent(mmValue(model.margin_left_mm))}],
)

#section[Typography Settings]
#grid(
  columns: (1fr,) * 3,
  column-gutter: 16pt,
  row-gutter: 1.50em,
  [#text(..fieldLabelStyle)[Section Label]],
  [#text(..fieldLabelStyle)[Field Label]],
  [#text(..fieldLabelStyle)[Field Value]],
  grid.cell(align: bottom)[#text(..sectionStyle)[Section Label]],
  grid.cell(align: bottom)[#text(..fieldLabelStyle)[Field Label]],
  grid.cell(align: bottom)[#text(..fieldValueStyle)[Field Value]],
)

#section[Table Settings]
#grid(
  columns: (1fr,) * 4,
  column-gutter: 12pt,
  row-gutter: 8pt,
  field[Cell Top][${typstContent(ptValue(model.table_cell_inset_top_pt))}],
  field[Cell Right][${typstContent(ptValue(model.table_cell_inset_right_pt))}],
  field[Cell Bottom][${typstContent(ptValue(model.table_cell_inset_bottom_pt))}],
  field[Cell Left][${typstContent(ptValue(model.table_cell_inset_left_pt))}],
  field[Border Stroke][${typstContent(ptValue(model.table_border_stroke_width_pt))}],
  field[Border Color][${typstContent(model.table_border_color || "#E2E8F0")}],
  field[Header Fill][${typstContent(model.table_header_background_color || "#F1F5F9")}],
  field[Striping][${typstContent(context.tableStriping ? "Enabled" : "Disabled")}],
  field[Stripe Fill][${typstContent(model.table_stripe_color || "#F8FAFC")}],
)

#v(0.65em)
#table(
  columns: (1fr, 1.7fr, auto, auto),
  inset: (
    top: ${num(model.table_cell_inset_top_pt)}pt,
    right: ${num(model.table_cell_inset_right_pt)}pt,
    bottom: ${num(model.table_cell_inset_bottom_pt)}pt,
    left: ${num(model.table_cell_inset_left_pt)}pt,
  ),
  stroke: (paint: rgb(${toTypstValue(model.table_border_color || "#E2E8F0")}), thickness: ${num(model.table_border_stroke_width_pt)}pt),
  fill: ${tableFill},
  table.header(
    [#text(..tableHeaderStyle)[Column 1]],
    [#text(..tableHeaderStyle)[Column 2]],
    [#align(right)[#text(..tableHeaderStyle)[Column 3]]],
    [#text(..tableHeaderStyle)[Column 4]],
  ),
  ${specimenRows.map((row) => `[#text(..tableBodyStyle)[${typstContent(row.label)}]], [#text(..tableBodyStyle)[${typstContent(row.value)}]], [#align(right)[#text(..tableBodyStyle)[${typstContent(row.amount)}]]], [#text(..tableBodyStyle)[${typstContent(row.status)}]],`).join("\n  ")}
)

#section[Branding]
#grid(
  columns: (1fr,) * 4,
  column-gutter: 12pt,
  row-gutter: 8pt,
  field[Mode][${typstContent(model.branding_mode || "None")}],
  field[Logo Source][${typstContent(model.branding_logo_source || "Company logo")}],
  field[Logo Width][${typstContent(mmValue(model.branding_logo_width_mm))}],
  field[Logo X][${typstContent(mmValue(model.branding_logo_offset_x_mm))}],
  field[Logo Y][${typstContent(mmValue(model.branding_logo_offset_y_mm))}],
  field[Letterhead Source][${typstContent(context.letterheadSourceLabel)}],
  field[Letterhead][${typstContent(context.letterheadLabel)}],
)

#section[QR Code]
#grid(
  columns: (1fr,) * 4,
  column-gutter: 12pt,
  row-gutter: 8pt,
  field[Enabled][${typstContent(context.qrEnabled ? "Yes" : "No")}],
  field[Size][${typstContent(mmValue(model.qr_code_size_mm))}],
  field[X][${typstContent(mmValue(model.qr_dx_mm))}],
  field[Y][${typstContent(mmValue(model.qr_dy_mm))}],
)
`
}

function buildSpecimenDictionary(context: CbpPreviewTypstContext) {
	const { model } = context
	const profile = {
		name: model.name || context.profileName,
		profile_name: model.profile_name || context.profileName,
		company: model.company || "",
		is_default: context.isDefault,
		code_only: context.effectiveCodeOnly,
	}
	const specimen = {
		page: {
			size: model.page_size || "A4",
			orientation: model.orientation || "portrait",
			margin_top_mm: num(model.margin_top_mm),
			margin_right_mm: num(model.margin_right_mm),
			margin_bottom_mm: num(model.margin_bottom_mm),
			margin_left_mm: num(model.margin_left_mm),
		},
		typography: {
			section_label: typstTypography(model, "section_label"),
			field_label: typstTypography(model, "field_label"),
			field_value: typstTypography(model, "field_value"),
			table_header: typstTypography(model, "table_header"),
			table_body: typstTypography(model, "table_body"),
		},
		table: {
			inset_top_pt: num(model.table_cell_inset_top_pt),
			inset_right_pt: num(model.table_cell_inset_right_pt),
			inset_bottom_pt: num(model.table_cell_inset_bottom_pt),
			inset_left_pt: num(model.table_cell_inset_left_pt),
			border_width_pt: num(model.table_border_stroke_width_pt),
			border_color: model.table_border_color || "#E2E8F0",
			header_fill: model.table_header_background_color || "#F1F5F9",
			striping_enabled: context.tableStriping,
			stripe_fill: model.table_stripe_color || "#F8FAFC",
			rows: specimenRows,
		},
		branding: {
			mode: model.branding_mode || "None",
			logo_source: model.branding_logo_source || "Company logo",
			logo_width_mm: num(model.branding_logo_width_mm),
			logo_offset_x_mm: num(model.branding_logo_offset_x_mm),
			logo_offset_y_mm: num(model.branding_logo_offset_y_mm),
			letterhead_source: context.letterheadSourceLabel,
			letterhead: context.letterheadLabel,
		},
		qr: {
			enabled: context.qrEnabled,
			size_mm: num(model.qr_code_size_mm),
			dx_mm: num(model.qr_dx_mm),
			dy_mm: num(model.qr_dy_mm),
		},
	}
	return `#let profile = ${toTypstValue(profile)}\n#let specimen = ${toTypstValue(specimen)}`
}

function typstTypography(model: CrispyBrandingProfileDoc, prefix: string) {
	return {
		family: String((model as any)[`${prefix}_font_family`] || "Arial"),
		size_pt: num((model as any)[`${prefix}_font_size_pt`]),
		style: String((model as any)[`${prefix}_font_style`] || "Normal"),
		weight: String((model as any)[`${prefix}_font_weight`] || "Regular"),
		color: String((model as any)[`${prefix}_font_color`] || "#000000"),
	}
}

function typstTextStyle(model: CrispyBrandingProfileDoc, prefix: string) {
	const typography = typstTypography(model, prefix)
	return `(font: ${toTypstValue(typography.family)}, size: ${typography.size_pt}pt, style: ${toTypstValue(typstFontStyle(typography.style))}, weight: ${toTypstValue(typstFontWeight(typography.weight))}, fill: rgb(${toTypstValue(typography.color)}))`
}

function typstFontStyle(value: string) {
	const style = String(value || "Normal").toLowerCase()
	return style === "italic" || style === "oblique" ? style : "normal"
}

function typstFontWeight(value: string) {
	return String(value || "Regular").toLowerCase()
}

function typstContent(value: any) {
	return `#(${toTypstValue(value)})`
}

function toTypstValue(value: any): string {
	if (value === null || value === undefined) return `""`
	if (Array.isArray(value)) {
		return `(${value.map((item) => `${toTypstValue(item)},`).join("")})`
	}
	if (typeof value === "object") {
		return `(${Object.entries(value)
			.map(([key, entryValue]) => `${key}: ${toTypstValue(entryValue)},`)
			.join("")})`
	}
	if (typeof value === "number" || typeof value === "boolean") return String(value)
	return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n")}"`
}

function assetFilename(path: string) {
	if (!path) return ""
	const clean = String(path).split("?")[0].split("#")[0]
	return decodeURIComponent(clean.split("/").filter(Boolean).at(-1) || "")
}

function mmValue(value: any) {
	return `${num(value)} mm`
}

function ptValue(value: any) {
	return `${num(value)} pt`
}

function titleCase(value: string) {
	return value ? value.charAt(0).toUpperCase() + value.slice(1) : ""
}
