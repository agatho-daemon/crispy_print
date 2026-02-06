import { describe, expect, it } from "vitest"

import { loadReportState, normalizeReportChartSvg } from "../../utils/reportState"

describe("reportState", () => {
	it("returns null on invalid JSON", () => {
		const key = "crispy-print:report:BadReport"
		window.sessionStorage.setItem(key, "{bad json")
		expect(loadReportState("BadReport")).toBeNull()
	})

	it("injects svg namespaces when missing", () => {
		const svg = '<svg width="10" height="10"><rect width="10" height="10"/></svg>'
		const normalized = normalizeReportChartSvg(svg)
		expect(normalized).toContain('xmlns="http://www.w3.org/2000/svg"')
		expect(normalized).toContain('xmlns:xlink="http://www.w3.org/1999/xlink"')
	})
})
