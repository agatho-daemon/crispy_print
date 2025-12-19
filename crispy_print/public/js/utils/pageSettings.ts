// Shared page settings model and helpers

export interface TypographyStyle {
	fontFamily: string
	fontSize: string
	fontStyle: string
	fontWeight: string
	color: string
}

export interface PageSettings {
	pageSize: string
	orientation: string
	margins: {
		top: number
		bottom: number
		left: number
		right: number
	}
	letterhead?: string
	letterheadData?: any
	language: string

	typography?: {
		fieldLabel: TypographyStyle
		fieldValue: TypographyStyle
		sectionLabel: TypographyStyle
	}
}

export const defaultPageSettings: PageSettings = {
	pageSize: "A4",
	orientation: "portrait",
	margins: { top: 25, bottom: 20, left: 20, right: 20 },
	letterhead: "",
	typography: undefined,
	language: "en"
}

export function mergePageSettings(
	base: PageSettings = defaultPageSettings,
	overrides: Partial<PageSettings> = {}
): PageSettings {
	// Backward-compatible: older saved settings may still include `fontFamily` / `fontSize`.
	// Drop them entirely so typography + Typst preamble/doc_header become the single source of truth.
	const { fontFamily: _ignoredFontFamily, fontSize: _ignoredFontSize, ...safeOverrides } =
		overrides as any
	return {
		...base,
		...safeOverrides,
		margins: { ...base.margins, ...(safeOverrides.margins || {}) },
		typography: safeOverrides.typography ?? base.typography,
	}
}
