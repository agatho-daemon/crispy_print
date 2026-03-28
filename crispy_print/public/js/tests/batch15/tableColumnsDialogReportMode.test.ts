import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import { defineComponent, h } from "vue";
import TableColumnsDialog from "../../components/TableColumnsDialog.vue";

const DraggableStub = defineComponent({
  name: "DraggableStub",
  props: {
    modelValue: {
      type: Array,
      default: (): unknown[] => [],
    },
  },
  setup(props, { slots }) {
    return () =>
      h(
        "div",
        { class: "draggable-stub" },
        (props.modelValue || []).map((element, index) =>
          slots.item ? slots.item({ element, index }) : null
        )
      );
  },
});

describe("TableColumnsDialog report columns source", () => {
  it("uses availableColumns override for add-column options", async () => {
    const wrapper = mount(TableColumnsDialog, {
      props: {
        modelValue: [],
        doctype: "",
        availableColumns: [
          { fieldname: "account", label: "Account", fieldtype: "Link" },
          { fieldname: "balance", label: "Balance", fieldtype: "Currency" },
        ],
      },
      global: {
        stubs: {
          draggable: DraggableStub,
        },
      },
    });

    const options = wrapper.findAll("select option").map((node) => ({
      label: node.text(),
      value: (node.element as HTMLOptionElement).value,
    }));

    expect(options.some((opt) => opt.value === "account")).toBe(true);
    expect(options.some((opt) => opt.value === "balance")).toBe(true);

    await wrapper.find("select").setValue("account");
    await wrapper.find(".table-dialog__add-btn").trigger("click");

    const emitted = wrapper.emitted("update:modelValue") || [];
    const payload = (emitted[emitted.length - 1]?.[0] || []) as Array<{
      fieldname?: string;
    }>;
    expect(payload[0]?.fieldname).toBe("account");
  });
});
