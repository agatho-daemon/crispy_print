// utils/typstFieldExtractor.ts
// Extract fields referenced in raw Typst code for minimal doc payloads.

export function extractUsedFieldsFromTypstSource(source: string): Set<string> {
	const usedFields = new Set<string>()
	if (!source || typeof source !== "string") return usedFields

	const addField = (field: string) => {
		const cleaned = field.trim()
		if (cleaned) {
			usedFields.add(cleaned)
		}
	}

	// Optional hint format: // fields: name, customer, items.item_code
	const hintRegex = /^\s*\/\/\s*fields?\s*:\s*(.+)$/gim
	let match: RegExpExecArray | null
	while ((match = hintRegex.exec(source))) {
		const rawList = match[1] || ""
		rawList
			.split(/[,;]+/)
			.map((entry) => entry.trim())
			.filter(Boolean)
			.forEach(addField)
	}

	// doc.field
	const dotRegex = /\bdoc\.([A-Za-z_][A-Za-z0-9_]*)/g
	while ((match = dotRegex.exec(source))) {
		addField(match[1])
	}

	// doc["field"] or doc['field']
	const bracketRegex = /\bdoc\[\s*["']([^"']+)["']\s*\]/g
	while ((match = bracketRegex.exec(source))) {
		addField(match[1])
	}

	return usedFields
}
