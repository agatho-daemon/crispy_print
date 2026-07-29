import { mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { nextTick } from "vue";

import TableColumnsDialog from "../../components/TableColumnsDialog.vue";
import {
  TABLE_PRESETS,
  resolveChildTableDoctype,
  resolveTablePreset,
} from "../../utils/tablePresets";

const salesInvoiceItemFields = [
  { fieldname: "item_code", label: "Item Code", fieldtype: "Link" },
  { fieldname: "description", label: "Description", fieldtype: "Text" },
  { fieldname: "qty", label: "Quantity", fieldtype: "Float" },
  { fieldname: "uom", label: "UOM", fieldtype: "Link" },
  { fieldname: "rate", label: "Rate", fieldtype: "Currency" },
  { fieldname: "amount", label: "Amount", fieldtype: "Currency" },
];

describe("compact table presets", () => {
  beforeEach(() => {
    (globalThis as any).frappe = {
      model: {
        no_value_type: ["Section Break", "Column Break"],
        with_doctype: (_doctype: string, callback: () => void) => callback(),
      },
      get_meta: () => ({ fields: salesInvoiceItemFields }),
      confirm: vi.fn((_message: string, confirm: () => void) => confirm()),
    };
  });

  it("recovers a legacy table's child DocType from live parent metadata", () => {
    expect(
      resolveChildTableDoctype("items", undefined, [
        {
          fieldname: "items",
          label: "Items",
          fieldtype: "Table",
          options: "Sales Invoice Item",
        },
      ]),
    ).toBe("Sales Invoice Item");
    expect(
      resolveChildTableDoctype("items", "Custom Invoice Item", []),
    ).toBe("Custom Invoice Item");
  });

  it("uses exact metadata fieldnames and reports unavailable optional fields", () => {
    const preset = TABLE_PRESETS.find((item) => item.id === "serial-batch")!;
    const resolved = resolveTablePreset(preset, [
      { fieldname: "item_code", label: "Item", fieldtype: "Link" },
      { fieldname: "qty", label: "Qty", fieldtype: "Float" },
    ]);

    expect(resolved.applicable).toBe(true);
    expect(resolved.columns.map((column) => column.fieldname)).toEqual([
      "idx",
      "item_code",
      "qty",
    ]);
    expect(resolved.missingOptional).toEqual([
      "serial_no",
      "batch_no",
      "warehouse",
    ]);
  });

  it("blocks a preset when a required exact field is unavailable", () => {
    const preset = TABLE_PRESETS.find((item) => item.id === "invoice-items")!;
    const resolved = resolveTablePreset(preset, [
      { fieldname: "item_code", label: "Item", fieldtype: "Link" },
      { fieldname: "qty", label: "Qty", fieldtype: "Float" },
    ]);

    expect(resolved.applicable).toBe(false);
    expect(resolved.missingRequired).toEqual(["amount"]);
  });

  it("replaces columns only after confirmation and switches to logical order", async () => {
    const wrapper = mount(TableColumnsDialog, {
      props: {
        modelValue: [
          {
            fieldname: "old_field",
            label: "Old",
            fieldtype: "Data",
            width: "auto",
          },
        ],
        doctype: "Sales Invoice Item",
        order: "physical",
      },
    });
    await nextTick();

    await wrapper
      .find(".table-dialog__preset-actions select")
      .setValue("invoice-items");
    await wrapper.find(".table-dialog__preset-actions button").trigger("click");
    await nextTick();

    expect((globalThis as any).frappe.confirm).toHaveBeenCalledOnce();
    const updates = wrapper.emitted("update:modelValue") || [];
    const applied = updates[updates.length - 1]?.[0] as Array<{
      fieldname: string;
    }>;
    expect(applied.map((column) => column.fieldname)).toEqual([
      "idx",
      "item_code",
      "description",
      "qty",
      "uom",
      "rate",
      "amount",
    ]);
    const orderUpdates = wrapper.emitted("update:order") || [];
    expect(orderUpdates[orderUpdates.length - 1]?.[0]).toBe("logical");
  });
});
