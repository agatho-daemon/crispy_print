const FONT_WEIGHT_TO_NUMBER: Record<string, number> = {
	thin: 100,
	extralight: 200,
	"extra-light": 200,
	light: 300,
	normal: 400,
	regular: 400,
	medium: 500,
	semibold: 600,
	"semi-bold": 600,
	bold: 700,
	extrabold: 800,
	"extra-bold": 800,
	black: 900,
}

export function fontWeightToNumber(weight: unknown): number {
	const normalized = String(weight || "").trim().toLowerCase()
	return FONT_WEIGHT_TO_NUMBER[normalized] || 400
}
