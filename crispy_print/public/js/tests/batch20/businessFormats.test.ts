import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { describe, expect, it } from "vitest";
import {
  buildDocDictionary,
  translateJSONToTypst,
} from "../../typst/JSONToTypst";
import { normalizeLayout } from "../../utils/layout";

const sampleDirectory = resolve(process.cwd(), "../../examples/formats");

const managedSamples = [
  "payment-entry-voucher",
  "remittance-advice",
  "stock-entry-movement",
  "material-request-requisition",
  "journal-entry-voucher",
  "pos-invoice-a4",
];

function loadSample(sampleId: string): any {
  return JSON.parse(
    readFileSync(`${sampleDirectory}/${sampleId}.json`, "utf8"),
  );
}

function syntheticDocument(layout: any, doctype: string): Record<string, any> {
  const document: Record<string, any> = {
    name: "V1-ACCEPTANCE-0001",
    doctype,
  };
  for (const section of layout.sections || []) {
    for (const column of section.columns || []) {
      for (const field of column.fields || []) {
        if (field.fieldtype === "Table") {
          const row: Record<string, string> = {};
          for (const tableColumn of field.columns || []) {
            row[tableColumn.fieldname] =
              tableColumn.fieldname.includes("amount") ||
              tableColumn.fieldname.includes("debit") ||
              tableColumn.fieldname.includes("credit") ||
              tableColumn.fieldname === "qty" ||
              tableColumn.fieldname === "rate"
                ? "-125.000"
                : `${tableColumn.label || tableColumn.fieldname} value`;
          }
          document[field.fieldname] = [row, { ...row }];
        } else if (field.fieldtype === "Currency") {
          document[field.fieldname] = -125;
        } else {
          document[field.fieldname] = `${field.label || field.fieldname} value`;
        }
      }
    }
  }
  return document;
}

describe("core v1 business-format catalog", () => {
  it.each(managedSamples)(
    "generates managed Typst for %s without unresolved values",
    (sampleId) => {
      const sample = loadSample(sampleId);
      const layout = normalizeLayout(JSON.parse(sample.format.layout_json));
      const settings = JSON.parse(sample.format.presentation_settings);
      const source = translateJSONToTypst(
        layout,
        null,
        sample.format.doc_type,
        syntheticDocument(layout, sample.format.doc_type),
        settings,
      );

      expect(source).toContain("#set page(");
      expect(source).toContain("V1-ACCEPTANCE-0001");
      expect(source).not.toContain("undefined");
      expect(source).not.toContain("NaN");
    },
  );

  it("keeps the thermal receipt on an explicit 80 mm auto-height page", () => {
    const sample = loadSample("pos-invoice-thermal");
    expect(sample.format.raw_typst).toBe(1);
    expect(sample.format.typst_code).toContain(
      "#set page(width: 80mm, height: auto",
    );
    expect(sample.format.typst_code).toContain("for item in doc.items");
    expect(sample.format.typst_code).toContain("for payment in doc.payments");
  });

  const typstIt =
    process.env.CRISPY_RUN_TYPST_INTEGRATION === "1" ? it : it.skip;

  typstIt("compiles the 80 mm thermal receipt with real Typst", () => {
    const sample = loadSample("pos-invoice-thermal");
    const directory = mkdtempSync(`${tmpdir()}/crispy-pos-thermal-`);
    const input = resolve(directory, "receipt.typ");
    const output = resolve(directory, "receipt.pdf");
    const document = {
      name: "POS-THERMAL-0001",
      posting_date: "2026-07-29",
      posting_time: "12:34:00",
      customer_name: "Walk-in Customer",
      grand_total: 12.5,
      paid_amount: 12.5,
      items: [
        {
          item_name: "Test Item",
          qty: 1,
          rate: 12.5,
          amount: 12.5,
        },
      ],
      payments: [{ mode_of_payment: "Cash", amount: 12.5 }],
    };
    writeFileSync(
      input,
      `${buildDocDictionary(document, "POS Invoice")}\n${sample.format.typst_code}`,
      "utf8",
    );

    const result = spawnSync("typst", ["compile", input, output], {
      encoding: "utf8",
    });
    expect(result.status, result.stderr || result.stdout).toBe(0);
    expect(readFileSync(output).subarray(0, 4).toString()).toBe("%PDF");
  });

  typstIt.each(managedSamples)(
    "compiles the managed %s sample with real Typst",
    (sampleId) => {
      const sample = loadSample(sampleId);
      const layout = normalizeLayout(JSON.parse(sample.format.layout_json));
      const settings = JSON.parse(sample.format.presentation_settings);
      const source = translateJSONToTypst(
        layout,
        null,
        sample.format.doc_type,
        syntheticDocument(layout, sample.format.doc_type),
        settings,
      );
      const directory = mkdtempSync(`${tmpdir()}/crispy-v1-${sampleId}-`);
      const input = resolve(directory, "document.typ");
      const output = resolve(directory, "document.pdf");
      writeFileSync(input, source, "utf8");

      const result = spawnSync("typst", ["compile", input, output], {
        encoding: "utf8",
      });
      expect(result.status, result.stderr || result.stdout).toBe(0);
      expect(readFileSync(output).subarray(0, 4).toString()).toBe("%PDF");
    },
  );

  it.each([
    ["statement-of-account", "general_ledger", "General Ledger"],
    [
      "accounts-receivable-aging",
      "receivable_payable",
      "Accounts Receivable",
    ],
    ["accounts-payable-aging", "receivable_payable", "Accounts Payable"],
  ])(
    "binds %s to the intended report renderer",
    (sampleId, renderer, report) => {
      const sample = loadSample(sampleId);
      expect(sample.format.crispy_format_type).toBe("Report");
      expect(sample.format.report_renderer).toBe(renderer);
      expect(sample.format.report).toContainEqual({ report, disabled: 0 });
      expect(sample.format.typst_code).toContain("table.header(");
      expect(sample.format.typst_code).toContain("repeat: true");
    },
  );
});
