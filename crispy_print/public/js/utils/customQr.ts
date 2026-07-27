import type { DocField } from "./layout";

export const CUSTOM_QR_SOURCE_MODE = "custom";
export const LEGACY_BASIC_QR_SOURCE_MODE = "basic";

const UNSAFE_QR_FIELDTYPES = new Set([
  "Password",
  "Attach",
  "Attach Image",
  "Table",
  "Table MultiSelect",
  "Section Break",
  "Column Break",
  "Tab Break",
  "HTML",
  "Code",
  "Text Editor",
  "Markdown Editor",
  "Geolocation",
  "Button",
  "Image",
]);
const BUILDER_ONLY_FIELDNAMES = new Set([
  "doctype",
  "empty",
  "spacer",
  "divider",
]);

export interface CustomQrField extends DocField {
  hidden?: number;
}

export function isSafeCustomQrField(
  field: CustomQrField | null | undefined,
): boolean {
  return Boolean(
    field?.fieldname &&
    field?.label &&
    !field.hidden &&
    !field.fieldname.startsWith("_") &&
    !BUILDER_ONLY_FIELDNAMES.has(field.fieldname) &&
    !UNSAFE_QR_FIELDTYPES.has(field.fieldtype || ""),
  );
}

export function getSafeCustomQrFields(
  fields: CustomQrField[] | null | undefined,
): CustomQrField[] {
  return (fields || []).filter(isSafeCustomQrField);
}

export function buildCustomQrPayload(
  doc: Record<string, unknown> | null | undefined,
  fields: string[],
): string {
  if (!doc || !fields.length) return "";
  return fields
    .map((fieldname) => `${fieldname}: ${String(doc[fieldname] ?? "")}`)
    .join("\n");
}

export function customQrPayloadBytes(payload: string): number {
  return new TextEncoder().encode(payload).length;
}

export function isDenseCustomQrPayload(byteLength: number): boolean {
  return byteLength > 900;
}
