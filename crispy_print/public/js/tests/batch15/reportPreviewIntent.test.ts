import { describe, expect, it } from "vitest";
import {
  getReportColumnDefault,
  serializeReportPreviewIntent,
} from "../../pages/reportPrintSettings";

describe("report preview intent serialization", () => {
  it("deduplicates equivalent reactive payload replacements", () => {
    const first = serializeReportPreviewIntent([
      "Accounts Receivable",
      { filters: { company: "ACME" } },
      { branding: { mode: "none" } },
    ]);
    const equivalentReplacement = serializeReportPreviewIntent([
      "Accounts Receivable",
      { filters: { company: "ACME" } },
      { branding: { mode: "none" } },
    ]);

    expect(equivalentReplacement).toBe(first);
  });

  it("changes when a compile-affecting value changes", () => {
    const first = serializeReportPreviewIntent([
      "Accounts Receivable",
      { filters: { company: "ACME" } },
      { showTotals: true },
    ]);
    const changed = serializeReportPreviewIntent([
      "Accounts Receivable",
      { filters: { company: "ACME" } },
      { showTotals: false },
    ]);

    expect(changed).not.toBe(first);
  });
});

describe("report column defaults", () => {
  it("uses a compact readable General Ledger profile", () => {
    expect(getReportColumnDefault("General Ledger", "posting_date")).toEqual({
      selected: true,
      width: "54pt",
    });
    expect(getReportColumnDefault("General Ledger", "account")).toEqual({
      selected: true,
      width: "1.4fr",
    });
    expect(getReportColumnDefault("General Ledger", "against_voucher")).toEqual({
      selected: false,
      width: "auto",
    });
  });

  it("keeps the existing all-column behavior for other reports", () => {
    expect(getReportColumnDefault("Accounts Receivable", "customer")).toEqual({
      selected: true,
      width: "auto",
    });
  });
});
