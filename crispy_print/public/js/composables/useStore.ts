// composables/useStore.ts
// State management for Crispy Print Format Builder

import { ref, computed, watch, nextTick } from "vue";
import { serializeLayout } from "../utils/layout";
import type { CrispyLayout, DocField, TableColumn } from "../utils/layout";
import {
  defaultTableSettings,
  default_presentation_settings,
  merge_presentation_settings,
  ensure_qr_settings,
  ensure_table_settings,
  type PresentationSettings,
} from "../utils/presentation_settings";
import {
  parseCrispyFormatDoc,
  clearLetterheadCache,
} from "../utils/formatLoader";
import { resolve_effective_presentation_settings } from "../utils/effectivePresentationSettings";
import {
  getCrispyFormat,
  getApplicableTypstBlocks,
  getDefaultReportBuilderConfig as getServerReportBuilderConfig,
  getCrispyTemplatePublishPreview,
  duplicateCrispyFormatForCompany,
  duplicateCrispyTemplateForCompany,
  publishTemplateFromCrispyFormat,
  createCrispyFormat,
  saveCrispyFormat,
  type CrispyFormatDuplicateResult,
  type CrispyTemplateDuplicateResult,
  type CrispyTemplatePublishPreview,
  type CrispyTemplatePublishResult,
  type CrispyTypstBlockOption,
} from "../api/crispy";
import { withDoctype } from "../api/frappe";
import { getLogger } from "../logger";
import {
  buildReportTypstFromConfig,
  computeReportBasicSignature,
  getDefaultReportBuilderConfig,
  normalizeReportBuilderConfig,
  type ReportBuilderMode,
  type ReportBuilderConfig,
} from "../utils/reportBuilder";
import { createReportStore } from "./useReportStore";
import { createLayoutStore } from "./useLayoutStore";
import { createSettingsStore } from "./useSettingsStore";

let storeInstance: ReturnType<typeof buildStore> | null = null;
const MAX_HISTORY_ENTRIES = 100;
const MAX_HISTORY_BYTES = 8 * 1024 * 1024;
const HISTORY_DEBOUNCE_MS = 250;
const PREVIEW_DEBOUNCE_MS = 350;
const REPORT_PREVIEW_DEBOUNCE_MS = 650;

const logger = getLogger({ module: "Store" });

interface CrispyFormat {
  name: string;
  __islocal?: number;
  doc_type?: string;
  // TODO: investigate the possibility of having a dynamic crispy_format_type for future.
  crispy_format_type?: string;
  report?: Array<{ report: string; disabled?: number }>;
  contract?: string;
  company?: string;
  is_default?: number;
  report_scope?: "All Compatible Reports" | "Selected Reports";
  report_renderer?: string;
  report_source_fingerprint?: string;
  doc_header?: string;
  doc_footer?: string;
  raw_typst?: number;
  typst_preamble?: string;
  typst_code?: string;
  pdf_standard?: string;
  default_print_language?: string;
  layout_json?: string;
  presentation_settings?: string;
  compact_item_print?: number;
  print_uom_after_quantity?: number;
  print_taxes_with_zero_amount?: number;
  __onload?: any;
}

export type PreviewRefreshPolicy = "auto" | "live" | "debounce" | "none";

export interface MarkDirtyOptions {
  preview?: PreviewRefreshPolicy;
}

function buildStore() {
  // State
  const crispyFormat = ref<CrispyFormat | null>(null);
  const builderContext = ref<Record<string, any>>({});
  const layout = ref<CrispyLayout | null>(null);
  const meta = ref<any>(null);
  const fields = ref<DocField[]>([]);
  const typstBlocks = ref<CrispyTypstBlockOption[]>([]);
  const reportColumns = ref<any[]>([]);
  const reportFilterFields = ref<any[]>([]);
  const reportFilters = ref<Record<string, any>>({});
  const reportPreviewData = ref<Record<string, any> | null>(null);
  const reportPreviewReady = ref(false);
  const sampleReports = ref<any[]>([]);
  const selectedReportName = ref("");
  const letterhead = ref<any>(null);
  const dirty = ref(false);
  const loading = ref(false);
  const initializing = ref(false); // Prevents dirty marking during init
  const previewRevision = ref(0);
  const rawTypst = ref(false);
  const typstCode = ref("");
  const reportBuilderConfig = ref<ReportBuilderConfig>(
    getDefaultReportBuilderConfig(),
  );
  const reportBasicReadOnly = ref(false);
  const reportModeNotice = ref("");
  const reportRendererMetadata = ref<any>(null);
  const presentation_settings = ref<PresentationSettings>(
    merge_presentation_settings(default_presentation_settings, {}),
  );
  const effective_presentation_settings = ref<PresentationSettings>(
    merge_presentation_settings(default_presentation_settings, {}),
  );
  const historyPast = ref<string[]>([]);
  const historyFuture = ref<string[]>([]);
  // True while a debounced history checkpoint is pending; canUndo consults this
  // so callers (and existing tests) see the change immediately after markDirty.
  const pendingHistoryCheckpoint = ref(false);
  const savedSnapshot = ref("");
  let savedSnapshotHash = "";
  const historyPastHashes = ref<string[]>([]);
  const historyFutureHashes = ref<string[]>([]);
  const applyingHistory = ref(false);
  const settingsStore = createSettingsStore({
    loading,
    initializing,
    dirty,
    letterhead,
    builderContext,
    requestPreviewRefresh,
  });

  // Computed
  const formatName = computed(() =>
    crispyFormat.value?.__islocal ? null : crispyFormat.value?.name || null,
  );
  const docType = computed(() => crispyFormat.value?.doc_type || null);
  const formatCompany = computed(() =>
    String(crispyFormat.value?.company || "").trim(),
  );
  const formatType = computed(
    () => crispyFormat.value?.crispy_format_type || "DocType",
  );
  const isReportMode = computed(() => formatType.value === "Report");
  const previewTriggerMode = computed<"manual" | "live">(() =>
    rawTypst.value ? "manual" : "live",
  );
  const reportCandidates = computed(() => sampleReports.value || []);
  const reportBaseFields = computed<DocField[]>(() => {
    if (!isReportMode.value) return [];
    return [
      { fieldname: "data.title", label: __("Title"), fieldtype: "Data" },
      { fieldname: "data.subtitle", label: __("Subtitle"), fieldtype: "Data" },
      { fieldname: "data.filters", label: __("Filters"), fieldtype: "Table" },
      {
        fieldname: "data.report_summary",
        label: __("Report Summary"),
        fieldtype: "Table",
      },
      {
        fieldname: "data.chart",
        label: __("Chart"),
        fieldtype: "Table",
      },
      {
        fieldname: "data.table",
        label: __("Report Table"),
        fieldtype: "Table",
      },
    ];
  });
  const reportBuilderFields = computed<DocField[]>(() => [
    ...reportBaseFields.value,
  ]);
  const reportBuilderMode = computed<ReportBuilderMode>({
    get: () => reportBuilderConfig.value.mode,
    set: (nextMode) => {
      updateReportBuilderConfig({ mode: nextMode }, { preview: "live" });
      if (!isReportMode.value) return;
      reportBasicReadOnly.value = false;
      reportModeNotice.value = "";
      rawTypst.value = nextMode === "advanced";
      if (crispyFormat.value) {
        crispyFormat.value.raw_typst = nextMode === "advanced" ? 1 : 0;
      }
    },
  });
  const docHeader = computed(() => crispyFormat.value?.doc_header || "");
  const docFooter = computed(() => crispyFormat.value?.doc_footer || "");
  const qrEnabled = computed(() => {
    const qr = effective_presentation_settings.value?.qr;
    if (qr && typeof qr.enabled === "boolean") {
      return qr.enabled;
    }
    return false;
  });
  const typstPreamble = computed(
    () => crispyFormat.value?.typst_preamble || "",
  );
  const canUndo = computed(
    () => historyPast.value.length > 1 || pendingHistoryCheckpoint.value,
  );
  const canRedo = computed(() => historyFuture.value.length > 0);

  function hashSnapshot(snapshot: string): string {
    let hash = 5381;
    for (let i = 0; i < snapshot.length; i += 1) {
      hash = (hash * 33) ^ snapshot.charCodeAt(i);
    }
    return (hash >>> 0).toString(16);
  }

  function assignReportBuilderConfigToPresentationSettings() {
    const nextReport = { ...reportBuilderConfig.value };
    const currentReport = presentation_settings.value.report;
    if (
      currentReport &&
      JSON.stringify(currentReport) === JSON.stringify(nextReport)
    ) {
      return false;
    }
    presentation_settings.value.report = nextReport;
    return true;
  }

  function normalizeReportBuilderConfigLinks(
    config: ReportBuilderConfig,
    patch: Partial<ReportBuilderConfig>,
  ) {
    if (
      Object.prototype.hasOwnProperty.call(patch, "include_total_row") &&
      !Object.prototype.hasOwnProperty.call(patch, "show_footer_total")
    ) {
      config.show_footer_total = config.include_total_row;
    }
  }

  function updateReportBuilderConfig(
    patch: Partial<ReportBuilderConfig>,
    options: MarkDirtyOptions = {},
  ) {
    const nextConfig = {
      ...reportBuilderConfig.value,
      ...patch,
    };
    normalizeReportBuilderConfigLinks(nextConfig, patch);
    reportBuilderConfig.value = nextConfig;
    assignReportBuilderConfigToPresentationSettings();
    if (
      isReportMode.value &&
      reportBuilderConfig.value.mode === "basic" &&
      !reportBasicReadOnly.value
    ) {
      syncReportBasicTypst();
    }
    markDirty({ preview: options.preview || "auto" });
  }

  function buildHistorySnapshot(): string {
    return JSON.stringify({
      layout: layout.value || null,
      presentation_settings: presentation_settings.value || null,
      typstCode: typstCode.value || "",
      rawTypst: Boolean(rawTypst.value),
      reportBuilderConfig: reportBuilderConfig.value || null,
      printBehavior: {
        compact_item_print: Number(crispyFormat.value?.compact_item_print || 0),
        print_uom_after_quantity: Number(
          crispyFormat.value?.print_uom_after_quantity || 0,
        ),
        print_taxes_with_zero_amount: Number(
          crispyFormat.value?.print_taxes_with_zero_amount || 0,
        ),
      },
    });
  }

  function applyHistorySnapshot(snapshot: string) {
    const parsed = JSON.parse(snapshot || "{}");
    const snapshotHash = hashSnapshot(snapshot);
    applyingHistory.value = true;
    try {
      layout.value = parsed.layout || null;
      presentation_settings.value = merge_presentation_settings(
        default_presentation_settings,
        parsed.presentation_settings || {},
      );
      typstCode.value = String(parsed.typstCode || "");
      rawTypst.value = Boolean(parsed.rawTypst);
      if (parsed.reportBuilderConfig) {
        reportBuilderConfig.value = parsed.reportBuilderConfig;
        assignReportBuilderConfigToPresentationSettings();
      }
      if (crispyFormat.value && parsed.printBehavior) {
        crispyFormat.value.compact_item_print = parsed.printBehavior
          .compact_item_print
          ? 1
          : 0;
        crispyFormat.value.print_uom_after_quantity = parsed.printBehavior
          .print_uom_after_quantity
          ? 1
          : 0;
        crispyFormat.value.print_taxes_with_zero_amount = parsed.printBehavior
          .print_taxes_with_zero_amount
          ? 1
          : 0;
      }
      assignReportBuilderConfigToPresentationSettings();
      dirty.value = snapshotHash !== savedSnapshotHash;
      requestPreviewRefresh();
    } finally {
      applyingHistory.value = false;
    }
  }

  function captureHistoryCheckpoint(resetFuture = true) {
    if (loading.value || initializing.value || applyingHistory.value) return;
    const snapshot = buildHistorySnapshot();
    const snapshotHash = hashSnapshot(snapshot);
    const lastHash =
      historyPastHashes.value[historyPastHashes.value.length - 1];
    if (snapshotHash === lastHash) return;

    historyPast.value.push(snapshot);
    historyPastHashes.value.push(snapshotHash);
    if (historyPast.value.length > MAX_HISTORY_ENTRIES) {
      historyPast.value.shift();
      historyPastHashes.value.shift();
    }
    while (
      historyPast.value.length > 1 &&
      historyPast.value.reduce((total, item) => total + item.length, 0) >
        MAX_HISTORY_BYTES
    ) {
      historyPast.value.shift();
      historyPastHashes.value.shift();
    }
    if (resetFuture) {
      historyFuture.value = [];
      historyFutureHashes.value = [];
    }
  }

  // Throttled wrapper around `captureHistoryCheckpoint` with leading + trailing
  // semantics: the first markDirty in a burst captures synchronously (so the
  // pre-burst state is recorded), and a single trailing capture (the post-burst
  // state) is scheduled `HISTORY_DEBOUNCE_MS` later. Repeated markDirty calls
  // during the cooldown coalesce into that one trailing capture.
  let historyDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  let historyDebounceResetFuture = true;
  let historyDebouncePendingTrailing = false;
  let previewDebounceTimer: ReturnType<typeof setTimeout> | null = null;
  function scheduleHistoryCheckpoint(resetFuture = true) {
    if (loading.value || initializing.value || applyingHistory.value) return;
    if (resetFuture) historyDebounceResetFuture = true;

    if (historyDebounceTimer === null) {
      // Leading edge: capture immediately so undo can return to this point.
      captureHistoryCheckpoint(historyDebounceResetFuture);
      historyDebounceResetFuture = true;
      historyDebounceTimer = setTimeout(() => {
        historyDebounceTimer = null;
        if (historyDebouncePendingTrailing) {
          historyDebouncePendingTrailing = false;
          captureHistoryCheckpoint(historyDebounceResetFuture);
          historyDebounceResetFuture = true;
        }
        pendingHistoryCheckpoint.value = false;
      }, HISTORY_DEBOUNCE_MS);
      return;
    }
    // Within cooldown: remember that a trailing capture is needed.
    historyDebouncePendingTrailing = true;
    pendingHistoryCheckpoint.value = true;
  }
  function flushPendingHistoryCheckpoint() {
    if (historyDebounceTimer === null) return;
    clearTimeout(historyDebounceTimer);
    historyDebounceTimer = null;
    if (historyDebouncePendingTrailing) {
      historyDebouncePendingTrailing = false;
      captureHistoryCheckpoint(historyDebounceResetFuture);
      historyDebounceResetFuture = true;
    }
    pendingHistoryCheckpoint.value = false;
  }

  function resetHistory(saved = false) {
    if (historyDebounceTimer !== null) {
      clearTimeout(historyDebounceTimer);
      historyDebounceTimer = null;
    }
    if (previewDebounceTimer !== null) {
      clearTimeout(previewDebounceTimer);
      previewDebounceTimer = null;
    }
    historyDebouncePendingTrailing = false;
    pendingHistoryCheckpoint.value = false;
    const snapshot = buildHistorySnapshot();
    const snapshotHash = hashSnapshot(snapshot);
    historyPast.value = [snapshot];
    historyPastHashes.value = [snapshotHash];
    historyFuture.value = [];
    historyFutureHashes.value = [];
    if (saved) {
      savedSnapshot.value = snapshot;
      savedSnapshotHash = snapshotHash;
      dirty.value = false;
    }
  }

  /**
   * Reset all per-format state so the singleton store can be reused across
   * navigations without leaking the previous format's layout/history/letterhead.
   * Safe to call repeatedly; always called at the top of `fetch()`.
   */
  function reset() {
    // Cancel any in-flight async work whose late responses might overwrite
    // freshly-loaded state.
    effectiveSettingsRequestSeq++;
    if (historyDebounceTimer !== null) {
      clearTimeout(historyDebounceTimer);
      historyDebounceTimer = null;
    }
    historyDebounceResetFuture = true;
    historyDebouncePendingTrailing = false;
    pendingHistoryCheckpoint.value = false;
    settingsStore.reset();
    clearLetterheadCache();

    applyingHistory.value = false;
    crispyFormat.value = null;
    layout.value = null;
    meta.value = null;
    fields.value = [];
    typstBlocks.value = [];
    reportColumns.value = [];
    reportFilterFields.value = [];
    reportFilters.value = {};
    reportPreviewData.value = null;
    reportPreviewReady.value = false;
    sampleReports.value = [];
    selectedReportName.value = "";
    letterhead.value = null;
    typstCode.value = "";
    rawTypst.value = false;
    reportBuilderConfig.value = getDefaultReportBuilderConfig();
    reportBasicReadOnly.value = false;
    reportModeNotice.value = "";
    presentation_settings.value = merge_presentation_settings(
      default_presentation_settings,
      {},
    );
    effective_presentation_settings.value = merge_presentation_settings(
      default_presentation_settings,
      {},
    );
    historyPast.value = [];
    historyPastHashes.value = [];
    historyFuture.value = [];
    historyFutureHashes.value = [];
    savedSnapshot.value = "";
    savedSnapshotHash = "";
    dirty.value = false;
    previewRevision.value = 0;
  }

  function markDirty(options: MarkDirtyOptions = {}) {
    settingsStore.markDirty();
    scheduleHistoryCheckpoint(true);
    if (!applyingHistory.value) {
      dirty.value = true;
    }
    syncEffectivePresentationSettingsNow();
    applyPreviewRefreshPolicy(options.preview || "auto");
  }

  function markCodeDirty() {
    scheduleHistoryCheckpoint(true);
    if (!loading.value && !initializing.value && !applyingHistory.value) {
      dirty.value = true;
    }
  }

  function requestPreviewRefresh() {
    if (previewDebounceTimer !== null) {
      clearTimeout(previewDebounceTimer);
      previewDebounceTimer = null;
    }
    syncEffectivePresentationSettingsNow();
    previewRevision.value++;
  }

  function setTypstCode(value: string) {
    if (typstCode.value === value) return;
    typstCode.value = value;
    markDirty({ preview: "none" });
  }

  function applyPreviewRefreshPolicy(policy: PreviewRefreshPolicy) {
    if (policy === "none") return;
    if (previewTriggerMode.value === "manual") return;
    if (isReportMode.value && reportPreviewReady.value) {
      schedulePreviewRefresh(REPORT_PREVIEW_DEBOUNCE_MS);
      return;
    }
    if (policy === "debounce") {
      schedulePreviewRefresh();
      return;
    }
    requestPreviewRefresh();
  }

  function schedulePreviewRefresh(delay = PREVIEW_DEBOUNCE_MS) {
    if (previewDebounceTimer !== null) {
      clearTimeout(previewDebounceTimer);
    }
    previewDebounceTimer = setTimeout(() => {
      previewDebounceTimer = null;
      requestPreviewRefresh();
    }, delay);
  }

  let effectiveSettingsRequestSeq = 0;

  function canResolveEffectivePresentationSettingsSynchronously() {
    const source = presentation_settings.value?.source || "";
    const profile = String(
      presentation_settings.value?.branding?.profile || "",
    ).trim();
    return source !== "branding_profile" || !profile;
  }

  function syncEffectivePresentationSettingsNow() {
    if (!canResolveEffectivePresentationSettingsSynchronously()) return false;
    effectiveSettingsRequestSeq++;
    effective_presentation_settings.value = merge_presentation_settings(
      default_presentation_settings,
      presentation_settings.value || {},
    );
    return true;
  }

  async function refreshEffectivePresentationSettings() {
    if (syncEffectivePresentationSettingsNow()) return;
    const requestSeq = ++effectiveSettingsRequestSeq;
    const resolved = await resolve_effective_presentation_settings(
      presentation_settings.value,
      getEffectiveCompany(),
    );
    if (requestSeq !== effectiveSettingsRequestSeq) return;
    effective_presentation_settings.value = resolved;
    if (isReportMode.value && reportBuilderConfig.value.mode === "basic") {
      syncReportBasicTypst();
    }
  }

  function getEffectiveCompany(): string | null {
    return (
      formatCompany.value ||
      presentation_settings.value?.branding?.company ||
      builderContext.value?.company ||
      null
    );
  }

  async function compileReportPreview(
    reportName: string,
    columnConfig: any[] = [],
  ) {
    await refreshEffectivePresentationSettings();
    return reportStore.compileReportPreview(reportName, columnConfig);
  }

  async function runSelectedReportPreview() {
    const reportName = selectedReportName.value;
    if (!reportName)
      throw new Error("Select a report before running the preview");
    const resolved = await resolveReportFiltersForCompile(reportName);
    await reportStore.loadReportColumns(reportName, resolved);
    layoutStore.hydrateReportLayoutFromRuntime();
    reportPreviewReady.value = true;
    previewRevision.value += 1;
  }

  function undo() {
    if (applyingHistory.value) return;
    flushPendingHistoryCheckpoint();
    if (!canUndo.value) return;
    const current = historyPast.value.pop();
    historyPastHashes.value.pop();
    if (!current) return;
    historyFuture.value.unshift(current);
    historyFutureHashes.value.unshift(hashSnapshot(current));
    const previous = historyPast.value[historyPast.value.length - 1];
    if (!previous) return;
    applyHistorySnapshot(previous);
  }

  function redo() {
    if (applyingHistory.value) return;
    flushPendingHistoryCheckpoint();
    if (!canRedo.value) return;
    const next = historyFuture.value.shift();
    historyFutureHashes.value.shift();
    if (!next) return;
    historyPast.value.push(next);
    historyPastHashes.value.push(hashSnapshot(next));
    applyHistorySnapshot(next);
  }

  function isNumericFieldtype(fieldtype: string | undefined): boolean {
    return ["Int", "Float", "Currency", "Percent"].includes(
      String(fieldtype || ""),
    );
  }

  function normalizeTypstColumnWidth(rawWidth: unknown): string {
    if (rawWidth === undefined || rawWidth === null) return "auto";

    if (typeof rawWidth === "number") {
      if (!Number.isFinite(rawWidth) || rawWidth <= 0) return "auto";
      return `${Math.round(rawWidth)}pt`;
    }

    const width = String(rawWidth).trim();
    if (!width) return "auto";
    if (/^auto$/i.test(width)) return "auto";
    if (/^\d+(\.\d+)?(fr|pt|em|rem|%|cm|mm|in)$/i.test(width)) {
      return width.toLowerCase();
    }
    if (/^\d+(\.\d+)?$/.test(width)) {
      return `${Math.round(Number(width))}pt`;
    }
    return "auto";
  }

  function buildReportTableColumns(): TableColumn[] {
    return (reportColumns.value || [])
      .filter((col: any) => Boolean(col?.fieldname))
      .map((col: any) => ({
        fieldname: col.fieldname,
        label: col.label || col.fieldname,
        fieldtype: col.fieldtype || "Data",
        width: normalizeTypstColumnWidth(col.width),
        align: isNumericFieldtype(col.fieldtype) ? "right" : "left",
      }));
  }

  function getReportBlockColumns(fieldname: string): TableColumn[] {
    if (fieldname === "data.filters") {
      const dynamicFilterColumns = (reportFilterFields.value || [])
        .filter((df: any) => Boolean(df?.fieldname))
        .map((df: any) => ({
          fieldname: df.fieldname,
          label: df.label || df.fieldname,
          fieldtype: df.fieldtype || "Data",
          width: "auto",
          align: "left" as const,
        }));
      if (dynamicFilterColumns.length > 0) {
        return dynamicFilterColumns;
      }
      return [
        {
          fieldname: "label",
          label: __("Label"),
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
        {
          fieldname: "value",
          label: __("Value"),
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
      ];
    }
    if (fieldname === "data.report_summary") {
      return [
        {
          fieldname: "label",
          label: __("Label"),
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
        {
          fieldname: "value",
          label: __("Value"),
          fieldtype: "Data",
          width: "auto",
          align: "right",
        },
        {
          fieldname: "indicator",
          label: __("Indicator"),
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
        {
          fieldname: "datatype",
          label: __("Data Type"),
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
        {
          fieldname: "currency",
          label: __("Currency"),
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
      ];
    }
    return [];
  }

  function computeColumnsSignature(
    columns: TableColumn[] | undefined | null,
  ): string {
    const normalized = (columns || []).map((col) => ({
      fieldname: col.fieldname || "",
      label: col.label || col.fieldname || "",
      fieldtype: col.fieldtype || "Data",
      width: col.width || "auto",
      align:
        col.align || (isNumericFieldtype(col.fieldtype) ? "right" : "left"),
    }));
    return JSON.stringify(normalized);
  }

  function sync_report_table_styles(report_settings: Record<string, any>) {
    if (!isReportMode.value) return;
    const tableSettings = ensure_table_settings(presentation_settings.value);
    const has_report_header = Object.prototype.hasOwnProperty.call(
      report_settings,
      "header_fill",
    );
    const has_report_stripe_color = Object.prototype.hasOwnProperty.call(
      report_settings,
      "row_stripe_fill",
    );
    const has_report_striping = Object.prototype.hasOwnProperty.call(
      report_settings,
      "row_striping",
    );

    if (has_report_header) {
      const report_header = String(report_settings.header_fill || "").trim();
      if (
        report_header &&
        (!tableSettings.header.backgroundColor ||
          tableSettings.header.backgroundColor ===
            defaultTableSettings.header.backgroundColor)
      ) {
        tableSettings.header.backgroundColor = report_header;
      }
    }

    if (has_report_stripe_color) {
      const report_stripe_color = String(
        report_settings.row_stripe_fill || "",
      ).trim();
      if (
        report_stripe_color &&
        (!tableSettings.stripe.color ||
          tableSettings.stripe.color === defaultTableSettings.stripe.color)
      ) {
        tableSettings.stripe.color = report_stripe_color;
      }
    }

    if (has_report_striping) {
      const report_striping = Boolean(report_settings.row_striping);
      if (
        tableSettings.stripe.enabled === defaultTableSettings.stripe.enabled
      ) {
        tableSettings.stripe.enabled = report_striping;
      }
    }
  }

  function getReportTableSettingsSnapshot() {
    const rawTable = presentation_settings.value?.table || {};
    return {
      ...defaultTableSettings,
      ...rawTable,
      inset: {
        ...defaultTableSettings.inset,
        ...(rawTable as any).inset,
      },
      stroke: {
        ...defaultTableSettings.stroke,
        ...(rawTable as any).stroke,
      },
      header: {
        ...defaultTableSettings.header,
        ...(rawTable as any).header,
      },
      stripe: {
        ...defaultTableSettings.stripe,
        ...(rawTable as any).stripe,
      },
      typography: {
        header: {
          ...defaultTableSettings.typography.header,
          ...((rawTable as any).typography?.header || {}),
        },
        body: {
          ...defaultTableSettings.typography.body,
          ...((rawTable as any).typography?.body || {}),
        },
      },
    };
  }

  function getReportColumnConfigFromLayout(): Array<{
    fieldname: string;
    width: string;
  }> {
    const tableField = layoutStore.findReportTableField();
    const columns = Array.isArray(tableField?.table_columns)
      ? tableField.table_columns
      : [];
    return columns
      .filter((col: any) => Boolean(col?.fieldname))
      .map((col: any) => ({
        fieldname: String(col.fieldname),
        width: normalizeTypstColumnWidth(col.width),
      }));
  }

  function normalizeReportFilterDefs(filters: any[]): any[] {
    return (filters || [])
      .filter((df: any) => Boolean(df?.fieldname))
      .filter(
        (df: any) =>
          !["Section Break", "Column Break", "HTML", "Button"].includes(
            String(df?.fieldtype || ""),
          ),
      )
      .map((df: any) => ({
        fieldname: df.fieldname,
        label: df.label || df.fieldname,
        fieldtype: df.fieldtype || "Data",
        options: df.options,
        default: df.default,
        reqd: Boolean(df.reqd || df.mandatory),
      }));
  }

  function hasValue(value: any): boolean {
    return ![undefined, null, ""].includes(value);
  }

  function evaluateFilterDefault(def: any): any {
    const rawDefault = def?.default;
    if (rawDefault === undefined || rawDefault === null || rawDefault === "") {
      return undefined;
    }
    if (typeof rawDefault === "function") {
      try {
        return rawDefault();
      } catch (error) {
        logger.warn("Failed to evaluate report filter default", {
          fieldname: def?.fieldname,
          error,
        });
        return undefined;
      }
    }
    return rawDefault;
  }

  function getHeuristicFilterDefault(def: any): any {
    const fieldname = String(def?.fieldname || "").toLowerCase();
    const fieldtype = String(def?.fieldtype || "");
    const options = def?.options;

    if (fieldname === "company") {
      return (
        frappe?.defaults?.get_user_default?.("Company") ||
        frappe?.defaults?.get_user_default?.("company") ||
        frappe?.defaults?.get_global_default?.("company") ||
        undefined
      );
    }

    if (
      fieldname === "fiscal_year" ||
      fieldname === "year" ||
      options === "Fiscal Year"
    ) {
      return (
        frappe?.defaults?.get_user_default?.("fiscal_year") ||
        frappe?.defaults?.get_global_default?.("fiscal_year") ||
        undefined
      );
    }

    if (fieldtype === "Date" || fieldtype === "Datetime") {
      const today =
        frappe?.datetime?.get_today?.() ||
        new Date().toISOString().slice(0, 10);
      const addDays = frappe?.datetime?.add_days;
      if (fieldname.includes("from") || fieldname.endsWith("_from")) {
        return addDays ? addDays(today, -30) : today;
      }
      return today;
    }

    return undefined;
  }

  function getNormalizedSelectOptions(def: any): string {
    const options = def?.options;
    if (Array.isArray(options)) {
      return options
        .map((opt: any) => {
          if (typeof opt === "string") return opt;
          if (opt && typeof opt === "object")
            return String(opt.value || opt.label || "");
          return "";
        })
        .filter(Boolean)
        .join("\n");
    }
    return typeof options === "string" ? options : "";
  }

  function buildAutoFilledReportFilters(
    baseFilters: Record<string, any>,
  ): Record<string, any> {
    const merged = { ...(baseFilters || {}) };
    if (
      formatCompany.value &&
      reportFilterFields.value.some((def: any) => def?.fieldname === "company")
    ) {
      merged.company = formatCompany.value;
    }
    for (const def of reportFilterFields.value || []) {
      if (!def?.fieldname) continue;
      if (hasValue(merged[def.fieldname])) continue;
      const fromDef = evaluateFilterDefault(def);
      if (hasValue(fromDef)) {
        merged[def.fieldname] = fromDef;
        continue;
      }
      const heuristic = getHeuristicFilterDefault(def);
      if (hasValue(heuristic)) {
        merged[def.fieldname] = heuristic;
      }
    }
    return merged;
  }

  function getMissingRequiredFilterDefs(
    selectedFilters: Record<string, any>,
  ): any[] {
    return (reportFilterFields.value || [])
      .filter((df: any) => Boolean(df?.reqd))
      .filter((df: any) => !hasValue(selectedFilters?.[df.fieldname]));
  }

  async function promptForRequiredReportFilters(
    missingDefs: any[],
  ): Promise<Record<string, any> | null> {
    if (!missingDefs.length) return {};
    if (!frappe?.prompt) return null;

    const promptFields = missingDefs.map((def: any) => {
      const fieldtype = String(def.fieldtype || "Data");
      const normalizedType = [
        "Data",
        "Int",
        "Float",
        "Date",
        "Datetime",
        "Link",
        "Select",
        "Check",
        "MultiSelectList",
      ].includes(fieldtype)
        ? fieldtype
        : "Data";

      return {
        fieldname: def.fieldname,
        label: def.label || def.fieldname,
        fieldtype: normalizedType,
        options: getNormalizedSelectOptions(def),
        reqd: 1,
      };
    });

    return await new Promise<Record<string, any> | null>((resolve) => {
      frappe.prompt(
        promptFields,
        (values: Record<string, any>) => resolve(values || {}),
        __("Set Required Report Filters"),
        __("Apply"),
      );
      const dialog = frappe.get_open_dialog?.();
      if (dialog?.set_secondary_action) {
        dialog.set_secondary_action(__("Cancel"), () => {
          dialog.hide();
          resolve(null);
        });
      }
      if (dialog?.onhide) {
        const originalOnHide = dialog.onhide.bind(dialog);
        dialog.onhide = (...args: any[]) => {
          originalOnHide(...args);
          resolve(null);
        };
      }
    });
  }

  async function resolveReportFiltersForCompile(
    reportName: string,
  ): Promise<Record<string, any>> {
    const autoFilled = buildAutoFilledReportFilters(reportFilters.value || {});
    const missingRequired = getMissingRequiredFilterDefs(autoFilled);

    if (!missingRequired.length) {
      reportFilters.value = autoFilled;
      return autoFilled;
    }

    logger.warn("Missing required report filters for preview", {
      report: reportName,
      missing: missingRequired.map((df: any) => df.fieldname),
    });

    const prompted = await promptForRequiredReportFilters(missingRequired);
    if (prompted === null) {
      throw new Error("Required report filters were not provided");
    }

    const resolved = { ...autoFilled, ...prompted };
    const stillMissing = getMissingRequiredFilterDefs(resolved);
    if (stillMissing.length) {
      throw new Error(
        `Missing required report filters: ${stillMissing
          .map((df: any) => df.fieldname)
          .join(", ")}`,
      );
    }

    reportFilters.value = resolved;
    return resolved;
  }

  function logReportFilterDebug(
    reportName: string,
    selectedFilters: Record<string, any>,
    includeFilters: boolean,
  ) {
    if (typeof window === "undefined" || typeof console === "undefined") return;
    const defs = reportFilterFields.value || [];
    const defaults = defs
      .filter(
        (df: any) =>
          df.default !== undefined && df.default !== null && df.default !== "",
      )
      .map((df: any) => ({
        fieldname: df.fieldname,
        default: df.default,
      }));
    const missingRequired = defs
      .filter((df: any) => df.reqd)
      .filter((df: any) => {
        const selected = selectedFilters?.[df.fieldname];
        const hasSelected = ![undefined, null, ""].includes(selected as any);
        const hasDefault = ![undefined, null, ""].includes(df.default as any);
        return !hasSelected && !hasDefault;
      })
      .map((df: any) => df.fieldname);

    console.groupCollapsed(
      `%c[Crispy Builder Report Debug] ${reportName}`,
      "background:#111827;color:#f9fafb;padding:4px 8px;border-radius:4px;font-weight:700;",
    );
    console.log(
      "%cSelected filters (sent):",
      "color:#2563eb;font-weight:700;",
      selectedFilters || {},
    );
    console.log(
      "%cFilter defaults (report definition):",
      "color:#16a34a;font-weight:700;",
      defaults,
    );
    console.log(
      "%cInclude filters flag:",
      "color:#7c3aed;font-weight:700;",
      includeFilters,
    );
    if (missingRequired.length) {
      console.warn(
        "%cMissing required filters (no selected value, no default):",
        "color:#dc2626;font-weight:700;",
        missingRequired,
      );
    } else {
      console.log(
        "%cMissing required filters:",
        "color:#16a34a;font-weight:700;",
        "none",
      );
    }
    console.table(
      defs.map((df: any) => ({
        fieldname: df.fieldname,
        label: df.label,
        fieldtype: df.fieldtype,
        reqd: df.reqd,
        default: df.default,
      })),
    );
    console.groupEnd();
  }

  async function askToRebindReportTableColumns(): Promise<boolean> {
    const message =
      "Report table columns were customized. Rebind to the selected report columns?";
    if (typeof frappe !== "undefined" && typeof frappe.confirm === "function") {
      return await new Promise<boolean>((resolve) => {
        frappe.confirm(
          __(message),
          () => resolve(true),
          () => resolve(false),
        );
      });
    }
    if (typeof window !== "undefined" && typeof window.confirm === "function") {
      return window.confirm(message);
    }
    return false;
  }

  const layoutStore = createLayoutStore({
    layout,
    meta,
    crispyFormat,
    isReportMode,
    presentation_settings,
    reportBuilderConfig,
    buildReportTableColumns,
    getReportBlockColumns,
    computeColumnsSignature,
    markDirty,
  });

  function getLayoutTypstBlockFields() {
    const found: any[] = [];
    const sections = layout.value?.sections || [];
    sections.forEach((section) => {
      (section.columns || []).forEach((column) => {
        (column.fields || []).forEach((field: any) => {
          if (field?.fieldtype === "Crispy Typst Block") {
            found.push(field);
          }
        });
      });
    });
    return found;
  }

  async function loadApplicableTypstBlocks(
    query = "",
    category: string | null = null,
  ) {
    if (!docType.value) {
      typstBlocks.value = [];
      return [];
    }
    const rows = await getApplicableTypstBlocks({
      doctype: docType.value,
      query,
      category,
      company: getEffectiveCompany(),
    });
    typstBlocks.value = rows;
    resolveLayoutTypstBlocks(rows);
    return rows;
  }

  function resolveLayoutTypstBlocks(
    rows: CrispyTypstBlockOption[] = typstBlocks.value,
  ) {
    const byKey = new Map(rows.map((block) => [block.block_key, block]));
    getLayoutTypstBlockFields().forEach((field: any) => {
      const key = String(field.crispy_typst_block || "").trim();
      if (!key) {
        delete field.crispy_typst_block_code;
        return;
      }
      const block = byKey.get(key);
      if (!block) {
        delete field.crispy_typst_block_code;
        return;
      }
      field.crispy_typst_block_name = block.block_name;
      field.crispy_typst_block_code = block.typst_code || "";
    });
  }

  const reportStore = createReportStore({
    formatName,
    presentation_settings: effective_presentation_settings,
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
    getFormatCompany: () => formatCompany.value || null,
	getPdfStandard: () => crispyFormat.value?.pdf_standard || null,
  });

  async function initializeTransientReport(draft: CrispyFormat) {
    reset();
    initializing.value = true;
    try {
      crispyFormat.value = {
        ...draft,
        __islocal: 1,
        crispy_format_type: "Report",
      };
      const renderer = draft.report_renderer || "generic_report";
      const linkedReports = (draft.report || [])
        .filter((row) => row?.report && !row?.disabled)
        .map((row) => ({ name: row.report }));
      sampleReports.value = linkedReports;
      selectedReportName.value = linkedReports[0]?.name || "";
      if (selectedReportName.value) {
        await reportStore.loadReportFilterFields(selectedReportName.value);
      }

      const catalogResponse = await frappe.call({
        method: "crispy_print.api.v1.get_report_renderer_catalog",
      });
      reportRendererMetadata.value = (
        catalogResponse?.message?.renderers || []
      ).find((item: any) => item.key === renderer);
      if (!sampleReports.value.length) {
        sampleReports.value = (reportRendererMetadata.value?.reports || []).map(
          (name: string) => ({ name }),
        );
      }

      presentation_settings.value = merge_presentation_settings(
        default_presentation_settings,
        {
          branding: {
            ...default_presentation_settings.branding,
            company: draft.company || "",
            logo: {
              ...default_presentation_settings.branding.logo,
              company: draft.company || "",
            },
          },
        },
      );
      const serverDefaults = await getServerReportBuilderConfig(renderer);
      reportBuilderConfig.value = normalizeReportBuilderConfig(
        {
          ...serverDefaults,
          renderer,
          sections:
            reportRendererMetadata.value?.sections || serverDefaults.sections,
        },
        renderer,
      );
      assignReportBuilderConfigToPresentationSettings();
      layout.value = layoutStore.getDefaultLayout();
      await refreshEffectivePresentationSettings();
      syncReportBasicTypst();
      dirty.value = true;
      resetHistory(false);
    } finally {
      await nextTick();
      initializing.value = false;
    }
  }

  /**
   * Fetch Crispy Format document and load DocType metadata
   */
  async function fetch(formatName: string) {
    reset();
    loading.value = true;
    initializing.value = true;
    previewRevision.value = 0;
    dirty.value = false; // Set clean state BEFORE triggering any reactive updates

    try {
      // Fetch the Crispy Format document
      const doc = await getCrispyFormat(formatName, {
        company: getEffectiveCompany(),
      });
      crispyFormat.value = doc;

      // Fetch builder mode from backend
      const modeResponse = await frappe.call({
        method: "crispy_print.api.v1.get_builder_mode",
        args: { format_name: formatName },
      });

      const builderMode = modeResponse?.message || {};

      // Report mode is always Typst-backed in builder (Basic generates Typst).
      rawTypst.value =
        builderMode.mode === "code" || Boolean(doc.raw_typst);
      typstCode.value = doc.typst_code || "";

      const formatType =
        doc.crispy_format_type ||
        builderContext.value?.crispy_format_type ||
        "DocType";

      // Load sample reports and initial selection for Report mode.
      if (formatType === "Report") {
        const linkedReports = (doc.report || [])
          .filter((row: any) => row?.report && !row?.disabled)
          .map((row: any) => ({ name: row.report }));
        sampleReports.value =
          doc.report_scope === "Selected Reports" && linkedReports.length
            ? linkedReports
            : [];
        logger.info("Sample reports loaded", sampleReports.value);
        selectedReportName.value = sampleReports.value[0]?.name || "";
        reportPreviewReady.value = false;
        if (selectedReportName.value) {
          await reportStore.loadReportFilterFields(selectedReportName.value);
        }
        reportColumns.value = [];
        try {
          const metadataResponse = await frappe.call({
            method: "crispy_print.api.v1.get_report_renderer_metadata",
            args: { format_name: doc.name },
          });
          reportRendererMetadata.value = metadataResponse?.message || null;
          if (!sampleReports.value.length) {
            sampleReports.value = (
              reportRendererMetadata.value?.preview_candidates || []
            ).map((name: string) => ({ name }));
          }
        } catch (error) {
          logger.warn("Failed to load report renderer metadata", error);
          reportRendererMetadata.value = null;
        }
      }

      // Load DocType metadata
      if (doc.doc_type) {
        await withDoctype(doc.doc_type);
        meta.value = frappe.get_meta(doc.doc_type);

        const skipTypes = ["Tab Break", "Section Break", "Column Break"];

        // Extract fields for the fields pane, matching builder behavior
        const baseFields: DocField[] = meta.value.fields
          .filter(
            (f: DocField) =>
              f.fieldname && !skipTypes.includes(f.fieldtype || ""),
          )
          .map((f: DocField) => ({
            fieldname: f.fieldname,
            label: f.label || f.fieldname,
            fieldtype: f.fieldtype,
            options: f.options,
            print_hide: f.print_hide,
          }));

        const extras: DocField[] = [
          { label: __("DocType"), fieldname: "doctype", fieldtype: "Data" },
          { label: __("ID (name)"), fieldname: "name", fieldtype: "Data" },
          {
            label: __("Crispy Typst Block"),
            fieldname: "_crispy_typst_block",
            fieldtype: "Crispy Typst Block",
          },
          {
            label: __("Crispy Image"),
            fieldname: "_crispy_image",
            fieldtype: "Crispy Image",
          },
          {
            label: __("Custom Typst"),
            fieldname: "_typst_snippet",
            fieldtype: "Typst",
          },
          { label: __("Empty Field"), fieldname: "empty", fieldtype: "Empty" },
          { label: __("Spacer"), fieldname: "spacer", fieldtype: "Spacer" },
          { label: __("Divider"), fieldname: "divider", fieldtype: "Divider" },
        ];
        const templateFields: DocField[] = !crispyFormat.value?.__onload
          ?.print_templates
          ? []
          : crispyFormat.value.__onload.print_templates
              .map((template: any) => {
                let df: any;
                if (template.field) {
                  df = frappe.meta.get_docfield(
                    meta.value.name,
                    template.field,
                  );
                } else {
                  const scrub =
                    typeof frappe.scrub === "function"
                      ? frappe.scrub(template.name)
                      : template.name.toLowerCase().replace(/\s+/g, "_");
                  df = {
                    label: template.name,
                    fieldname: scrub,
                  };
                }

                if (!df?.fieldname) return null;

                return {
                  label: `${df.label} (${__("Field Template")})`,
                  fieldname: `${df.fieldname}_template`,
                  fieldtype: "Field Template",
                  options: template.name,
                } as DocField;
              })
              .filter(Boolean);

        fields.value = [...extras, ...templateFields, ...baseFields];
      }

      // Parse + normalize persisted state (shared with crispy-print)
      const parsed = parseCrispyFormatDoc(doc);

      // Load or create layout
      const persistedLayout = parsed.layout;
      layout.value = persistedLayout || layoutStore.getDefaultLayout();

      // Load page settings (already merged with defaults by parser)
      presentation_settings.value = merge_presentation_settings(
        default_presentation_settings,
        parsed.presentation_settings || {},
      );
      if (doc.company && !presentation_settings.value.branding.company) {
        presentation_settings.value.branding.company = doc.company;
      }
      if (presentation_settings.value.branding.company) {
        presentation_settings.value.branding.logo.company =
          presentation_settings.value.branding.company;
      }
      if (doc.doc_type) {
        await loadApplicableTypstBlocks();
      }
      await refreshEffectivePresentationSettings();
      let serverDefaults: Record<string, any> = {};
      if (formatType === "Report") {
        try {
          serverDefaults = await getServerReportBuilderConfig(
            doc.report_renderer || null,
          );
        } catch (error) {
          logger.warn(
            "Failed to fetch server report builder defaults, using local defaults",
            error,
          );
        }
      }

      const reportAdvancedMode = Boolean(doc.raw_typst);
      const report_settings =
        (presentation_settings.value as any)?.report || {};
      const normalizedReportBuilder = normalizeReportBuilderConfig(
        {
          ...serverDefaults,
          ...report_settings,
        },
        doc.report_renderer,
      );
      // Set mode before assigning into reactive state so the deep watcher
      // doesn't generate basic Typst over advanced raw Typst during fetch.
      if (formatType === "Report") {
        normalizedReportBuilder.mode = reportAdvancedMode
          ? "advanced"
          : "basic";
      }
      reportBuilderConfig.value = normalizedReportBuilder;
      assignReportBuilderConfigToPresentationSettings();
      sync_report_table_styles(report_settings);

      if (formatType === "Report") {
        initializeReportBuilderMode(doc);
        if (layout.value) {
          layoutStore.rebuildReportTableColumns(true);
        }
      }
      const qrSettings = ensure_qr_settings(presentation_settings.value);
      const parsedQrEnabled = (
        parsed.presentation_settings as PresentationSettings | undefined
      )?.qr?.enabled;
      if (typeof parsedQrEnabled !== "boolean") {
        qrSettings.enabled = false;
      }

      // Load letterhead if specified
      if (effective_presentation_settings.value.branding.letterhead) {
        await settingsStore.fetchLetterhead(
          effective_presentation_settings.value.branding.letterhead,
        );
      }

      resetHistory(true);
    } catch (error) {
      logger.error("Failed to fetch Crispy Format", error);
      frappe.throw(__("Failed to load Crispy Format"));
    } finally {
      loading.value = false;
      // Use nextTick to ensure initializing flag persists through all queued watchers
      await nextTick();
      initializing.value = false;
    }
  }
  /**
   * Save changes to backend
   */
  async function saveChanges() {
    if (!crispyFormat.value || (!layout.value && !rawTypst.value)) {
      logger.warn("Nothing to save");
      return;
    }

    flushPendingHistoryCheckpoint();
    loading.value = true;

    try {
      // Serialize layout to JSON
      const layoutJson = layout.value ? serializeLayout(layout.value) : "";

      // Prepare update data
      const updateData = {
        layout_json: layoutJson,
        typst_code: typstCode.value,
        company: presentation_settings.value.branding.company || null,
        presentation_settings: JSON.stringify(presentation_settings.value),
        raw_typst: isReportMode.value
          ? reportBuilderMode.value === "advanced"
            ? 1
            : 0
          : rawTypst.value
            ? 1
            : 0,
        compact_item_print: crispyFormat.value.compact_item_print ? 1 : 0,
        print_uom_after_quantity: crispyFormat.value.print_uom_after_quantity
          ? 1
          : 0,
        print_taxes_with_zero_amount: crispyFormat.value
          .print_taxes_with_zero_amount
          ? 1
          : 0,
      };

      if (crispyFormat.value.__islocal) {
        const created = await createCrispyFormat({
          name: crispyFormat.value.name,
          __newname: crispyFormat.value.name,
          crispy_format_type: "Report",
          report_scope: crispyFormat.value.report_scope || "Selected Reports",
          report_renderer:
            crispyFormat.value.report_renderer ||
            reportBuilderConfig.value.renderer,
          report_source_fingerprint:
            crispyFormat.value.report_source_fingerprint || "",
          report: (crispyFormat.value.report || []).map((row) => ({
            report: row.report,
            disabled: row.disabled || 0,
          })),
          is_default: crispyFormat.value.is_default || 0,
          pdf_standard: crispyFormat.value.pdf_standard || "PDF/A-2u",
          default_print_language:
            crispyFormat.value.default_print_language || "",
          typst_preamble: crispyFormat.value.typst_preamble || "",
          ...updateData,
        });
        crispyFormat.value = {
          ...crispyFormat.value,
          ...created,
          __islocal: 0,
        };
        if (typeof frappe !== "undefined" && frappe?.set_route) {
          frappe.set_route("crispy-format-builder", created.name);
        }
      } else {
        await saveCrispyFormat(crispyFormat.value.name, updateData);
      }

      frappe.show_alert({
        message: __("Crispy Format saved"),
        indicator: "green",
      });

      dirty.value = false;
      savedSnapshot.value = buildHistorySnapshot();
      savedSnapshotHash = hashSnapshot(savedSnapshot.value);
    } catch (error) {
      logger.error("Failed to save changes", error);
      frappe.show_alert({
        message: __("Failed to save changes"),
        indicator: "red",
      });
    } finally {
      loading.value = false;
    }
  }

  async function getTemplatePublishPreview(
    versionBump: "minor" | "major",
  ): Promise<CrispyTemplatePublishPreview | null> {
    if (!crispyFormat.value?.name) return null;
    return await getCrispyTemplatePublishPreview({
      source_crispy_format: crispyFormat.value.name,
      version_bump: versionBump,
      company: getEffectiveCompany(),
    });
  }

  async function publishTemplate(args: {
    version_bump: "minor" | "major";
    make_active: boolean;
    effective_from?: string | null;
    notes?: string | null;
  }): Promise<CrispyTemplatePublishResult | null> {
    if (!crispyFormat.value?.name) return null;
    if (dirty.value) {
      await saveChanges();
    }
    loading.value = true;
    try {
      const result = await publishTemplateFromCrispyFormat({
        source_crispy_format: crispyFormat.value.name,
        version_bump: args.version_bump,
        make_active: args.make_active,
        effective_from: args.effective_from || null,
        notes: args.notes || null,
        company: getEffectiveCompany(),
      });
      frappe.show_alert({
        message: __("Crispy Template published: {0}", [result.name]),
        indicator: "green",
      });
      return result;
    } catch (error) {
      logger.error("Failed to publish Crispy Template", error);
      frappe.show_alert({
        message: __("Failed to publish Crispy Template"),
        indicator: "red",
      });
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function duplicateFormatForCompany(args: {
    target_company: string;
    set_default?: boolean;
    name?: string | null;
    name_strategy?: "copy" | "replace";
  }): Promise<CrispyFormatDuplicateResult | null> {
    if (!crispyFormat.value?.name) return null;
    if (dirty.value) {
      await saveChanges();
    }
    loading.value = true;
    try {
      const result = await duplicateCrispyFormatForCompany({
        source_name: crispyFormat.value.name,
        target_company: args.target_company,
        set_default: Boolean(args.set_default),
        name: args.name || null,
        name_strategy: args.name_strategy || "copy",
      });
      frappe.show_alert({
        message: __("Crispy Format duplicated: {0}", [result.name]),
        indicator: "green",
      });
      return result;
    } catch (error) {
      logger.error("Failed to duplicate Crispy Format", error);
      frappe.show_alert({
        message: __("Failed to duplicate Crispy Format"),
        indicator: "red",
      });
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function duplicateTemplateForCompany(args: {
    source_template: string;
    target_company: string;
    clone_mode?: "snapshot" | "current_format";
    make_active?: boolean;
    version_bump?: "minor" | "major";
  }): Promise<CrispyTemplateDuplicateResult | null> {
    loading.value = true;
    try {
      const result = await duplicateCrispyTemplateForCompany({
        source_template: args.source_template,
        target_company: args.target_company,
        clone_mode: args.clone_mode || "snapshot",
        make_active: Boolean(args.make_active),
        version_bump: args.version_bump || "minor",
      });
      frappe.show_alert({
        message: __("Crispy Template duplicated: {0}", [result.template.name]),
        indicator: "green",
      });
      return result;
    } catch (error) {
      logger.error("Failed to duplicate Crispy Template", error);
      frappe.show_alert({
        message: __("Failed to duplicate Crispy Template"),
        indicator: "red",
      });
      throw error;
    } finally {
      loading.value = false;
    }
  }

  function initializeReportBuilderMode(doc: CrispyFormat) {
    if (!isReportMode.value) return;
    const advancedMode = Boolean(doc.raw_typst);
    reportBuilderConfig.value.mode = advancedMode ? "advanced" : "basic";
    rawTypst.value = advancedMode;

    if (advancedMode) {
      reportBasicReadOnly.value = false;
      reportModeNotice.value = "";
      return;
    }
    reportBasicReadOnly.value = false;
    reportModeNotice.value = "";
    syncReportBasicTypst();
  }

  function syncReportBasicTypst() {
    if (!isReportMode.value) return;
    if (reportBuilderConfig.value.mode !== "basic") return;
    if (reportBasicReadOnly.value) return;
    const generated = buildReportTypstFromConfig(reportBuilderConfig.value, {
      tableSettings: getReportTableSettingsSnapshot(),
      reportTheme: effective_presentation_settings.value.reportTheme,
      language: effective_presentation_settings.value.language,
    });
    const signature = computeReportBasicSignature(generated);
    reportBuilderConfig.value.raw_signature = signature;
    assignReportBuilderConfigToPresentationSettings();
    typstCode.value = generated;
  }

  function resetReportBasicTemplate() {
    if (!isReportMode.value) return;
    reportBasicReadOnly.value = false;
    reportModeNotice.value = "";
    reportBuilderConfig.value.mode = "basic";
    syncReportBasicTypst();
    markDirty();
  }

  // Watch for letterhead changes in presentation_settings
  watch(
    () => effective_presentation_settings.value.branding.letterhead,
    (newLetterhead) => {
      settingsStore.fetchLetterhead(newLetterhead ?? "");
    },
  );

  watch(
    presentation_settings,
    () => {
      refreshEffectivePresentationSettings();
    },
    { deep: true, immediate: true },
  );

  watch(
    () => presentation_settings.value.branding.company,
    async () => {
      if (loading.value || initializing.value || !docType.value) return;
      await loadApplicableTypstBlocks();
    },
  );

  watch(
    () => presentation_settings.value.table,
    () => {
      if (
        isReportMode.value &&
        reportBuilderConfig.value.mode === "basic" &&
        !reportBasicReadOnly.value
      ) {
        syncReportBasicTypst();
      }
    },
    { deep: true },
  );

  const store = {
    // State
    crispyFormat,
    builderContext,
    layout,
    meta,
    fields,
    typstBlocks,
    reportColumns,
    reportFilterFields,
    reportBaseFields,
    reportBuilderFields,
    reportFilters,
    reportPreviewData,
    reportPreviewReady,
    sampleReports,
    reportCandidates,
    selectedReportName,
    letterhead,
    presentation_settings,
    effective_presentation_settings,
    dirty,
    loading,
    initializing,
    previewRevision,

    // History (exposed for diagnostics & tests)
    historyPast,
    historyFuture,

    // Computed
    formatName,
    formatCompany,
    docType,
    formatType,
    isReportMode,
    previewTriggerMode,
    docHeader,
    docFooter,
    qrEnabled,
    typstPreamble,
    rawTypst,
    typstCode,
    reportBuilderConfig,
    reportBuilderMode,
    reportBasicReadOnly,
    reportModeNotice,
    reportRendererMetadata,

    // Methods
    fetch,
    initializeTransientReport,
    saveChanges,
    getTemplatePublishPreview,
    publishTemplate,
    duplicateFormatForCompany,
    duplicateTemplateForCompany,
    loadApplicableTypstBlocks,
    resolveLayoutTypstBlocks,
    markDirty,
    markCodeDirty,
    requestPreviewRefresh,
    setTypstCode,
    updateReportBuilderConfig,
    undo,
    redo,
    canUndo,
    canRedo,
    reset,
    resetHistory,
    resetLayout: layoutStore.resetLayout,
    getDefaultLayout: layoutStore.getDefaultLayout,
    setBuilderContext: settingsStore.setBuilderContext,
    loadReportColumns: reportStore.loadReportColumns,
    loadReportFilterFields: reportStore.loadReportFilterFields,
    loadSampleReports: reportStore.loadSampleReports,
    setSelectedReport: reportStore.setSelectedReport,
    compileReportPreview,
    runSelectedReportPreview,
    invalidateReportPreviewData: reportStore.invalidateReportPreviewData,
    syncReportBasicTypst,
    resetReportBasicTemplate,
    rebuildReportTableColumns: layoutStore.rebuildReportTableColumns,
    isReportTableCustomized: layoutStore.isReportTableCustomized,
  };
  return store;
}

export function useStore() {
  if (storeInstance !== null) {
    return storeInstance;
  }
  storeInstance = buildStore();
  return storeInstance;
}
