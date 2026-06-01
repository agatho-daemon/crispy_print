const DANGEROUS_SVG_ELEMENTS = new Set([
	"script",
	"foreignobject",
	"iframe",
	"object",
	"embed",
	"link",
	"meta",
	"style",
	"animate",
	"animatemotion",
	"animatetransform",
	"set",
]);
const MAX_DATA_URI_LENGTH = 256 * 1024;

const ALLOWED_SVG_ELEMENTS = new Set([
	"svg",
	"g",
	"path",
	"rect",
	"circle",
	"ellipse",
	"line",
	"polyline",
	"polygon",
	"text",
	"tspan",
	"defs",
	"clippath",
	"mask",
	"pattern",
	"lineargradient",
	"radialgradient",
	"stop",
	"image",
	"use",
	"symbol",
	"marker",
	"title",
	"desc",
]);

const ALLOWED_SVG_ATTRIBUTES = new Set([
	"xmlns",
	"xmlns:xlink",
	"version",
	"viewbox",
	"id",
	"class",
	"x",
	"y",
	"x1",
	"y1",
	"x2",
	"y2",
	"cx",
	"cy",
	"r",
	"rx",
	"ry",
	"width",
	"height",
	"d",
	"points",
	"transform",
	"fill",
	"fill-opacity",
	"fill-rule",
	"stroke",
	"stroke-width",
	"stroke-linecap",
	"stroke-linejoin",
	"stroke-miterlimit",
	"stroke-dasharray",
	"stroke-dashoffset",
	"stroke-opacity",
	"opacity",
	"overflow",
	"font-family",
	"font-size",
	"font-weight",
	"font-style",
	"text-anchor",
	"dominant-baseline",
	"dx",
	"dy",
	"offset",
	"stop-color",
	"stop-opacity",
	"gradientunits",
	"gradienttransform",
	"patternunits",
	"patterncontentunits",
	"clip-path",
	"clip-rule",
	"mask",
	"marker-start",
	"marker-mid",
	"marker-end",
	"preserveaspectratio",
	"href",
	"xlink:href",
]);

function isUrlAttribute(name: string): boolean {
	const attrName = name.toLowerCase();
	return attrName === "href" || attrName.endsWith(":href");
}

function sanitizeUrl(value: string, element: Element): string | null {
	const trimmed = value.trim();
	const normalized = trimmed.replace(/[\u0000-\u001f\u007f\s]+/g, "").toLowerCase();
	if (normalized.length > MAX_DATA_URI_LENGTH) {
		return null;
	}
	if (normalized.startsWith("#")) return trimmed;
	if (/^data:image\/(?:png|jpeg|jpg|gif|webp);base64,[a-z0-9+/=]+$/i.test(normalized)) {
		return normalized;
	}
	if (
		element.tagName.toLowerCase() === "image" &&
		/^data:image\/svg\+xml;base64,[a-z0-9+/=]+$/i.test(normalized)
	) {
		// SVGs referenced through <image> are rendered as image resources, not as
		// inline DOM. Preserve them so branded SVGs keep their internal styles,
		// gradients, and symbols. Active href surfaces such as <use> still reject
		// SVG data URIs because this branch is image-only.
		return trimmed;
	}
	return null;
}

function unwrapElement(element: Element) {
	const parent = element.parentNode;
	if (!parent) return;
	while (element.firstChild) {
		parent.insertBefore(element.firstChild, element);
	}
	element.remove();
}

export function sanitizeSvg(svg: string): string {
	const source = String(svg || "").trim();
	if (!source) return "";

	const parser = new DOMParser();
	const doc = parser.parseFromString(source, "image/svg+xml");
	if (doc.querySelector("parsererror")) return "";

	const root = doc.documentElement;
	if (!root || root.tagName.toLowerCase() !== "svg") return "";

	const showElement = doc.defaultView?.NodeFilter?.SHOW_ELEMENT ?? 1;
	const walker = doc.createTreeWalker(root, showElement);
	const dangerous: Element[] = [];
	const unsupported: Element[] = [];

	let current = walker.currentNode as Element | null;
	while (current) {
		const tagName = current.tagName.toLowerCase();
		if (DANGEROUS_SVG_ELEMENTS.has(tagName)) {
			dangerous.push(current);
		} else if (!ALLOWED_SVG_ELEMENTS.has(tagName)) {
			unsupported.push(current);
		} else {
			for (const attr of Array.from(current.attributes)) {
				const attrName = attr.name.toLowerCase();
				if (
					attrName.startsWith("on") ||
					!ALLOWED_SVG_ATTRIBUTES.has(attrName)
				) {
					current.removeAttribute(attr.name);
					continue;
				}
				if (isUrlAttribute(attr.name)) {
					const safeUrl = sanitizeUrl(attr.value, current);
					if (!safeUrl) {
						current.removeAttribute(attr.name);
					} else if (safeUrl !== attr.value) {
						current.setAttribute(attr.name, safeUrl);
					}
				}
			}
		}
		current = walker.nextNode() as Element | null;
	}

	for (const node of dangerous) {
		node.remove();
	}
	for (const node of unsupported.reverse()) {
		unwrapElement(node);
	}

	return new XMLSerializer().serializeToString(root);
}
