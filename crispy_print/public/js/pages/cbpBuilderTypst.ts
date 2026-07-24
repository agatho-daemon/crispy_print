import type { CrispyBrandingProfileDoc } from "../api/crispy";
import { typstTextStyle as renderTypstTextStyle } from "../typst/textStyles";
import {
  cbpTypographySpecimen,
  cbpTypographyStyle,
} from "./cbpTypographyAdapter";
import {
  defaultReportChartPalette,
  num,
  pageDimensions,
  specimenRows,
} from "./cbpBuilderSupport";

export type CbpPreviewChartKind =
  | "line"
  | "bar"
  | "grouped_bar"
  | "mixed"
  | "horizontal_bar"
  | "percentage_stacked"
  | "waterfall";

export interface CbpPreviewTypstContext {
  model: CrispyBrandingProfileDoc;
  installedFonts?: string[];
  profileName: string;
  isDefault: boolean;
  effectiveCodeOnly: boolean;
  tableStriping: boolean;
  qrEnabled: boolean;
  usesLogo: boolean;
  logoImage: string;
  letterheadImage: string;
  letterheadLabel: string;
  letterheadSourceLabel: string;
  previewChartKind?: CbpPreviewChartKind;
}

export function buildCodePreviewTypst(
  source: string,
  context: CbpPreviewTypstContext,
) {
  return `${buildSpecimenDictionary(context)}\n\n${source}`;
}

export function buildVisualPreviewTypst(context: CbpPreviewTypstContext) {
  const model = previewModelWithInstalledFonts(context);
  const page = pageDimensions(
    model.page_size || "A4",
    model.orientation || "portrait",
  );
  const letterhead = assetFilename(context.letterheadImage);
  const logo = context.usesLogo ? assetFilename(context.logoImage) : "";
  const pageBackground = letterhead
    ? `\n  background: image(${toTypstValue(letterhead)}, width: 100%),`
    : "";
  const logoPlacement = logo
    ? `\n    #place(top + left, dx: ${num(model.branding_logo_offset_x_mm)}mm, dy: ${num(model.branding_logo_offset_y_mm)}mm, image(${toTypstValue(logo)}, width: ${num(model.branding_logo_width_mm)}mm))`
    : "";
  const qrPlacement = context.qrEnabled
    ? `\n    #place(bottom + left, dx: ${num(model.qr_dx_mm)}mm, dy: ${num(model.qr_dy_mm)}mm)[#box(width: ${num(model.qr_code_size_mm)}mm, height: ${num(model.qr_code_size_mm)}mm, stroke: (paint: black, thickness: 0.7pt))[#align(center + horizon)[#text(size: 8pt, weight: "bold")[QR]]]]`
    : "";
  const pageForeground =
    logoPlacement || qrPlacement
      ? `\n  foreground: [${logoPlacement}${qrPlacement}\n  ],`
      : "";
  const tableFill = context.tableStriping
    ? `(x, y) => if y == 0 { rgb(${toTypstValue(model.table_header_background_color || "#F1F5F9")}) } else if y == 2 { rgb(${toTypstValue(model.table_stripe_color || "#F8FAFC")}) }`
    : `(x, y) => if y == 0 { rgb(${toTypstValue(model.table_header_background_color || "#F1F5F9")}) }`;
  const chartPalette = parseChartPalette(model.report_chart_palette);
  const previewChart = buildPreviewChartSpec(
    context.previewChartKind || "line",
    chartPalette.length,
  );
  const chartTheme = `(
  palette: (${chartPalette.map(toTypstValue).join(", ")}),
  horizontal_grid: ${Boolean(model.report_chart_horizontal_grid)},
  vertical_grid: ${Boolean(model.report_chart_vertical_grid)},
  minor_grid: ${Boolean(model.report_chart_minor_grid)},
  grid_color: ${toTypstValue(model.report_chart_grid_color || "#CBD5E1")},
  grid_stroke_pt: ${num(model.report_chart_grid_stroke_pt)},
  axis_color: ${toTypstValue(model.report_chart_axis_color || "#64748B")},
  axis_stroke_pt: ${num(model.report_chart_axis_stroke_pt)},
  zero_line_color: ${toTypstValue(model.report_chart_zero_line_color || "#475569")},
  zero_line_stroke_pt: ${num(model.report_chart_zero_line_stroke_pt)},
  legend_position: ${toTypstValue(String(model.report_chart_legend_position || "Auto").toLowerCase())},
  label_size_pt: ${num(model.report_chart_label_size_pt)},
  data_labels: ${toTypstValue(String(model.report_chart_data_labels || "Auto").toLowerCase())},
  line_stroke_pt: ${num(model.report_chart_line_stroke_pt)},
  marker_size_pt: ${num(model.report_chart_marker_size_pt)},
  accessibility_mode: ${Boolean(model.report_chart_accessibility_mode)},
  negative_color: ${toTypstValue(model.report_negative_color || "#B91C1C")},
  muted_color: ${toTypstValue(model.report_muted_color || "#64748B")},
)`;

  return `#import "@local/crispy-charts:0.1.1": crispy-chart

#set page(
  width: ${page.width}mm,
  height: ${page.height}mm,
  margin: (
    top: ${num(model.margin_top_mm)}mm,
    right: ${num(model.margin_right_mm)}mm,
    bottom: ${num(model.margin_bottom_mm)}mm,
    left: ${num(model.margin_left_mm)}mm,
  ),${pageBackground}${pageForeground}
)

#set text(font: ${toTypstValue(model.field_value_font_family || "Arial")}, size: ${num(model.field_value_font_size_pt)}pt)

#let sectionStyle = ${renderTypstTextStyle(cbpTypographyStyle(model, "section_label"), 14)}
#let fieldLabelStyle = ${renderTypstTextStyle(cbpTypographyStyle(model, "field_label"), 8)}
#let fieldValueStyle = ${renderTypstTextStyle(cbpTypographyStyle(model, "field_value"), 10)}
#let tableHeaderStyle = ${renderTypstTextStyle(cbpTypographyStyle(model, "table_header"), 9)}
#let tableBodyStyle = ${renderTypstTextStyle(cbpTypographyStyle(model, "table_body"), 9)}

#let section(title) = [
  #v(1.75em)
  #text(..sectionStyle)[#title]
  #v(-0.50em)
  #line(length: 100%, stroke: 0.8pt + rgb(${toTypstValue(model.report_accent_color || "#1E3A8A")}))
  #v(0.20em)
]

#let field(label, value) = [
  #text(..fieldLabelStyle)[#label]#linebreak()#text(..fieldValueStyle)[#value]
]

#field[Company][${typstContent(model.company || "Company Name")}]

#v(1.25em)
#text(
  font: ${toTypstValue(model.report_title_font_family || "Arial")},
  size: ${num(model.report_title_font_size_pt)}pt,
  weight: ${toTypstValue(String(model.report_title_font_weight || "bold"))},
  fill: rgb(${toTypstValue(model.report_title_font_color || "#1E293B")}),
)[Financial Statement Title]
#v(0.35em)
#text(size: ${num(model.report_context_font_size_pt)}pt, fill: rgb(${toTypstValue(model.report_context_font_color || "#64748B")}))[Fiscal Year 2026 · KWD]

#section[Account Summary]
#table(
  columns: (1fr, 1.7fr, auto, auto),
  inset: (
    top: ${num(model.table_cell_inset_top_pt)}pt,
    right: ${num(model.table_cell_inset_right_pt)}pt,
    bottom: ${num(model.table_cell_inset_bottom_pt)}pt,
    left: ${num(model.table_cell_inset_left_pt)}pt,
  ),
  stroke: (paint: rgb(${toTypstValue(model.table_border_color || "#E2E8F0")}), thickness: ${num(model.table_border_stroke_width_pt)}pt),
  fill: ${tableFill},
  table.header(
    [#text(..tableHeaderStyle)[Account]],
    [#text(..tableHeaderStyle)[Description]],
    [#align(right)[#text(..tableHeaderStyle)[Balance]]],
    [#text(..tableHeaderStyle)[Class]],
  ),
  ${specimenRows.map((row) => `[#text(..tableBodyStyle)[${typstContent(row.label)}]], [#text(..tableBodyStyle)[${typstContent(row.value)}]], [#align(right)[#text(..tableBodyStyle)[${typstContent(row.amount)}]]], [#text(..tableBodyStyle)[${typstContent(row.status)}]],`).join("\n  ")}
)

#v(0.85em)
#block(width: 100%, fill: rgb(${toTypstValue(model.report_group_fill_color || "#EFF6FF")}), inset: 6pt)[#text(weight: "semibold")[Assets]]
#block(width: 100%, inset: (top: 5pt, right: 6pt, bottom: 5pt, left: ${num(model.report_hierarchy_indent_pt) + 6}pt))[#grid(columns: (1fr, auto), [Cash and Bank], [KWD 125.000])]
#block(width: 100%, fill: rgb(${toTypstValue(model.report_subtotal_fill_color || "#F8FAFC")}), inset: 6pt)[#grid(columns: (1fr, auto), [Subtotal], [KWD 173.000])]
#block(width: 100%, fill: rgb(${toTypstValue(model.report_grand_total_fill_color || "#E2E8F0")}), inset: 6pt)[#grid(columns: (1fr, auto), [#text(weight: "bold")[Grand total]], [#text(weight: "bold", fill: rgb(${toTypstValue(model.report_negative_color || "#B91C1C")}))[-1,250.000]])]
#v(0.45em)
#text(size: ${num(model.report_context_font_size_pt)}pt, weight: "semibold", fill: rgb(${toTypstValue(model.report_warning_color || "#B45309")}))[Warning · Provisional figures]
#linebreak()
#text(size: ${num(model.report_context_font_size_pt)}pt, fill: rgb(${toTypstValue(model.report_muted_color || "#64748B")}))[Comparative figures are unaudited.]

#section[Performance Overview]
#crispy-chart(
  (
    kind: ${toTypstValue(previewChart.kind)},
    labels: (${previewChart.labels.map(toTypstValue).join(", ")},),
    series: (
      ${previewChart.series.join(",\n      ")},
    ),
    options: (:),
    accessibility: (summary: "Quarterly performance comparison across ${chartPalette.length} series."),
  ),
  theme: ${chartTheme},
  width: 100%,
  height: 150pt,
)

#v(0.65em)
#text(size: ${num(model.report_footer_font_size_pt)}pt, fill: rgb(${toTypstValue(model.report_footer_font_color || "#64748B")}))[Report footer · Page 1]
`;
}

function buildPreviewChartSpec(
  kind: CbpPreviewChartKind,
  paletteLength: number,
) {
  const seriesCount = Math.max(1, paletteLength);
  const quarterValues = (index: number) =>
    [18, 24, 20, 29].map(
      (value, quarter) => value + index * 3 + quarter * ((index % 2) + 1),
    );
  const renderSeries = (
    name: string,
    seriesKind: "line" | "bar",
    values: number[],
  ) =>
    `(name: ${toTypstValue(name)}, kind: ${toTypstValue(seriesKind)}, values: (${values.join(", ")},))`;

  if (kind === "horizontal_bar") {
    return {
      kind,
      labels: ["Cash", "Receivables", "Inventory", "Equipment"],
      series: [renderSeries("Balance", "bar", [42, 31, 25, 18])],
    };
  }
  if (kind === "percentage_stacked") {
    const values = [38, 27, 18, 10, 5, 2];
    return {
      kind,
      labels: ["Aging distribution"],
      series: Array.from({ length: seriesCount }, (_item, index) =>
        renderSeries(`Bucket ${index + 1}`, "bar", [
          values[index % values.length],
        ]),
      ),
    };
  }
  if (kind === "waterfall") {
    return {
      kind,
      labels: ["Opening", "Income", "Expenses", "Closing"],
      series: [renderSeries("Movement", "bar", [36, 24, -18, 12])],
    };
  }
  if (kind === "bar") {
    return {
      kind,
      labels: ["Q1", "Q2", "Q3", "Q4"],
      series: [renderSeries("Actual", "bar", quarterValues(0))],
    };
  }

  return {
    kind,
    labels: ["Q1", "Q2", "Q3", "Q4"],
    series: Array.from({ length: seriesCount }, (_item, index) =>
      renderSeries(
        `Series ${index + 1}`,
        kind === "grouped_bar" || (kind === "mixed" && index % 2 === 0)
          ? "bar"
          : "line",
        quarterValues(index),
      ),
    ),
  };
}

function previewModelWithInstalledFonts(
  context: CbpPreviewTypstContext,
): CrispyBrandingProfileDoc {
  const installed = context.installedFonts || [];
  if (!installed.length) return context.model;

  const canonicalFonts = new Map(
    installed.map((font) => [font.trim().toLowerCase(), font]),
  );
  const fallback =
    canonicalFonts.get("inter") ||
    installed.find((font) => font.trim()) ||
    "Inter";
  const model = { ...context.model } as CrispyBrandingProfileDoc;
  for (const field of [
    "section_label_font_family",
    "field_label_font_family",
    "field_value_font_family",
    "table_header_font_family",
    "table_body_font_family",
    "report_title_font_family",
  ]) {
    const requested = String((context.model as any)[field] || "").trim();
    (model as any)[field] =
      canonicalFonts.get(requested.toLowerCase()) || fallback;
  }
  return model;
}

function buildSpecimenDictionary(context: CbpPreviewTypstContext) {
  const { model } = context;
  const profile = {
    name: model.name || context.profileName,
    profile_name: model.profile_name || context.profileName,
    company: model.company || "",
    is_default: context.isDefault,
    code_only: context.effectiveCodeOnly,
  };
  const specimen = {
    page: {
      size: model.page_size || "A4",
      orientation: model.orientation || "portrait",
      margin_top_mm: num(model.margin_top_mm),
      margin_right_mm: num(model.margin_right_mm),
      margin_bottom_mm: num(model.margin_bottom_mm),
      margin_left_mm: num(model.margin_left_mm),
    },
    typography: {
      section_label: cbpTypographySpecimen(model, "section_label"),
      field_label: cbpTypographySpecimen(model, "field_label"),
      field_value: cbpTypographySpecimen(model, "field_value"),
      table_header: cbpTypographySpecimen(model, "table_header"),
      table_body: cbpTypographySpecimen(model, "table_body"),
    },
    table: {
      inset_top_pt: num(model.table_cell_inset_top_pt),
      inset_right_pt: num(model.table_cell_inset_right_pt),
      inset_bottom_pt: num(model.table_cell_inset_bottom_pt),
      inset_left_pt: num(model.table_cell_inset_left_pt),
      border_width_pt: num(model.table_border_stroke_width_pt),
      border_color: model.table_border_color || "#E2E8F0",
      header_fill: model.table_header_background_color || "#F1F5F9",
      striping_enabled: context.tableStriping,
      stripe_fill: model.table_stripe_color || "#F8FAFC",
      rows: specimenRows,
    },
    branding: {
      mode: model.branding_mode || "None",
      logo_source: model.branding_logo_source || "Company logo",
      logo_width_mm: num(model.branding_logo_width_mm),
      logo_offset_x_mm: num(model.branding_logo_offset_x_mm),
      logo_offset_y_mm: num(model.branding_logo_offset_y_mm),
      letterhead_source: context.letterheadSourceLabel,
      letterhead: context.letterheadLabel,
    },
    qr: {
      enabled: context.qrEnabled,
      symbology: model.qr_symbology || "QR Code",
      error_correction: model.qr_error_correction || "Medium",
      quiet_zone: num(model.qr_quiet_zone),
      module_size_pt: num(model.qr_module_size_pt),
      datamatrix_encodation: model.datamatrix_encodation || "",
      datamatrix_symbols: model.datamatrix_symbols || "",
      size_mm: num(model.qr_code_size_mm),
      dx_mm: num(model.qr_dx_mm),
      dy_mm: num(model.qr_dy_mm),
    },
  };
  return `#let profile = ${toTypstValue(profile)}\n#let specimen = ${toTypstValue(specimen)}`;
}

function typstContent(value: any) {
  return `#(${toTypstValue(value)})`;
}

function toTypstValue(value: any): string {
  if (value === null || value === undefined) return `""`;
  if (Array.isArray(value)) {
    return `(${value.map((item) => `${toTypstValue(item)},`).join("")})`;
  }
  if (typeof value === "object") {
    return `(${Object.entries(value)
      .map(([key, entryValue]) => `${key}: ${toTypstValue(entryValue)},`)
      .join("")})`;
  }
  if (typeof value === "number" || typeof value === "boolean")
    return String(value);
  return `"${String(value).replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n/g, "\\n")}"`;
}

function assetFilename(path: string) {
  if (!path) return "";
  const clean = String(path).split("?")[0].split("#")[0];
  const segments = clean.split("/").filter(Boolean);
  return decodeURIComponent(segments[segments.length - 1] || "");
}

function parseChartPalette(value: unknown) {
  const colors = String(value || "")
    .split(",")
    .map((color) => color.trim().toUpperCase())
    .filter((color) => /^#[0-9A-F]{6}$/.test(color))
    .slice(0, 12);
  return colors.length ? colors : defaultReportChartPalette;
}
