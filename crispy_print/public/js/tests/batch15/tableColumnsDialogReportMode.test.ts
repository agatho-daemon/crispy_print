import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
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
  beforeEach(() => {
    (globalThis as any).frappe = {
      show_alert: vi.fn(),
    };
  });

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

  it("emits valid column width edits immediately", async () => {
    const wrapper = mount(TableColumnsDialog, {
      props: {
        modelValue: [
          {
            fieldname: "qty",
            label: "Quantity",
            fieldtype: "Float",
            width: "auto",
            align: "right",
          },
        ],
        doctype: "",
      },
      global: {
        stubs: {
          draggable: DraggableStub,
        },
      },
    });

    await wrapper.find(".table-dialog__width-input").setValue("1fr");

    const emitted = wrapper.emitted("update:modelValue") || [];
    const payload = (emitted[0]?.[0] || []) as Array<{ width?: string }>;
    expect(payload[0]?.width).toBe("1fr");
  });

  it("shows invalid width alert without emitting invalid values", async () => {
    vi.useFakeTimers();
    const wrapper = mount(TableColumnsDialog, {
      props: {
        modelValue: [
          {
            fieldname: "qty",
            label: "Quantity",
            fieldtype: "Float",
            width: "auto",
            align: "right",
          },
        ],
        doctype: "",
      },
      global: {
        stubs: {
          draggable: DraggableStub,
        },
      },
    });

    await wrapper.find(".table-dialog__width-input").setValue("1");
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    expect((globalThis as any).frappe.show_alert).not.toHaveBeenCalled();

    vi.advanceTimersByTime(200);

    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
    expect((globalThis as any).frappe.show_alert).toHaveBeenCalledWith(
      expect.objectContaining({ indicator: "orange" }),
    );
    vi.useRealTimers();
  });
});
