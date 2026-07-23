import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick, ref } from "vue";
import CrispyPFB from "../../pages/CrispyPFB.vue";

const STORAGE_KEY = "crispy-print:format-builder-layout:v1";
let storage: Record<string, string>;
const createFormatFromSample = vi.fn(async (_args: Record<string, unknown>) => ({
  success: true,
  name: "Sample Sales Invoice Starter",
  sample_id: "sales-invoice-basic",
  company: "ACME",
  warnings: ["Adjusted presentation settings"],
}));

const makeStore = (): Record<string, unknown> => ({
  fields: ref([]),
  reportBuilderFields: ref([]),
  reportBuilderConfig: ref({
    mode: "basic",
    font_family: "Inter",
    show_filters: true,
    show_summary: true,
    include_total_row: true,
  }),
  reportBasicReadOnly: ref(false),
  crispyFormat: ref({
    name: "CPF-Test",
    doc_type: "Sales Invoice",
    crispy_format_type: "DocType",
    company: "ACME",
    is_default: 1,
    pdf_standard: "PDF/A-2u",
  }),
  formatType: ref("DocType"),
  isReportMode: ref(false),
  loading: ref(false),
  dirty: ref(false),
  layout: ref({ sections: [] }),
  presentation_settings: ref({
    source: "branding_profile",
    branding: { company: "ACME", profile: "CBP-1" },
  }),
  rawTypst: ref(false),
  typstCode: ref(""),
  markDirty: vi.fn(),
  fetch: vi.fn(async () => {}),
});

vi.mock("../../composables/useStore", () => ({
  useStore: vi.fn(),
}));

vi.mock("../../utils/routes", () => ({
  getCrispyBuilderFormatName: vi.fn((): string | null => null),
}));

vi.mock("../../api/crispy", () => ({
  createFormatFromSample: (args: Record<string, unknown>) =>
    createFormatFromSample(args),
  getCompanies: vi.fn(async () => []),
  listSampleFormats: vi.fn(async () => []),
}));

async function mountBuilder() {
  const { useStore } = await import("../../composables/useStore");
  (useStore as any).mockReturnValue(makeStore());

  const wrapper = mount(CrispyPFB, {
    global: {
      stubs: {
        FieldsPane: {
          template:
            '<div class="pane pane--fields" data-test="fields-pane"><slot name="header-actions" /></div>',
        },
        LayoutPane: {
          template: '<div class="pane pane--layout" data-test="layout-pane" />',
        },
        TypstCodePane: { template: '<div data-test="typst-pane" />' },
        PreviewPane: {
          template:
            '<div class="pane pane--preview" data-test="preview-pane" />',
        },
        SettingsPane: {
          template:
            '<div class="pane pane--settings" data-test="settings-pane"><slot name="header-actions" /></div>',
        },
        SampleFormatsDialog: {
          props: ["open", "submitting"],
          emits: ["close", "confirm"],
          template:
            '<div v-if="open" data-test="sample-dialog"><button data-test="sample-confirm" @click="$emit(\'confirm\', { sample_id: \'sales-invoice-basic\', company: \'ACME\', name: \'Sample Sales Invoice Starter\', set_default: true })">Create</button></div>',
        },
      },
    },
  });
  await nextTick();
  return wrapper;
}

describe("CrispyPFB persisted pane layout", () => {
  beforeEach(() => {
    storage = {};
    Object.defineProperty(window, "localStorage", {
      value: {
        getItem: vi.fn((key: string) => storage[key] ?? null),
        setItem: vi.fn((key: string, value: string) => {
          storage[key] = String(value);
        }),
        removeItem: vi.fn((key: string) => {
          delete storage[key];
        }),
        clear: vi.fn(() => {
          storage = {};
        }),
      },
      configurable: true,
    });
    vi.clearAllMocks();
    createFormatFromSample.mockClear();
    (globalThis as any).frappe = {
      show_alert: vi.fn(),
      msgprint: vi.fn(),
      set_route: vi.fn(),
      router: { on: vi.fn() },
    };
  });

  it("starts collapsed, toggles side panes, and persists expanded state", async () => {
    const wrapper = await mountBuilder();

    expect(wrapper.find(".pane-shell--fields").classes()).toContain(
      "pane-shell--collapsed",
    );

    await wrapper.find(".pane-toggle--fields").trigger("click");
    await nextTick();

    expect(wrapper.find(".pane-shell--fields").classes()).not.toContain(
      "pane-shell--collapsed",
    );
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.fieldsCollapsed).toBe(false);
  });

  it("loads persisted layout state and clamps invalid split values", async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        fieldsCollapsed: true,
        settingsCollapsed: true,
        middleSplitPercent: 95,
        previewMode: "normal",
      }),
    );

    const wrapper = await mountBuilder();
    await nextTick();

    expect(wrapper.find(".pane-shell--fields").classes()).toContain(
      "pane-shell--collapsed",
    );
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.middleSplitPercent).toBe(70);
    expect(stored.previewZoomMode).toBeUndefined();
    expect(stored.previewZoomPercent).toBeUndefined();
  });

  it("falls back safely when persisted state is malformed", async () => {
    window.localStorage.setItem(STORAGE_KEY, "{bad json");

    const wrapper = await mountBuilder();
    await nextTick();

    expect(wrapper.find(".pane-shell--fields").classes()).toContain(
      "pane-shell--collapsed",
    );
    expect(wrapper.attributes("style")).toContain("50fr");
  });

  it("drags and clamps the middle split, then resets on double click", async () => {
    const wrapper = await mountBuilder();
    const layout = wrapper.find(".pane--layout").element as HTMLElement;
    const preview = wrapper.find(".pane--preview").element as HTMLElement;
    layout.getBoundingClientRect = vi.fn(
      () =>
        ({
          left: 100,
          right: 500,
          top: 0,
          bottom: 0,
          width: 400,
          height: 0,
        }) as DOMRect,
    );
    preview.getBoundingClientRect = vi.fn(
      () =>
        ({
          left: 510,
          right: 900,
          top: 0,
          bottom: 0,
          width: 390,
          height: 0,
        }) as DOMRect,
    );

    await wrapper.find(".middle-resize-handle").trigger("pointerdown", {
      clientX: 500,
      button: 0,
    });
    window.dispatchEvent(
      new MouseEvent("pointermove", { clientX: 1000 }) as any,
    );
    window.dispatchEvent(new MouseEvent("pointerup") as any);
    await nextTick();

    let stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.middleSplitPercent).toBe(70);

    await wrapper.find(".middle-resize-handle").trigger("dblclick");
    await nextTick();

    stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "{}");
    expect(stored.middleSplitPercent).toBe(50);
  });

  it("creates an example format and routes to the new builder record", async () => {
    const store = makeStore();
    const { useStore } = await import("../../composables/useStore");
    (useStore as any).mockReturnValue(store);

    const wrapper = mount(CrispyPFB, {
      global: {
        stubs: {
          FieldsPane: {
            template:
              '<div class="pane pane--fields" data-test="fields-pane"><slot name="header-actions" /></div>',
          },
          LayoutPane: {
            template:
              '<div class="pane pane--layout" data-test="layout-pane" />',
          },
          TypstCodePane: { template: '<div data-test="typst-pane" />' },
          PreviewPane: {
            template:
              '<div class="pane pane--preview" data-test="preview-pane" />',
          },
          SettingsPane: {
            template:
              '<div class="pane pane--settings" data-test="settings-pane"><slot name="header-actions" /></div>',
          },
          SampleFormatsDialog: {
            props: ["open", "submitting"],
            emits: ["close", "confirm"],
            template:
              '<div v-if="open" data-test="sample-dialog"><button data-test="sample-confirm" @click="$emit(\'confirm\', { sample_id: \'sales-invoice-basic\', company: \'ACME\', name: \'Sample Sales Invoice Starter\', set_default: true })">Create</button></div>',
          },
        },
      },
    });

    await wrapper.find(".pane-toggle--fields").trigger("click");
    await nextTick();
    await wrapper.find(".examples-button").trigger("click");
    await nextTick();
    await wrapper.find("[data-test='sample-confirm']").trigger("click");
    await nextTick();

    expect(createFormatFromSample).toHaveBeenCalledWith({
      sample_id: "sales-invoice-basic",
      company: "ACME",
      name: "Sample Sales Invoice Starter",
      set_default: true,
    });
    expect((globalThis as any).frappe.set_route).toHaveBeenCalledWith(
      "crispy-format-builder",
      "Sample Sales Invoice Starter",
    );
    expect(store.fetch).toHaveBeenCalledWith("Sample Sales Invoice Starter");
    expect((globalThis as any).frappe.msgprint).toHaveBeenCalled();
  });

  it("warns when multiple default Branding Profiles match the company", async () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        fieldsCollapsed: true,
        settingsCollapsed: false,
        middleSplitPercent: 50,
        previewMode: "normal",
      }),
    );

    const { useStore } = await import("../../composables/useStore");
    (useStore as any).mockReturnValue(makeStore());

    const wrapper = mount(CrispyPFB, {
      global: {
        stubs: {
          FieldsPane: {
            template:
              '<div class="pane pane--fields" data-test="fields-pane"><slot name="header-actions" /></div>',
          },
          LayoutPane: {
            template:
              '<div class="pane pane--layout" data-test="layout-pane" />',
          },
          TypstCodePane: { template: '<div data-test="typst-pane" />' },
          PreviewPane: {
            template:
              '<div class="pane pane--preview" data-test="preview-pane" />',
          },
          SettingsPane: {
            emits: ["branding-profiles-change"],
            mounted() {
              this.$emit("branding-profiles-change", [
                {
                  name: "CBP-1",
                  profile_name: "Invoice Brand",
                  company: "ACME",
                  is_default: 1,
                },
                {
                  name: "CBP-2",
                  profile_name: "Contract Brand",
                  company: "ACME",
                  is_default: 1,
                },
              ]);
            },
            template:
              '<div class="pane pane--settings" data-test="settings-pane"><slot name="header-actions" /><slot name="before-form" /></div>',
          },
        },
      },
    });
    await nextTick();

    await wrapper.find("button.settings-pane__section-header").trigger("click");
    await nextTick();

    expect(wrapper.text()).toContain(
      "Multiple default Branding Profiles match this company",
    );
  });
});
