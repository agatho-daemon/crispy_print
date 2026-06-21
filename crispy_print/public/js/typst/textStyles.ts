import type {
	TableSettings,
	TypographySettings,
	TypographyStyle,
} from "../utils/presentation_settings"
import { fontWeightToNumber } from "../utils/typstTextStyle"
import { typstColor, typstLength, typstQuoted } from "./typstEscaping"

export type TypstNamedStyle = {
	name: string
	style: Partial<TypographyStyle>
	fallbackSizePt: number
}

export function typstTextStyle(
	style: Partial<TypographyStyle> = {},
	fallbackSizePt: number
) {
	const lines = ["("]
	lines.push(`  font: ${typstQuoted(style.fontFamily, "Inter 18pt")},`)
	lines.push(`  size: ${typstLength(style.fontSize, fallbackSizePt)},`)
	lines.push(`  style: ${typstQuoted(style.fontStyle, "normal")},`)
	lines.push(`  weight: ${fontWeightToNumber(style.fontWeight)},`)
	lines.push(`  fill: ${typstColor(style.color, "black")}`)
	lines.push(")")
	return lines.join("\n")
}

export function buildNamedTextStyleDef({
	name,
	style,
	fallbackSizePt,
}: TypstNamedStyle) {
	return `#let ${name} = ${typstTextStyle(style, fallbackSizePt)}`
}

export function buildTypographyStyleDefs(
	typography: TypographySettings,
	tableSettings: TableSettings,
	options: { typographyComment?: string; tableComment?: string } = {}
) {
	const lines: string[] = []
	if (options.typographyComment) {
		lines.push(options.typographyComment)
	}
	lines.push(
		buildNamedTextStyleDef({
			name: "fieldLabelStyle",
			style: typography.fieldLabel,
			fallbackSizePt: 8,
		})
	)
	lines.push("")
	lines.push(
		buildNamedTextStyleDef({
			name: "fieldValueStyle",
			style: typography.fieldValue,
			fallbackSizePt: 10,
		})
	)
	lines.push("")
	lines.push(
		buildNamedTextStyleDef({
			name: "sectionLabelStyle",
			style: typography.sectionLabel,
			fallbackSizePt: 14,
		})
	)
	lines.push("")

	if (options.tableComment) {
		lines.push(options.tableComment)
	}
	lines.push(
		buildNamedTextStyleDef({
			name: "tableHeaderStyle",
			style: tableSettings.typography.header,
			fallbackSizePt: 9,
		})
	)
	lines.push("")
	lines.push(
		buildNamedTextStyleDef({
			name: "tableBodyStyle",
			style: tableSettings.typography.body,
			fallbackSizePt: 9,
		})
	)
	lines.push("")
	return lines.join("\n")
}

export function buildTableStyleConstants(tableSettings: TableSettings) {
	const tableInset = tableSettings.inset
	const tableStrokeWidth = Number.isFinite(tableSettings.stroke.width)
		? tableSettings.stroke.width
		: 0
	const tableStrokeColor = typstColor(tableSettings.stroke.color, "black")
	const tableHeaderFill = typstColor(tableSettings.header.backgroundColor, "none")
	const tableStripeFill = typstColor(tableSettings.stripe.color, "none")
	const tableStripeEnabled = Boolean(tableSettings.stripe.enabled)

	return [
		`#let tableCellInset = (top: ${typstLength(
			tableInset.top,
			2
		)}, right: ${typstLength(tableInset.right, 2)}, bottom: ${typstLength(
			tableInset.bottom,
			2
		)}, left: ${typstLength(tableInset.left, 2)})`,
		`#let tableStroke = ${
			tableStrokeWidth > 0
				? `${typstLength(tableStrokeWidth, 0)} + ${tableStrokeColor}`
				: "none"
		}`,
		`#let tableHeaderFill = ${tableHeaderFill}`,
		`#let tableStripeFill = ${tableStripeFill}`,
		`#let tableStripeEnabled = ${tableStripeEnabled ? "true" : "false"}`,
	].join("\n")
}

