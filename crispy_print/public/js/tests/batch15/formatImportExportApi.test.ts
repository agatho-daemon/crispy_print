import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/frappe", () => ({
  call: vi.fn(),
  getDoc: vi.fn(),
  getList: vi.fn(),
  setValue: vi.fn(),
}));

describe("crispy format import/export api wrappers", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();
  });

  it("exports a format payload", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: {
        schema_version: 1,
        exported_at: "2026-02-07T10:00:00",
        app: "crispy_print",
        format: { name: "My Format" },
      },
    });

    const { exportCrispyFormat } = await import("../../api/crispy");
    const payload = await exportCrispyFormat("My Format");

    expect(payload.schema_version).toBe(1);
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.export_crispy_format",
      args: { name: "My Format" },
    });
  });

  it("checks conflicts with serialized payload", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: {
        schema_version: 1,
        name: "My Format",
        exists: true,
        conflict: true,
      },
    });

    const { checkImportConflicts } = await import("../../api/crispy");
    const payload = { schema_version: 1, format: { name: "My Format" } };
    const res = await checkImportConflicts(payload);

    expect(res.exists).toBe(true);
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.check_import_conflicts",
    });
    expect(typeof (call as any).mock.calls[0][0].args.payload).toBe("string");
  });

  it("imports with selected conflict action", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: {
        success: true,
        name: "My Format (Imported)",
        warnings: ["Missing reference: Letter Head 'X'"],
        conflict_action: "copy",
      },
    });

    const { importCrispyFormat } = await import("../../api/crispy");
    const result = await importCrispyFormat('{"schema_version":1}', "copy");

    expect(result.success).toBe(true);
    expect(result.warnings.length).toBe(1);
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.import_crispy_format",
      args: {
        payload: '{"schema_version":1}',
        on_conflict: "copy",
      },
    });
  });

  it("lists sample format catalog entries", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: [
        {
          id: "sales-invoice-basic",
          title: "Sales Invoice Starter",
          target_type: "DocType",
          tags: ["invoice"],
        },
      ],
    });

    const { listSampleFormats } = await import("../../api/crispy");
    const samples = await listSampleFormats();

    expect(samples[0].id).toBe("sales-invoice-basic");
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.list_sample_formats",
    });
  });

  it("gets a full sample format payload", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: {
        schema_version: 1,
        app: "crispy_print",
        sample: { id: "sales-invoice-basic" },
        format: { name: "Sales Invoice Starter" },
      },
    });

    const { getSampleFormat } = await import("../../api/crispy");
    const payload = await getSampleFormat("sales-invoice-basic");

    expect(payload.format.name).toBe("Sales Invoice Starter");
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.get_sample_format",
      args: { sample_id: "sales-invoice-basic" },
    });
  });

  it("creates a format from a sample", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: {
        success: true,
        name: "Sales Invoice Starter",
        sample_id: "sales-invoice-basic",
        company: "ACME",
        warnings: [],
      },
    });

    const { createFormatFromSample } = await import("../../api/crispy");
    const result = await createFormatFromSample({
      sample_id: "sales-invoice-basic",
      company: "ACME",
      name: "Sales Invoice Starter",
      set_default: true,
    });

    expect(result.name).toBe("Sales Invoice Starter");
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.create_format_from_sample",
      args: {
        sample_id: "sales-invoice-basic",
        company: "ACME",
        name: "Sales Invoice Starter",
        set_default: true,
      },
    });
  });

  it("gets report builder defaults from backend", async () => {
    const { call } = await import("../../api/frappe");
    (call as any).mockResolvedValueOnce({
      message: {
        mode: "basic",
        renderer: "financial_statement",
        preset: "tree",
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
      },
    });

    const { getDefaultReportBuilderConfig } = await import("../../api/crispy");
    const defaults = await getDefaultReportBuilderConfig("financial_statement");

    expect(defaults.renderer).toBe("financial_statement");
    expect((call as any).mock.calls[0][0]).toMatchObject({
      method: "crispy_print.api.v1.get_default_report_builder_config",
      args: { report_renderer: "financial_statement" },
    });
  });
});
