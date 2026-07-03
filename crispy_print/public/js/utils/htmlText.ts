const HTML_TAG_PATTERN = /<[^>]+>/g
const HTML_LINE_BREAK_PATTERN = /<\s*br\s*\/?\s*>/gi
const HTML_BLOCK_BREAK_PATTERN =
	/<\/?\s*(div|p|li|tr|table|section|article|header|footer|h[1-6])[^>]*>/gi
const MULTIPLE_LINE_BREAKS_PATTERN = /\n{2,}/g

const HTML_ENTITIES: Record<string, string> = {
	amp: "&",
	lt: "<",
	gt: ">",
	quot: '"',
	apos: "'",
	"#39": "'",
	"#x27": "'",
	"#x2F": "/",
	nbsp: " ",
}

export function decodeHtmlEntities(value: unknown): string {
	return String(value ?? "").replace(/&(#x?[0-9a-f]+|[a-z][a-z0-9]+);/gi, (match, entity) => {
		const key = String(entity)
		const lowerKey = key.toLowerCase()
		if (lowerKey.startsWith("#x")) {
			const codepoint = Number.parseInt(lowerKey.slice(2), 16)
			return Number.isFinite(codepoint) ? String.fromCodePoint(codepoint) : match
		}
		if (lowerKey.startsWith("#")) {
			const codepoint = Number.parseInt(lowerKey.slice(1), 10)
			return Number.isFinite(codepoint) ? String.fromCodePoint(codepoint) : match
		}
		return HTML_ENTITIES[lowerKey] ?? match
	})
}

export function normalizeHtmlText(value: unknown): string {
	let text = decodeHtmlEntities(value)
	text = text.replace(HTML_LINE_BREAK_PATTERN, "\n")
	text = text.replace(HTML_BLOCK_BREAK_PATTERN, "\n")
	text = text.replace(HTML_TAG_PATTERN, "")
	text = decodeHtmlEntities(text)
	text = text.replace(MULTIPLE_LINE_BREAKS_PATTERN, "\n")
	return text.trim()
}
