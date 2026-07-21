import { enableAutoUnmount, flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, ref } from "vue";
import PreviewPane from "../../components/PreviewPane.vue";

enableAutoUnmount(afterEach);

const previewRevision = ref(0);
const reportPreviewReady = ref(false);
const selectedReportName = ref("Accounts Receivable");

const compileReportPreview = vi.fn(async () => ({
  success: true,
  pdf_data: "JVBERi0xLjQK",
  page_count: 1,
}));

vi.mock("../../composables/useStore", () => ({
  useStore: () => ({
    formatName: ref("Report Format"),
    layout: ref({ sections: [] }),
    docHeader: ref(""),
    docFooter: ref(""),
    typstPreamble: ref(""),
    typstCode: ref(""),
    rawTypst: ref(false),
    qrEnabled: ref(false),
    letterhead: ref(null),
    docType: ref(null),
    presentation_settings: ref({}),
    previewRevision,
		reportPreviewReady,
		selectedReportName,
    crispyFormat: ref({ crispy_format_type: "Report", is_generic: 1 }),
    reportBuilderConfig: ref({
      show_filters: true,
      show_summary: true,
      include_total_row: true,
    }),
    compileReportPreview,
  }),
}));

describe("PreviewPane report mode", () => {
  beforeEach(() => {
    previewRevision.value = 0;
    reportPreviewReady.value = false;
    selectedReportName.value = "Accounts Receivable";
    compileReportPreview.mockReset();
    compileReportPreview.mockResolvedValue({
      success: true,
	  pdf_data: "JVBERi0xLjQK",
      page_count: 1,
    });
  });

  it("uses report-mode preview orchestration and disables worker data watching", async () => {
    const PreviewRendererStub = defineComponent({
      props: {
        watchDataChanges: { type: Boolean, default: true },
      },
      setup(props, { slots }) {
        return () =>
          h(
            "div",
            { "data-watch": String(props.watchDataChanges) },
            slots.menu?.(),
          );
      },
    });

    const wrapper = mount(PreviewPane, {
      global: {
        stubs: {
			ReportPreviewVariables: true,
          PreviewRenderer: PreviewRendererStub,
        },
      },
    });

    expect(wrapper.find("[data-watch='false']").exists()).toBe(true);
  });

  it("does not compile until preview variables have been applied", async () => {
    const wrapper = mount(PreviewPane, {
      global: {
        stubs: {
			ReportPreviewVariables: true,
          PreviewRenderer: {
            template: "<div><slot name='menu'></slot></div>",
          },
        },
      },
    });

    expect(wrapper.find("#sample-report-select").exists()).toBe(false);
		expect(wrapper.text()).toContain("Set report variables");
		expect(compileReportPreview).not.toHaveBeenCalled();
  });

  it("coalesces changes while a report compile is in flight", async () => {
    let resolveFirst: ((value: any) => void) | null = null;
    compileReportPreview
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveFirst = resolve;
          }),
      )
      .mockResolvedValue({
        success: true,
		pdf_data: "JVBERi0xLjQK",
        page_count: 1,
      });
    reportPreviewReady.value = true;

    mount(PreviewPane, {
      global: {
        stubs: {
          ReportPreviewVariables: true,
          PreviewRenderer: {
            template: "<div><slot name='menu'></slot></div>",
          },
        },
      },
    });

    previewRevision.value += 1;
    await flushPromises();
    expect(compileReportPreview).toHaveBeenCalledTimes(1);

    previewRevision.value += 1;
    previewRevision.value += 1;
    previewRevision.value += 1;
    await flushPromises();
    expect(compileReportPreview).toHaveBeenCalledTimes(1);

    resolveFirst?.({ success: true, pdf_data: "JVBERi0xLjQK", page_count: 1 });
    await flushPromises();
    expect(compileReportPreview).toHaveBeenCalledTimes(2);
  });
});
