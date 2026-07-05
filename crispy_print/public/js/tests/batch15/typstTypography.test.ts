import { describe, expect, it, vi } from "vitest";

vi.mock("../../api/crispy", () => ({
  getTypstLocalFonts: vi.fn(async () => ["Inter", "Serif"]),
  getTypstFontFaces: vi.fn(async () => [
    {
      family: "Rajdhani",
      styles: ["normal"],
      weights: ["regular", "bold"],
      faces: [],
    },
  ]),
}));

describe("typstTypography utils", async () => {
  const { fetchTypstFontFaces, fetchTypstFonts, formatPt, parseSize } =
    await import("../../utils/typstTypography");
  const { getTypstFontFaces, getTypstLocalFonts } =
    await import("../../api/crispy");

  it("parseSize handles valid inputs", () => {
    expect(parseSize("10pt")).toEqual({
      value: 10,
      unit: "pt",
      decimals: 0,
      valid: true,
    });
    expect(parseSize(" 12.50 px ")).toEqual({
      value: 12.5,
      unit: "px",
      decimals: 2,
      valid: true,
    });
  });

  it("parseSize returns defaults on invalid input", () => {
    expect(parseSize("bad")).toEqual({
      value: 0,
      unit: "pt",
      decimals: 0,
      valid: false,
    });
  });

  it("formatPt clamps to at least 1pt and strips zeros", () => {
    expect(formatPt(0.1)).toBe("1pt");
    expect(formatPt(10.5)).toBe("10.5pt");
  });

  it("fetchTypstFonts uses dev fallback when frappe is undefined", async () => {
    const prevFrappe = (globalThis as any).frappe;
    delete (globalThis as any).frappe;
    const fonts = await fetchTypstFonts();
    expect(fonts).toEqual(["Arial", "Helvetica", "Times New Roman", "Courier"]);
    (globalThis as any).frappe = prevFrappe;
  });

  it("fetchTypstFonts returns API fonts when available", async () => {
    (globalThis as any).frappe = {};
    const fonts = await fetchTypstFonts();
    expect(getTypstLocalFonts).toHaveBeenCalledTimes(1);
    expect(fonts).toEqual(["Inter", "Serif"]);
  });

  it("fetchTypstFonts falls back on API error", async () => {
    (getTypstLocalFonts as any).mockRejectedValueOnce(new Error("fail"));
    (globalThis as any).frappe = {};
    const fonts = await fetchTypstFonts();
    expect(fonts).toEqual(["Arial", "Helvetica", "Times New Roman"]);
  });

  it("fetchTypstFontFaces returns API font face metadata", async () => {
    (globalThis as any).frappe = {};
    const faces = await fetchTypstFontFaces();
    expect(getTypstFontFaces).toHaveBeenCalledTimes(1);
    expect(faces[0]).toMatchObject({
      family: "Rajdhani",
      weights: ["regular", "bold"],
    });
  });
});
