import {
  getTypstFontFaces,
  getTypstLocalFonts,
  type TypstFontFamilyFaces,
} from "../api/crispy";

export type SizeParseResult = {
  value: number;
  unit: string;
  decimals: number;
  valid: boolean;
};

export type FontFetchOptions = {
  devFallback?: string[];
  errorFallback?: string[];
  logger?: { error?: (message: string, error?: unknown) => void };
};

export function parseSize(input: string | null | undefined): SizeParseResult {
  const raw = String(input || "").trim();
  const match = raw.match(/^([0-9]+(?:\.[0-9]+)?)\s*([a-z%]+)?$/i);
  if (!match) return { value: 0, unit: "pt", decimals: 0, valid: false };
  const value = Number(match[1]);
  const unit = (match[2] || "pt").toLowerCase();
  const decimals = (match[1].split(".")[1] || "").length;
  const finite = Number.isFinite(value);
  return {
    value: finite ? value : 0,
    unit,
    decimals,
    valid: finite,
  };
}

export function formatPt(value: number): string {
  const safe = Math.max(1, value);
  const num = safe.toFixed(2).replace(/\.?0+$/, "");
  return `${num}pt`;
}

export async function fetchTypstFonts(
  options: FontFetchOptions = {},
): Promise<string[]> {
  const devFallback = options.devFallback || [
    "Arial",
    "Helvetica",
    "Times New Roman",
    "Courier",
  ];
  const errorFallback = options.errorFallback || [
    "Arial",
    "Helvetica",
    "Times New Roman",
  ];

  if (typeof frappe === "undefined") {
    return devFallback;
  }

  try {
    return await getTypstLocalFonts();
  } catch (error) {
    options.logger?.error?.("Failed to fetch fonts", error);
    return errorFallback;
  }
}

export async function fetchTypstFontFaces(
  options: FontFetchOptions = {},
): Promise<TypstFontFamilyFaces[]> {
  if (typeof frappe === "undefined") {
    return [];
  }

  try {
    return await getTypstFontFaces();
  } catch (error) {
    options.logger?.error?.("Failed to fetch font faces", error);
    return [];
  }
}
