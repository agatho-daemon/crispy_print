// utils/layout.ts
// Utility functions for creating and manipulating Typst print layouts

import { getLogger } from "../logger";
import { deepClone, safeJsonParse } from "./json";
import type { LogicalAlignment, TableOrder } from "./direction";

const logger = getLogger({ module: "Layout" });

export interface DocField {
  name?: string;
  fieldname: string;
  label: string;
  fieldtype?: string;
  options?: string;
  print_hide?: number;
  raw_typst_field?: string;
  crispy_typst_block?: string;
  crispy_typst_block_name?: string;
  crispy_typst_block_code?: string;
  crispy_image?: string;
  crispy_image_width?: string;
  crispy_image_height?: string;
  crispy_image_fit?: string;
  spacer_value?: string;
  divider_length?: string;
  divider_stroke?: string;
  divider_color?: string;
}

export interface TableColumn {
  fieldname: string;
  label: string;
  fieldtype: string;
  width?: string;
  align?: LogicalAlignment;
}

export interface LayoutField {
  id?: string | number;
  fieldname: string;
  label: string;
  fieldtype: string;
  options?: string;
  align?: LogicalAlignment;
  table_columns?: TableColumn[];
  table_order?: TableOrder;
  field_template?: string;
  raw_typst_field?: string;
  crispy_typst_block?: string;
  crispy_typst_block_name?: string;
  crispy_typst_block_code?: string;
  crispy_image?: string;
  crispy_image_width?: string;
  crispy_image_height?: string;
  crispy_image_fit?: string;
  // Spacer configuration
  spacer_value?: string; // e.g., "1em", "2cm", "10pt"
  // Divider configuration
  divider_length?: string; // e.g., "100%", "80%", "10cm"
  divider_stroke?: string; // e.g., "0.5pt", "1pt", "2pt"
  divider_color?: string; // e.g., "gray", "#333", "rgb(0,0,0)"
}

export interface LayoutColumn {
  id?: string | number;
  label: string;
  fields: LayoutField[];
  width?: string | number;
}

export interface LayoutSection {
  label: string;
  columns: LayoutColumn[];
  id?: string | number;
  page_break?: boolean;
}

export interface CrispyLayout {
  header?: string;
  sections: LayoutSection[];
}

export function createLayoutId(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
}

// Defensive caps for `normalizeLayout`. A well-formed layout sits comfortably
// below these limits; values beyond them strongly suggest a corrupt or
// adversarial `layout_json`. Excess entries are dropped (with a warning) so the
// builder cannot be DoS'd by a single huge payload.
const MAX_LAYOUT_SECTIONS = 200;
const MAX_LAYOUT_COLUMNS_PER_SECTION = 50;
const MAX_LAYOUT_FIELDS_PER_COLUMN = 500;
const MAX_LAYOUT_TABLE_COLUMNS = 200;

function capArray<T>(arr: T[], limit: number, label: string): T[] {
  if (arr.length <= limit) return arr;
  logger.warn(
    `normalizeLayout: truncating ${label} from ${arr.length} to ${limit}`,
  );
  return arr.slice(0, limit);
}

/**
 * Normalize layout structure for consistent UI + serialization.
 * - Ensures arrays exist (`sections`, `columns`, `fields`)
 * - Ensures every section/column/field has a stable `id`
 * - Strips legacy/derived keys (e.g. `has_fields`)
 * - Leaves layout empty if it's empty (no auto-seeding)
 * - Enforces defensive caps on section/column/field counts
 */
export function normalizeLayout(
  layout: CrispyLayout | null | undefined,
): CrispyLayout {
  const base: CrispyLayout = {
    header: layout?.header || "",
    sections: Array.isArray(layout?.sections) ? layout!.sections : [],
  };

  const cappedSections = capArray(
    base.sections,
    MAX_LAYOUT_SECTIONS,
    "sections",
  );
  const normalizedSections: LayoutSection[] = cappedSections.map(
    (rawSection) => {
      const { has_fields: _ignoredHasFields, ...section } = (rawSection ||
        {}) as any;

      const columns = Array.isArray(section.columns) ? section.columns : [];
      const cappedColumns = capArray(
        columns,
        MAX_LAYOUT_COLUMNS_PER_SECTION,
        "columns",
      );
      const normalizedColumns: LayoutColumn[] = cappedColumns.map(
        (rawColumn: any) => {
          const column: LayoutColumn = {
            id:
              typeof rawColumn?.id === "string" ||
              typeof rawColumn?.id === "number"
                ? rawColumn.id
                : createLayoutId(),
            label: typeof rawColumn?.label === "string" ? rawColumn.label : "",
            width:
              typeof rawColumn?.width === "string" ||
              typeof rawColumn?.width === "number"
                ? rawColumn.width
                : undefined,
            fields: Array.isArray(rawColumn?.fields)
              ? capArray(
                  rawColumn.fields,
                  MAX_LAYOUT_FIELDS_PER_COLUMN,
                  "fields",
                )
              : [],
          };

          column.fields = column.fields
            .filter(Boolean)
            .map((rawField: any) => {
              const fieldtype = rawField?.fieldtype || "Data";
              const normalizedField: LayoutField = {
                ...rawField,
                id:
                  typeof rawField?.id === "string" ||
                  typeof rawField?.id === "number"
                    ? rawField.id
                    : createLayoutId(),
                fieldtype,
                label:
                  typeof rawField?.label === "string" ? rawField.label : "",
                fieldname:
                  typeof rawField?.fieldname === "string"
                    ? rawField.fieldname
                    : "",
                align: rawField?.align,
              };
              if (
                fieldtype === "Table" &&
                !Array.isArray(normalizedField.table_columns) &&
                Array.isArray(rawField?.columns)
              ) {
                normalizedField.table_columns = rawField.columns;
              }
              if (
                fieldtype === "Table" &&
                !normalizedField.table_order &&
                (rawField?.orderMode === "logical" ||
                  rawField?.orderMode === "physical")
              ) {
                normalizedField.table_order = rawField.orderMode;
              }
              if (Array.isArray(normalizedField.table_columns)) {
                normalizedField.table_columns = capArray(
                  normalizedField.table_columns,
                  MAX_LAYOUT_TABLE_COLUMNS,
                  "table_columns",
                );
              }
              return normalizedField;
            })
            .filter((f) => Boolean(f.fieldname));

          return column;
        },
      );

      return {
        label: typeof section.label === "string" ? section.label : "",
        columns: normalizedColumns,
        id:
          typeof section.id === "string" || typeof section.id === "number"
            ? section.id
            : createLayoutId(),
      };
    },
  );

  return {
    ...base,
    sections: normalizedSections,
  };
}

/**
 * Creates a default Typst-based layout from DocType metadata
 * Mirrors Frappe's print format builder behavior
 */
export function createDefaultLayout(
  meta: any,
  crispyFormat: any,
): CrispyLayout {
  if (!meta?.fields) {
    return { sections: [] };
  }

  const layout: CrispyLayout & { sections: LayoutSection[] } = {
    header: getDefaultHeader(),
    sections: [],
  };

  const sections = layout.sections;

  let currentSection: LayoutSection | null = null;
  let currentColumn: LayoutColumn | null = null;

  const setSection = (df?: DocField) => {
    const source = df || { label: "" };
    currentSection = {
      label: source.label || "",
      columns: [],
      id: createLayoutId(),
    };
    currentColumn = null;
    sections.push(currentSection);
  };

  const setColumn = (df?: DocField) => {
    if (!currentSection) {
      setSection();
    }
    const source = df || { label: "" };
    currentColumn = {
      id: createLayoutId(),
      label: source.label || "",
      fields: [],
    };
    currentSection!.columns.push(currentColumn);
  };

  for (let dfRaw of meta.fields as DocField[]) {
    let df = dfRaw.fieldname ? (deepClone(dfRaw) as DocField) : null;
    if (!df) continue;

    if (df.fieldtype === "Section Break") {
      setSection(df);
    } else if (df.fieldtype === "Column Break") {
      setColumn(df);
    } else if (df.label) {
      if (!currentColumn) setColumn();

      if (!df.print_hide) {
        const fieldtype = df.fieldtype || "Data";

        const field: LayoutField = {
          id: createLayoutId(),
          label: df.label,
          fieldname: df.fieldname,
          fieldtype: fieldtype,
          options: df.options,
          align: getDefaultFieldAlignment(fieldtype),
        };

        const fieldTemplate = getFieldTemplate(crispyFormat, df.fieldname);
        if (fieldTemplate) {
          field.label = `${__(df.label, null, (df as any).parent)} (${__("Field Template")})`;
          field.fieldtype = "Field Template";
          field.field_template = (fieldTemplate as any).name;
          field.fieldname = "_template";
        }

        if (df.fieldtype === "Table") {
          field.table_columns = getTableColumns(df);
          field.table_order = "logical";
        }

        currentColumn!.fields.push(field);
      }
    }
  }

  const filteredSections = sections.filter((section: LayoutSection) =>
    section.columns?.some((col: LayoutColumn) => col.fields?.length),
  );
  layout.sections = filteredSections;

  return normalizeLayout(layout);
}

/**
 * Get table columns for a child table field
 */
export function getTableColumns(dfOrDoctype: DocField | string): TableColumn[] {
  const childDoctype =
    typeof dfOrDoctype === "string" ? dfOrDoctype : dfOrDoctype.options;
  const parentHasLabel =
    typeof dfOrDoctype === "string"
      ? true
      : Boolean((dfOrDoctype as DocField).label);

  if (typeof frappe === "undefined") {
    return [];
  }

  if (!childDoctype) {
    return [];
  }

  const childMeta = frappe.get_meta(childDoctype);
  if (!childMeta?.fields) {
    return [];
  }

  const tableColumns: TableColumn[] = [];

  const candidates = childMeta.fields
    .filter((f: DocField) => !f.print_hide && f.fieldname && f.label)
    .filter(
      (f: DocField) =>
        f.fieldtype && !["Section Break", "Column Break"].includes(f.fieldtype),
    );

  for (const f of candidates) {
    if (!parentHasLabel) break;

    // Use Typst width values
    const width = "auto"; // Default to auto width

    tableColumns.push({
      fieldname: f.fieldname,
      label: f.label,
      fieldtype: f.fieldtype,
      width,
      align: getDefaultFieldAlignment(f.fieldtype),
    });
  }

  return tableColumns;
}

function getFieldTemplate(crispyFormat: any, fieldname: string) {
  const templates = crispyFormat?.__onload?.print_templates || [];
  for (const template of templates) {
    if (template.field === fieldname) {
      return template;
    }
  }
  return null;
}

function getDefaultHeader() {
  // Header rendering is handled via Typst `doc_header` on the Crispy Format doctype.
  // Keep layout.header empty for legacy compatibility.
  return "";
}

/**
 * Pick specific keys from an object (for serialization)
 */
export function pluck<T extends Record<string, any>>(
  obj: T,
  keys: (keyof T)[],
): Partial<T> {
  const result: Partial<T> = {};
  for (const key of keys) {
    if (key in obj) {
      result[key] = obj[key];
    }
  }
  return result;
}

/**
 * Convert layout to JSON string for storage
 */
export function serializeLayout(layout: CrispyLayout): string {
  const normalized = normalizeLayout(layout);

  const cleanedSections = (normalized.sections || []).map((section) => {
    const { has_fields: _ignored, ...restSection } = section as any;
    return {
      ...restSection,
      columns: (restSection.columns || []).map((column: any) => ({
        ...column,
        fields: (column.fields || []).map((field: any) => {
          const {
            crispy_typst_block_code: _transientBlockCode,
            ...cleanField
          } = field;
          return cleanField;
        }),
      })),
    };
  });

  return JSON.stringify(
    {
      ...normalized,
      sections: cleanedSections,
    },
    // null,
    // 2
  );
}

/**
 * Parse layout from JSON string
 */
export function deserializeLayout(json: string): CrispyLayout | null {
  const parsed = safeJsonParse<CrispyLayout | null>(json, {
    fallback: null,
    logger,
    errorMessage: "Failed to parse layout JSON",
  });
  return parsed ? normalizeLayout(parsed) : null;
}

/**
 * Get default alignment for a field based on its fieldtype
 * Numeric fields default to right alignment, like Frappe
 */
export function getDefaultFieldAlignment(fieldtype: string): LogicalAlignment {
  const numericTypes = ["Int", "Float", "Currency", "Percent"];
  return numericTypes.includes(fieldtype) ? "right" : "auto";
}
