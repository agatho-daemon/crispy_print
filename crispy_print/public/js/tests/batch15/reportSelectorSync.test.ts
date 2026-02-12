import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { defineComponent, h, ref } from "vue";
import PreviewPane from "../../components/PreviewPane.vue";

const changeKey = ref(0);

const compileReportPreview = vi.fn(async () => ({
	success: true,
	svg_pages: [],
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
		pageSettings: ref({}),
		changeKey,
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
		changeKey.value = 0;
		compileReportPreview.mockReset();
		compileReportPreview.mockResolvedValue({
			success: true,
			svg_pages: [],
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
					h("div", { "data-watch": String(props.watchDataChanges) }, slots.menu?.());
			},
		});

		const wrapper = mount(PreviewPane, {
			global: {
				stubs: {
					PreviewRenderer: PreviewRendererStub,
				},
			},
		});

		expect(wrapper.find("[data-watch='false']").exists()).toBe(true);
	});

	it("renders style-preview note and does not render report selector", async () => {
		const wrapper = mount(PreviewPane, {
			global: {
				stubs: {
					PreviewRenderer: {
						template: "<div><slot name='menu'></slot></div>",
					},
				},
			},
		});

		expect(wrapper.find("#sample-report-select").exists()).toBe(false);
		expect(wrapper.text()).toContain("Style preview with placeholder data");
		expect(compileReportPreview).toHaveBeenCalledWith("Style Preview", []);
	});

});
