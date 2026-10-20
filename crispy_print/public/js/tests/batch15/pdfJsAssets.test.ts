import { describe, expect, it } from "vitest"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"

const read = (path: string) => readFileSync(fileURLToPath(new URL(path, import.meta.url)), "utf8")

describe("vendored PDF.js assets", () => {
	it("ships the module and worker version pinned by the package", () => {
		const expected = JSON.parse(read("../../package.json")).dependencies["pdfjs-dist"]
		const loader = read("../../utils/pdfJs.ts")
		const urls = [...loader.matchAll(/"(\/assets\/crispy_print\/vendor\/pdfjs\/[^\"]+)"/g)].map((match) => match[1])
		expect(urls).toHaveLength(2)
		for (const url of urls) {
			const filename = url.split("/").pop()
			const asset = read(`../../../vendor/pdfjs/${filename}`)
			expect(asset.match(/pdfjsVersion\s*=\s*([\d.]+)/)?.[1]).toBe(expected)
		}
	})
})
