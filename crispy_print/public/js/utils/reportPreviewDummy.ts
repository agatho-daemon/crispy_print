import type { TableColumn } from "./layout";

type DummyCell = {
  value: string;
  fieldname: string;
  label: string;
  is_numeric: boolean;
};

type DummyRow = {
  _idx: number;
  cells: DummyCell[];
  is_bold: boolean;
  is_total_row: boolean;
  [key: string]: any;
};

const DUMMY_FILTERS = [
  { label: "Filter 1", value: "Value 1" },
  { label: "Filter 2", value: "Value 2" },
  { label: "Filter 3", value: "Value 3" },
];

const DUMMY_SUMMARY = [
  { label: "Summary 1", value: "Value 1" },
  { label: "Summary 2", value: "Value 2" },
  { label: "Summary 3", value: "Value 3" },
  { label: "Summary 4", value: "Value 4" },
];

const DUMMY_TABLE_COLUMN_CATALOG: TableColumn[] = [
  {
    fieldname: "column_1",
    label: "Column 1",
    fieldtype: "Data",
    width: "1fr",
    align: "left",
  },
  {
    fieldname: "column_2",
    label: "Column 2",
    fieldtype: "Data",
    width: "auto",
    align: "left",
  },
  {
    fieldname: "column_3",
    label: "Column 3",
    fieldtype: "Currency",
    width: "auto",
    align: "right",
  },
  {
    fieldname: "column_4",
    label: "Column 4",
    fieldtype: "Currency",
    width: "auto",
    align: "right",
  },
  {
    fieldname: "column_5",
    label: "Column 5",
    fieldtype: "Currency",
    width: "auto",
    align: "right",
  },
  {
    fieldname: "column_6",
    label: "Column 6",
    fieldtype: "Currency",
    width: "auto",
    align: "right",
  },
];

const DUMMY_TABLE_ROWS: Array<Record<string, string>> = [
  {
    column_1: "Value 1-1",
    column_2: "Value 1-2",
    column_3: "100",
    column_4: "110",
    column_5: "120",
    column_6: "130",
  },
  {
    column_1: "Value 2-1",
    column_2: "Value 2-2",
    column_3: "200",
    column_4: "210",
    column_5: "220",
    column_6: "230",
  },
  {
    column_1: "Value 3-1",
    column_2: "Value 3-2",
    column_3: "300",
    column_4: "310",
    column_5: "320",
    column_6: "330",
  },
  {
    column_1: "Value 4-1",
    column_2: "Value 4-2",
    column_3: "400",
    column_4: "410",
    column_5: "420",
    column_6: "430",
  },
];

const DUMMY_CHART_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="720" height="280" viewBox="0 0 720 280">
  <rect x="0" y="0" width="720" height="280" fill="#f8fafc" />
  <text x="24" y="32" font-size="16" font-family="sans-serif" fill="#334155">
    Placeholder Chart
  </text>
  <text x="24" y="52" font-size="11" font-family="sans-serif" fill="#64748b">
    Sample Only
  </text>
  <line x1="60" y1="230" x2="670" y2="230" stroke="#cbd5e1" stroke-width="1" />
  <line x1="60" y1="70" x2="60" y2="230" stroke="#cbd5e1" stroke-width="1" />

  <rect x="140" y="170" width="80" height="60" fill="#93c5fd" />
  <rect x="300" y="130" width="80" height="100" fill="#60a5fa" />
  <rect x="460" y="90" width="80" height="140" fill="#3b82f6" />

  <text x="170" y="248" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#334155">A</text>
  <text x="340" y="248" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#334155">B</text>
  <text x="500" y="248" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#334155">C</text>

  <text x="170" y="164" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#1e293b">10</text>
  <text x="340" y="124" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#1e293b">20</text>
  <text x="500" y="84" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#1e293b">30</text>
</svg>
`.trim();

function isNumericFieldtype(fieldtype: string | undefined): boolean {
  return ["Int", "Float", "Currency", "Percent"].includes(String(fieldtype || ""));
}

export function getDummyReportFilterColumns(): TableColumn[] {
  return [
    {
      fieldname: "label",
      label: "Label",
      fieldtype: "Data",
      width: "auto",
      align: "left",
    },
    {
      fieldname: "value",
      label: "Value",
      fieldtype: "Data",
      width: "auto",
      align: "left",
    },
  ];
}

export function getDummyReportTableColumns(): TableColumn[] {
  return DUMMY_TABLE_COLUMN_CATALOG.map((col) => ({ ...col }));
}

export function buildDummyReportPreviewData(options: {
  title?: string;
  subtitle?: string;
  includeFilters?: boolean;
  includeSummary?: boolean;
  includeTotalRow?: boolean;
  tableColumns?: TableColumn[];
  columnConfig?: Array<{ fieldname: string; width: string }>;
}) {
  const requestedColumns = Array.isArray(options.tableColumns) && options.tableColumns.length
    ? options.tableColumns
    : getDummyReportTableColumns();
  const widthMap = new Map(
    (options.columnConfig || []).map((col) => [String(col.fieldname), String(col.width || "auto")]),
  );
  const columns = requestedColumns
    .filter((col) => Boolean(col?.fieldname))
    .map((col) => ({
      label: col.label || col.fieldname,
      fieldname: col.fieldname,
      fieldtype: col.fieldtype || "Data",
      is_numeric: isNumericFieldtype(col.fieldtype),
      width: widthMap.get(col.fieldname) || col.width || "auto",
    }));

  const rows: DummyRow[] = DUMMY_TABLE_ROWS.map((row, index) => {
    const cells: DummyCell[] = columns.map((col) => ({
      value: String(row[col.fieldname] ?? ""),
      fieldname: col.fieldname,
      label: col.label,
      is_numeric: Boolean(col.is_numeric),
    }));
    const out: DummyRow = {
      _idx: index,
      cells,
      is_bold: false,
      is_total_row: false,
    };
    columns.forEach((col) => {
      out[col.fieldname] = String(row[col.fieldname] ?? "");
    });
    return out;
  });

  if (options.includeTotalRow) {
    const totalCells: DummyCell[] = columns.map((col, idx) => ({
      value:
        idx === 0
          ? "Total (Placeholder)"
          : col.is_numeric
            ? "0.00"
            : "",
      fieldname: col.fieldname,
      label: col.label,
      is_numeric: Boolean(col.is_numeric),
    }));
    rows.push({
      _idx: rows.length,
      cells: totalCells,
      is_bold: true,
      is_total_row: true,
    });
  }

  return {
    title: options.title || "Generic Preview",
    subtitle: options.subtitle || "Placeholder data for style simulation only",
    filters: options.includeFilters ? DUMMY_FILTERS : [],
    report_summary: options.includeSummary === false ? [] : DUMMY_SUMMARY,
    chart: {},
    chart_svg: DUMMY_CHART_SVG,
    columns,
    rows,
    total_rows: DUMMY_TABLE_ROWS.length,
    skip_total_row: !options.includeTotalRow,
  };
}
