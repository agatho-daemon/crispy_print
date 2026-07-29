import type { TableColumn } from "./layout";
import type { LogicalAlignment } from "./direction";

export interface TablePresetField {
  fieldname: string;
  width: string;
  align: LogicalAlignment;
  required?: boolean;
}

export interface TablePresetDefinition {
  id: string;
  label: string;
  description: string;
  fields: TablePresetField[];
}

export interface TablePresetFieldOption {
  fieldname: string;
  label: string;
  fieldtype?: string;
  options?: string;
}

export interface ResolvedTablePreset {
  preset: TablePresetDefinition;
  columns: TableColumn[];
  missingRequired: string[];
  missingOptional: string[];
  applicable: boolean;
}

export const TABLE_PRESETS: TablePresetDefinition[] = [
  {
    id: "invoice-items",
    label: "Invoice items",
    description: "Item, description, quantity, rate, and amount.",
    fields: [
      { fieldname: "idx", width: "32pt", align: "end" },
      { fieldname: "item_code", width: "1fr", align: "start", required: true },
      { fieldname: "description", width: "2fr", align: "start" },
      { fieldname: "qty", width: "0.7fr", align: "end", required: true },
      { fieldname: "uom", width: "0.7fr", align: "start" },
      { fieldname: "rate", width: "0.9fr", align: "end" },
      { fieldname: "amount", width: "1fr", align: "end", required: true },
    ],
  },
  {
    id: "service-rows",
    label: "Service rows",
    description: "Description-led rows for services and professional work.",
    fields: [
      { fieldname: "idx", width: "32pt", align: "end" },
      {
        fieldname: "description",
        width: "3fr",
        align: "start",
        required: true,
      },
      { fieldname: "qty", width: "0.7fr", align: "end" },
      { fieldname: "uom", width: "0.7fr", align: "start" },
      { fieldname: "rate", width: "0.9fr", align: "end", required: true },
      { fieldname: "amount", width: "1fr", align: "end", required: true },
    ],
  },
  {
    id: "tax-rows",
    label: "Tax rows",
    description: "Tax description, rate, tax amount, and running total.",
    fields: [
      { fieldname: "idx", width: "32pt", align: "end" },
      {
        fieldname: "description",
        width: "2fr",
        align: "start",
        required: true,
      },
      { fieldname: "rate", width: "0.8fr", align: "end" },
      { fieldname: "tax_amount", width: "1fr", align: "end", required: true },
      {
        fieldname: "total",
        width: "1fr",
        align: "end",
      },
    ],
  },
  {
    id: "serial-batch",
    label: "Serial and batch rows",
    description: "Item identity, serial/batch values, quantity, and warehouse.",
    fields: [
      { fieldname: "idx", width: "32pt", align: "end" },
      { fieldname: "item_code", width: "1fr", align: "start", required: true },
      { fieldname: "serial_no", width: "1.5fr", align: "start" },
      { fieldname: "batch_no", width: "1fr", align: "start" },
      { fieldname: "qty", width: "0.7fr", align: "end", required: true },
      { fieldname: "warehouse", width: "1.2fr", align: "start" },
    ],
  },
  {
    id: "pos-compact",
    label: "Compact POS rows",
    description: "Compact item, quantity, rate, and amount receipt rows.",
    fields: [
      { fieldname: "idx", width: "28pt", align: "end" },
      {
        fieldname: "item_code",
        width: "1.6fr",
        align: "start",
        required: true,
      },
      { fieldname: "qty", width: "0.55fr", align: "end", required: true },
      { fieldname: "rate", width: "0.8fr", align: "end" },
      { fieldname: "amount", width: "0.9fr", align: "end", required: true },
    ],
  },
];

export function resolveChildTableDoctype(
  fieldname: string,
  storedOptions: string | undefined,
  parentFields: TablePresetFieldOption[],
): string {
  if (storedOptions) return storedOptions;
  const parentField = parentFields.find(
    (field) => field.fieldname === fieldname && field.fieldtype === "Table",
  );
  return String(parentField?.options || "");
}

export function resolveTablePreset(
  preset: TablePresetDefinition,
  availableFields: TablePresetFieldOption[],
): ResolvedTablePreset {
  const available = new Map(
    availableFields
      .filter((field) => field?.fieldname)
      .map((field) => [field.fieldname, field]),
  );
  if (!available.has("idx")) {
    available.set("idx", {
      fieldname: "idx",
      label: "Sr No.",
      fieldtype: "Data",
    });
  }

  const missingRequired: string[] = [];
  const missingOptional: string[] = [];
  const columns: TableColumn[] = [];

  for (const field of preset.fields) {
    const option = available.get(field.fieldname);
    if (!option) {
      (field.required ? missingRequired : missingOptional).push(
        field.fieldname,
      );
      continue;
    }
    columns.push({
      fieldname: field.fieldname,
      label: option.label || field.fieldname,
      fieldtype: option.fieldtype || "Data",
      width: field.width,
      align: field.align,
    });
  }

  return {
    preset,
    columns,
    missingRequired,
    missingOptional,
    applicable: missingRequired.length === 0,
  };
}
