import type { LogicalAlignment } from "./direction";

export function getDefaultAlignment(fieldtype?: string): LogicalAlignment {
  const numericTypes = ["Int", "Float", "Currency", "Percent"];
  return numericTypes.includes(fieldtype || "") ? "right" : "auto";
}
