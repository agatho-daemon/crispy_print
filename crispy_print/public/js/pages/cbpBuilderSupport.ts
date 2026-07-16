import type { CrispyBrandingProfileDoc } from "../api/crispy";
import cbpCodeOnlyTemplate from "../templates/cbp_code_only_template.json";

export const showCodeMode = false;
export const pageSizes = [
  "A3",
  "A4",
  "A5",
  "Letter",
  "Legal",
  "Tabloid",
  "Executive",
];

export const defaultCodeOnlyTypst = String(cbpCodeOnlyTemplate.template || "");
export const defaultReportChartPalette = [
  "#1E3A8A",
  "#2563EB",
  "#0F766E",
  "#B45309",
  "#7C3AED",
  "#BE123C",
];
const codeReferenceComment = defaultCodeOnlyTypst.split("*/")[0] + "*/";

export const specimenRows = [
  {
    label: "Row 1",
    value: "Cell 1",
    amount: "KWD 125.000",
    status: "Open",
  },
  {
    label: "Row 2",
    value: "Cell 2",
    amount: "KWD 48.000",
    status: "Pending",
  },
  {
    label: "Row 3",
    value: "Cell 3",
    amount: "KWD 6.500",
    status: "Closed",
  },
];

export function createFallbackModel(
  profileName: string,
): CrispyBrandingProfileDoc {
  return {
    name: profileName,
    profile_name: profileName,
    company: "",
    is_default: 0,
    code_only: 0,
    custom_typst_code: defaultCodeOnlyTypst,
    page_size: "A4",
    orientation: "portrait",
    margin_top_mm: 20,
    margin_bottom_mm: 20,
    margin_left_mm: 20,
    margin_right_mm: 20,
    section_label_font_family: "Arial",
    section_label_font_size_pt: 14,
    section_label_font_style: "normal",
    section_label_font_weight: "bold",
    section_label_font_color: "#000000",
    field_label_font_family: "Arial",
    field_label_font_size_pt: 8,
    field_label_font_style: "normal",
    field_label_font_weight: "semibold",
    field_label_font_color: "#64748B",
    field_value_font_family: "Arial",
    field_value_font_size_pt: 10,
    field_value_font_style: "normal",
    field_value_font_weight: "regular",
    field_value_font_color: "#000000",
    table_cell_inset_top_pt: 5,
    table_cell_inset_right_pt: 5,
    table_cell_inset_bottom_pt: 5,
    table_cell_inset_left_pt: 5,
    table_border_stroke_width_pt: 0.5,
    table_border_color: "#E2E8F0",
    table_header_background_color: "#F1F5F9",
    table_row_striping: 0,
    table_stripe_color: "#F8FAFC",
    table_header_font_family: "Arial",
    table_header_font_size_pt: 9,
    table_header_font_style: "normal",
    table_header_font_weight: "semibold",
    table_header_font_color: "#000000",
    table_body_font_family: "Arial",
    table_body_font_size_pt: 9,
    table_body_font_style: "normal",
    table_body_font_weight: "regular",
    table_body_font_color: "#000000",
    report_title_font_family: "Arial",
    report_title_font_size_pt: 18,
    report_title_font_weight: "bold",
    report_title_font_color: "#1E293B",
    report_context_font_size_pt: 9,
    report_context_font_color: "#64748B",
    report_footer_font_size_pt: 8,
    report_footer_font_color: "#64748B",
    report_accent_color: "#1E3A8A",
    report_muted_color: "#64748B",
    report_negative_color: "#B91C1C",
    report_warning_color: "#B45309",
    report_group_fill_color: "#EFF6FF",
    report_subtotal_fill_color: "#F8FAFC",
    report_grand_total_fill_color: "#E2E8F0",
    report_hierarchy_indent_pt: 10,
    report_chart_palette: defaultReportChartPalette.join(", "),
    branding_mode: "None",
    branding_logo_source: "Company logo",
    branding_logo_width_mm: 20,
    branding_logo_offset_x_mm: 0,
    branding_logo_offset_y_mm: 0,
    branding_letterhead_source: "Use System Letterhead",
    enable_qr_code: 0,
    qr_symbology: "QR Code",
    qr_error_correction: "Medium",
    qr_quiet_zone: 1,
    qr_module_size_pt: 3,
    datamatrix_encodation: "",
    datamatrix_symbols: "",
    qr_code_size_mm: 20,
    qr_dx_mm: 0,
    qr_dy_mm: 0,
  };
}

export function ensureCodeReference(source: string) {
  const code = String(source || "").trim();
  if (!code) return defaultCodeOnlyTypst;
  if (
    code.includes(
      "CBP code-only template for the Branding Profile Specimen preview",
    ) ||
    code.includes("CBP code-only template for the dummy e-invoice preview") ||
    code.includes("CBP dummy e-invoice data available in code-only preview")
  ) {
    return source;
  }
  return `${codeReferenceComment}\n\n${source}`;
}

export function pageDimensions(pageSize: string, orientation: string) {
  const sizes: Record<string, { width: number; height: number }> = {
    A3: { width: 297, height: 420 },
    A4: { width: 210, height: 297 },
    A5: { width: 148, height: 210 },
    Letter: { width: 216, height: 279 },
    Legal: { width: 216, height: 356 },
    Tabloid: { width: 279, height: 432 },
    Executive: { width: 184, height: 267 },
  };
  const size = sizes[pageSize] || sizes.A4;
  if (orientation === "landscape")
    return { width: size.height, height: size.width };
  return size;
}

export function num(value: any) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : 0;
}
