import type {
  ReportThemeSettings,
  TableSettings,
} from "./presentation_settings";
import { typstTextStyle } from "../typst/textStyles";
import { escapeTypstString } from "./typstEscape";

export const REPORT_BASIC_SIGNATURE_PREFIX = "CRISPY_REPORT_BASIC_SIGNATURE:";
export const REPORT_BASIC_GENERATOR_VERSION = 4;

export type ReportBuilderMode = "basic" | "advanced";
export type ReportBuilderPreset = "grid" | "tree" | "summary" | "minimal";
export type ColumnAlignStrategy = "auto" | "left" | "center" | "right";
export type ChartRepresentation = "auto" | "bar" | "line" | "horizontal_bar";
export type ReportLayoutStyle =
  | "Standard"
  | "Compact"
  | "Minimal"
  | "Summary Focus";

export interface ReportSectionConfig {
  key: string;
  label: string;
  optional: boolean;
  movable: boolean;
  visible: boolean;
}

export interface ReportBuilderConfig {
  mode: ReportBuilderMode;
  renderer: string;
  preset: ReportBuilderPreset;
  layout_style: ReportLayoutStyle;
  sections: ReportSectionConfig[];
  show_filters: boolean;
  show_summary: boolean;
  include_total_row: boolean;
  show_footer_total: boolean;
  chart_enabled: boolean;
  chart_representation: ChartRepresentation;
  chart_width_percent: number;
  chart_max_height_pt: number;
  chart_card_border: boolean;
  chart_spacing_top_pt: number;
  chart_spacing_bottom_pt: number;
  header_fill: string;
  header_text_weight: string;
  font_family: string;
  font_size_pt: number;
  row_striping: boolean;
  row_stripe_fill: string;
  column_align_strategy: ColumnAlignStrategy;
  table_inset_x_pt: number;
  table_inset_y_pt: number;
  table_stroke_top_pt: number;
  table_stroke_body_pt: number;
  raw_signature: string | null;
  report_table_sync_signature: string | null;
}

interface ReportTypstBuildOptions {
  tableSettings?: TableSettings | null;
  reportTheme?: ReportThemeSettings | null;
  language?: string | null;
}

const RTL_LANGUAGE_PREFIXES = new Set(["ar", "fa", "he", "ur"]);

function normalizeReportLanguage(value: string | null | undefined): string {
  const normalized = String(value || "en")
    .trim()
    .replace(/_/g, "-");
  return normalized || "en";
}

function isRtlReportLanguage(language: string): boolean {
  return RTL_LANGUAGE_PREFIXES.has(language.split("-", 1)[0].toLowerCase());
}

export function getDefaultReportBuilderConfig(
  reportRenderer?: string | null,
): ReportBuilderConfig {
  void reportRenderer;
  const preset: ReportBuilderPreset = "grid";

  return {
    mode: "basic",
    renderer: reportRenderer || "generic_report",
    preset,
    layout_style: "Standard",
    sections: [],
    show_filters: true,
    show_summary: true,
    include_total_row: true,
    show_footer_total: true,
    chart_enabled: true,
    chart_representation: "auto",
    chart_width_percent: 100,
    chart_max_height_pt: 220,
    chart_card_border: false,
    chart_spacing_top_pt: 0,
    chart_spacing_bottom_pt: 12,
    header_fill: "#B3D7FF",
    header_text_weight: "bold",
    font_family: "Inter",
    font_size_pt: 9,
    row_striping: false,
    row_stripe_fill: "#F8FBFF",
    column_align_strategy: "auto",
    table_inset_x_pt: 8,
    table_inset_y_pt: 6,
    table_stroke_top_pt: 1,
    table_stroke_body_pt: 0.5,
    raw_signature: null,
    report_table_sync_signature: null,
  };
}

export function normalizeReportBuilderConfig(
  input: unknown,
  reportRenderer?: string | null,
): ReportBuilderConfig {
  const defaults = getDefaultReportBuilderConfig(reportRenderer);
  const raw = (input && typeof input === "object" ? input : {}) as Record<
    string,
    unknown
  >;

  const mode = raw.mode === "advanced" ? "advanced" : "basic";
  const presetCandidate = String(raw.preset || defaults.preset).toLowerCase();
  const preset: ReportBuilderPreset =
    presetCandidate === "tree" ||
    presetCandidate === "summary" ||
    presetCandidate === "minimal"
      ? (presetCandidate as ReportBuilderPreset)
      : "grid";

  const alignCandidate = String(
    raw.column_align_strategy || defaults.column_align_strategy,
  );
  const column_align_strategy: ColumnAlignStrategy =
    alignCandidate === "left" ||
    alignCandidate === "center" ||
    alignCandidate === "right" ||
    alignCandidate === "auto"
      ? (alignCandidate as ColumnAlignStrategy)
      : "auto";

  const includeTotalRow = toBool(
    raw.include_total_row,
    toBool(raw.show_footer_total, defaults.include_total_row),
  );
  const chartRepresentationCandidate = String(
    raw.chart_representation || defaults.chart_representation,
  )
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_");
  const chart_representation: ChartRepresentation =
    chartRepresentationCandidate === "bar" ||
    chartRepresentationCandidate === "line" ||
    chartRepresentationCandidate === "horizontal_bar"
      ? chartRepresentationCandidate
      : "auto";

  return {
    ...defaults,
    mode,
    renderer: asString(raw.renderer, defaults.renderer),
    preset,
    layout_style: normalizeLayoutStyle(raw.layout_style),
    sections: normalizeSections(raw.sections, defaults.sections),
    show_filters: toBool(raw.show_filters, defaults.show_filters),
    show_summary: toBool(raw.show_summary, defaults.show_summary),
    include_total_row: includeTotalRow,
    show_footer_total: includeTotalRow,
    chart_enabled: toBool(raw.chart_enabled, defaults.chart_enabled),
    chart_representation,
    chart_width_percent: clamp(
      toNumber(raw.chart_width_percent, defaults.chart_width_percent),
      10,
      100,
    ),
    chart_max_height_pt: clamp(
      toNumber(raw.chart_max_height_pt, defaults.chart_max_height_pt),
      60,
      600,
    ),
    chart_card_border: toBool(
      raw.chart_card_border,
      defaults.chart_card_border,
    ),
    chart_spacing_top_pt: clamp(
      toNumber(raw.chart_spacing_top_pt, defaults.chart_spacing_top_pt),
      0,
      120,
    ),
    chart_spacing_bottom_pt: clamp(
      toNumber(raw.chart_spacing_bottom_pt, defaults.chart_spacing_bottom_pt),
      0,
      120,
    ),
    header_fill: asString(raw.header_fill, defaults.header_fill),
    header_text_weight: asString(
      raw.header_text_weight,
      defaults.header_text_weight,
    ),
    font_family: asString(raw.font_family, defaults.font_family),
    font_size_pt: clamp(
      toNumber(raw.font_size_pt, defaults.font_size_pt),
      4,
      96,
    ),
    row_striping: toBool(raw.row_striping, defaults.row_striping),
    row_stripe_fill: asString(raw.row_stripe_fill, defaults.row_stripe_fill),
    column_align_strategy,
    table_inset_x_pt: toNumber(raw.table_inset_x_pt, defaults.table_inset_x_pt),
    table_inset_y_pt: toNumber(raw.table_inset_y_pt, defaults.table_inset_y_pt),
    table_stroke_top_pt: toNumber(
      raw.table_stroke_top_pt,
      defaults.table_stroke_top_pt,
    ),
    table_stroke_body_pt: toNumber(
      raw.table_stroke_body_pt,
      defaults.table_stroke_body_pt,
    ),
    raw_signature:
      typeof raw.raw_signature === "string" && raw.raw_signature.trim()
        ? raw.raw_signature.trim()
        : null,
    report_table_sync_signature:
      typeof raw.report_table_sync_signature === "string" &&
      raw.report_table_sync_signature.trim()
        ? raw.report_table_sync_signature.trim()
        : null,
  };
}

function normalizeLayoutStyle(value: unknown): ReportLayoutStyle {
  const candidate = String(value || "Standard");
  return candidate === "Compact" ||
    candidate === "Minimal" ||
    candidate === "Summary Focus"
    ? candidate
    : "Standard";
}

function normalizeSections(
  value: unknown,
  fallback: ReportSectionConfig[],
): ReportSectionConfig[] {
  if (!Array.isArray(value)) return fallback.map((section) => ({ ...section }));
  return value
    .filter(
      (section) =>
        section &&
        typeof section === "object" &&
        String((section as any).key || ""),
    )
    .map((section: any) => ({
      key: String(section.key),
      label: String(section.label || section.key),
      optional: Boolean(section.optional),
      movable: Boolean(section.movable),
      visible: section.visible !== false,
    }));
}

export function buildReportTypstFromConfig(
  config: ReportBuilderConfig,
  options: ReportTypstBuildOptions = {},
): string {
  const reportLanguage = normalizeReportLanguage(options.language);
  const [reportLanguageCode, reportRegion] = reportLanguage.split("-", 2);
  const reportIsRtl = isRtlReportLanguage(reportLanguage);
  const reportDirection = reportIsRtl ? "rtl" : "ltr";
  const densityScale =
    config.layout_style === "Compact"
      ? 0.85
      : config.layout_style === "Minimal"
        ? 0.92
        : 1;
  const fontSize = Math.max(
    1,
    (Number(config.font_size_pt) || 9) * densityScale,
  );
  const sectionVisible = (key: string) => {
    const section = (config.sections || []).find((item) => item.key === key);
    return !section || section.visible !== false;
  };
  const tableHeaderAlign = resolveHeaderAlign(config.column_align_strategy);
  const tableBodyAlign = resolveBodyAlign(config.column_align_strategy);
  const tableSettings = options.tableSettings || null;
  const reportTheme = options.reportTheme || null;
  const titleFontFamily = asString(
    reportTheme?.title?.fontFamily,
    config.font_family,
  );
  const titleFontSize = formatPt(
    toPointNumber(reportTheme?.title?.fontSize, 16),
  );
  const titleFontWeight = asString(reportTheme?.title?.fontWeight, "bold");
  const titleFontColor = asHexColor(
    reportTheme?.title?.color || "#1e293b",
    "#1e293b",
  );
  const contextFontSize = formatPt(
    toPointNumber(reportTheme?.context?.fontSize, 9),
  );
  const contextFontColor = asHexColor(
    reportTheme?.context?.color || "#64748b",
    "#64748b",
  );
  const footerFontSize = formatPt(
    toPointNumber(reportTheme?.footer?.fontSize, 8),
  );
  const footerFontColor = asHexColor(
    reportTheme?.footer?.color || "#64748b",
    "#64748b",
  );
  const hierarchyIndentPt = toNumber(reportTheme?.hierarchyIndentPt, 10);
  const groupFill = asHexColor(
    reportTheme?.rows?.groupFill || "#eff6ff",
    "#eff6ff",
  );
  const subtotalFill = asHexColor(
    reportTheme?.rows?.subtotalFill || "#f8fafc",
    "#f8fafc",
  );
  const grandTotalFill = asHexColor(
    reportTheme?.rows?.grandTotalFill || "#e2e8f0",
    "#e2e8f0",
  );
  const stripeEnabled = tableSettings
    ? Boolean(tableSettings.stripe.enabled)
    : config.row_striping;
  const stripeFill = asHexColor(
    tableSettings?.stripe?.color || config.row_stripe_fill,
    "#F8FBFF",
  );
  const headerFill = asHexColor(
    tableSettings?.header?.backgroundColor || config.header_fill,
    "#B3D7FF",
  );
  const tableStrokeTopPt = tableSettings
    ? toNumber(tableSettings.stroke?.width, config.table_stroke_top_pt)
    : config.table_stroke_top_pt;
  const tableStrokeBodyPt = tableSettings
    ? toNumber(tableSettings.stroke?.width, config.table_stroke_body_pt)
    : config.table_stroke_body_pt;
  const tableInsetTopPt =
    (tableSettings
      ? toNumber(tableSettings.inset?.top, config.table_inset_y_pt)
      : config.table_inset_y_pt) * densityScale;
  const tableInsetRightPt =
    (tableSettings
      ? toNumber(tableSettings.inset?.right, config.table_inset_x_pt)
      : config.table_inset_x_pt) * densityScale;
  const tableInsetBottomPt =
    (tableSettings
      ? toNumber(tableSettings.inset?.bottom, config.table_inset_y_pt)
      : config.table_inset_y_pt) * densityScale;
  const tableInsetLeftPt =
    (tableSettings
      ? toNumber(tableSettings.inset?.left, config.table_inset_x_pt)
      : config.table_inset_x_pt) * densityScale;
  const headerFontFamily = asString(
    tableSettings?.typography?.header?.fontFamily,
    config.font_family,
  );
  const headerFontSize = formatPt(
    toPointNumber(tableSettings?.typography?.header?.fontSize, fontSize),
  );
  const headerFontStyle = asString(
    tableSettings?.typography?.header?.fontStyle,
    "normal",
  );
  const headerFontWeight = asString(
    tableSettings?.typography?.header?.fontWeight,
    config.header_text_weight,
  );
  const headerFontColor = asHexColor(
    tableSettings?.typography?.header?.color || "#0f172a",
    "#0f172a",
  );
  const headerTextStyle = typstTextStyle(
    {
      fontFamily: headerFontFamily,
      fontSize: headerFontSize,
      fontStyle: headerFontStyle,
      fontWeight: headerFontWeight,
      color: `#${headerFontColor}`,
    },
    fontSize,
  );
  const bodyFontFamily = asString(
    tableSettings?.typography?.body?.fontFamily,
    config.font_family,
  );
  const bodyFontSize = formatPt(
    toPointNumber(tableSettings?.typography?.body?.fontSize, fontSize),
  );
  const bodyFontStyle = asString(
    tableSettings?.typography?.body?.fontStyle,
    "normal",
  );
  const bodyFontWeight = asString(
    tableSettings?.typography?.body?.fontWeight,
    "regular",
  );
  const bodyFontColor = asHexColor(
    tableSettings?.typography?.body?.color || "#0f172a",
    "#0f172a",
  );
  const bodyTextStyle = typstTextStyle(
    {
      fontFamily: bodyFontFamily,
      fontSize: bodyFontSize,
      fontStyle: bodyFontStyle,
      fontWeight: bodyFontWeight,
      color: `#${bodyFontColor}`,
    },
    fontSize,
  );
  const boldBodyTextStyle = typstTextStyle(
    {
      fontFamily: bodyFontFamily,
      fontSize: bodyFontSize,
      fontStyle: bodyFontStyle,
      fontWeight: "bold",
      color: `#${bodyFontColor}`,
    },
    fontSize,
  );

  const lines: string[] = [];
  lines.push("// Generated by Crispy Report Basic Mode");
  lines.push(
    `// CRISPY_REPORT_BASIC_GENERATOR:${REPORT_BASIC_GENERATOR_VERSION}`,
  );
  lines.push("// Edit in Advanced mode for full control.");
  if (config.chart_enabled && sectionVisible("chart")) {
    lines.push('#import "@local/crispy-charts:0.1.1": crispy-chart');
  }
  lines.push(
    `#set text(font: ("${escapeTypstString(config.font_family)}", "Noto Naskh Arabic", "Noto Sans Arabic", "Inter"), size: ${formatPt(fontSize)}, lang: "${escapeTypstString(reportLanguageCode)}"${reportRegion ? `, region: "${escapeTypstString(reportRegion.toUpperCase())}"` : ""}, dir: ${reportDirection})`,
  );
  lines.push("");
  if (sectionVisible("heading")) {
    lines.push("#align(center)[");
    lines.push(
      `  #text(font: "${escapeTypstString(titleFontFamily)}", size: ${titleFontSize}, weight: "${escapeTypstString(titleFontWeight)}", fill: rgb("${titleFontColor}"))[#data.title]`,
    );
    lines.push("  #v(0.3em)");
    lines.push(
      `  #text(size: ${contextFontSize}, fill: rgb("${contextFontColor}"))[#data.subtitle]`,
    );
    lines.push("]");
    lines.push("");
    lines.push("#v(1em)");
    lines.push("");
  }

  if (config.renderer === "receivable_payable") {
    lines.push('#if "filters_map" in data [');
    lines.push(
      '  #align(center)[#text(size: 10pt, weight: "semibold")[#if "party" in data.filters_map { data.filters_map.party }]]',
    );
    lines.push(
      '  #align(center)[#text(size: 8pt)[#if "tax_id" in data.filters_map { [Tax ID: #data.filters_map.tax_id] }]]',
    );
    lines.push(
      '  #align(center)[#text(size: 8pt)[#if "ageing_based_on" in data.filters_map { data.filters_map.ageing_based_on } #h(0.5em) #if "report_date" in data.filters_map { data.filters_map.report_date }]]',
    );
    lines.push("]");
  } else if (config.renderer === "financial_statement") {
    lines.push('#if "filters_map" in data [');
    lines.push(
      '  #align(center)[#text(size: 11pt, weight: "semibold")[#if "company" in data.filters_map { data.filters_map.company }]]',
    );
    lines.push(
      '  #align(center)[#text(size: 8pt)[#if "fiscal_year" in data.filters_map { data.filters_map.fiscal_year } #h(1em) #if "presentation_currency" in data.filters_map { data.filters_map.presentation_currency }]]',
    );
    lines.push("]");
  } else if (config.renderer === "general_ledger") {
    lines.push('#if "filters_map" in data [');
    lines.push(
      '  #align(center)[#text(size: 11pt, weight: "semibold")[#if "party" in data.filters_map { data.filters_map.party } else if "account" in data.filters_map { data.filters_map.account }]]',
    );
    lines.push(
      '  #align(center)[#text(size: 8pt)[#if "from_date" in data.filters_map { data.filters_map.from_date } #h(0.5em)–#h(0.5em) #if "to_date" in data.filters_map { data.filters_map.to_date }]]',
    );
    lines.push("]");
  } else if (config.renderer === "bank_reconciliation") {
    lines.push('#if "filters_map" in data [');
    lines.push(
      '  #align(center)[#text(size: 10pt, weight: "semibold")[#if "account" in data.filters_map { data.filters_map.account }]]',
    );
    lines.push(
      '  #align(center)[#text(size: 8pt)[#if "company" in data.filters_map { data.filters_map.company } #h(1em) #if "report_date" in data.filters_map { data.filters_map.report_date }]]',
    );
    lines.push("]");
  }

  if (config.show_filters && sectionVisible("filters")) {
    lines.push('#if "filters" in data and data.filters.len() > 0 [');
    lines.push("  #block(");
    lines.push('    fill: rgb("f5f5f5"),');
    lines.push("    inset: 10pt,");
    lines.push("    radius: 4pt,");
    lines.push("    width: 100%,");
    lines.push("  )[");
    lines.push('    #text(size: 9pt, weight: "semibold")[Filters:]');
    lines.push("    #v(0.5em)");
    lines.push("    #grid(");
    lines.push("      columns: (auto, 1fr) * 2,");
    lines.push("      column-gutter: 12pt,");
    lines.push("      row-gutter: 6pt,");
    lines.push("      ..data");
    lines.push("        .filters");
    lines.push("        .map(f => (");
    lines.push('          text(size: 8pt, weight: "medium")[#f.label:],');
    lines.push("          text(size: 8pt)[#f.value],");
    lines.push("        ))");
    lines.push("        .flatten()");
    lines.push("    )");
    lines.push("  ]");
    lines.push("  #v(1em)");
    lines.push("]");
    lines.push("");
  }

  if (config.chart_enabled && sectionVisible("chart")) {
    lines.push("// CRISPY-CHART-SECTION v2");
    lines.push(
      '#if "chart_spec" in data and data.chart_spec.engine == "lilaq" [',
    );
    if (config.chart_spacing_top_pt > 0) {
      lines.push(`  #v(${formatPt(config.chart_spacing_top_pt)})`);
    }
    lines.push("    #align(center)[");
    lines.push(
      `      #crispy-chart(data.chart_spec, theme: data.chart_theme, width: ${Math.round(
        config.chart_width_percent,
      )}%, height: ${formatPt(config.chart_max_height_pt)})`,
    );
    lines.push("    ]");
    if (config.chart_spacing_bottom_pt > 0) {
      lines.push(`  #v(${formatPt(config.chart_spacing_bottom_pt)})`);
    }
    lines.push("]");
    lines.push(
      '#if "chart_spec" in data and data.chart_spec.engine == "frappe_svg" and "chart_svg" in data and data.chart_svg != "" [',
    );
    if (config.chart_spacing_top_pt > 0) {
      lines.push(`  #v(${formatPt(config.chart_spacing_top_pt)})`);
    }
    lines.push("  #align(center)[");
    lines.push(
      `    #image(data.chart_svg, width: ${Math.round(
        config.chart_width_percent,
      )}%, height: ${formatPt(config.chart_max_height_pt)}, fit: "contain")`,
    );
    lines.push("  ]");
    if (config.chart_spacing_bottom_pt > 0) {
      lines.push(`  #v(${formatPt(config.chart_spacing_bottom_pt)})`);
    }
    lines.push("]");
    lines.push("// /CRISPY-CHART-SECTION");
    lines.push("");
  }

  if (config.show_summary && sectionVisible("report_summary")) {
    lines.push(
      '#if "report_summary" in data and data.report_summary.len() > 0 [',
    );
    lines.push("  #block(");
    lines.push("    inset: (x: 8pt, y: 6pt),");
    lines.push("    width: 100%,");
    lines.push("  )[");
    lines.push("    #grid(");
    lines.push("      columns: (1fr, auto),");
    lines.push("      column-gutter: 12pt,");
    lines.push("      row-gutter: 4pt,");
    lines.push("      ..data");
    lines.push("        .report_summary");
    lines.push("        .map(item => (");
    lines.push('          text(size: 8pt, weight: "medium")[#item.label],');
    lines.push(
      '          text(size: 8pt, fill: if "color_class" in item and item.color_class == "green" { rgb("#22C55E") } else if "color_class" in item and item.color_class == "red" { rgb("#EF4444") } else if "color_class" in item and item.color_class == "blue" { rgb("#3B82F6") } else { rgb("#0f172a") })[',
    );
    lines.push(
      '            #if "formatted_value" in item and item.formatted_value != "" { item.formatted_value } else { item.value }',
    );
    lines.push("          ],");
    lines.push("        ))");
    lines.push("        .flatten()");
    lines.push("    )");
    lines.push("  ]");
    lines.push("  #v(0.8em)");
    lines.push("]");
    lines.push("");
  }

  if (sectionVisible("table")) {
    lines.push("#let cp_column_width(col) = {");
    lines.push('  if "width_kind" in col {');
    lines.push('    if col.width_kind == "auto" { auto }');
    lines.push('    else if col.width_kind == "fr" { col.width_value * 1fr }');
    lines.push('    else if col.width_kind == "pt" { col.width_value * 1pt }');
    lines.push('    else if col.width_kind == "em" { col.width_value * 1em }');
    lines.push('    else if col.width_kind == "rem" { col.width_value * 1em }');
    lines.push('    else if col.width_kind == "%" { col.width_value * 1% }');
    lines.push('    else if col.width_kind == "cm" { col.width_value * 1cm }');
    lines.push('    else if col.width_kind == "mm" { col.width_value * 1mm }');
    lines.push('    else if col.width_kind == "in" { col.width_value * 1in }');
    lines.push("    else { auto }");
    lines.push("  } else { auto }");
    lines.push("}");
    lines.push("");
    lines.push("#table(");
    lines.push("  columns: data.columns.map(cp_column_width),");
    lines.push("");
    lines.push("  stroke: (x, y) => (");
    lines.push(
      `    top: if y == 0 { ${formatPt(tableStrokeTopPt)} } else { ${formatPt(tableStrokeBodyPt)} },`,
    );
    lines.push(`    bottom: ${formatPt(tableStrokeBodyPt)},`);
    lines.push("    left: 0pt,");
    lines.push("    right: 0pt,");
    lines.push("  ),");
    lines.push("");
    lines.push("  align: (x, y) => {");
    lines.push("    if y == 0 {");
    if (reportIsRtl) {
      lines.push(
        "      if data.columns.at(x).is_numeric { left + horizon } else { right + horizon }",
      );
    } else {
      lines.push(`      ${tableHeaderAlign} + horizon`);
    }
    lines.push("    } else if data.columns.at(x).is_numeric {");
    lines.push(reportIsRtl ? "      left + horizon" : `      ${tableBodyAlign}`);
    lines.push("    } else {");
    lines.push(
      reportIsRtl
        ? "      right + horizon"
        : `      ${tableBodyAlign === "right + horizon" ? "left + horizon" : tableBodyAlign}`,
    );
    lines.push("    }");
    lines.push("  },");
    lines.push("");
    lines.push("  fill: (x, y) => {");
    lines.push('    if y == 0 { rgb("' + headerFill + '") }');
    if (stripeEnabled) {
      lines.push(`    else if calc.even(y) { rgb("${stripeFill}") }`);
    }
    lines.push("  },");
    lines.push("");
    lines.push(
      `  inset: (top: ${formatPt(tableInsetTopPt)}, right: ${formatPt(tableInsetRightPt)}, bottom: ${formatPt(tableInsetBottomPt)}, left: ${formatPt(tableInsetLeftPt)}),`,
    );
    lines.push("");
    lines.push("  table.header(");
    lines.push("    repeat: true,");
    lines.push(
      `    ..data.columns.map(col => text(..${headerTextStyle})[#col.label])`,
    );
    lines.push("  ),");
    lines.push("");
    lines.push("  ..data");
    lines.push("    .rows");
    if (!config.include_total_row) {
      lines.push("    .filter(row => row.is_total_row != true)");
    }
    lines.push("    .enumerate()");
    lines.push("    .map(row_entry => {");
    lines.push("      let row-index = row_entry.at(0)");
    lines.push("      let row = row_entry.at(1)");
    lines.push(
      "      let next-row = if row-index + 1 < data.rows.len() { data.rows.at(row-index + 1) } else { none }",
    );
    lines.push(
      '      let keep-with-next = row.role == "section" or (next-row != none and (next-row.role == "calculation" or next-row.role == "grand_total"))',
    );
    lines.push(
      '      let row-breakable = row.role == "detail" or row.role == "auxiliary" or row.role == "spacer"',
    );
    lines.push(
      `      let row-fill = if row.role == "section" { rgb("${groupFill}") } else if row.role == "calculation" { rgb("${subtotalFill}") } else if row.role == "grand_total" { rgb("${grandTotalFill}") } else { none }`,
    );
    lines.push('      if row.role == "section" {');
    lines.push("        let heading = row.cells.at(0)");
    lines.push(
      `        (table.cell(colspan: data.columns.len(), fill: row-fill, breakable: false)[#block(sticky: true)[#text(..${boldBodyTextStyle})[#heading.value]]],)`,
    );
    lines.push("      } else {");
    lines.push("      row.cells.enumerate().map(cell_entry => {");
    lines.push("        let idx = cell_entry.at(0)");
    lines.push("        let cell = cell_entry.at(1)");
    lines.push("        let cell-dir = if cell.is_numeric { ltr } else { " + reportDirection + " }");
    lines.push("        let content = if row.is_bold {");
    lines.push(`          text(dir: cell-dir, ..${boldBodyTextStyle})[#cell.value]`);
    lines.push("        } else {");
    lines.push(`          text(dir: cell-dir, ..${bodyTextStyle})[#cell.value]`);
    lines.push("        }");
    lines.push(
      '        if idx == 0 and "indent" in row and row.indent != none and row.indent > 0 {',
    );
    lines.push(
      `          table.cell(fill: row-fill, breakable: row-breakable)[#block(sticky: keep-with-next)[#box(inset: (left: row.indent * ${formatPt(hierarchyIndentPt)}))[#content]]]`,
    );
    lines.push("        } else {");
    lines.push(
      "          table.cell(fill: row-fill, breakable: row-breakable)[#block(sticky: keep-with-next)[#content]]",
    );
    lines.push("        }");
    lines.push("      })");
    lines.push("      }");
    lines.push("    })");
    lines.push("    .flatten()");
    lines.push(")");
  }

  if (config.show_footer_total && sectionVisible("footer")) {
    lines.push("");
    lines.push("#v(1em)");
    lines.push("#align(right)[");
    lines.push(
      `  #text(size: ${footerFontSize}, fill: rgb("${footerFontColor}"))[`,
    );
    lines.push("    Total Records: #data.total_rows");
    lines.push("  ]");
    lines.push("]");
  }

  const body = lines.join("\n").trim();
  const signature = computeReportBasicSignature(body);
  return `// ${REPORT_BASIC_SIGNATURE_PREFIX}${signature}\n${body}\n`;
}

export function computeReportBasicSignature(source: string): string {
  const normalized = stripSignature(source);
  let hash = 5381;
  for (let i = 0; i < normalized.length; i += 1) {
    hash = (hash * 33) ^ normalized.charCodeAt(i);
  }
  return (hash >>> 0).toString(16);
}

export function extractReportBasicSignature(source: string): string | null {
  if (!source) return null;
  const firstLine = source.split("\n", 1)[0] || "";
  const marker = `// ${REPORT_BASIC_SIGNATURE_PREFIX}`;
  if (!firstLine.startsWith(marker)) return null;
  const value = firstLine.replace(marker, "").trim();
  return value || null;
}

export function isBasicManagedTypst(
  source: string,
  signature?: string | null,
): boolean {
  if (!source || !source.trim()) return false;
  const embedded = extractReportBasicSignature(source);
  if (!embedded) return false;
  const expected = signature || embedded;
  const actual = computeReportBasicSignature(source);
  return expected === actual;
}

function stripSignature(source: string): string {
  const lines = (source || "").replace(/\r\n/g, "\n").split("\n");
  if (!lines.length) return "";
  const marker = `// ${REPORT_BASIC_SIGNATURE_PREFIX}`;
  const filtered = lines[0].startsWith(marker) ? lines.slice(1) : lines;
  return filtered.join("\n").trim();
}

function toBool(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

function toNumber(value: unknown, fallback: number): number {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

function toPointNumber(value: unknown, fallback: number): number {
  if (typeof value === "string") {
    const match = value.trim().match(/^(-?\d+(?:\.\d+)?)pt$/i);
    if (match) {
      const parsed = Number(match[1]);
      return Number.isFinite(parsed) ? parsed : fallback;
    }
  }
  return toNumber(value, fallback);
}

function asString(value: unknown, fallback: string): string {
  return typeof value === "string" && value.trim() ? value.trim() : fallback;
}

function formatPt(value: number): string {
  const num = Number.isFinite(value) ? value : 0;
  return `${Math.max(0, num)}pt`;
}

function asHexColor(value: string, fallback: string): string {
  const raw = String(value || "").trim();
  const withHash = raw.startsWith("#") ? raw : `#${raw}`;
  return /^#[0-9a-fA-F]{6}$/.test(withHash)
    ? withHash.slice(1)
    : fallback.replace("#", "");
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function resolveHeaderAlign(strategy: ColumnAlignStrategy): string {
  switch (strategy) {
    case "left":
      return "left";
    case "right":
      return "right";
    case "center":
      return "center";
    default:
      return "center";
  }
}

function resolveBodyAlign(strategy: ColumnAlignStrategy): string {
  switch (strategy) {
    case "left":
      return "left + horizon";
    case "center":
      return "center + horizon";
    case "right":
      return "right + horizon";
    default:
      return "right + horizon";
  }
}
