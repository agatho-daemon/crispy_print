import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/crispy", () => ({
  getCrispyFormat: vi.fn(async (): Promise<Record<string, unknown>> => ({
    name: "Generic Report Format",
    crispy_format_type: "Report",
    is_generic: 1,
    is_advanced: 0,
    generic_report_type: "Grid",
    report: "Account Balance",
    doc_type: null as unknown,
    layout_json: JSON.stringify({
      sections: [
        {
          label: "Legacy",
          columns: [{ label: "Legacy Col", fields: [{ fieldname: "legacy" }] }],
        },
      ],
    }),
    presentation_settings: JSON.stringify({}),
    typst_code: "",
    raw_typst: 0,
  })),
  getDefaultReportBuilderConfig: vi.fn(async (): Promise<Record<string, unknown>> => ({
    mode: "basic",
    preset: "grid",
    show_filters: true,
    show_summary: true,
    include_total_row: true,
    show_footer_total: true,
    chart_enabled: true,
    chart_width_percent: 100,
    chart_max_height_pt: 220,
    chart_card_border: true,
    chart_spacing_top_pt: 0,
    chart_spacing_bottom_pt: 12,
    header_fill: "#B3D7FF",
    header_text_weight: "bold",
    font_family: "Inter 18pt",
    font_size_pt: 9,
    row_striping: false,
    row_stripe_fill: "#F8FBFF",
    column_align_strategy: "auto",
    table_inset_x_pt: 8,
    table_inset_y_pt: 6,
    table_stroke_top_pt: 1,
    table_stroke_body_pt: 0.5,
    raw_signature: null as unknown,
    report_table_sync_signature: null as unknown,
  })),
  saveCrispyFormat: vi.fn(async () => {}),
}));

vi.mock("../../api/frappe", () => ({
  withDoctype: vi.fn(async () => {}),
}));

vi.mock("../../utils/formatLoader", async (orig) => {
  const actual = (await orig()) as Record<string, any>;
  return {
    ...actual,
    parseCrispyFormatDoc: () => ({
      layout: { sections: [] as unknown[] },
      presentation_settings: {},
      docHeader: "",
      formatDoc: {},
    }),
    resolveLetterheadDoc: vi.fn(async (): Promise<null> => null),
  };
});

describe("report layout fallback", () => {
  beforeEach(() => {
    vi.resetModules();
    (globalThis as any).__ = (msg: string): string => msg;
    (globalThis as any).frappe = {
      call: vi.fn(async ({ method }: { method: string }) => {
        if (method === "crispy_print.api.v1.get_builder_mode") {
          return { message: { mode: "visual" } };
        }
        if (method === "frappe.desk.query_report.run") {
          return { message: { columns: [] as unknown[] } };
        }
        if (method === "crispy_print.api.v1.get_reports_without_custom_html") {
          return { message: [] as unknown[] };
        }
        return { message: {} };
      }),
      show_alert: vi.fn(),
    };
  });

  it("always resets generic report builder layout to style-preview defaults", async () => {
    const { useStore } = await import("../../composables/useStore");
    const { saveCrispyFormat } = await import("../../api/crispy");
    const store = useStore();

    await store.fetch("Generic Report Format");

    expect(store.layout.value?.sections?.length).toBe(1);
    expect(store.layout.value?.sections?.[0]?.columns?.length).toBe(1);
    expect(store.layout.value?.sections?.[0]?.columns?.[0]?.fields?.[0]?.fieldname).toBe(
      "data.title"
    );
    expect(saveCrispyFormat).toHaveBeenCalledTimes(0);
  });
});
