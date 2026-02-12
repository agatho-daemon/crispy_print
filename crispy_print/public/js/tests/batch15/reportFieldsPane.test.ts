import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import FieldsPane from "../../components/FieldsPane.vue";

describe("FieldsPane report basic controls", () => {
  it("does not render report toggles in fields pane", async () => {
    const wrapper = mount(FieldsPane, {
      props: {
        fields: [],
        isReportMode: true,
        reportFields: [
          { fieldname: "data.title", label: "Title", fieldtype: "Data" },
          { fieldname: "data.subtitle", label: "Subtitle", fieldtype: "Data" },
          { fieldname: "data.filters", label: "Filters", fieldtype: "Table" },
          {
            fieldname: "data.report_summary",
            label: "Report Summary",
            fieldtype: "Table",
          },
          { fieldname: "data.chart", label: "Chart", fieldtype: "Table" },
          { fieldname: "data.table", label: "Report Table", fieldtype: "Table" },
        ],
      },
    });

    expect(wrapper.text()).not.toContain("Show filters block");
    expect(wrapper.text()).not.toContain("Include total row");
  });

  it("keeps report field ordering (block-only model)", () => {
    const wrapper = mount(FieldsPane, {
      props: {
        fields: [],
        isReportMode: true,
        reportFields: [
          { fieldname: "data.title", label: "Title", fieldtype: "Data" },
          { fieldname: "data.subtitle", label: "Subtitle", fieldtype: "Data" },
          { fieldname: "data.filters", label: "Filters", fieldtype: "Table" },
          {
            fieldname: "data.report_summary",
            label: "Report Summary",
            fieldtype: "Table",
          },
          { fieldname: "data.chart", label: "Chart", fieldtype: "Table" },
          { fieldname: "data.table", label: "Report Table", fieldtype: "Table" },
        ],
      },
    });

    const labels = wrapper.findAll(".field-label").map((node) => node.text());
    expect(labels.slice(0, 6)).toEqual([
      "Title",
      "Subtitle",
      "Filters",
      "Report Summary",
      "Chart",
      "Report Table",
    ]);
  });
});
