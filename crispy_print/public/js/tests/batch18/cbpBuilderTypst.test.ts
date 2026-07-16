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
    expect(source).toContain('fill: rgb("#112233")');
    expect(source).toContain('fill: rgb("#445566")');
    expect(source).toContain('fill: rgb("#778899")');
    expect(source).not.toContain("Page Settings");
    expect(source).not.toContain("Typography Settings");
    expect(source).not.toContain("Table Settings");
    expect(source).not.toContain("#section[Report Theme]");
    expect(source).not.toContain("#section[Branding]");
    expect(source).not.toContain("#section[QR Code]");
  });
});
