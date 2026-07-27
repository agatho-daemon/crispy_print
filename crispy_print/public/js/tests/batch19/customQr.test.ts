import { mount } from "@vue/test-utils";
import { describe, expect, it, vi } from "vitest";
import QrFieldsDialog from "../../components/QrFieldsDialog.vue";
import {
  buildCustomQrPayload,
  customQrPayloadBytes,
  getSafeCustomQrFields,
  isDenseCustomQrPayload,
} from "../../utils/customQr";

const fields = [
  { fieldname: "name", label: "ID", fieldtype: "Data" },
  { fieldname: "customer_name", label: "Customer Name", fieldtype: "Data" },
  { fieldname: "grand_total", label: "Grand Total", fieldtype: "Currency" },
  { fieldname: "items", label: "Items", fieldtype: "Table" },
  { fieldname: "password", label: "Password", fieldtype: "Password" },
  { fieldname: "_private", label: "Private", fieldtype: "Data" },
];

describe("Custom Document QR", () => {
  it("keeps exact fieldnames and payload order", () => {
    expect(
      buildCustomQrPayload(
        {
          name: "INV-001",
          customer_name: "عميل Example",
          grand_total: "-125.000",
        },
        ["grand_total", "name", "customer_name"],
      ),
    ).toBe("grand_total: -125.000\nname: INV-001\ncustomer_name: عميل Example");
  });

  it("filters unsupported fields without changing fieldnames", () => {
    expect(
      getSafeCustomQrFields(fields).map((field) => field.fieldname),
    ).toEqual(["name", "customer_name", "grand_total"]);
  });

  it("reports encoded bytes and dense payloads deterministically", () => {
    expect(customQrPayloadBytes("name: فاتورة")).toBeGreaterThan(
      "name: فاتورة".length,
    );
    expect(isDenseCustomQrPayload(900)).toBe(false);
    expect(isDenseCustomQrPayload(901)).toBe(true);
  });

  it("edits the canonical string array in visible order", async () => {
    const wrapper = mount(QrFieldsDialog, {
      props: {
        fields,
        modelValue: ["name", "customer_name"],
        sampleValues: { name: "INV-001", customer_name: "Example" },
        onClose: vi.fn(),
      },
    });

    expect(wrapper.find("pre").text()).toBe(
      "name: INV-001\ncustomer_name: Example",
    );
    await wrapper.find('[aria-label="Move down"]').trigger("click");
    await wrapper.find(".qr-dialog__btn--primary").trigger("click");
    expect(wrapper.emitted("update:modelValue")?.[0]?.[0]).toEqual([
      "customer_name",
      "name",
    ]);
  });
});
