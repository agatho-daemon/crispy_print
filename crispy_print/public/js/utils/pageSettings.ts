// Shared page settings model and helpers

export interface PageSettings {
	pageSize: string
	orientation: string
	margins: {
		top: number
		bottom: number
		left: number
		right: number
	}
	fontFamily?: string
	fontSize?: number
	letterhead: string
	letterheadData?: any
	typography?: any
	language?: string
}

export const defaultPageSettings: PageSettings = {
	pageSize: "A4",
	orientation: "portrait",
	margins: { top: 25, bottom: 20, left: 20, right: 20 },
	fontFamily: "Arial",
	fontSize: 11,
	letterhead: "",
	typography: undefined,
	language: "en"
}

export function mergePageSettings(
	base: PageSettings = defaultPageSettings,
	overrides: Partial<PageSettings> = {}
): PageSettings {
	return {
		...base,
		...overrides,
		margins: { ...base.margins, ...(overrides.margins || {}) },
		typography: overrides.typography ?? base.typography,
	}
}
