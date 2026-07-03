import html
import re

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
HTML_LINE_BREAK_PATTERN = re.compile(r"<\s*br\s*/?\s*>", re.IGNORECASE)
HTML_BLOCK_BREAK_PATTERN = re.compile(
	r"</?\s*(div|p|li|tr|table|section|article|header|footer|h[1-6])[^>]*>",
	re.IGNORECASE,
)
MULTIPLE_LINE_BREAKS_PATTERN = re.compile(r"\n{2,}")


def normalize_html_text(value: object) -> object:
	"""Return plain text for values that may contain literal or escaped HTML."""
	if not isinstance(value, str):
		return value

	text = html.unescape(value)
	text = HTML_LINE_BREAK_PATTERN.sub("\n", text)
	text = HTML_BLOCK_BREAK_PATTERN.sub("\n", text)
	text = HTML_TAG_PATTERN.sub("", text)
	text = html.unescape(text)
	text = MULTIPLE_LINE_BREAKS_PATTERN.sub("\n", text)
	return text.strip()
