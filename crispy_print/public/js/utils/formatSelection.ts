export type FormatLike = {
	name: string
	is_default?: number | boolean
}

export function pickFormatName(formats: FormatLike[], requested?: string | null): string | null {
	if (!Array.isArray(formats) || formats.length === 0) return null

	if (requested && formats.some((f) => f.name === requested)) {
		return requested
	}

	const defaultFormat = formats.find((f) => f.is_default === 1 || f.is_default === true)
	return defaultFormat?.name || formats[0].name || null
}

