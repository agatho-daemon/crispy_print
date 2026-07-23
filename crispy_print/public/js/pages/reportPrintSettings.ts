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

export type ReportColumnSelection = { selected: boolean; width: string };

const GENERAL_LEDGER_COLUMN_DEFAULTS: Record<string, string> = {
  posting_date: "54pt",
  account: "1.4fr",
  debit: "62pt",
  credit: "62pt",
  balance: "66pt",
  voucher_type: "64pt",
  voucher_no: "82pt",
  party_name: "1fr",
};

export function getReportColumnDefault(
  reportName: string | null | undefined,
  fieldname: string,
): ReportColumnSelection {
  if (reportName === "General Ledger") {
    const width = GENERAL_LEDGER_COLUMN_DEFAULTS[fieldname];
    return width
      ? { selected: true, width }
      : { selected: false, width: "auto" };
  }

  return { selected: true, width: "auto" };
}

export function serializeReportPreviewIntent(parts: unknown[]): string {
  return JSON.stringify(parts);
}

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
