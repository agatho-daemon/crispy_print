import type { DocField } from "./layout"

export interface RawTypstInsertField extends DocField {
	name?: string
	raw_typst_field?: string
	crispy_typst_block?: string
	crispy_typst_block_name?: string
	crispy_typst_block_code?: string
	spacer_value?: string
	divider_length?: string
	divider_stroke?: string
	divider_color?: string
	insert_kind?: string
}

function typstLength(value: unknown, fallback: string): string {
	const raw = String(value || "").trim()
	return raw || fallback
}

function typstColor(value: unknown, fallback: string): string {
	const raw = String(value || "").trim()
	if (!raw) return fallback
	if (/^#[0-9a-fA-F]{3,8}$/.test(raw)) {
		return `rgb("${raw.slice(1)}")`
	}
	return raw
}

export function getRawTypstInsertText(field: RawTypstInsertField): string {
	const fieldname = String(field?.fieldname || "").trim()
	const fieldtype = String(field?.fieldtype || "").trim()

	if (fieldtype === "Crispy Typst Block" || fieldname === "_crispy_typst_block") {
		return `#crispy_block("")`
	}

	if (fieldtype === "Crispy Image" || fieldname === "_crispy_image") {
		return `#crispy_image("")`
	}

	if (fieldtype === "Typst" || fieldname === "_typst_snippet") {
		return String(field.raw_typst_field || "").trim()
	}

	if (fieldtype === "Empty" || fieldname === "empty") {
		return `[]`
	}

	if (fieldtype === "Spacer" || fieldname === "spacer") {
		return `#v(${typstLength(field.spacer_value, "1em")})`
	}

	if (fieldtype === "Divider" || fieldname === "divider") {
		const length = typstLength(field.divider_length, "100%")
		const stroke = typstLength(field.divider_stroke, "0.5pt")
		const color = typstColor(field.divider_color, "gray")
		return `#line(length: ${length}, stroke: ${stroke} + ${color})`
	}

	return fieldname ? `#doc.${fieldname}` : ""
}
