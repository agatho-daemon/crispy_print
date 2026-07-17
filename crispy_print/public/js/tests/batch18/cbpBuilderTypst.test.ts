import { describe, expect, it } from "vitest";

import { createFallbackModel } from "../../pages/cbpBuilderSupport";
import { buildVisualPreviewTypst } from "../../pages/cbpBuilderTypst";

describe("Branding Profile visual specimen", () => {
  it("demonstrates settings through a natural document instead of settings summaries", () => {
    const model = createFallbackModel("Default Branding Profile");
    model.company = "Example Company";
    model.report_chart_palette = "#112233, #445566, #778899";

    const source = buildVisualPreviewTypst({
      model,
      profileName: "Default Branding Profile",
      isDefault: true,
      effectiveCodeOnly: false,
      tableStriping: false,
      qrEnabled: false,
      usesLogo: false,
      logoImage: "",
      letterheadImage: "",
      letterheadLabel: "",
      letterheadSourceLabel: "",
    });

    expect(source).toContain('#field[Company][#("Example Company")]');
    expect(source).toContain("Financial Statement Title");
    expect(source).toContain("#section[Account Summary]");
    expect(source).toContain("[Account]");
    expect(source).toContain("Cash and Bank");
    expect(source).toContain("Warning · Provisional figures");
    expect(source).toContain("Comparative figures are unaudited");
    expect(source).toContain("#section[Performance Overview]");
    expect(source).toContain(
      '#import "@local/crispy-charts:0.1.1": crispy-chart',
    );
    expect(source).toContain("#crispy-chart(");
    expect(source).toContain('palette: ("#112233", "#445566", "#778899")');
    expect(source).not.toContain("Page Settings");
    expect(source).not.toContain("Typography Settings");
    expect(source).not.toContain("Table Settings");
    expect(source).not.toContain("#section[Report Theme]");
    expect(source).not.toContain("#section[Branding]");
    expect(source).not.toContain("#section[QR Code]");
  });

  it("uses an installed font fallback without changing the saved profile choice", () => {
    const model = createFallbackModel("Default Branding Profile");
    model.field_value_font_family = "Arial";
    model.report_title_font_family = "Arial";

    const source = buildVisualPreviewTypst({
      model,
      installedFonts: ["Inter", "Noto Sans Arabic"],
      profileName: "Default Branding Profile",
      isDefault: true,
      effectiveCodeOnly: false,
      tableStriping: false,
      qrEnabled: false,
      usesLogo: false,
      logoImage: "",
      letterheadImage: "",
      letterheadLabel: "",
      letterheadSourceLabel: "",
    });

    expect(source).toContain('#set text(font: "Inter"');
    expect(source).not.toContain('font: "Arial"');
    expect(model.report_title_font_family).toBe("Arial");
  });

  it("passes disabled chart grid controls through as false", () => {
    const model = createFallbackModel("Default Branding Profile");
    model.report_chart_horizontal_grid = 0;
    model.report_chart_vertical_grid = 0;
    model.report_chart_minor_grid = 0;

    const source = buildVisualPreviewTypst({
      model,
      profileName: "Default Branding Profile",
      isDefault: true,
      effectiveCodeOnly: false,
      tableStriping: false,
      qrEnabled: false,
      usesLogo: false,
      logoImage: "",
      letterheadImage: "",
      letterheadLabel: "",
      letterheadSourceLabel: "",
    });

    expect(source).toContain("horizontal_grid: false");
    expect(source).toContain("vertical_grid: false");
    expect(source).toContain("minor_grid: false");
  });

  it.each([
    "line",
    "bar",
    "grouped_bar",
    "mixed",
    "horizontal_bar",
    "percentage_stacked",
    "waterfall",
  ] as const)("renders the %s chart specimen", (previewChartKind) => {
    const model = createFallbackModel("Default Branding Profile");
    const source = buildVisualPreviewTypst({
      model,
      profileName: "Default Branding Profile",
      isDefault: true,
      effectiveCodeOnly: false,
      tableStriping: false,
      qrEnabled: false,
      usesLogo: false,
      logoImage: "",
      letterheadImage: "",
      letterheadLabel: "",
      letterheadSourceLabel: "",
      previewChartKind,
    });

    expect(source).toContain(`kind: "${previewChartKind}"`);
  });
});
