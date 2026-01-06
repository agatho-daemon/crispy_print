// Shared page settings model and helpers

export interface TypographyStyle {
	fontFamily: string
	fontSize: string
	fontStyle: string
	fontWeight: string
	color: string
}

export interface TypographySettings {
	fieldLabel: TypographyStyle
	fieldValue: TypographyStyle
	sectionLabel: TypographyStyle
}

export interface QrSettings {
	dx: number
	dy: number
	size: number
	fields: string[]
}

export interface LogoSettings {
	company: string
	image: string
	size: number
	dx: number
	dy: number
}

export const defaultTypography: TypographySettings = {
	fieldLabel: {
		fontFamily: "Inter 18pt",
		fontSize: "8pt",
		fontStyle: "normal",
		fontWeight: "semibold",
		color: "#64748b",
	},
	fieldValue: {
		fontFamily: "Inter 18pt",
		fontSize: "10pt",
		fontStyle: "normal",
		fontWeight: "regular",
		color: "#0f172a",
	},
	sectionLabel: {
		fontFamily: "Inter 18pt",
		fontSize: "14pt",
		fontStyle: "normal",
		fontWeight: "bold",
		color: "#1e293b",
	},
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
	brandingMode?: "letterhead" | "logo" | "none"
	logo?: LogoSettings
	language: string

	typography?: TypographySettings
	qr?: QrSettings
}

export const defaultPageSettings: PageSettings = {
	pageSize: "A4",
	orientation: "portrait",
	margins: { top: 25, bottom: 20, left: 20, right: 20 },
	letterhead: "",
	brandingMode: "letterhead",
	logo: { company: "", image: "", size: 25, dx: 0, dy: 0 },
	typography: undefined,
	language: "en",
	qr: { dx: 0, dy: 0, size: 15, fields: [] },
}

export function ensureTypography(pageSettings: PageSettings): TypographySettings {
	if (!pageSettings.typography) {
		pageSettings.typography = JSON.parse(JSON.stringify(defaultTypography))
	}
	return pageSettings.typography
}

export function ensureQrSettings(pageSettings: PageSettings): QrSettings {
	if (!pageSettings.qr) {
		pageSettings.qr = { dx: 0, dy: 0, size: 15, fields: [] }
	}
	if (!Array.isArray(pageSettings.qr.fields)) {
		pageSettings.qr.fields = []
	}
	return pageSettings.qr
}

export function ensureLogoSettings(pageSettings: PageSettings): LogoSettings {
	if (!pageSettings.logo) {
		pageSettings.logo = { company: "", image: "", size: 25, dx: 0, dy: 0 }
	}
	pageSettings.logo.company = pageSettings.logo.company || ""
	pageSettings.logo.image = pageSettings.logo.image || ""
	pageSettings.logo.size = Number.isFinite(pageSettings.logo.size) ? pageSettings.logo.size : 25
	pageSettings.logo.dx = Number.isFinite(pageSettings.logo.dx) ? pageSettings.logo.dx : 0
	pageSettings.logo.dy = Number.isFinite(pageSettings.logo.dy) ? pageSettings.logo.dy : 0
	return pageSettings.logo
}

export function mergePageSettings(
	base: PageSettings = defaultPageSettings,
	overrides: Partial<PageSettings> = {}
): PageSettings {
	// Backward-compatible: older saved settings may still include `fontFamily` / `fontSize`.
	// Drop them entirely so typography + Typst preamble/doc_header become the single source of truth.
	const {
		fontFamily: _ignoredFontFamily,
		fontSize: _ignoredFontSize,
		...safeOverrides
	} = overrides as any
	return {
		...base,
		...safeOverrides,
		margins: { ...base.margins, ...(safeOverrides.margins || {}) },
		typography: safeOverrides.typography ?? base.typography,
		qr: {
			...(base.qr || { dx: 0, dy: 0, size: 15, fields: [] }),
			...((safeOverrides as PageSettings).qr || {}),
		},
		logo: {
			...(base.logo || { company: "", image: "", size: 25, dx: 0, dy: 0 }),
			...((safeOverrides as PageSettings).logo || {}),
		},
	}
}
