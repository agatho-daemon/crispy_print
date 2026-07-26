export const RTL_LANGUAGE_PREFIXES = new Set(["ar", "fa", "he", "ur"]);

export type TextDirection = "ltr" | "rtl";
export type LogicalAlignment =
  | "auto"
  | "start"
  | "center"
  | "end"
  | "left"
  | "right";
export type TableOrder = "physical" | "logical";

export interface LanguageDirection {
  language: string;
  languageCode: string;
  region: string;
  direction: TextDirection;
}

const LTR_FIELD_TYPES = new Set([
  "Int",
  "Float",
  "Currency",
  "Percent",
  "Date",
  "Datetime",
  "Time",
  "Duration",
  "Barcode",
]);

const LTR_FIELDNAME_PATTERN =
  /^(?:name|id)$|(?:^|_)(?:uuid|hash|code|sku|tax|vat|iban|swift|bic|phone|mobile|email|url|website|barcode|qr|reference|serial|batch)(?:_|$)/i;

export function normalizeLanguage(language: unknown, fallback = "en"): string {
  const normalized = String(language || fallback)
    .trim()
    .replace(/_/g, "-");
  return normalized || fallback;
}

export function getLanguageDirection(
  language: unknown,
  fallback = "en",
): LanguageDirection {
  const normalized = normalizeLanguage(language, fallback);
  const [languageCodeRaw, regionRaw = ""] = normalized.split("-", 2);
  const languageCode = languageCodeRaw.toLowerCase();
  return {
    language: regionRaw
      ? `${languageCode}-${regionRaw.toUpperCase()}`
      : languageCode,
    languageCode,
    region: regionRaw.toUpperCase(),
    direction: RTL_LANGUAGE_PREFIXES.has(languageCode) ? "rtl" : "ltr",
  };
}

export function getInterfaceLanguage(): string {
  const frappeGlobal = (globalThis as any)?.frappe;
  return normalizeLanguage(
    frappeGlobal?.boot?.lang ||
      frappeGlobal?.boot?.user?.language ||
      frappeGlobal?.session?.user_language ||
      document?.documentElement?.lang ||
      "en",
  );
}

export function applyDirectionAttributes(
  element: Element,
  language: unknown = getInterfaceLanguage(),
): LanguageDirection {
  const context = getLanguageDirection(language);
  element.setAttribute("lang", context.language);
  element.setAttribute("dir", context.direction);
  element.classList.toggle("crispy-rtl", context.direction === "rtl");
  element.classList.toggle("crispy-ltr", context.direction === "ltr");
  return context;
}

export function resolveLogicalAlignment(
  alignment: LogicalAlignment | null | undefined,
  direction: TextDirection,
): "left" | "center" | "right" {
  switch (alignment || "auto") {
    case "center":
      return "center";
    case "left":
      return "left";
    case "right":
      return "right";
    case "end":
      return direction === "rtl" ? "left" : "right";
    case "auto":
    case "start":
    default:
      return direction === "rtl" ? "right" : "left";
  }
}

export function isLtrField(
  fieldtype?: string | null,
  fieldname?: string | null,
): boolean {
  return (
    LTR_FIELD_TYPES.has(String(fieldtype || "")) ||
    LTR_FIELDNAME_PATTERN.test(String(fieldname || ""))
  );
}

export function getContentDirection(
  fieldtype: string | null | undefined,
  fieldname: string | null | undefined,
  documentDirection: TextDirection,
): TextDirection {
  return isLtrField(fieldtype, fieldname) ? "ltr" : documentDirection;
}

export function orderForDirection<T>(
  values: readonly T[],
  _order: TableOrder | null | undefined,
  _direction: TextDirection,
): T[] {
  // Keep semantic source order stable. Direction-aware renderers place the
  // first logical item at inline-start; reversing here would mirror it twice.
  return [...values];
}
