// Shared page settings model and helpers

import { deepClone } from "./json"

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

export interface TableTypographySettings {
	header: TypographyStyle
	body: TypographyStyle
}

export interface QrSettings {
	dx: number
	dy: number
	size: number
	fields: string[]
	enabled?: boolean
}

export interface LogoSettings {
	company: string
	image: string
	size: number
	dx: number
	dy: number
}

export interface TableSettings {
	inset: {
		top: number
		right: number
		bottom: number
		left: number
	}
	stroke: {
		width: number
		color: string
	}
	header: {
		backgroundColor: string
	}
	stripe: {
		enabled: boolean
		color: string
	}
	typography: TableTypographySettings
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

export const defaultTableTypography: TableTypographySettings = {
	header: {
		fontFamily: "Inter 18pt",
		fontSize: "9pt",
		fontStyle: "normal",
		fontWeight: "semibold",
		color: "#0f172a",
	},
	body: {
		fontFamily: "Inter 18pt",
		fontSize: "9pt",
		fontStyle: "normal",
		fontWeight: "regular",
		color: "#0f172a",
	},
}

export const defaultTableSettings: TableSettings = {
	inset: { top: 2, right: 2, bottom: 2, left: 2 },
	stroke: { width: 0.5, color: "#e2e8f0" },
	header: { backgroundColor: "#f1f5f9" },
	stripe: { enabled: false, color: "#f8fafc" },
	typography: defaultTableTypography,
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
	table?: TableSettings
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
	table: undefined,
	language: "en",
	qr: { dx: 0, dy: 0, size: 15, fields: [], enabled: false },
}

export function ensureTypography(pageSettings: PageSettings): TypographySettings {
	if (!pageSettings.typography) {
		pageSettings.typography = deepClone(defaultTypography)
	}
	return pageSettings.typography
}

export function ensureTableSettings(pageSettings: PageSettings): TableSettings {
	if (!pageSettings.table) {
		pageSettings.table = deepClone(defaultTableSettings)
		return pageSettings.table
	}
	pageSettings.table.inset = {
		...defaultTableSettings.inset,
		...(pageSettings.table.inset || {}),
	}
	pageSettings.table.stroke = {
		...defaultTableSettings.stroke,
		...(pageSettings.table.stroke || {}),
	}
	pageSettings.table.header = {
		...defaultTableSettings.header,
		...(pageSettings.table.header || {}),
	}
	pageSettings.table.stripe = {
		...defaultTableSettings.stripe,
		...(pageSettings.table.stripe || {}),
	}
	pageSettings.table.typography = {
		header: {
			...defaultTableTypography.header,
			...(pageSettings.table.typography?.header || {}),
		},
		body: {
			...defaultTableTypography.body,
			...(pageSettings.table.typography?.body || {}),
		},
	}
	return pageSettings.table
}

export function ensureQrSettings(pageSettings: PageSettings): QrSettings {
	if (!pageSettings.qr) {
		pageSettings.qr = { dx: 0, dy: 0, size: 15, fields: [], enabled: false }
	}
	if (!Array.isArray(pageSettings.qr.fields)) {
		pageSettings.qr.fields = []
	}
	if (typeof pageSettings.qr.enabled !== "boolean") {
		pageSettings.qr.enabled = false
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
		table: {
			...(base.table || defaultTableSettings),
			...((safeOverrides as PageSettings).table || {}),
			inset: {
				...(base.table?.inset || defaultTableSettings.inset),
				...((safeOverrides as PageSettings).table?.inset || {}),
			},
			stroke: {
				...(base.table?.stroke || defaultTableSettings.stroke),
				...((safeOverrides as PageSettings).table?.stroke || {}),
			},
			header: {
				...(base.table?.header || defaultTableSettings.header),
				...((safeOverrides as PageSettings).table?.header || {}),
			},
			stripe: {
				...(base.table?.stripe || defaultTableSettings.stripe),
				...((safeOverrides as PageSettings).table?.stripe || {}),
			},
			typography: {
				header: {
					...(base.table?.typography?.header || defaultTableTypography.header),
					...((safeOverrides as PageSettings).table?.typography?.header || {}),
				},
				body: {
					...(base.table?.typography?.body || defaultTableTypography.body),
					...((safeOverrides as PageSettings).table?.typography?.body || {}),
				},
			},
		},
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
