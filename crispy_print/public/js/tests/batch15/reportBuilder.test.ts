import { describe, expect, it } from "vitest";
import { defaultTableSettings } from "../../utils/presentation_settings";
import {
  buildReportTypstFromConfig,
  computeReportBasicSignature,
  extractReportBasicSignature,
  getDefaultReportBuilderConfig,
  isBasicManagedTypst,
  normalizeReportBuilderConfig,
} from "../../utils/reportBuilder";

describe("reportBuilder utils", () => {
  it("builds signed basic template", () => {
    const config = getDefaultReportBuilderConfig("Grid");
    const typst = buildReportTypstFromConfig(config);

    expect(typst).toContain("CRISPY_REPORT_BASIC_SIGNATURE:");
    expect(typst).toContain("CRISPY_REPORT_BASIC_GENERATOR:4");
    expect(typst).toContain(
      '#import "@local/crispy-charts:0.1.1": crispy-chart',
    );
    expect(typst).toContain("#crispy-chart(data.chart_spec");
    expect(typst).toContain(
      'data.chart_spec.engine == "frappe_svg" and "chart_svg" in data',
    );
    expect(typst).toContain("data.columns");
    expect(typst).toContain("cp-columns.map(cp_column_width)");
    expect(typst).toContain("table.header(");
    expect(typst).toContain("repeat: true");
    expect(typst).toContain(
      'let row-breakable = row.role == "detail" or row.role == "auxiliary" or row.role == "spacer"',
    );
    expect(typst).toContain(
      "table.cell(colspan: data.columns.len(), fill: row-fill, breakable: false)",
    );
    expect(typst).toContain("block(sticky: keep-with-next)");
    expect(typst).not.toContain("eval(col.width)");
    expect(typst).toContain("Total Records: #data.total_rows");
  });

  it("hides total records footer when show_footer_total is disabled", () => {
    const config = {
      ...getDefaultReportBuilderConfig("Grid"),
      include_total_row: false,
      show_footer_total: false,
    };
    const typst = buildReportTypstFromConfig(config);

    expect(typst).toContain(".filter(row => row.is_total_row != true)");
    expect(typst).not.toContain("Total Records: #data.total_rows");
  });

  it("detects managed template and invalidates tampering", () => {
    const config = getDefaultReportBuilderConfig("Grid");
    const typst = buildReportTypstFromConfig(config);
    const signature = extractReportBasicSignature(typst);

    expect(isBasicManagedTypst(typst, signature)).toBe(true);

    const tampered = typst.replace("Total Records", "Rows Count");
    expect(isBasicManagedTypst(tampered, signature)).toBe(false);
  });

  it("normalizes report builder config safely", () => {
    const config = normalizeReportBuilderConfig(
      {
        mode: "advanced",
        preset: "summary",
        font_size_pt: "11",
        column_align_strategy: "center",
        chart_representation: "Horizontal Bar",
      },
      "Grid",
    );

    expect(config.mode).toBe("advanced");
    expect(config.preset).toBe("summary");
    expect(config.font_size_pt).toBe(11);
    expect(config.column_align_strategy).toBe("center");
    expect(config.chart_representation).toBe("horizontal_bar");
    expect(
      normalizeReportBuilderConfig({ chart_representation: "pie" })
        .chart_representation,
    ).toBe("auto");
    expect(typeof computeReportBasicSignature("x")).toBe("string");
  });

  it("uses table settings as authoritative style source when provided", () => {
    const config = getDefaultReportBuilderConfig("Grid");
    const typst = buildReportTypstFromConfig(config, {
      tableSettings: {
        ...defaultTableSettings,
        inset: { top: 4, right: 5, bottom: 6, left: 7 },
        stroke: { width: 0.8, color: "#111111" },
        header: { backgroundColor: "#abcdef" },
        stripe: { enabled: true, color: "#fedcba" },
        typography: {
          header: {
            fontFamily: "Inter",
            fontSize: "11pt",
            fontStyle: "normal",
            fontWeight: "semibold",
            color: "#123456",
          },
          body: {
            fontFamily: "Inter",
            fontSize: "10pt",
            fontStyle: "italic",
            fontWeight: "regular",
            color: "#654321",
          },
        },
      },
    });

    expect(typst).toContain('if y == 0 { rgb("abcdef") }');
    expect(typst).toContain('else if calc.even(y) { rgb("fedcba") }');
    expect(typst).toContain(
      "inset: (top: 4pt, right: 5pt, bottom: 6pt, left: 7pt)",
    );
    expect(typst).toContain('fill: rgb("123456")');
    expect(typst).toContain('fill: rgb("654321")');
    expect(typst).toContain('style: "italic"');
  });

  it("omits summary block when show_summary is disabled", () => {
    const config = {
      ...getDefaultReportBuilderConfig("Grid"),
      show_summary: false,
    };
    const typst = buildReportTypstFromConfig(config);

    expect(typst).not.toContain("data.report_summary");
  });

  it("adds indentation support for first table column in row rendering", () => {
    const config = getDefaultReportBuilderConfig("Tree");
    const typst = buildReportTypstFromConfig(config);

    expect(typst).toContain("cp-row-cells(row).enumerate().map(cell_entry => {");
    expect(typst).toContain(
      'if idx == 0 and "indent" in row and row.indent != none and row.indent > 0 {',
    );
    expect(typst).toContain("box(inset: (left: row.indent * 10pt))[#content]");
  });

  it("emits an RTL bilingual accounting contract for Arabic", () => {
    const typst = buildReportTypstFromConfig(
      getDefaultReportBuilderConfig("Tree"),
      { language: "ar-KW" },
    );

    expect(typst).toContain('lang: "ar", region: "KW", dir: rtl');
    expect(typst).toContain('"Noto Naskh Arabic", "Noto Sans Arabic", "Inter"');
    expect(typst).toContain(
      "if cp-columns.at(x).is_numeric { left + horizon } else { right + horizon }",
    );
    expect(typst).toContain(
      'let cell-dir = if cell.is_numeric or ("is_ltr" in cell and cell.is_ltr) { ltr } else { rtl }',
    );
    expect(typst).toContain("text(dir: cell-dir");
  });
});
