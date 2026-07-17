import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick, reactive, ref } from "vue";
import SettingsPane from "../../components/SettingsPane.vue";
import TypographyStyleEditor from "../../components/TypographyStyleEditor.vue";

const hoisted = vi.hoisted(() => ({
  storeMock: {
    fields: { value: [] as unknown[] },
    loading: { value: false },
    initializing: { value: false },
    isReportMode: { value: false },
    rawTypst: { value: false },
    reportBuilderConfig: {
      value: {
        preset: "grid",
        font_family: "Inter",
        font_size_pt: 9,
        show_filters: true,
        show_summary: true,
        include_total_row: true,
        chart_enabled: true,
        chart_representation: "auto",
        chart_card_border: true,
        chart_width_percent: 100,
        chart_max_height_pt: 220,
        chart_spacing_top_pt: 0,
        chart_spacing_bottom_pt: 12,
      },
    },
    reportBasicReadOnly: { value: false },
    updateReportBuilderConfig: vi.fn(),
  },
}));

vi.mock("../../api/crispy", () => ({
  getTypstLocalFonts: vi.fn(async () => ["Inter", "Serif"]),
  getTypstFontFaces: vi.fn(async () => []),
  getBrandingProfiles: vi.fn(async () => [
    {
      name: "CBP-1",
      profile_name: "Default Brand",
      company: "ACME",
      is_default: 1,
    },
  ]),
}));

vi.mock("../../composables/useBrandingData", () => ({
  useBrandingData: () => ({
    availableLetterheads: ref(["LH-1"]),
    loadingLetterheads: ref(false),
    availableCompanies: ref([{ name: "ACME", abbr: "AC" }]),
    loadingCompanies: ref(false),
    resolveCompanyLogo: (company: string) =>
      company === "ACME" ? "/files/acme.png" : "",
    fetchLetterheads: vi.fn(),
    fetchCompanies: vi.fn(),
  }),
}));

vi.mock("../../composables/useStore", () => ({
  useStore: () => hoisted.storeMock,
}));

describe("SettingsPane", () => {
  beforeEach(() => {
    hoisted.storeMock.isReportMode.value = false;
    hoisted.storeMock.rawTypst.value = false;
    hoisted.storeMock.updateReportBuilderConfig.mockClear();
  });

  it("updates logo image when company changes", async () => {
    const presentation_settings = reactive({
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      source: "custom",
      typography: {},
      qr: {},
    }) as any;

    const markDirty = vi.fn();

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });

    const headers = wrapper.findAll("button.settings-pane__section-header");
    const brandingHeader = headers.find((btn) =>
      btn.text().includes("Branding"),
    );
    expect(brandingHeader).toBeTruthy();
    await brandingHeader!.trigger("click");
    await nextTick();

    const selects = wrapper.findAll("select");
    const brandingSelect = selects.find((select) =>
      select.find('option[value="logo"]').exists(),
    );
    expect(brandingSelect).toBeTruthy();
    await brandingSelect!.setValue("logo");
    await nextTick();

    const companySelect = wrapper
      .findAll("select")
      .find((select) => select.find('option[value="ACME"]').exists());
    expect(companySelect).toBeTruthy();
    await companySelect!.setValue("ACME");
    await nextTick();

    expect(presentation_settings.branding.logo.image).toBe("/files/acme.png");
  });

  it("keeps chart controls under Chart Settings in report mode", async () => {
    hoisted.storeMock.isReportMode.value = true;
    const presentation_settings = reactive({
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      source: "custom",
      typography: {},
      qr: {},
      table: {
        inset: { top: 2, right: 2, bottom: 2, left: 2 },
        stroke: { width: 0.5, color: "#e2e8f0" },
        header: { backgroundColor: "#f1f5f9" },
        stripe: { enabled: false, color: "#f8fafc" },
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
    }) as any;

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty: vi.fn() },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });

    const headers = wrapper.findAll("button.settings-pane__section-header");
    const reportTemplateHeader = headers.find((btn) =>
      btn.text().includes("Report Template"),
    );
    expect(reportTemplateHeader).toBeTruthy();
    await reportTemplateHeader!.trigger("click");
    await nextTick();

    const reportTemplateCardText = wrapper.text();
    expect(reportTemplateCardText).not.toContain("Header Fill");
    expect(reportTemplateCardText).not.toContain("Row Stripe Fill");
    expect(reportTemplateCardText).not.toContain("Chart Block");

    const chartHeader = wrapper
      .findAll("button.settings-pane__section-header")
      .find((btn) => btn.text().includes("Chart Settings"));
    expect(chartHeader).toBeTruthy();
    await chartHeader!.trigger("click");
    await nextTick();
    expect(wrapper.text()).toContain("Enable Chart");
    expect(wrapper.text()).toContain("Chart Representation");
    expect(wrapper.text()).toContain("Show Summary");
    const representationSelect = wrapper
      .findAll("select")
      .find((select) => select.find('option[value="horizontal_bar"]').exists());
    expect(representationSelect).toBeTruthy();
    await representationSelect!.setValue("bar");
    expect(hoisted.storeMock.updateReportBuilderConfig).toHaveBeenCalledWith(
      { chart_representation: "bar" },
      { preview: "live" },
    );

    hoisted.storeMock.isReportMode.value = false;
  });

  it("keeps format override settings available with a branding profile", async () => {
    const presentation_settings = reactive({
      source: "custom",
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      typography: {},
      qr: {},
    }) as any;
    const markDirty = vi.fn();

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });
    await flushPromises();
    await nextTick();

    expect(wrapper.text()).toContain("Page Settings");
    const profileSelect = wrapper
      .findAll("select")
      .find((select) => select.find('option[value="CBP-1"]').exists());
    expect(profileSelect).toBeTruthy();
    await profileSelect!.setValue("CBP-1");
    await nextTick();

    expect(presentation_settings.branding.profile).toBe("CBP-1");
    expect(wrapper.text()).toContain("Page Settings");
    expect(wrapper.text()).toContain("Typography");
    expect(wrapper.text()).toContain("Enable QR Code");
    // Company identity remains owned by the Branding Profile.
    expect(wrapper.find('option[value="logo"]').exists()).toBe(false);

    await profileSelect!.setValue("custom");
    await nextTick();
    expect(presentation_settings.branding.profile).toBe("");
    expect(wrapper.text()).toContain("Page Settings");
    expect(markDirty).toHaveBeenCalled();
  });

  it("uses debounced preview policy for numeric settings input", async () => {
    const presentation_settings = reactive({
      source: "custom",
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      typography: {},
      qr: {},
    }) as any;
    const markDirty = vi.fn();

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });

    const pageHeader = wrapper
      .findAll("button.settings-pane__section-header")
      .find((btn) => btn.text().includes("Page Settings"));
    expect(pageHeader).toBeTruthy();
    await pageHeader!.trigger("click");
    await nextTick();
    markDirty.mockClear();

    const marginInput = wrapper.find(".box-sides-editor__control");
    expect(marginInput.exists()).toBe(true);
    await marginInput.trigger("input");
    expect(markDirty).toHaveBeenCalledWith({ preview: "debounce" });
  });

  it("routes report settings through explicit store actions", async () => {
    hoisted.storeMock.isReportMode.value = true;
    const presentation_settings = reactive({
      source: "custom",
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      typography: {},
      qr: {},
    }) as any;

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty: vi.fn() },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });

    const pageHeader = wrapper
      .findAll("button.settings-pane__section-header")
      .find((btn) => btn.text().includes("Report Template"));
    expect(pageHeader).toBeTruthy();
    await pageHeader!.trigger("click");
    await nextTick();

    const preset = wrapper.find('select option[value="Summary Focus"]').element
      .parentElement as HTMLSelectElement;
    await wrapper
      .findAll("select")
      .find((select) => select.element === preset)!
      .setValue("Summary Focus");
    expect(hoisted.storeMock.updateReportBuilderConfig).toHaveBeenCalledWith(
      { layout_style: "Summary Focus" },
      { preview: "live" },
    );

    hoisted.storeMock.updateReportBuilderConfig.mockClear();
    const fontSizeInput = wrapper.find('input[min="1"][step="1"]');
    await fontSizeInput.setValue("11");
    expect(hoisted.storeMock.updateReportBuilderConfig).toHaveBeenCalledWith(
      { font_size_pt: 11 },
      { preview: "debounce" },
    );
  });

  it("renders typography controls when saved typography is partially empty", async () => {
    const presentation_settings = reactive({
      source: "custom",
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      typography: {},
      qr: {},
    }) as any;

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty: vi.fn() },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });

    const typographyHeader = wrapper
      .findAll("button.settings-pane__section-header")
      .find((btn) => btn.text().includes("Typography"));
    expect(typographyHeader).toBeTruthy();
    await typographyHeader!.trigger("click");
    await nextTick();

    expect(wrapper.text()).toContain("Section Labels");
    expect(wrapper.text()).toContain("Field Labels");
    expect(wrapper.text()).toContain("Field Values");
    expect(presentation_settings.typography.sectionLabel.fontFamily).toBe(
      "Inter",
    );
  });

  it("hides only raw-owned presentation sections in raw typst mode", async () => {
    hoisted.storeMock.rawTypst.value = true;
    const presentation_settings = reactive({
      source: "custom",
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      typography: {},
      qr: {},
      table: {},
    }) as any;

    const wrapper = mount(SettingsPane, {
      props: { presentation_settings, markDirty: vi.fn() },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });

    expect(wrapper.text()).not.toContain("Print Behavior");
    expect(wrapper.text()).not.toContain("Page Settings");
    expect(wrapper.text()).not.toContain("Typography");
    expect(wrapper.text()).not.toContain("Table Settings");
    expect(wrapper.text()).toContain("Branding");
    expect(wrapper.text()).toContain("Enable QR Code");
  });

  it("auto-selects the default branding profile for fresh undecided settings", async () => {
    const presentation_settings = reactive({
      source: "",
      page: {
        size: "A4",
        orientation: "portrait",
        margins: { top: 10, bottom: 10, left: 10, right: 10 },
      },
      branding: {
        profile: "",
        mode: "none",
        letterhead: "",
        letterhead_image: "",
        logo: { company: "", image: "", size: 20, dx: 0, dy: 0 },
      },
      typography: {},
      qr: {},
    }) as any;
    const markDirty = vi.fn();

    mount(SettingsPane, {
      props: { presentation_settings, markDirty },
      global: {
        stubs: {
          ColorInput: true,
          QrFieldsDialog: true,
        },
      },
    });
    await flushPromises();
    await nextTick();

    expect(presentation_settings.source).toBe("branding_profile");
    expect(presentation_settings.branding.profile).toBe("CBP-1");
    expect(markDirty).toHaveBeenCalled();
  });

  it("restricts typography weight and style options to the selected font faces", async () => {
    const wrapper = mount(TypographyStyleEditor, {
      props: {
        title: "Section Labels",
        availableFonts: ["Rajdhani"],
        fontFaces: [
          {
            family: "Rajdhani",
            styles: ["normal"],
            weights: ["light", "regular", "medium", "semibold", "bold"],
            faces: [],
          },
        ],
        modelValue: {
          fontFamily: "Rajdhani",
          fontSize: "12pt",
          fontStyle: "italic",
          fontWeight: "black",
          color: "#1e293b",
        },
      },
    });
    await nextTick();

    const selects = wrapper.findAll("select");
    const styleOptions = selects[1]
      .findAll("option")
      .map((option) => option.text());
    const weightOptions = selects[2]
      .findAll("option")
      .map((option) => option.text());

    expect(styleOptions).toEqual(["Normal"]);
    expect(weightOptions).toEqual([
      "Light",
      "Regular",
      "Medium",
      "Semibold",
      "Bold",
    ]);
    expect(weightOptions).not.toContain("Black");
    expect(wrapper.emitted("update:modelValue")?.[0]?.[0]).toMatchObject({
      fontStyle: "normal",
      fontWeight: "bold",
    });
  });
});
