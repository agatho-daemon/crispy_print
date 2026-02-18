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
<svg xmlns="http://www.w3.org/2000/svg" width="760" height="300" viewBox="0 0 760 300">
  <text x="380" y="36" text-anchor="middle" font-size="16" font-family="sans-serif" fill="#334155">
    Placeholder Chart
  </text>
  <text x="380" y="58" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#64748b">
    Sample Only
  </text>
  <text
    x="40"
    y="160"
    text-anchor="middle"
    transform="rotate(-90 40 160)"
    font-size="11"
    font-family="sans-serif"
    fill="#475569"
  >
    Value
  </text>
  <text x="80" y="244" text-anchor="end" font-size="11" font-family="sans-serif" fill="#475569">0</text>
  <text x="80" y="184" text-anchor="end" font-size="11" font-family="sans-serif" fill="#475569">10</text>
  <text x="80" y="144" text-anchor="end" font-size="11" font-family="sans-serif" fill="#475569">20</text>
  <text x="80" y="104" text-anchor="end" font-size="11" font-family="sans-serif" fill="#475569">30</text>
  <line x1="90" y1="180" x2="690" y2="180" stroke="#dbe4ee" stroke-width="1" />
  <line x1="90" y1="140" x2="690" y2="140" stroke="#dbe4ee" stroke-width="1" />
  <line x1="90" y1="100" x2="690" y2="100" stroke="#dbe4ee" stroke-width="1" />
  <line x1="90" y1="240" x2="690" y2="240" stroke="#cbd5e1" stroke-width="1" />
  <line x1="90" y1="80" x2="90" y2="240" stroke="#cbd5e1" stroke-width="1" />

  <rect x="170" y="180" width="80" height="60" fill="#93c5fd" />
  <rect x="330" y="140" width="80" height="100" fill="#60a5fa" />
  <rect x="490" y="100" width="80" height="140" fill="#3b82f6" />

  <text x="210" y="260" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#334155">A</text>
  <text x="370" y="260" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#334155">B</text>
  <text x="530" y="260" text-anchor="middle" font-size="12" font-family="sans-serif" fill="#334155">C</text>

  <text x="210" y="174" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#1e293b">10</text>
  <text x="370" y="134" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#1e293b">20</text>
  <text x="530" y="94" text-anchor="middle" font-size="11" font-family="sans-serif" fill="#1e293b">30</text>
</svg>
`.trim();

const FRAPPE_CHART_EXPORT_CSS =
  ".chart-container{position:relative;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Roboto','Oxygen','Ubuntu','Cantarell','Fira Sans','Droid Sans','Helvetica Neue',sans-serif}.chart-container .axis,.chart-container .chart-label{fill:#555b51}.chart-container .axis line,.chart-container .chart-label line{stroke:#dadada}.chart-container .dataset-units circle{stroke:#fff;stroke-width:2}.chart-container .dataset-units path{fill:none;stroke-opacity:1;stroke-width:2px}.chart-container .dataset-path{stroke-width:2px}.chart-container .path-group path{fill:none;stroke-opacity:1;stroke-width:2px}.chart-container line.dashed{stroke-dasharray:5,3}.chart-container .axis-line .specific-value{text-anchor:start}.chart-container .axis-line .y-line{text-anchor:end}.chart-container .axis-line .x-line{text-anchor:middle}.chart-container .legend-dataset-text{fill:#6c7680;font-weight:600}.graph-svg-tip{position:absolute;z-index:99999;padding:10px;font-size:12px;color:#959da5;text-align:center;background:rgba(0,0,0,.8);border-radius:3px}.graph-svg-tip ul{padding-left:0;display:flex}.graph-svg-tip ol{padding-left:0;display:flex}.graph-svg-tip ul.data-point-list li{min-width:90px;flex:1;font-weight:600}.graph-svg-tip strong{color:#dfe2e5;font-weight:600}.graph-svg-tip .svg-pointer{position:absolute;height:5px;margin:0 0 0 -5px;content:' ';border:5px solid transparent;}.graph-svg-tip.comparison{padding:0;text-align:left;pointer-events:none}.graph-svg-tip.comparison .title{display:block;padding:10px;margin:0;font-weight:600;line-height:1;pointer-events:none}.graph-svg-tip.comparison ul{margin:0;white-space:nowrap;list-style:none}.graph-svg-tip.comparison li{display:inline-block;padding:5px 10px}";

const DUMMY_FRAPPE_CHART_OPTIONS = {
  title: "Sample Chart",
  type: "axis-mixed",
  height: 300,
  animate: 0,
  showLegend: 1,
  truncateLegends: 0,
  colors: ["purple", "#ffa3ef", "light-blue"],
  axisOptions: {
    xAxisMode: "tick",
    yAxisMode: "span",
    xIsSeries: true,
    shortenYAxisNumbers: 0,
  },
  barOptions: {
    stacked: 1,
    spaceRatio: 0.5,
  },
  lineOptions: {
    showDots: 1,
    hideLine: 0,
    regionFill: 0,
  },
  tooltipOptions: {
    formatTooltipX: (d: string) => String(d || "").toUpperCase(),
    formatTooltipY: (d: number) => `${d} pts`,
  },
  data: {
    labels: ["Group A", "Group B", "Group C", "Group D", "Group E", "Group F", "Group G"],
    datasets: [
      {
        name: "Some Data",
        chartType: "bar",
        values: [30, 45, 28, 36, 50, 34, 22],
      },
      {
        name: "Another Set",
        chartType: "bar",
        values: [18, 26, 22, 19, 24, 20, 16],
      },
      {
        name: "Yet Another",
        chartType: "line",
        values: [12, 18, 14, 20, 17, 22, 19],
      },
    ],
    yMarkers: [{ label: "Marker", value: 70, options: { labelPos: "left" } }],
    yRegions: [
      { label: "Region", start: -10, end: 50, options: { labelPos: "right" } },
    ],
  },
};

function mergeChartOptions(overrides?: Record<string, any>) {
  const next = { ...(overrides || {}) };
  const merged = {
    ...DUMMY_FRAPPE_CHART_OPTIONS,
    ...next,
    data: {
      ...DUMMY_FRAPPE_CHART_OPTIONS.data,
      ...(next.data || {}),
      labels:
        Array.isArray(next?.data?.labels) && next.data.labels.length
          ? next.data.labels
          : DUMMY_FRAPPE_CHART_OPTIONS.data.labels,
      datasets:
        Array.isArray(next?.data?.datasets) && next.data.datasets.length
          ? next.data.datasets
          : DUMMY_FRAPPE_CHART_OPTIONS.data.datasets,
      yMarkers:
        Array.isArray(next?.data?.yMarkers) && next.data.yMarkers.length
          ? next.data.yMarkers
          : undefined,
      yRegions:
        Array.isArray(next?.data?.yRegions) && next.data.yRegions.length
          ? next.data.yRegions
          : undefined,
    },
    axisOptions: {
      ...DUMMY_FRAPPE_CHART_OPTIONS.axisOptions,
      ...(next.axisOptions || {}),
    },
    barOptions: {
      ...DUMMY_FRAPPE_CHART_OPTIONS.barOptions,
      ...(next.barOptions || {}),
    },
    lineOptions: {
      ...(next.lineOptions || {}),
    },
    tooltipOptions: {
      ...DUMMY_FRAPPE_CHART_OPTIONS.tooltipOptions,
      ...(next.tooltipOptions || {}),
    },
  };
  return merged;
}

export async function renderDummyReportChartSvg(
  overrides?: Record<string, any>,
): Promise<string> {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return DUMMY_CHART_SVG;
  }

  const ChartCtor = (window as any)?.frappe?.Chart;
  if (!ChartCtor) return DUMMY_CHART_SVG;

  const host = document.createElement("div");
  host.style.position = "fixed";
  host.style.left = "-99999px";
  host.style.top = "0";
  host.style.width = "760px";
  host.style.pointerEvents = "none";
  host.style.opacity = "0";
  document.body.appendChild(host);

  let chart: any = null;
  try {
    const chartOptions = mergeChartOptions(overrides);
    chart = new ChartCtor(host, chartOptions);
    if (typeof chart?.update === "function") {
      chart.update(chartOptions.data);
    }

    await new Promise<void>((resolve) => {
      window.requestAnimationFrame(() => {
        window.requestAnimationFrame(() => resolve());
      });
    });

    const svg = host.querySelector("svg")?.outerHTML?.trim();
    return prepareChartSvgForTypst(svg) || DUMMY_CHART_SVG;
  } catch {
    return DUMMY_CHART_SVG;
  } finally {
    try {
      chart?.destroy?.();
    } catch {
      // no-op
    }
    host.remove();
  }
}

function prepareChartSvgForTypst(svg: string | undefined | null): string | null {
  if (!svg || typeof svg !== "string") return null;
  const raw = svg.trim();
  if (!raw.startsWith("<svg")) return null;

  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(raw, "image/svg+xml");
    const root = doc.documentElement;
    if (!root || root.tagName.toLowerCase() !== "svg") return null;

    root.classList.add("chart-container");
    root.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    root.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");

    const hasExportStyle = Array.from(root.children).some((node) => {
      if (node.tagName.toLowerCase() !== "style") return false;
      return node.textContent?.includes(".chart-container .axis");
    });
    if (!hasExportStyle) {
      const style = doc.createElementNS("http://www.w3.org/2000/svg", "style");
      style.textContent = FRAPPE_CHART_EXPORT_CSS;
      root.insertBefore(style, root.firstChild);
    }

    // Strip elements that can cause Typst SVG XML parsing trouble.
    doc.querySelectorAll("script, foreignObject").forEach((el) => el.remove());

    return new XMLSerializer().serializeToString(root);
  } catch {
    return null;
  }
}

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
