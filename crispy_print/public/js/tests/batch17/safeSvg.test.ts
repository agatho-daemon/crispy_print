import { describe, expect, it } from "vitest";
import { sanitizeSvg } from "../../utils/safeSvg";

describe("sanitizeSvg", () => {
	it("removes executable SVG content while preserving the root SVG", () => {
		const out = sanitizeSvg(`
			<svg viewBox="0 0 10 10" onclick="alert(1)">
				<script>alert(1)</script>
				<a href="javascript:alert(2)"><rect width="10" height="10" /></a>
				<text style="fill: red; background: url(javascript:alert(3))">OK</text>
			</svg>
		`);

		expect(out).toContain("<svg");
		expect(out).toContain("OK");
		expect(out).not.toContain("<script");
		expect(out).not.toContain("onclick");
		expect(out).not.toContain("javascript:");
	});

	it("allowlists SVG markup and removes unsupported active surfaces", () => {
		const out = sanitizeSvg(`
			<svg viewBox="0 0 10 10" data-extra="drop">
				<a href="#safe"><rect width="10" height="10" style="fill: red" /></a>
				<image href="https://example.test/remote.png" width="1" height="1" />
				<animate attributeName="x" from="0" to="1" />
			</svg>
		`);

		expect(out).toContain("<rect");
		expect(out).not.toContain("<a ");
		expect(out).not.toContain("style=");
		expect(out).not.toContain("data-extra");
		expect(out).not.toContain("https://example.test");
		expect(out).not.toContain("<animate");
	});

	it("rejects non-SVG markup", () => {
		expect(sanitizeSvg("<div>not svg</div>")).toBe("");
	});

	it("preserves embedded SVG data hrefs on images and rejects other SVG href surfaces", () => {
		const styledSvg = `<svg viewBox="0 0 1 1"><style>.brand{fill:red}</style><rect class="brand" width="1" height="1"/></svg>`;
		const dataUri = `data:image/svg+xml;base64,${btoa(styledSvg)}`;
		const out = sanitizeSvg(`
			<svg viewBox="0 0 10 10">
				<image href="${dataUri}" width="1" height="1" />
				<use href="${dataUri}" />
			</svg>
		`);

		const imageHref = out.match(/<image[^>]+href="([^"]+)"/)?.[1] || "";
		expect(out).toContain("<use");
		expect(imageHref).toBe(dataUri);
		expect(atob(imageHref.split(",", 2)[1])).toContain("<style>");
		expect(out).not.toContain(`<use href="${dataUri}"`);
	});

	it("rejects oversized raster data URIs", () => {
		const hugeDataUri = `data:image/png;base64,${"a".repeat(256 * 1024 + 32)}`;
		const out = sanitizeSvg(`
			<svg viewBox="0 0 10 10">
				<image href="${hugeDataUri}" width="1" height="1" />
			</svg>
		`);

		expect(out).toContain("<svg");
		expect(out).not.toContain(hugeDataUri);
		expect(out).toContain("<image");
		expect(out).not.toContain("href=");
	});

	it("preserves overflow on Typst glyph symbols so descenders are not clipped", () => {
		const out = sanitizeSvg(`
			<svg viewBox="0 0 20 20">
				<g class="typst-text">
					<use href="#glyph-g" x="0" y="0" fill="#000" />
				</g>
				<defs>
					<symbol id="glyph-g" overflow="visible">
						<path d="M 0 0m 1 -1 l 2 -3 v 7 h -2 z" />
					</symbol>
				</defs>
			</svg>
		`);

		expect(out).toContain('<symbol id="glyph-g" overflow="visible">');
	});

	it("preserves Typst/Zebra barcode path output", () => {
		const out = sanitizeSvg(`
			<svg viewBox="0 0 32 32" width="32" height="32">
				<path fill="#000" fill-rule="evenodd" d="M 0 0h 1v 1h -1z M 2 0h 1v 1h -1z" transform="matrix(3.5 0 0 3.5 0 0)" />
			</svg>
		`);

		expect(out).toContain("<path");
		expect(out).toContain('fill-rule="evenodd"');
		expect(out).toContain("matrix(3.5 0 0 3.5 0 0)");
	});
});
