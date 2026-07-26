import { describe, expect, it } from "vitest";
import {
  getContentDirection,
  getLanguageDirection,
  orderForDirection,
  resolveLogicalAlignment,
} from "../../utils/direction";

describe("shared language direction", () => {
  it("normalizes language, region, and supported RTL prefixes", () => {
    expect(getLanguageDirection("ar_kw")).toEqual({
      language: "ar-KW",
      languageCode: "ar",
      region: "KW",
      direction: "rtl",
    });
    expect(getLanguageDirection("fa-IR").direction).toBe("rtl");
    expect(getLanguageDirection("he").direction).toBe("rtl");
    expect(getLanguageDirection("ur").direction).toBe("rtl");
    expect(getLanguageDirection("en-US").direction).toBe("ltr");
  });

  it("resolves semantic alignment without redefining physical sides", () => {
    expect(resolveLogicalAlignment("start", "rtl")).toBe("right");
    expect(resolveLogicalAlignment("end", "rtl")).toBe("left");
    expect(resolveLogicalAlignment("left", "rtl")).toBe("left");
    expect(resolveLogicalAlignment("right", "ltr")).toBe("right");
  });

  it("isolates accounting and identifier values as LTR", () => {
    expect(getContentDirection("Currency", "grand_total", "rtl")).toBe("ltr");
    expect(getContentDirection("Data", "tax_id", "rtl")).toBe("ltr");
    expect(getContentDirection("Data", "customer_name", "rtl")).toBe("rtl");
    expect(getContentDirection("Text", "description", "rtl")).toBe("rtl");
  });

  it("keeps semantic table source order stable for the renderer", () => {
    expect(orderForDirection(["a", "b"], "logical", "rtl")).toEqual(["a", "b"]);
    expect(orderForDirection(["a", "b"], "physical", "rtl")).toEqual([
      "a",
      "b",
    ]);
    expect(orderForDirection(["a", "b"], "logical", "ltr")).toEqual(["a", "b"]);
  });
});
