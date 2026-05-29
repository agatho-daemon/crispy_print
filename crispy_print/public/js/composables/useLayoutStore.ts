import type { Ref } from "vue";
import { createDefaultLayout, createLayoutId } from "../utils/layout";
import type { CrispyLayout, TableColumn } from "../utils/layout";
import type { PresentationSettings } from "../utils/presentation_settings";
import type { ReportBuilderConfig } from "../utils/reportBuilder";

const REPORT_TABLE_FIELDNAME = "data.table";

interface CreateLayoutStoreOptions {
  layout: Ref<CrispyLayout | null>;
  meta: Ref<any>;
  crispyFormat: Ref<any>;
  isReportMode: Ref<boolean>;
  presentation_settings: Ref<PresentationSettings>;
  reportBuilderConfig: Ref<ReportBuilderConfig>;
  buildReportTableColumns: () => TableColumn[];
  getReportBlockColumns: (fieldname: string) => TableColumn[];
  computeColumnsSignature: (columns: TableColumn[] | undefined | null) => string;
  markDirty: () => void;
}

export function createLayoutStore(options: CreateLayoutStoreOptions) {
  const {
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
  } = options;

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

  function findReportTableField(): any | null {
    return findReportLayoutField(REPORT_TABLE_FIELDNAME);
  }

  function isReportTableCustomized(): boolean {
    const tableField = findReportTableField();
    if (!tableField) return false;
    const currentSignature = computeColumnsSignature(tableField.table_columns || []);
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
    presentation_settings.value.report = reportBuilderConfig.value;
    return true;
  }

  function syncFiltersBlockColumns(): boolean {
    if (!isReportMode.value) return false;
    const filtersField = findReportLayoutField("data.filters");
    if (!filtersField) return false;
    filtersField.table_columns = getReportBlockColumns("data.filters");
    return true;
  }

  function getDefaultLayout(): CrispyLayout {
    if (isReportMode.value) {
      const reportTableColumns = buildReportTableColumns();
      reportBuilderConfig.value.report_table_sync_signature =
        computeColumnsSignature(reportTableColumns);

      const reportFields = [
        { fieldname: "data.title", label: __("Title"), fieldtype: "Data" },
        { fieldname: "data.subtitle", label: __("Subtitle"), fieldtype: "Data" },
        {
          fieldname: "data.filters",
          label: __("Filters"),
          fieldtype: "Table",
          table_columns: getReportBlockColumns("data.filters"),
        },
        {
          fieldname: "data.report_summary",
          label: __("Report Summary"),
          fieldtype: "Table",
          table_columns: getReportBlockColumns("data.report_summary"),
        },
        { fieldname: "data.chart", label: __("Chart"), fieldtype: "Table" },
        {
          fieldname: "data.table",
          label: __("Report Table"),
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

  function resetLayout() {
    layout.value = getDefaultLayout();
    markDirty();
  }

  function getReportTableColumnsForPreview(): any[] {
    const tableField = findReportTableField();
    return Array.isArray(tableField?.table_columns)
      ? tableField.table_columns
      : buildReportTableColumns();
  }

  return {
    findReportLayoutField,
    findReportTableField,
    isReportTableCustomized,
    rebuildReportTableColumns,
    syncFiltersBlockColumns,
    getDefaultLayout,
    resetLayout,
    getReportTableColumnsForPreview,
  };
}
