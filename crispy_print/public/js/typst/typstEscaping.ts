import { escapeTypstString, quoteTypstString } from "../utils/typstEscape"

const HEX_COLOR_RE = /^#[0-9a-fA-F]{3,8}$/
const TYPST_LENGTH_RE = /^-?\d+(?:\.\d+)?(?:pt|mm|cm|in|em|%)?$/

export function typstString(value: unknown, fallback = "") {
	return escapeTypstString(value ?? fallback)
}

export function typstQuoted(value: unknown, fallback = "") {
	return quoteTypstString(value ?? fallback)
}

export function typstColor(value: unknown, fallback = "none") {
	const raw = String(value || "").trim()
	if (!raw) return fallback
	if (HEX_COLOR_RE.test(raw)) {
		return `rgb("${raw.substring(1)}")`
	}
	return fallback
}

export function typstLength(value: unknown, fallback: number | string) {
	const raw = String(value ?? "").trim()
	if (TYPST_LENGTH_RE.test(raw)) {
		return /[a-z%]+$/i.test(raw) ? raw : `${raw}pt`
	}
	const fallbackRaw = String(fallback).trim()
	if (TYPST_LENGTH_RE.test(fallbackRaw)) {
		return /[a-z%]+$/i.test(fallbackRaw) ? fallbackRaw : `${fallbackRaw}pt`
	}
	return "0pt"
}
