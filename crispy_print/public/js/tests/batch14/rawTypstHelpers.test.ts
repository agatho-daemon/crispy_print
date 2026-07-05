import { describe, expect, it } from "vitest"
import {
	buildRawTypstHelperBlock,
	extractCrispyBlockIds,
	extractCrispyImageAssetFiles,
} from "../../typst/rawTypstHelpers"

describe("raw Typst helpers", () => {
	it("builds block helper entries only for referenced Crispy Typst Blocks", () => {
		const blocks = [
			{
				name: "document_title-v1.0",
				typst_code: "#text[Document Title]",
			},
			{
				name: "unused-v1.0",
				typst_code: "#text[Unused]",
			},
		]
		const source = buildRawTypstHelperBlock(blocks, '#crispy_block("document_title-v1.0")')

		expect(source).toContain('"document_title-v1.0": [')
		expect(source).toContain("#text[Document Title]")
		expect(source).not.toContain('"unused-v1.0": [')
		expect(source).not.toContain("#text[Unused]")
		expect(source).toContain("#let crispy_block")
		expect(source).toContain("#let crispy_image")
	})

	it("does not inline block bodies when raw code does not reference a block", () => {
		const source = buildRawTypstHelperBlock([
			{
				name: "document_title-v1.0",
				typst_code: "#text[Document Title]",
			},
		])

		expect(source).toContain("#let crispy_block")
		expect(source).not.toContain("#text[Document Title]")
	})

	it("extracts referenced Crispy Typst Block ids", () => {
		expect(
			Array.from(
				extractCrispyBlockIds(
					['#crispy_block("document_title-v1.0")', 'crispy_block("footer-v1.0")'].join("\n")
				)
			)
		).toEqual(["document_title-v1.0", "footer-v1.0"])
	})

	it("extracts only plain private image filenames", () => {
		const assets = extractCrispyImageAssetFiles(
			[
				'#crispy_image("logo.png")',
				'#crispy_image("../secret.png")',
				'#crispy_image("/private/files/logo.png")',
				'#crispy_image("https://example.com/logo.png")',
				'#crispy_image("nested/logo.png")',
			].join("\n"),
			"fdev.local"
		)

		expect(assets).toEqual(["/assets/fdev.local/private/files/logo.png"])
	})
})
