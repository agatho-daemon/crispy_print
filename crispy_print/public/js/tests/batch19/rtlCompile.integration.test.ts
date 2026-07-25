import { execFileSync } from "node:child_process";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { translateJSONToTypst } from "../../typst/JSONToTypst";
import {
  buildReportTypstFromConfig,
  getDefaultReportBuilderConfig,
} from "../../utils/reportBuilder";

const enabled = process.env.CRISPY_PRINT_RUN_TYPST_INTEGRATION === "1";
const workdir = enabled ? mkdtempSync(join(tmpdir(), "crispy-rtl-")) : "";

afterAll(() => {
  if (workdir) rmSync(workdir, { recursive: true, force: true });
});

describe.skipIf(!enabled)("real RTL Typst PDF", () => {
  it("compiles Arabic/Persian shaping and preserves extractable accounting order", () => {
    const source = translateJSONToTypst(
      {
        sections: [
          {
            id: "main",
            label: "فاتورة تجريبية",
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
      {
        customer_name: "شركة Example تهران",
        grand_total: "KWD -12.375",
      },
      { language: "ar-KW" },
    );
    const input = join(workdir, "rtl.typ");
    const output = join(workdir, "rtl.pdf");
    writeFileSync(input, source, "utf8");

    execFileSync("typst", ["compile", input, output], { stdio: "pipe" });

    expect(existsSync(output)).toBe(true);
    expect(readFileSync(output).subarray(0, 4).toString()).toBe("%PDF");

    try {
      const text = execFileSync("pdftotext", [output, "-"], {
        encoding: "utf8",
      });
      expect(text).toContain("KWD -12.375");
      expect(text).toMatch(/Example|العميل|الإجمالي/);
    } catch (error: any) {
      if (error?.code !== "ENOENT") throw error;
    }

    try {
      const fonts = execFileSync("pdffonts", [output], { encoding: "utf8" });
      expect(fonts).toMatch(/Noto|Inter/);
      expect(fonts).toMatch(/\byes\b/i);
    } catch (error: any) {
      if (error?.code !== "ENOENT") throw error;
    }
  });

  it("compiles logical RTL report columns and identifier isolation", () => {
    const report = buildReportTypstFromConfig(
      getDefaultReportBuilderConfig("generic_report"),
      { language: "fa-IR" },
    );
    const source = `#let data = (
  title: "گزارش",
  subtitle: "RTL",
  filters: (),
  report_summary: (),
  columns: (
    (fieldname: "customer_name", label: "مشتری", is_numeric: false, width_kind: "auto"),
    (fieldname: "tax_id", label: "شناسه مالیاتی", is_numeric: false, width_kind: "auto"),
    (fieldname: "amount", label: "مبلغ", is_numeric: true, width_kind: "auto"),
  ),
  rows: ((
    role: "detail",
    is_total_row: false,
    is_bold: false,
    indent: 0,
    cells: (
      (value: "شرکت Example", is_numeric: false, is_ltr: false),
      (value: "KW-12345", is_numeric: false, is_ltr: true),
      (value: "KWD -12.375", is_numeric: true, is_ltr: true),
    ),
  ),),
  total_rows: 1,
)
${report}`;
    const input = join(workdir, "rtl-report.typ");
    const output = join(workdir, "rtl-report.pdf");
    writeFileSync(input, source, "utf8");

    execFileSync(
      "typst",
      [
        "compile",
        "--package-path",
        join(process.cwd(), "../vendor/typst/packages"),
        input,
        output,
      ],
      { stdio: "pipe" },
    );

    expect(readFileSync(output).subarray(0, 4).toString()).toBe("%PDF");
  });
});
