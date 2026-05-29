// utils/typstEscape.ts
// Centralized Typst string escaping. Used by any code that interpolates
// caller-controlled values into Typst source. The contract mirrors the
// backend `_quote_typst_string` helper (typst_doc.py).
//
// Order matters: backslashes MUST be doubled first; otherwise replacements
// for `"`, `\n`, etc. would be re-escaped.

/**
 * Escape a string for safe embedding inside Typst double-quoted strings.
 * The returned value does NOT include surrounding quotes.
 */
export function escapeTypstString(value: unknown): string {
	let s = String(value ?? "");
	s = s.replace(/\\/g, "\\\\");
	s = s.replace(/"/g, '\\"');
	s = s.replace(/\r/g, "\\r");
	s = s.replace(/\n/g, "\\n");
	s = s.replace(/\t/g, "\\t");
	// Strip remaining ASCII control chars (0x00–0x1F except already-escaped \r\n\t).
	// Using a function form so the regex itself remains readable.
	s = s.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "");
	return s;
}

/**
 * Convenience: return the value already wrapped in Typst double quotes.
 */
export function quoteTypstString(value: unknown): string {
	return `"${escapeTypstString(value)}"`;
}
