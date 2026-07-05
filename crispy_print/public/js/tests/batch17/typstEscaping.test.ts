import { describe, expect, it } from "vitest";
import {
  typstColor,
  typstLength,
  typstQuoted,
} from "../../typst/typstEscaping";
import {
  buildTypographyStyleDefs,
  typstTextStyle,
} from "../../typst/textStyles";
import {
  defaultTableSettings,
  defaultTypography,
} from "../../utils/presentation_settings";
import { fontWeightToNumber } from "../../utils/typstTextStyle";

describe("typst escaping helpers", () => {
  it("escapes strings before embedding in Typst literals", () => {
    expect(typstQuoted('Inter"; #panic() //')).toBe('"Inter\\"; #panic() //"');
    expect(typstQuoted("Line\nBreak\\")).toBe('"Line\\nBreak\\\\"');
  });

  it("only accepts strict hex colors", () => {
    expect(typstColor("#abc")).toBe('rgb("abc")');
    expect(typstColor("#aabbccdd")).toBe('rgb("aabbccdd")');
    expect(typstColor('#fff"); #panic()')).toBe("none");
    expect(typstColor("red")).toBe("none");
  });

  it("normalizes safe Typst lengths and rejects injected values", () => {
    expect(typstLength("12", 9)).toBe("12pt");
    expect(typstLength("10mm", 9)).toBe("10mm");
    expect(typstLength("10pt); #panic() //", 9)).toBe("9pt");
  });

  it("maps font weights consistently for Typst renderers", () => {
    expect(fontWeightToNumber("thin")).toBe(100);
    expect(fontWeightToNumber("extra-bold")).toBe(800);
    expect(fontWeightToNumber("semibold")).toBe(600);
    expect(fontWeightToNumber("unknown")).toBe(400);
  });

  it("renders shared Typst text style dictionaries safely", () => {
    const style = typstTextStyle(
      {
        fontFamily: 'Inter"; #panic() //',
        fontSize: "12pt); #panic() //",
        fontStyle: 'italic"; #panic() //',
        fontWeight: "semibold",
        color: "red",
      },
      9,
    );

    expect(style).toContain('font: "Inter\\"; #panic() //",');
    expect(style).toContain("size: 9pt,");
    expect(style).toContain('style: "italic\\"; #panic() //",');
    expect(style).toContain("weight: 600,");
    expect(style).toContain("fill: black");
  });

  it("builds the standard shared typography style definitions", () => {
    const defs = buildTypographyStyleDefs(
      defaultTypography,
      defaultTableSettings,
    );

    expect(defs).toContain("#let fieldLabelStyle = (");
    expect(defs).toContain("#let fieldValueStyle = (");
    expect(defs).toContain("#let sectionLabelStyle = (");
    expect(defs).toContain("#let tableHeaderStyle = (");
    expect(defs).toContain("#let tableBodyStyle = (");
    expect(defs).toContain('font: "Inter",');
    expect(defs).toContain('fill: rgb("64748b")');
  });
});
