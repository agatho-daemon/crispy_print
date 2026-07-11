export type ReportFormatsResponse = {
  formats?: Array<{
    name: string;
    report_renderer?: string;
    layout_style?: string;
    company?: string;
    is_default?: number;
  }>;
  default_format?: string | null;
};

export type ReportFormatOption = { label: string; value: string };

export type ReportColumn = { fieldname: string; label: string };

export function buildReportFormatOptions(
  formats: ReportFormatsResponse | null | undefined,
): {
  options: ReportFormatOption[];
  defaultValue: string | null;
} {
  const options: ReportFormatOption[] = [];
  let defaultValue = formats?.default_format || null;

  if (formats?.formats?.length) {
    formats.formats.forEach((fmt) => {
      const suffix = [fmt.report_renderer, fmt.layout_style]
        .filter(Boolean)
        .join(" · ");
      options.push({
        label: suffix ? `${fmt.name} (${suffix})` : fmt.name,
        value: fmt.name,
      });
    });
    if (!defaultValue) defaultValue = formats.formats[0].name;
  }

  return { options, defaultValue };
}

export function normalizeReportColumns(
  columns: any[] | null | undefined,
): ReportColumn[] {
  if (!columns || !columns.length) {
    return [];
  }

  return columns.map((col) => {
    if (typeof col === "string") {
      return {
        fieldname: col,
        label: col.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()),
      };
    }

    const fieldname = col.fieldname || col.id || "";
    const label = col.label || fieldname;
    return { fieldname, label };
  });
}
