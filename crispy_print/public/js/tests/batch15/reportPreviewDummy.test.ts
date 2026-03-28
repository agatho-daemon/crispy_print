import { describe, expect, it } from "vitest";
import {
	buildDummyReportPreviewData,
	getDummyReportTableColumns,
} from "../../utils/reportPreviewDummy";

describe("report preview dummy data", () => {
	it("uses unmistakably placeholder copy and values", () => {
		const out = buildDummyReportPreviewData({
			includeFilters: true,
			includeTotalRow: true,
			tableColumns: getDummyReportTableColumns(),
		});

		expect(out.title).toBe("Generic Preview");
		expect(out.subtitle).toBe("Placeholder data for style simulation only");
		expect(out.filters[0]).toEqual({ label: "Filter 1", value: "Value 1" });
		expect(out.report_summary[0]).toEqual({ label: "Summary 1", value: "Value 1" });

		expect(out.columns.map((col: any) => col.label).slice(0, 3)).toEqual([
			"Column 1",
			"Column 2",
			"Column 3",
		]);
		expect(out.columns[0].width).toBe("1fr");
		expect(out.rows[0].cells[0].value).toBe("Value 1-1");
		expect(out.rows[0].cells[1].value).toBe("Value 1-2");

		const totalRow = out.rows.find((row: any) => row.is_total_row === true);
		expect(totalRow).toBeTruthy();
		if (!totalRow) throw new Error("Expected total row in dummy report payload");
		expect(totalRow.cells[0].value).toBe("Total (Placeholder)");
		expect(typeof out.chart_svg).toBe("string");
		expect(out.chart_svg.length).toBeGreaterThan(0);
		expect(out.chart_svg).toContain("Placeholder Chart");
		expect(out.chart_svg).toContain("Sample Only");

		const raw = JSON.stringify(out);
		expect(raw).not.toContain("Wasaq");
		expect(raw).not.toContain("Accounts Payable");
		expect(raw).not.toContain("KWD");
	});

	it("keeps total_rows stable regardless of include_total_row toggle", () => {
		const withTotal = buildDummyReportPreviewData({
			includeFilters: true,
			includeTotalRow: true,
			tableColumns: getDummyReportTableColumns(),
		});
		const withoutTotal = buildDummyReportPreviewData({
			includeFilters: true,
			includeTotalRow: false,
			tableColumns: getDummyReportTableColumns(),
		});

		expect(withTotal.total_rows).toBe(4);
		expect(withoutTotal.total_rows).toBe(4);
		expect(withTotal.rows.length).toBe(withoutTotal.rows.length + 1);
	});

	it("can hide summary block data when includeSummary is false", () => {
		const withSummary = buildDummyReportPreviewData({
			includeSummary: true,
			tableColumns: getDummyReportTableColumns(),
		});
		const withoutSummary = buildDummyReportPreviewData({
			includeSummary: false,
			tableColumns: getDummyReportTableColumns(),
		});

		expect(withSummary.report_summary.length).toBeGreaterThan(0);
		expect(withoutSummary.report_summary).toEqual([]);
	});
});
