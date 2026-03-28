import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ref } from "vue";
import CrispyPFB from "../../pages/CrispyPFB.vue";

const makeStore = (rawTypst: boolean): Record<string, unknown> => ({
  fields: ref([]),
  reportBuilderFields: ref([]),
  reportBuilderConfig: ref({
    show_filters: true,
    show_summary: true,
    include_total_row: true,
  }),
  reportBuilderMode: ref("basic"),
  reportColumns: ref([]),
  isReportMode: ref(true),
  loading: ref(false),
  pageSettings: ref({}),
  rawTypst: ref(rawTypst),
  markDirty: vi.fn(),
  fetch: vi.fn(async () => {}),
});

vi.mock("../../composables/useStore", () => ({
  useStore: vi.fn(),
}));

vi.mock("../../utils/routes", () => ({
  getCrispyBuilderFormatName: vi.fn((): string | null => null),
}));

describe("CrispyPFB report pane mode", () => {
  beforeEach(async () => {
    vi.resetModules();
  });

  it("shows LayoutPane in report basic mode", async () => {
    const { useStore } = await import("../../composables/useStore");
    (useStore as any).mockReturnValue(makeStore(false));

    const wrapper = mount(CrispyPFB, {
      global: {
        stubs: {
          FieldsPane: { template: '<div data-test="fields-pane" />' },
          LayoutPane: { template: '<div data-test="layout-pane" />' },
          TypstCodePane: { template: '<div data-test="typst-pane" />' },
          PreviewPane: { template: "<div />" },
          SettingsPane: { template: "<div />" },
        },
      },
    });

    expect(wrapper.find('[data-test="layout-pane"]').exists()).toBe(true);
    expect(wrapper.find('[data-test="typst-pane"]').exists()).toBe(false);
  });

  it("shows TypstCodePane in report advanced mode", async () => {
    const { useStore } = await import("../../composables/useStore");
    (useStore as any).mockReturnValue(makeStore(true));

    const wrapper = mount(CrispyPFB, {
      global: {
        stubs: {
          FieldsPane: { template: '<div data-test="fields-pane" />' },
          LayoutPane: { template: '<div data-test="layout-pane" />' },
          TypstCodePane: { template: '<div data-test="typst-pane" />' },
          PreviewPane: { template: "<div />" },
          SettingsPane: { template: "<div />" },
        },
      },
    });

    expect(wrapper.find('[data-test="layout-pane"]').exists()).toBe(false);
    expect(wrapper.find('[data-test="typst-pane"]').exists()).toBe(true);
  });
});
