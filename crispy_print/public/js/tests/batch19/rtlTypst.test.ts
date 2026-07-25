import { describe, expect, it } from "vitest";
import { translateJSONToTypst } from "../../typst/JSONToTypst";
import {
  buildReportTypstFromConfig,
  getDefaultReportBuilderConfig,
  normalizeReportBuilderConfig,
} from "../../utils/reportBuilder";

describe("RTL Typst generation parity", () => {
  it("sets Arabic document metadata and isolates accounting values", () => {
    const typst = translateJSONToTypst(
      {
        sections: [
          {
            id: "main",
            label: "الفاتورة",
            columns: [
              {
                id: "column",
                label: "",
                fields: [
                  {
                    id: "customer",
                    fieldtype: "Data",
                    fieldname: "customer_name",
                    label: "العميل",
                    align: "start",
                  },
                  {
                    id: "total",
                    fieldtype: "Currency",
                    fieldname: "grand_total",
                    label: "الإجمالي",
                    align: "end",
                  },
                ],
              },
            ],
          },
        ],
      },
      null,
      "Sales Invoice",
      { customer_name: "شركة Example", grand_total: "KWD -10.000" },
      { language: "ar-KW" },
    );

    expect(typst).toContain('lang: "ar", region: "KW", dir: rtl');
    expect(typst).toContain("#align(right)[#text(dir: rtl, ..fieldLabelStyle)");
    expect(typst).toContain(
      "#align(right)[#text(dir: rtl, ..fieldValueStyle)[#doc.customer_name]]",
    );
    expect(typst).toContain(
      "#align(left)[#text(dir: ltr, ..fieldValueStyle)[#doc.grand_total]]",
    );
    expect(typst).toContain(
      "cp_measure_value_table_cell(value) = table.cell(stroke: (left: none))[#box[#text(dir: ltr",
    );
    expect(typst).toContain(
      "box(text(dir: ltr, ..tableCellLabelStyle)[#label])",
    );
    expect(typst).toContain('"Noto Naskh Arabic"');
  });

  it("uses the same language contract for basic reports", () => {
    const config = normalizeReportBuilderConfig({
      ...getDefaultReportBuilderConfig("generic_report"),
      column_align_strategy: "start",
    });
    const typst = buildReportTypstFromConfig(config, { language: "fa-IR" });

    expect(typst).toContain('lang: "fa", region: "IR", dir: rtl');
    expect(typst).toContain(
      'if cell.is_numeric or ("is_ltr" in cell and cell.is_ltr) { ltr } else { rtl }',
    );
    expect(typst).toContain("#let cp-columns = data.columns.rev()");
    expect(typst).toContain("#let cp-row-cells(row) = row.cells.rev()");
    expect(typst).toContain("right + horizon");
    expect(typst).toContain('"Noto Naskh Arabic"');
  });
});
