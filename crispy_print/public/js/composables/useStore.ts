// composables/useStore.ts
// State management for Crispy Print Format Builder

import { ref, computed, watch, nextTick } from "vue";
import {
  createDefaultLayout,
  createLayoutId,
  serializeLayout,
} from "../utils/layout";
import type { CrispyLayout, DocField, TableColumn } from "../utils/layout";
import {
  defaultTableSettings,
  defaultPageSettings,
  ensureQrSettings,
  ensureTableSettings,
  type PageSettings,
} from "../utils/pageSettings";
import {
  parseCrispyFormatDoc,
  resolveLetterheadDoc,
} from "../utils/formatLoader";
import {
  getCrispyFormat,
  getDefaultReportBuilderConfig as getServerReportBuilderConfig,
  saveCrispyFormat,
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
import {
  buildDummyReportPreviewData,
  getDummyReportFilterColumns,
  getDummyReportTableColumns,
} from "../utils/reportPreviewDummy";

let storeInstance: ReturnType<typeof buildStore> | null = null;

const logger = getLogger({ module: "Store" });
const REPORT_TABLE_FIELDNAME = "data.table";
const DEFAULT_REPORT_PREVIEW_LIMIT = 50;

interface CrispyFormat {
  name: string;
  doc_type?: string;
  // TODO: invistigate teh possibility of having a dynamic crispy_format_type for future.
  crispy_format_type?: string;
  report?: string;
  contract?: string;
  is_default?: number;
  is_generic?: number;
  is_advanced?: number;
  generic_report_type?: string;
  doc_header?: string;
  doc_footer?: string;
  raw_typst?: number;
  typst_preamble?: string;
  typst_code?: string;
  layout_json?: string;
  page_settings?: string;
  __onload?: any;
}

function buildStore() {
  // State
  const crispyFormat = ref<CrispyFormat | null>(null);
  const builderContext = ref<Record<string, any>>({});
  const layout = ref<CrispyLayout | null>(null);
  const meta = ref<any>(null);
  const fields = ref<DocField[]>([]);
  const reportColumns = ref<any[]>(getDummyReportTableColumns());
  const reportFilterFields = ref<any[]>(
    getDummyReportFilterColumns().map((col) => ({
      fieldname: col.fieldname,
      label: col.label,
      fieldtype: col.fieldtype || "Data",
      reqd: false,
    })),
  );
  const reportFilters = ref<Record<string, any>>({});
  const sampleReports = ref<any[]>([{ name: "Style Preview" }]);
  const selectedReportName = ref("Style Preview");
  const letterhead = ref<any>(null);
  const dirty = ref(false);
  const loading = ref(false);
  const initializing = ref(false); // Prevents dirty marking during init
  const changeKey = ref(0);
  const rawTypst = ref(false);
  const typstCode = ref("");
  const reportBuilderConfig = ref<ReportBuilderConfig>(
    getDefaultReportBuilderConfig(),
  );
  const reportBasicReadOnly = ref(false);
  const reportModeNotice = ref("");
  let letterheadRequestSeq = 0;

  const pageSettings = ref<PageSettings>({ ...defaultPageSettings });

  // Computed
  const formatName = computed(() => crispyFormat.value?.name || null);
  const docType = computed(() => crispyFormat.value?.doc_type || null);
  const formatType = computed(
    () => crispyFormat.value?.crispy_format_type || "DocType",
  );
  const isReportMode = computed(() => formatType.value === "Report");
  const reportCandidates = computed(() => sampleReports.value || []);
  const reportBaseFields = computed<DocField[]>(() => {
    if (!isReportMode.value) return [];
    return [
      { fieldname: "data.title", label: "Title", fieldtype: "Data" },
      { fieldname: "data.subtitle", label: "Subtitle", fieldtype: "Data" },
      { fieldname: "data.filters", label: "Filters", fieldtype: "Table" },
      {
        fieldname: "data.report_summary",
        label: "Report Summary",
        fieldtype: "Table",
      },
      {
        fieldname: "data.chart",
        label: "Chart",
        fieldtype: "Table",
      },
      {
        fieldname: "data.table",
        label: "Report Table",
        fieldtype: "Table",
      },
    ];
  });
  const reportBuilderFields = computed<DocField[]>(() => [...reportBaseFields.value]);
  const reportBuilderMode = computed<ReportBuilderMode>({
    get: () => reportBuilderConfig.value.mode,
    set: (nextMode) => {
      reportBuilderConfig.value.mode = nextMode;
      if (!isReportMode.value) return;
      if (nextMode === "basic") {
        syncReportBasicTypst();
      }
      reportBasicReadOnly.value = false;
      reportModeNotice.value = "";
      rawTypst.value = nextMode === "advanced";
      if (crispyFormat.value) {
        crispyFormat.value.is_advanced = nextMode === "advanced" ? 1 : 0;
      }
      markDirty();
    },
  });
  const docHeader = computed(() => crispyFormat.value?.doc_header || "");
  const docFooter = computed(() => crispyFormat.value?.doc_footer || "");
  const qrEnabled = computed(() => {
    const qr = pageSettings.value?.qr;
    if (qr && typeof qr.enabled === "boolean") {
      return qr.enabled;
    }
    return false;
  });
  const typstPreamble = computed(
    () => crispyFormat.value?.typst_preamble || "",
  );

  function isNumericFieldtype(fieldtype: string | undefined): boolean {
    return ["Int", "Float", "Currency", "Percent"].includes(String(fieldtype || ""));
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
    if (fieldname === "data.report_summary") {
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
          align: "right",
        },
        {
          fieldname: "indicator",
          label: "Indicator",
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
        {
          fieldname: "datatype",
          label: "Data Type",
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
        {
          fieldname: "currency",
          label: "Currency",
          fieldtype: "Data",
          width: "auto",
          align: "left",
        },
      ];
    }
    return [];
  }

  function computeColumnsSignature(columns: TableColumn[] | undefined | null): string {
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

  function findReportTableField(): any | null {
    const sections = layout.value?.sections || [];
    for (const section of sections) {
      for (const column of section.columns || []) {
        for (const field of column.fields || []) {
          if (field?.fieldname === REPORT_TABLE_FIELDNAME) {
            return field;
          }
        }
      }
    }
    return null;
  }

  function escapeTypstString(value: string): string {
    return String(value || "").replace(/"/g, '\\"');
  }

  function buildReportFontPreambleOverride(): string {
    const config = reportBuilderConfig.value;
    const fontFamily = String(config?.font_family || "").trim();
    if (!fontFamily) return "";
    const fontSize = Number(config?.font_size_pt);
    const safeSize = Number.isFinite(fontSize) && fontSize > 0 ? fontSize : 9;
    return `#set text(font: "${escapeTypstString(fontFamily)}", size: ${safeSize}pt)`;
  }

  function migrateLegacyReportBuilderTableStyles(
    persistedReportBuilder: Record<string, any>,
  ) {
    if (!isReportMode.value) return;
    const tableSettings = ensureTableSettings(pageSettings.value);
    const hasLegacyHeader = Object.prototype.hasOwnProperty.call(
      persistedReportBuilder,
      "header_fill",
    );
    const hasLegacyStripeColor = Object.prototype.hasOwnProperty.call(
      persistedReportBuilder,
      "row_stripe_fill",
    );
    const hasLegacyStriping = Object.prototype.hasOwnProperty.call(
      persistedReportBuilder,
      "row_striping",
    );

    if (hasLegacyHeader) {
      const legacyHeader = String(persistedReportBuilder.header_fill || "").trim();
      if (
        legacyHeader &&
        (!tableSettings.header.backgroundColor ||
          tableSettings.header.backgroundColor ===
            defaultTableSettings.header.backgroundColor)
      ) {
        tableSettings.header.backgroundColor = legacyHeader;
      }
    }

    if (hasLegacyStripeColor) {
      const legacyStripeColor = String(
        persistedReportBuilder.row_stripe_fill || "",
      ).trim();
      if (
        legacyStripeColor &&
        (!tableSettings.stripe.color ||
          tableSettings.stripe.color === defaultTableSettings.stripe.color)
      ) {
        tableSettings.stripe.color = legacyStripeColor;
      }
    }

    if (hasLegacyStriping) {
      const legacyStriping = Boolean(persistedReportBuilder.row_striping);
      if (tableSettings.stripe.enabled === defaultTableSettings.stripe.enabled) {
        tableSettings.stripe.enabled = legacyStriping;
      }
    }
  }

  function getReportTableSettingsSnapshot() {
    const rawTable = pageSettings.value?.table || {};
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

  function getReportColumnConfigFromLayout(): Array<{ fieldname: string; width: string }> {
    const tableField = findReportTableField();
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

    if (fieldname === "fiscal_year" || fieldname === "year" || options === "Fiscal Year") {
      return (
        frappe?.defaults?.get_user_default?.("fiscal_year") ||
        frappe?.defaults?.get_global_default?.("fiscal_year") ||
        undefined
      );
    }

    if (fieldtype === "Date" || fieldtype === "Datetime") {
      const today =
        frappe?.datetime?.get_today?.() || new Date().toISOString().slice(0, 10);
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
          if (opt && typeof opt === "object") return String(opt.value || opt.label || "");
          return "";
        })
        .filter(Boolean)
        .join("\n");
    }
    return typeof options === "string" ? options : "";
  }

  function buildAutoFilledReportFilters(baseFilters: Record<string, any>): Record<string, any> {
    const merged = { ...(baseFilters || {}) };
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

  function getMissingRequiredFilterDefs(selectedFilters: Record<string, any>): any[] {
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
      const normalizedType =
        ["Data", "Int", "Float", "Date", "Datetime", "Link", "Select", "Check", "MultiSelectList"].includes(
          fieldtype,
        )
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

  async function resolveReportFiltersForCompile(reportName: string): Promise<Record<string, any>> {
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
      .filter((df: any) => df.default !== undefined && df.default !== null && df.default !== "")
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
      "background:#111827;color:#f9fafb;padding:4px 8px;border-radius:4px;font-weight:700;"
    );
    console.log(
      "%cSelected filters (sent):",
      "color:#2563eb;font-weight:700;",
      selectedFilters || {}
    );
    console.log(
      "%cFilter defaults (report definition):",
      "color:#16a34a;font-weight:700;",
      defaults
    );
    console.log(
      "%cInclude filters flag:",
      "color:#7c3aed;font-weight:700;",
      includeFilters
    );
    if (missingRequired.length) {
      console.warn(
        "%cMissing required filters (no selected value, no default):",
        "color:#dc2626;font-weight:700;",
        missingRequired
      );
    } else {
      console.log(
        "%cMissing required filters:",
        "color:#16a34a;font-weight:700;",
        "none"
      );
    }
    console.table(
      defs.map((df: any) => ({
        fieldname: df.fieldname,
        label: df.label,
        fieldtype: df.fieldtype,
        reqd: df.reqd,
        default: df.default,
      }))
    );
    console.groupEnd();
  }

  function findReportLayoutField(fieldname: string): any | null {
    const sections = layout.value?.sections || [];
    for (const section of sections) {
      for (const column of section.columns || []) {
        for (const field of column.fields || []) {
          if (field?.fieldname === fieldname) {
            return field;
          }
        }
      }
    }
    return null;
  }

  async function askToRebindReportTableColumns(): Promise<boolean> {
    const message =
      "Report table columns were customized. Rebind to the selected report columns?";
    if (
      typeof frappe !== "undefined" &&
      typeof frappe.confirm === "function"
    ) {
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

  function isReportTableCustomized(): boolean {
    const tableField = findReportTableField();
    if (!tableField) return false;
    const currentSignature = computeColumnsSignature(
      tableField.table_columns || [],
    );
    const latestRuntimeSignature = computeColumnsSignature(buildReportTableColumns());
    const syncedSignature = reportBuilderConfig.value.report_table_sync_signature;
    if (syncedSignature) {
      return currentSignature !== syncedSignature;
    }
    return currentSignature !== latestRuntimeSignature;
  }

  function rebuildReportTableColumns(force = false): boolean {
    if (!isReportMode.value) return false;
    const tableField = findReportTableField();
    if (!tableField) return false;

    const newColumns = buildReportTableColumns();
    const newSignature = computeColumnsSignature(newColumns);
    const currentSignature = computeColumnsSignature(tableField.table_columns || []);
    const syncedSignature = reportBuilderConfig.value.report_table_sync_signature;
    const customized = syncedSignature
      ? currentSignature !== syncedSignature
      : currentSignature !== newSignature;

    if (!force && customized) {
      return false;
    }

    tableField.table_columns = newColumns;
    reportBuilderConfig.value.report_table_sync_signature = newSignature;
    pageSettings.value.report_builder = reportBuilderConfig.value;
    return true;
  }

  function syncFiltersBlockColumns(): boolean {
    if (!isReportMode.value) return false;
    const filtersField = findReportLayoutField("data.filters");
    if (!filtersField) return false;
    const columns = getReportBlockColumns("data.filters");
    filtersField.table_columns = columns;
    return true;
  }

  /**
   * Fetch Crispy Format document and load DocType metadata
   */
  async function fetch(formatName: string) {
    loading.value = true;
    initializing.value = true;
    changeKey.value = 0;
    dirty.value = false; // Set clean state BEFORE triggering any reactive updates

    try {
      // Fetch the Crispy Format document
      const doc = await getCrispyFormat(formatName);
      crispyFormat.value = doc;

      // Fetch builder mode from backend
      const modeResponse = await frappe.call({
        method: "crispy_print.api.v1.get_builder_mode",
        args: { format_name: formatName },
      });

      const builderMode = modeResponse?.message || {};

      // Report mode is always Typst-backed in builder (Basic generates Typst).
      rawTypst.value =
        (doc.crispy_format_type || builderContext.value?.crispy_format_type) ===
        "Report"
          ? Boolean(doc.is_advanced || doc.raw_typst)
          : builderMode.mode === "code" || Boolean(doc.raw_typst);
      typstCode.value = doc.typst_code || "";

      const formatType =
        doc.crispy_format_type ||
        builderContext.value?.crispy_format_type ||
        "DocType";

      // Load sample reports and initial selection for Report mode.
      if (formatType === "Report") {
        await loadSampleReports();
        logger.info("Sample reports loaded", sampleReports.value);
        selectedReportName.value = "Style Preview";
        await loadReportFilterFields("Style Preview");
        await loadReportColumns("Style Preview", {});
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
          { label: "DocType", fieldname: "doctype", fieldtype: "Data" },
          { label: "ID (name)", fieldname: "name", fieldtype: "Data" },
          {
            label: "Custom Typst",
            fieldname: "_typst_snippet",
            fieldtype: "Typst",
          },
          { label: "Empty Field", fieldname: "empty", fieldtype: "Empty" },
          { label: "Spacer", fieldname: "spacer", fieldtype: "Spacer" },
          { label: "Divider", fieldname: "divider", fieldtype: "Divider" },
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
                  label: `${df.label} (Field Template)`,
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
      const hadNoLayout = !persistedLayout;
      // Generic report builder uses a fixed style-preview layout model.
      layout.value = formatType === "Report" ? getDefaultLayout() : (persistedLayout || getDefaultLayout());

      // Load page settings (already merged with defaults by parser)
      pageSettings.value = parsed.pageSettings || { ...defaultPageSettings };
      let serverDefaults: Record<string, any> = {};
      if (formatType === "Report") {
        try {
          serverDefaults = await getServerReportBuilderConfig(
            doc.generic_report_type || null,
          );
        } catch (error) {
          logger.warn(
            "Failed to fetch server report builder defaults, using local defaults",
            error,
          );
        }
      }

      const persistedReportBuilder =
        (pageSettings.value as any)?.report_builder || {};
      reportBuilderConfig.value = normalizeReportBuilderConfig(
        {
          ...serverDefaults,
          ...persistedReportBuilder,
        },
        doc.generic_report_type,
      );
      pageSettings.value.report_builder = reportBuilderConfig.value;
      migrateLegacyReportBuilderTableStyles(persistedReportBuilder);

      if (formatType === "Report") {
        initializeReportBuilderMode(doc);
        if (layout.value) {
          rebuildReportTableColumns(true);
        }
      }
      const qrSettings = ensureQrSettings(pageSettings.value);
      const parsedQrEnabled = (parsed.pageSettings as PageSettings | undefined)
        ?.qr?.enabled;
      if (typeof parsedQrEnabled !== "boolean") {
        qrSettings.enabled = false;
      }

      // Load letterhead if specified
      if (pageSettings.value.letterhead) {
        letterhead.value = await resolveLetterheadDoc(
          pageSettings.value.letterhead,
        );
      }

      // Auto-save if this was the first time (no layout_json in DB)
      if (hadNoLayout && layout.value) {
        await saveChanges();
      }
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
   * Create default layout from DocType metadata
   */
  function getDefaultLayout(): CrispyLayout {
    if (isReportMode.value) {
      const reportTableColumns = buildReportTableColumns();
      reportBuilderConfig.value.report_table_sync_signature =
        computeColumnsSignature(reportTableColumns);

      const reportFields = [
        { fieldname: "data.title", label: "Title", fieldtype: "Data" },
        { fieldname: "data.subtitle", label: "Subtitle", fieldtype: "Data" },
        {
          fieldname: "data.filters",
          label: "Filters",
          fieldtype: "Table",
          table_columns: getReportBlockColumns("data.filters"),
        },
        {
          fieldname: "data.report_summary",
          label: "Report Summary",
          fieldtype: "Table",
          table_columns: getReportBlockColumns("data.report_summary"),
        },
        { fieldname: "data.chart", label: "Chart", fieldtype: "Table" },
        {
          fieldname: "data.table",
          label: "Report Table",
          fieldtype: "Table",
          table_columns: reportTableColumns,
        },
      ];

      return {
        sections: [
          {
            id: createLayoutId(),
            label: "",
            columns: [
              {
                id: createLayoutId(),
                label: "",
                fields: reportFields.map((field) => ({
                  id: createLayoutId(),
                  align: "left" as const,
                  ...field,
                })),
              },
            ],
          },
        ],
      };
    }

    if (!meta.value) {
      return { sections: [] };
    }

    return createDefaultLayout(meta.value, crispyFormat.value);
  }

  /**
   * Save changes to backend
   */
  async function saveChanges() {
    if (!crispyFormat.value || (!layout.value && !rawTypst.value)) {
      logger.warn("Nothing to save");
      return;
    }

    loading.value = true;

    try {
      // Serialize layout to JSON
      const layoutJson = layout.value ? serializeLayout(layout.value) : "";

      // Prepare update data
      const updateData = {
        layout_json: layoutJson,
        typst_code: typstCode.value,
        page_settings: JSON.stringify(pageSettings.value),
        raw_typst: isReportMode.value
          ? reportBuilderMode.value === "advanced"
            ? 1
            : 0
          : rawTypst.value
            ? 1
            : 0,
        is_advanced: isReportMode.value
          ? reportBuilderMode.value === "advanced"
            ? 1
            : 0
          : 0,
      };

      await saveCrispyFormat(crispyFormat.value.name, updateData);

      frappe.show_alert({
        message: __("Crispy Format saved"),
        indicator: "green",
      });

      dirty.value = false;
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

  /**
   * Mark as dirty when layout changes
   */
  function markDirty() {
    // Don't mark dirty during initial load
    if (loading.value || initializing.value) {
      return;
    }

    dirty.value = true;
    changeKey.value++;
  }

  /**
   * Reset layout to default
   */
  function resetLayout() {
    layout.value = getDefaultLayout();
    markDirty();
  }

  /**
   * Fetch letterhead when letterhead setting changes
   */
  async function fetchLetterhead(letterheadName: string) {
    const requestSeq = ++letterheadRequestSeq;
    if (typeof frappe === "undefined") {
      logger.warn("Cannot fetch letterhead - Frappe not available");
      return;
    }

    if (!letterheadName) {
      letterhead.value = null;
      changeKey.value++;
      return;
    }

    // Clear current letterhead immediately to avoid showing stale branding
    // while the new letterhead document is loading.
    letterhead.value = null;
    try {
      const resolved = await resolveLetterheadDoc(letterheadName);
      if (requestSeq !== letterheadRequestSeq) return;
      letterhead.value = resolved;
      changeKey.value++;
    } catch (error) {
      if (requestSeq !== letterheadRequestSeq) return;
      logger.warn("Failed to resolve letterhead", { letterheadName, error });
      letterhead.value = null;
      changeKey.value++;
    }
  }

  /**
   * Set builder context from route options
   */
  function setBuilderContext(context: Record<string, any> = {}) {
    builderContext.value = context;
    logger.info("Builder context set", context);
  }

  /**
   * Load report columns for Report mode
   */
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

  /**
   * Load sample reports for generic template preview
   */
  async function loadSampleReports() {
    sampleReports.value = [{ name: "Style Preview" }];
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

  /**
   * Build and compile report preview (reuses existing compile_typst)
   */
  async function compileReportPreview(
    reportName: string,
    columnConfig: any[] = [],
  ) {
    try {
      logger.info("Building report source", reportName);

      // Step 1: Get Typst source
      const effectiveColumnConfig =
        Array.isArray(columnConfig) && columnConfig.length
          ? columnConfig
          : getReportColumnConfigFromLayout();
      const includeFilters = Boolean(reportBuilderConfig.value.show_filters);
      const orientation = pageSettings.value?.orientation || "landscape";
      const pageSettingsPayload = { ...pageSettings.value };
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
      const tableField = findReportTableField();
      const tableColumns = Array.isArray(tableField?.table_columns)
        ? tableField.table_columns
        : buildReportTableColumns();
      const previewData = buildDummyReportPreviewData({
        title: reportName || selectedReportName.value || "Style Preview",
        includeFilters,
        includeSummary: Boolean(reportBuilderConfig.value.show_summary),
        includeTotalRow: Boolean(reportBuilderConfig.value.include_total_row),
        tableColumns,
        columnConfig: effectiveColumnConfig,
      });
      const previewChartSvg =
        typeof previewData.chart_svg === "string" && previewData.chart_svg.trim()
          ? previewData.chart_svg
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
          filters: {},
          column_config: effectiveColumnConfig,
          include_filters: includeFilters ? 1 : 0,
          orientation,
          page_settings: pageSettingsPayload,
          chart_svg: null,
          typst_preamble_override: typstPreambleOverride,
          typst_code_override: typstCode.value || "",
          preview_data: previewDataPayload,
          letterhead_image: letterheadImage,
          limit: DEFAULT_REPORT_PREVIEW_LIMIT,
        },
      });

      const typstSource = sourceResponse?.message;
      if (!typstSource) {
        throw new Error("No Typst source returned");
      }

      logger.info("Compiling to SVG");

      // Step 2: Compile using existing endpoint (same as DocType mode)
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

  function initializeReportBuilderMode(doc: CrispyFormat) {
    if (!isReportMode.value) return;
    const advancedMode = Boolean(doc.is_advanced || doc.raw_typst);
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
    });
    const signature = computeReportBasicSignature(generated);
    reportBuilderConfig.value.raw_signature = signature;
    pageSettings.value.report_builder = reportBuilderConfig.value;
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

  // Watch for letterhead changes in pageSettings
  watch(
    () => pageSettings.value.letterhead,
    (newLetterhead) => {
      fetchLetterhead(newLetterhead);
    },
  );

  watch(
    () => pageSettings.value.table,
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

  watch(
    reportBuilderConfig,
    () => {
      if (
        reportBuilderConfig.value.show_footer_total !==
        reportBuilderConfig.value.include_total_row
      ) {
        reportBuilderConfig.value.show_footer_total =
          reportBuilderConfig.value.include_total_row;
      }
      pageSettings.value.report_builder = reportBuilderConfig.value;
      if (
        isReportMode.value &&
        reportBuilderConfig.value.mode === "basic" &&
        !reportBasicReadOnly.value
      ) {
        syncReportBasicTypst();
      }
      if (!loading.value && !initializing.value) {
        markDirty();
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
    reportColumns,
    reportFilterFields,
    reportBaseFields,
    reportBuilderFields,
    reportFilters,
    sampleReports,
    reportCandidates,
    selectedReportName,
    letterhead,
    pageSettings,
    dirty,
    loading,
    initializing,
    changeKey,

    // Computed
    formatName,
    docType,
    formatType,
    isReportMode,
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

    // Methods
    fetch,
    saveChanges,
    markDirty,
    resetLayout,
    getDefaultLayout,
    setBuilderContext,
    loadReportColumns,
    loadReportFilterFields,
    loadSampleReports,
    setSelectedReport,
    compileReportPreview,
    syncReportBasicTypst,
    resetReportBasicTemplate,
    rebuildReportTableColumns,
    isReportTableCustomized,
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
