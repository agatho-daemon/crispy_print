import { flushPromises, mount, shallowMount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";

const compileReportPreviewRequest = vi.fn(async (_args: Record<string, unknown>) => ({
  success: true,
  typst_source: "#set page(width: 100pt, height: 100pt)\nReport",
  pdf_data: "JVBERi0xLjQK",
  asset_files: [],
}));
const createIssuedDocumentSnapshotRequest = vi.fn();
const compileTypstRequest = vi.fn(async () => ({ pdf_data: "JVBERi0xLjQK" }));
let sampleSnapshotSequence = 0;
const getSampleReportDataRequest = vi.fn(
  async (_args: Record<string, any>): Promise<Record<string, any>> => {
  sampleSnapshotSequence += 1;
  return { preview_snapshot_id: `snapshot-${sampleSnapshotSequence}` };
  },
);

vi.mock("../../api/crispy", () => ({
  compileReportPreview: (args: Record<string, unknown>) =>
    compileReportPreviewRequest(args),
  compileTypst: compileTypstRequest,
  createIssuedDocumentSnapshot: createIssuedDocumentSnapshotRequest,
  getActiveCrispyTemplatesForDocument: vi.fn(async () => []),
  getResolvedCrispyTemplateForDocument: vi.fn(),
  getSampleReportData: getSampleReportDataRequest,
}));

vi.mock("../../utils/formatLoader", () => ({
  loadFormatData: vi.fn(async () => ({
    formatDoc: {
      name: "AR Format",
      effective_company: "ACME",
      pdf_standard: "PDF/A-2u",
    },
    layout: { sections: [] },
    presentation_settings: {
      source: "custom",
      branding: { company: "ACME", mode: "none" },
    },
  })),
  parseCrispyFormatDoc: vi.fn(),
  resolveLetterheadDoc: vi.fn(async () => null),
}));

vi.mock("../../composables/useBrandingData", () => ({
  useBrandingData: () => ({
    availableLetterheads: ref([]),
    loadingLetterheads: ref(false),
    availableCompanies: ref([]),
    loadingCompanies: ref(false),
    resolveCompanyLogo: vi.fn(() => ""),
    fetchLetterheads: vi.fn(async () => {}),
    fetchCompanies: vi.fn(async () => {}),
  }),
}));

vi.mock("../../utils/effectivePresentationSettings", async () => {
  const presentation = await import("../../utils/presentation_settings");
  return {
    resolve_effective_presentation_settings: vi.fn(async (settings) =>
      presentation.merge_presentation_settings(
        presentation.default_presentation_settings,
        settings,
      ),
    ),
  };
});

vi.mock("../../utils/typstTypography", () => ({
  fetchTypstFonts: vi.fn(async () => ["Inter"]),
  formatPt: (value: number) => `${value}pt`,
  parseSize: () => ({ value: 10, unit: "pt" }),
}));

describe("standalone report preview runtime", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    sampleSnapshotSequence = 0;
    (globalThis as any).__ = (message: string) => message;
    (globalThis as any).frappe = {
      call: vi.fn(async () => ({
        message: {
          formats: [{ name: "AR Format" }],
          default_format: "AR Format",
        },
      })),
      show_alert: vi.fn(),
    };
  });

  it("routes DocType printing through the compiled preview PDF", async () => {
    const printRequest = vi.fn();
    window.addEventListener("crispy-preview:request-pdf", printRequest, {
      once: true,
    });
    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = shallowMount(CrispyPP, {
      props: {
        doctype: "Sales Invoice",
        docname: "ACC-SINV-2026-04953",
      },
    });
    await flushPromises();

    await (wrapper.vm as any).printPDF();

    expect(printRequest).toHaveBeenCalledOnce();
    expect((printRequest.mock.calls[0][0] as CustomEvent).detail).toEqual({
      action: "print",
    });
    wrapper.unmount();
  });

  it("reaches the report compile API once on initial mount", async () => {
    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = mount(CrispyPP, {
      props: {
        source: "report",
        report: "Accounts Receivable",
        reportFilters: { company: "ACME" },
        reportColumns: [{ fieldname: "party", label: "Party" }],
      },
    });

    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    expect(compileReportPreviewRequest).toHaveBeenCalledTimes(1);
    expect(compileReportPreviewRequest.mock.calls[0][0]).toMatchObject({
      report: "Accounts Receivable",
      format_name: "AR Format",
      filters: { company: "ACME" },
    });
    expect(createIssuedDocumentSnapshotRequest).not.toHaveBeenCalled();

    wrapper.unmount();
  });

  it("views the report PDF without creating a CID snapshot", async () => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:view-report"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    const openWindow = vi.spyOn(window, "open").mockImplementation(() => null);
    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = mount(CrispyPP, {
      props: {
        source: "report",
        report: "Accounts Receivable",
        reportFilters: { company: "ACME" },
        reportColumns: [{ fieldname: "party", label: "Party" }],
      },
    });
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    await (wrapper.vm as any).generatePDF();

    expect(compileReportPreviewRequest).toHaveBeenCalledOnce();
    expect(compileTypstRequest).not.toHaveBeenCalled();
    expect(openWindow).toHaveBeenCalledWith("blob:view-report", "_blank");
    expect(createIssuedDocumentSnapshotRequest).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it("downloads the report PDF without creating a CID snapshot", async () => {
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:download-report"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });
    const clickDownload = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = shallowMount(CrispyPP, {
      props: {
        source: "report",
        report: "Accounts Payable",
        reportFilters: { company: "ACME" },
        reportColumns: [{ fieldname: "party", label: "Party" }],
      },
    });
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    await (wrapper.vm as any).downloadPDF();

    expect(compileReportPreviewRequest).toHaveBeenCalledOnce();
    expect(compileTypstRequest).not.toHaveBeenCalled();
    expect(clickDownload).toHaveBeenCalledOnce();
    expect(createIssuedDocumentSnapshotRequest).not.toHaveBeenCalled();
    wrapper.unmount();
  });

  it("prints the compiled report PDF without creating a CID snapshot", async () => {
    const loadHandlers: Array<() => void> = [];
    const printWindow = {
      addEventListener: vi.fn((event: string, callback: () => void) => {
        if (event === "load") loadHandlers.push(callback);
      }),
      focus: vi.fn(),
      print: vi.fn(),
    };
    const openWindow = vi
      .spyOn(window, "open")
      .mockReturnValue(printWindow as unknown as Window);
    Object.defineProperty(URL, "createObjectURL", {
      configurable: true,
      value: vi.fn(() => "blob:salary-report"),
    });
    Object.defineProperty(URL, "revokeObjectURL", {
      configurable: true,
      value: vi.fn(),
    });

    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = shallowMount(CrispyPP, {
      props: {
        source: "report",
        report: "Salary Register",
        reportFilters: { company: "ACME" },
        reportColumns: [{ fieldname: "employee", label: "Employee" }],
      },
    });
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    await (wrapper.vm as any).printPDF();
    expect(openWindow).toHaveBeenCalledWith("blob:salary-report", "_blank");
    expect(loadHandlers).toHaveLength(1);
    loadHandlers[0]();

    expect(printWindow.focus).toHaveBeenCalledOnce();
    expect(printWindow.print).toHaveBeenCalledOnce();
    expect(createIssuedDocumentSnapshotRequest).not.toHaveBeenCalled();
    expect((globalThis as any).frappe.show_alert).toHaveBeenCalledWith({
      message: "Print dialog opened.",
      indicator: "green",
    });

    wrapper.unmount();
  });

  it("reruns report data for filter changes but reuses it for presentation changes", async () => {
    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = mount(CrispyPP, {
      props: {
        source: "report",
        report: "General Ledger",
        reportFilters: {
          company: "ACME",
          from_date: "2026-01-01",
          to_date: "2026-01-31",
        },
        reportColumns: [{ fieldname: "account", label: "Account" }],
      },
      global: {
        stubs: {
          PreviewRenderer: true,
          PreviewDiagnosticsDrawer: true,
        },
      },
    });
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    expect(getSampleReportDataRequest).toHaveBeenCalledTimes(1);
    expect(compileReportPreviewRequest).toHaveBeenCalledTimes(1);
    expect(compileReportPreviewRequest.mock.calls[0][0].preview_snapshot_id).toBe(
      "snapshot-1",
    );

    const fontSize = wrapper.get('input[type="number"]');
    await fontSize.setValue("11");
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    expect(getSampleReportDataRequest).toHaveBeenCalledTimes(1);
    expect(compileReportPreviewRequest).toHaveBeenCalledTimes(2);
    expect(compileReportPreviewRequest.mock.calls[1][0].preview_snapshot_id).toBe(
      "snapshot-1",
    );

    await wrapper.setProps({
      reportFilters: {
        company: "ACME",
        from_date: "2026-02-01",
        to_date: "2026-02-28",
      },
    });
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    expect(getSampleReportDataRequest).toHaveBeenCalledTimes(2);
    expect(getSampleReportDataRequest.mock.calls[1][0].filters).toMatchObject({
      from_date: "2026-02-01",
      to_date: "2026-02-28",
    });
    expect(compileReportPreviewRequest).toHaveBeenCalledTimes(3);
    expect(compileReportPreviewRequest.mock.calls[2][0].preview_snapshot_id).toBe(
      "snapshot-2",
    );
    wrapper.unmount();
  });

  it("shows a Run Preview again state when a snapshot expires", async () => {
    compileReportPreviewRequest.mockRejectedValueOnce(
      new Error("Report preview data has expired. Run Preview again."),
    );
    const { default: CrispyPP } = await import("../../pages/CrispyPP.vue");
    const wrapper = mount(CrispyPP, {
      props: {
        source: "report",
        report: "Accounts Receivable",
        reportFilters: { company: "ACME" },
        reportColumns: [{ fieldname: "party", label: "Party" }],
      },
      global: {
        stubs: {
          PreviewRenderer: true,
          PreviewDiagnosticsDrawer: true,
        },
      },
    });

    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    const retry = wrapper.get("button.btn-default");
    expect(retry.text()).toBe("Run Preview again");
    expect(wrapper.text()).toContain("Report preview access expired");

    const firstTabId = getSampleReportDataRequest.mock.calls[0][0].preview_tab_id;
    expect(firstTabId).toBeTruthy();
    expect(compileReportPreviewRequest.mock.calls[0][0].preview_tab_id).toBe(firstTabId);

    await retry.trigger("click");
    await flushPromises();
    await new Promise((resolve) => setTimeout(resolve, 300));
    await flushPromises();

    expect(getSampleReportDataRequest).toHaveBeenCalledTimes(2);
    expect(getSampleReportDataRequest.mock.calls[1][0].preview_tab_id).toBe(firstTabId);
    expect(compileReportPreviewRequest.mock.calls[1][0]).toMatchObject({
      preview_snapshot_id: "snapshot-2",
      preview_tab_id: firstTabId,
    });
    expect(wrapper.text()).not.toContain("Report preview access expired");
    wrapper.unmount();
  });
});
