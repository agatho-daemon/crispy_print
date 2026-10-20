import { describe, expect, it } from "vitest"
import { dependencies } from "../../package.json"
import { PDFJS_MODULE_URL, PDFJS_WORKER_URL } from "../../utils/pdfJs"

describe("PDF.js loader URLs", () => {
	it("uses the pinned dependency version for both module and worker", () => {
		const version = dependencies["pdfjs-dist"]
		expect(PDFJS_MODULE_URL).toBe(`/assets/crispy_print/vendor/pdfjs/pdf-${version}.min.js`)
		expect(PDFJS_WORKER_URL).toBe(`/assets/crispy_print/vendor/pdfjs/pdf.worker-${version}.min.js`)
	})
})
