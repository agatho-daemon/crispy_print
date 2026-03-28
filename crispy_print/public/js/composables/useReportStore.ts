import { ref, type Ref } from "vue";
import { getLogger } from "../logger";
import type { PageSettings } from "../utils/pageSettings";
import type {
  ReportBuilderConfig,
  ReportBuilderMode,
} from "../utils/reportBuilder";
import {
  buildDummyReportPreviewData,
  getDummyReportFilterColumns,
  getDummyReportTableColumns,
  renderDummyReportChartSvg,
} from "../utils/reportPreviewDummy";
import { dispatchCrispyPreviewSource } from "../utils/events";

const DEFAULT_REPORT_PREVIEW_LIMIT = 50;
const logger = getLogger({ module: "ReportStore" });

type ColumnConfig = Array<{ fieldname: string; width: string }>;

interface CreateReportStoreOptions {
  formatName: Ref<string | null>;
  pageSettings: Ref<PageSettings>;
  letterhead: Ref<any>;
  typstCode: Ref<string>;
  reportBuilderConfig: Ref<ReportBuilderConfig>;
  reportBuilderMode: Ref<ReportBuilderMode>;
  selectedReportName: Ref<string>;
  isReportMode: Ref<boolean>;
  reportColumns: Ref<any[]>;
  reportFilterFields: Ref<any[]>;
  reportFilters: Ref<Record<string, any>>;
  getReportColumnConfigFromLayout: () => ColumnConfig;
  getReportTableColumnsForPreview: () => any[];
}

function escapeTypstString(value: string): string {
  return String(value || "").replace(/"/g, '\\"');
}

export function createReportStore(options: CreateReportStoreOptions) {
  const {
    formatName,
    pageSettings,
    letterhead,
    typstCode,
    reportBuilderConfig,
    reportBuilderMode,
    selectedReportName,
    isReportMode,
    reportColumns,
    reportFilterFields,
    reportFilters,
    getReportColumnConfigFromLayout,
    getReportTableColumnsForPreview,
  } = options;

  function buildReportFontPreambleOverride(): string {
    const config = reportBuilderConfig.value;
    const fontFamily = String(config?.font_family || "").trim();
    if (!fontFamily) return "";
    const fontSize = Number(config?.font_size_pt);
    const safeSize = Number.isFinite(fontSize) && fontSize > 0 ? fontSize : 9;
    return `#set text(font: "${escapeTypstString(fontFamily)}", size: ${safeSize}pt)`;
  }

  function buildReportTypstOverrideForPreview(source: string): string {
    const rawSource = String(source || "");
    if (!rawSource.trim()) return rawSource;
    if (!isReportMode.value) return rawSource;
    if (reportBuilderMode.value !== "advanced") return rawSource;
    if (!rawSource.includes("data.chart_svg")) return rawSource;

    const width = Math.max(
      10,
      Math.min(
        100,
        Math.round(Number(reportBuilderConfig.value.chart_width_percent) || 100),
      ),
    );
    const height = Math.max(
      60,
      Math.min(
        600,
        Math.round(Number(reportBuilderConfig.value.chart_max_height_pt) || 220),
      ),
    );

    return rawSource.replace(
      /#image\(data\.chart_svg,\s*width:\s*[^,)\n]+(?:,\s*height:\s*[^)\n]+)?\)/g,
      `#align(center)[#image(data.chart_svg, width: ${width}%, height: ${height}pt, fit: "contain")]`,
    );
  }

  async function loadReportColumns(
    reportName: string,
    filters: Record<string, any> = {},
  ) {
    void reportName;
    void filters;
    reportColumns.value = getDummyReportTableColumns();
  }

  async function loadReportFilterFields(reportName: string) {
    void reportName;
    reportFilterFields.value = getDummyReportFilterColumns().map((col) => ({
      fieldname: col.fieldname,
      label: col.label,
      fieldtype: col.fieldtype || "Data",
      reqd: false,
    }));
  }

  async function loadSampleReports() {
    selectedReportName.value = "Style Preview";
  }

  async function setSelectedReport(
    name: string,
    options: { refreshKey?: boolean; promptOnCustomized?: boolean } = {},
  ) {
    void name;
    void options;
    selectedReportName.value = "Style Preview";
    await loadReportFilterFields("Style Preview");
    await loadReportColumns("Style Preview", {});
  }

  async function compileReportPreview(
    reportName: string,
    columnConfig: any[] = [],
  ) {
    try {
      logger.info("Building report source", reportName);

      const effectiveColumnConfig =
        Array.isArray(columnConfig) && columnConfig.length
          ? columnConfig
          : getReportColumnConfigFromLayout();
      const includeFilters = Boolean(reportBuilderConfig.value.show_filters);
      const orientation = pageSettings.value?.orientation || "landscape";
      const pageSettingsPayload = {
        ...pageSettings.value,
        report_builder: { ...reportBuilderConfig.value },
      };
      const configuredBrandingMode = String(
        pageSettings.value?.brandingMode || "",
      ).toLowerCase();
      const brandingMode =
        configuredBrandingMode === "letterhead" ||
        configuredBrandingMode === "logo"
          ? configuredBrandingMode
          : pageSettings.value?.letterhead
            ? "letterhead"
            : pageSettings.value?.logo?.image
              ? "logo"
              : "none";
      const letterheadImage =
        brandingMode === "letterhead" ? letterhead.value?.image || null : null;
      const logoImage =
        brandingMode === "logo" ? pageSettings.value?.logo?.image || null : null;
      const typstPreambleOverride = buildReportFontPreambleOverride();
      const tableColumns = getReportTableColumnsForPreview();
      const previewData = buildDummyReportPreviewData({
        title: reportName || selectedReportName.value || "Style Preview",
        includeFilters,
        includeSummary: Boolean(reportBuilderConfig.value.show_summary),
        includeTotalRow: Boolean(reportBuilderConfig.value.include_total_row),
        tableColumns,
        columnConfig: effectiveColumnConfig,
      });
      const chartEnabled = Boolean(reportBuilderConfig.value.chart_enabled);
      const previewChartSvg = chartEnabled
        ? await renderDummyReportChartSvg({
            height: Math.max(
              140,
              Math.min(
                600,
                Math.round(
                  Number(reportBuilderConfig.value.chart_max_height_pt) || 220,
                ),
              ),
            ),
            axisOptions: {
              yAxisMode: "span",
            },
          })
        : null;
      const previewDataPayload = {
        ...previewData,
        chart_svg: previewChartSvg ? "report_chart.svg" : "",
      };

      const sourceResponse = await frappe.call({
        method: "crispy_print.api.v1.get_report_typst_source",
        args: {
          report: reportName || "Style Preview",
          format_name: formatName.value,
          filters: reportFilters.value || {},
          column_config: effectiveColumnConfig,
          include_filters: includeFilters ? 1 : 0,
          orientation,
          page_settings: pageSettingsPayload,
          chart_svg: null,
          typst_preamble_override: typstPreambleOverride,
          typst_code_override: buildReportTypstOverrideForPreview(
            typstCode.value || "",
          ),
          preview_data: previewDataPayload,
          letterhead_image: letterheadImage,
          limit: DEFAULT_REPORT_PREVIEW_LIMIT,
        },
      });

      const sourcePayload = sourceResponse?.message;
      const typstSource =
        typeof sourcePayload === "string"
          ? sourcePayload
          : sourcePayload?.typst_source;
      if (!typstSource) {
        throw new Error("No Typst source returned");
      }
      dispatchCrispyPreviewSource({ source: typstSource });

      logger.info("Compiling to SVG");

      const compileResponse = await frappe.call({
        method: "crispy_print.api.v1.compile_typst",
        args: {
          typst_source: typstSource,
          output_format: "svg",
          letterhead_image: letterheadImage,
          logo_image: logoImage,
          chart_svg: previewChartSvg,
        },
      });

      logger.info("Compilation result", compileResponse?.message);
      return compileResponse?.message || null;
    } catch (error) {
      logger.error("Failed to compile report preview", error);
      throw error;
    }
  }

  return {
    loadReportColumns,
    loadReportFilterFields,
    loadSampleReports,
    setSelectedReport,
    compileReportPreview,
  };
}

