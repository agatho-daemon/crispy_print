import { flushPromises } from "@vue/test-utils";
import { nextTick } from "vue";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../api/frappe", () => ({
  withDoctype: vi.fn(async () => {}),
}));

vi.mock("../../api/crispy", () => ({
  getCrispyFormat: vi.fn(),
  getDefaultReportBuilderConfig: vi.fn(async () => ({})),
  getBrandingProfilePresentationSettings: vi.fn(async () => ({
    source: "branding_profile",
    branding: {
      profile: "CBP-1",
      company: "ACME",
      mode: "none",
      letterhead: "",
      letterhead_image: "",
      logo: { company: "ACME", image: "", size: 25, dx: 0, dy: 0 },
    },
  })),
  duplicateCrispyFormatForCompany: vi.fn(),
  duplicateCrispyTemplateForCompany: vi.fn(),
  saveCrispyFormat: vi.fn(async () => {}),
}));

vi.mock("../../utils/formatLoader", () => ({
  parseCrispyFormatDoc: vi.fn(),
  resolveLetterheadDoc: vi.fn(async (): Promise<null> => null),
  clearLetterheadCache: vi.fn(),
}));

describe("useStore report builder table style sync", () => {
  beforeEach(() => {
    vi.resetModules();
    (globalThis as any).__ = (msg: string): string => msg;
    (globalThis as any).frappe = {
      call: vi.fn(async () => ({ message: {} })),
      get_meta: vi.fn(() => ({ fields: [] as unknown[] })),
      show_alert: vi.fn(),
    };
  });

  it("applies report table styles when table settings are unset/default", async () => {
    const { getCrispyFormat } = await import("../../api/crispy");
    const { parseCrispyFormatDoc } = await import("../../utils/formatLoader");
    (getCrispyFormat as any).mockResolvedValue({
      name: "FMT-1",
      crispy_format_type: "Report",
      generic_report_type: "Grid",
      raw_typst: 0,
      typst_code: "",
    });
    (parseCrispyFormatDoc as any).mockReturnValue({
      layout: { sections: [] as unknown[] },
      presentation_settings: {
        page: {
          size: "A4",
          orientation: "portrait",
          margins: { top: 25, bottom: 20, left: 20, right: 20 },
        },
        branding: {
          mode: "none",
          letterhead: "",
          letterhead_image: "",
          logo: { company: "", image: "", size: 25, dx: 0, dy: 0 },
        },
        language: "en",
        report: {
          header_fill: "#112233",
          row_striping: true,
          row_stripe_fill: "#445566",
        },
      },
      docHeader: "",
      docFooter: "",
    });

    const { useStore } = await import("../../composables/useStore");
    const store = useStore();
    await store.fetch("FMT-1");

    expect(
      store.presentation_settings.value.table?.header.backgroundColor,
    ).toBe(store.reportBuilderConfig.value.header_fill);
    expect(store.presentation_settings.value.table?.stripe.enabled).toBe(
      Boolean(store.reportBuilderConfig.value.row_striping),
    );
    expect(store.presentation_settings.value.table?.stripe.color).toBe(
      store.reportBuilderConfig.value.row_stripe_fill,
    );
  });

  it("does not override explicitly configured table styles", async () => {
    const { getCrispyFormat } = await import("../../api/crispy");
    const { parseCrispyFormatDoc } = await import("../../utils/formatLoader");
    (getCrispyFormat as any).mockResolvedValue({
      name: "FMT-2",
      crispy_format_type: "Report",
      generic_report_type: "Grid",
      raw_typst: 0,
      typst_code: "",
    });
    (parseCrispyFormatDoc as any).mockReturnValue({
      layout: { sections: [] as unknown[] },
      presentation_settings: {
        page: {
          size: "A4",
          orientation: "portrait",
          margins: { top: 25, bottom: 20, left: 20, right: 20 },
        },
        branding: {
          mode: "none",
          letterhead: "",
          letterhead_image: "",
          logo: { company: "", image: "", size: 25, dx: 0, dy: 0 },
        },
        language: "en",
        table: {
          inset: { top: 2, right: 2, bottom: 2, left: 2 },
          stroke: { width: 0.5, color: "#e2e8f0" },
          header: { backgroundColor: "#aa0000" },
          stripe: { enabled: false, color: "#00bb00" },
          typography: {
            header: {
              fontFamily: "Inter",
              fontSize: "9pt",
              fontStyle: "normal",
              fontWeight: "semibold",
              color: "#0f172a",
            },
            body: {
              fontFamily: "Inter",
              fontSize: "9pt",
              fontStyle: "normal",
              fontWeight: "regular",
              color: "#0f172a",
            },
          },
        },
        report: {
          header_fill: "#112233",
          row_striping: true,
          row_stripe_fill: "#445566",
        },
      },
      docHeader: "",
      docFooter: "",
    });

    const { useStore } = await import("../../composables/useStore");
    const store = useStore();
    await store.fetch("FMT-2");

    expect(
      store.presentation_settings.value.table?.header.backgroundColor,
    ).toBe("#aa0000");
    expect(store.presentation_settings.value.table?.stripe.enabled).toBe(false);
    expect(store.presentation_settings.value.table?.stripe.color).toBe(
      "#00bb00",
    );
  });

  it("does not loop branding-profile requests when basic report Typst synchronizes", async () => {
    const { getBrandingProfilePresentationSettings } = await import("../../api/crispy");
    const { useStore } = await import("../../composables/useStore");
    const store = useStore();

    store.crispyFormat.value = {
      name: "FMT-BRANDING",
      crispy_format_type: "Report",
      raw_typst: 0,
    } as any;
    store.presentation_settings.value.source = "branding_profile";
    store.presentation_settings.value.branding.profile = "CBP-1";
    store.presentation_settings.value.branding.company = "ACME";

    for (let index = 0; index < 5; index += 1) {
      await flushPromises();
      await nextTick();
    }
    const settledRequestCount = vi.mocked(getBrandingProfilePresentationSettings).mock.calls.length;

    for (let index = 0; index < 5; index += 1) {
      await flushPromises();
      await nextTick();
    }

    expect(settledRequestCount).toBeGreaterThan(0);
    expect(settledRequestCount).toBeLessThanOrEqual(2);
    expect(getBrandingProfilePresentationSettings).toHaveBeenCalledTimes(
      settledRequestCount,
    );
  });
});
