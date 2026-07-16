import { describe, expect, it } from "vitest";

import { cbpTypographyModel } from "../../pages/cbpTypographyAdapter";

describe("CBP typography adapter", () => {
  it("stores DocType select labels while exposing Typst tokens", () => {
    const model = {
      section_label_font_family: "Inter",
      section_label_font_size_pt: 14,
      section_label_font_style: "normal",
      section_label_font_weight: "semibold",
      section_label_font_color: "#123456",
    } as any;
    const typography = cbpTypographyModel(model, "section_label");

    expect(typography.value.fontStyle).toBe("normal");
    expect(typography.value.fontWeight).toBe("semibold");

    typography.value = {
      ...typography.value,
      fontStyle: "italic",
      fontWeight: "bold",
    };

    expect(model.section_label_font_style).toBe("italic");
    expect(model.section_label_font_weight).toBe("bold");
  });
});
