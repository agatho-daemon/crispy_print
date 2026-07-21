import { ref, type Ref } from "vue";
import { getLogger } from "../logger";
import {
  default_presentation_settings,
  merge_presentation_settings,
  type PresentationSettings,
} from "../utils/presentation_settings";
import type {
  ReportBuilderConfig,
  ReportBuilderMode,
} from "../utils/reportBuilder";
import { dispatchCrispyPreviewSource } from "../utils/events";
import { escapeTypstString } from "../utils/typstEscape";
import {
  compileReportPreview as compileReportPreviewApi,
  type TypstCompileResult,
} from "../api/crispy";

const logger = getLogger({ module: "ReportStore" });

type ColumnConfig = Array<{ fieldname: string; width: string }>;

interface CreateReportStoreOptions {
  formatName: Ref<string | null>;
  presentation_settings: Ref<PresentationSettings>;
  letterhead: Ref<any>;
  typstCode: Ref<string>;
  reportBuilderConfig: Ref<ReportBuilderConfig>;
  reportBuilderMode: Ref<ReportBuilderMode>;
  selectedReportName: Ref<string>;
  isReportMode: Ref<boolean>;
  reportColumns: Ref<any[]>;
  reportFilterFields: Ref<any[]>;
  reportFilters: Ref<Record<string, any>>;
  reportPreviewData: Ref<Record<string, any> | null>;
  reportPreviewReady: Ref<boolean>;
  getReportColumnConfigFromLayout: () => ColumnConfig;
  getEffectiveCompany: () => string | null;
  getFormatCompany: () => string | null;
	getPdfStandard: () => string | null;
}

export function createReportStore(options: CreateReportStoreOptions) {
  const {
    formatName,
    presentation_settings,
    letterhead,
    typstCode,
    reportBuilderConfig,
    reportBuilderMode,
    selectedReportName,
    isReportMode,
    reportColumns,
    reportFilterFields,
    reportFilters,
    reportPreviewData,
    reportPreviewReady,
    getReportColumnConfigFromLayout,
    getEffectiveCompany,
    getFormatCompany,
	getPdfStandard,
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
        Math.round(
          Number(reportBuilderConfig.value.chart_width_percent) || 100,
        ),
      ),
    );
    const height = Math.max(
      60,
      Math.min(
        600,
        Math.round(
          Number(reportBuilderConfig.value.chart_max_height_pt) || 220,
        ),
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
    if (!reportName || reportName === "Style Preview") {
      reportColumns.value = [];
      reportPreviewData.value = null;
      return;
    }
    const response = await frappe.call({
      method: "crispy_print.api.v1.get_sample_report_data",
      args: {
        report: reportName,
        filters,
        limit: 0,
        store_snapshot: 1,
      },
    });
    const previewData = response?.message || null;
    reportPreviewData.value = previewData;
    reportColumns.value = previewData?.columns || [];
  }

  function invalidateReportPreviewData() {
    reportPreviewData.value = null;
    reportPreviewReady.value = false;
  }

  async function loadReportFilterFields(reportName: string) {
    if (!reportName || reportName === "Style Preview") {
      reportFilterFields.value = [];
      return;
    }
    const definitions =
      await frappe.report_utils.get_report_filters(reportName);
    reportFilterFields.value = Array.isArray(definitions)
      ? definitions.filter((field: any) => field?.fieldname && !field?.hidden)
      : [];
    const defaults: Record<string, any> = {};
    for (const field of reportFilterFields.value) {
      if (
        field.default !== undefined &&
        field.default !== null &&
        field.default !== ""
      ) {
        defaults[field.fieldname] = field.default;
      }
    }
    if (
      reportFilterFields.value.some(
        (field: any) => field.fieldname === "company",
      )
    ) {
      defaults.company =
        getFormatCompany() || getEffectiveCompany() || defaults.company || "";
    }
    reportFilters.value = defaults;
  }

  async function loadSampleReports() {
    selectedReportName.value = "";
    invalidateReportPreviewData();
  }

  async function setSelectedReport(
    name: string,
    options: { refreshKey?: boolean; promptOnCustomized?: boolean } = {},
  ) {
    void options;
    selectedReportName.value = name || "";
    invalidateReportPreviewData();
    await loadReportFilterFields(selectedReportName.value);
    reportColumns.value = [];
  }

  async function compileReportPreview(
    reportName: string,
    columnConfig: any[] = [],
  ): Promise<
    | (TypstCompileResult & {
        typst_source?: string;
        truncation?: Record<string, any>;
        asset_files?: string[];
        chart_spec?: Record<string, any>;
        chart_render?: import("../api/crispy").ReportChartRender;
      })
    | null
  > {
    try {
      logger.info("Building report source", reportName);

      const previewSnapshotId = String(
        reportPreviewData.value?.preview_snapshot_id || "",
      );
      if (!previewSnapshotId) {
        throw new Error("Run Preview to load report data before compiling");
      }

      const effectiveColumnConfig =
        Array.isArray(columnConfig) && columnConfig.length
          ? columnConfig
          : getReportColumnConfigFromLayout();
      const includeFilters = Boolean(reportBuilderConfig.value.show_filters);
      const orientation =
        presentation_settings.value?.page?.orientation || "landscape";
      const presentation_settings_payload = merge_presentation_settings(
        default_presentation_settings,
        presentation_settings.value || {},
      );
      presentation_settings_payload.report = { ...reportBuilderConfig.value };
      const configured_branding_mode = String(
        presentation_settings.value?.branding?.mode ||
          presentation_settings_payload.branding?.mode ||
          "",
      ).toLowerCase();
      const branding_mode =
        configured_branding_mode === "letterhead" ||
        configured_branding_mode === "logo" ||
        configured_branding_mode === "logo_letterhead"
          ? configured_branding_mode
          : presentation_settings_payload.branding?.letterhead
            ? "letterhead"
            : presentation_settings_payload.branding?.logo?.image
              ? "logo"
              : "none";
      const letterhead_image =
        branding_mode === "letterhead" || branding_mode === "logo_letterhead"
          ? letterhead.value?.image || null
          : null;
      const logo_image =
        branding_mode === "logo" || branding_mode === "logo_letterhead"
          ? presentation_settings_payload.branding?.logo?.image || null
          : null;
      const branding_asset_files = [letterhead_image, logo_image].filter(
        (value): value is string => Boolean(value),
      );
      const typst_preamble_override = buildReportFontPreambleOverride();
      const formatCompany = getFormatCompany();
      const previewFilters = { ...(reportFilters.value || {}) };
      if (
        formatCompany &&
        reportFilterFields.value.some(
          (field: any) => field?.fieldname === "company",
        )
      ) {
        previewFilters.company = formatCompany;
        reportFilters.value = previewFilters;
      }
      const result = await compileReportPreviewApi({
        report: reportName,
        format_name: formatName.value,
        format_company: formatCompany,
        filters: previewFilters,
        column_config: effectiveColumnConfig,
        include_filters: includeFilters ? 1 : 0,
		include_summary: reportBuilderConfig.value.show_summary ? 1 : 0,
		include_total_row: reportBuilderConfig.value.include_total_row ? 1 : 0,
        orientation,
        chart_svg: null,
        typst_preamble_override: typst_preamble_override,
        typst_code_override: buildReportTypstOverrideForPreview(
          typstCode.value || "",
        ),
        presentation_settings: {
          ...presentation_settings_payload,
          branding: {
            ...presentation_settings_payload.branding,
            letterhead_image: letterhead_image || "",
          },
        },
        preview_snapshot_id: previewSnapshotId,
        limit: 0,
        asset_files: branding_asset_files,
		pdf_standard: getPdfStandard(),
      });

      const typst_source = result?.typst_source || "";
      if (!typst_source) {
        throw new Error("No Typst source returned");
      }
      dispatchCrispyPreviewSource({ source: typst_source });

      logger.info("Compilation result", result);
      return result || null;
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
    invalidateReportPreviewData,
  };
}
