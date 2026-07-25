import { describe, expect, it, vi } from "vitest";
import {
  deserializeLayout,
  getDefaultFieldAlignment,
  getTableColumns,
  normalizeLayout,
  pluck,
} from "../../utils/layout";

describe("layout helpers", () => {
  it("normalizes fields and filters empty fieldnames", () => {
    const normalized = normalizeLayout({
      sections: [
        {
          label: "",
          columns: [
            {
              label: "",
              fields: [
                { fieldname: "amount", fieldtype: "Currency", label: "Amount" },
                { fieldname: "", fieldtype: "Data", label: "Empty" },
              ],
            },
          ],
        },
      ],
    } as any);

    expect(normalized.sections[0].columns[0].fields.length).toBe(1);
    expect(normalized.sections[0].columns[0].fields[0].align).toBeUndefined();
  });

  it("pluck returns specified keys", () => {
    const result = pluck({ a: 1, b: 2, c: 3 }, ["a", "c"]);
    expect(result).toEqual({ a: 1, c: 3 });
  });

  it("defaults numeric alignments", () => {
    expect(getDefaultFieldAlignment("Currency")).toBe("right");
    expect(getDefaultFieldAlignment("Data")).toBe("auto");
  });

  it("returns null on invalid JSON", () => {
    expect(deserializeLayout("{bad json")).toBeNull();
  });

  it("builds table columns from child meta", () => {
    const original = (globalThis as any).frappe;
    (globalThis as any).frappe = {
      get_meta: vi.fn(() => ({
        fields: [
          { fieldname: "item_code", label: "Item Code", fieldtype: "Data" },
          { fieldname: "qty", label: "Qty", fieldtype: "Float" },
        ],
      })),
    };

    const columns = getTableColumns({
      fieldname: "items",
      label: "Items",
      fieldtype: "Table",
      options: "Item",
    });

    expect(columns.length).toBe(2);
    expect(columns[1].align).toBe("right");
    (globalThis as any).frappe = original;
  });
});
