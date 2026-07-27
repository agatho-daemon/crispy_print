import { expect, test, type Page } from "@playwright/test";
import { decodeQrPdf } from "./qr-decode";

const user = process.env.CRISPY_E2E_USER;
const password = process.env.CRISPY_E2E_PASSWORD;
const customFormat =
  process.env.CRISPY_QR_E2E_CUSTOM_FORMAT ||
  "Crispy QR E2E Custom Sales Invoice";
const regulatoryFormat =
  process.env.CRISPY_QR_E2E_REGULATORY_FORMAT || "Crispy QR E2E Regulatory";
const legacyFormat =
  process.env.CRISPY_QR_E2E_LEGACY_FORMAT || "Crispy QR E2E Legacy Basic";
const invoice = process.env.CRISPY_QR_E2E_SALES_INVOICE;
const crossDoctypeFixtures = [
  {
    doctype: "Purchase Invoice",
    format: "Crispy QR E2E Custom Purchase Invoice",
    docname: process.env.CRISPY_QR_E2E_PURCHASE_INVOICE,
  },
  {
    doctype: "Delivery Note",
    format: "Crispy QR E2E Custom Delivery Note",
    docname: process.env.CRISPY_QR_E2E_DELIVERY_NOTE,
  },
  {
    doctype: "Payment Entry",
    format: "Crispy QR E2E Custom Payment Entry",
    docname: process.env.CRISPY_QR_E2E_PAYMENT_ENTRY,
  },
] as const;

async function login(page: Page) {
  await page.goto("/login");
  await page.locator("#login_email").fill(user!);
  await page.locator("#login_password").fill(password!);
  await page.locator(".btn-login").click();
  await page.waitForURL(/\/app(?:\/|$)/);
}

async function setLanguage(page: Page, language: "en" | "ar" | "fa") {
  await page.goto("/app");
  await page.evaluate(async (value) => {
    const frappeGlobal = (window as any).frappe;
    await frappeGlobal.call({
      method: "frappe.client.set_value",
      args: {
        doctype: "User",
        name: frappeGlobal.session.user,
        fieldname: "language",
        value,
      },
    });
  }, language);
}

async function openBuilder(page: Page, formatName: string) {
  await page.goto(
    `/app/crispy-format-builder/${encodeURIComponent(formatName)}`,
  );
  await page.locator("#crispy-print-app.crispy-layout").waitFor();
}

async function openQrSettings(page: Page) {
  await page.locator(".pane-toggle--settings").first().click();
  const headers = page.locator(".settings-pane__section-header");
  await headers.nth(6).click();
  await expect(page.locator(".settings-pane__qr-btn")).toBeVisible();
}

async function selectDocument(page: Page, doctype: string, docname: string) {
  const input = page.locator("#typst-sample-doc-input");
  await expect(input).toHaveAttribute("data-doctype", doctype);
  await input.fill(docname);
  await input.evaluate((element) => {
    element.dispatchEvent(
      new CustomEvent("awesomplete-selectcomplete", { bubbles: true }),
    );
  });
  await page.locator(".pdf-preview__page canvas").first().waitFor({
    timeout: 90_000,
  });
}

async function selectInvoice(page: Page) {
  if (!invoice) throw new Error("CRISPY_QR_E2E_SALES_INVOICE is required");
  await selectDocument(page, "Sales Invoice", invoice);
}

test.describe("Custom and Regulatory QR acceptance", () => {
  test.skip(!user || !password, "Set CRISPY_E2E_USER and CRISPY_E2E_PASSWORD");

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  for (const language of ["en", "ar", "fa"] as const) {
    test(`${language} custom QR editor preserves exact ordered fieldnames`, async ({
      page,
    }) => {
      await setLanguage(page, language);
      await openBuilder(page, customFormat);
      await openQrSettings(page);
      await page.locator(".settings-pane__qr-btn").click();

      const dialog = page.locator(".qr-dialog__card");
      await expect(dialog).toHaveAttribute(
        "dir",
        language === "en" ? "ltr" : "rtl",
      );
      const rows = dialog.locator(".qr-dialog__item");
      await expect(rows).not.toHaveCount(0);
      const firstFieldname = await rows.nth(0).locator("code").textContent();
      const secondFieldname = await rows.nth(1).locator("code").textContent();
      await rows
        .nth(0)
        .locator("[aria-label]")
        .filter({ hasText: "↓" })
        .click();
      await expect(rows.nth(0).locator("code")).toHaveText(secondFieldname!);
      await expect(rows.nth(1).locator("code")).toHaveText(firstFieldname!);
      await expect(dialog.locator(".qr-dialog__preview pre")).toContainText(
        `${secondFieldname}:`,
      );
      await expect(dialog.locator(".qr-dialog__preview-heading")).toContainText(
        /\d+/,
      );
    });
  }

  for (const fixture of crossDoctypeFixtures) {
    test(`renders ordered Custom QR for ${fixture.doctype}`, async ({ page }) => {
      test.skip(!fixture.docname, `Set the ${fixture.doctype} docname returned by seed_qr_acceptance`);
      await setLanguage(page, "en");
      await openBuilder(page, fixture.format);
      await selectDocument(page, fixture.doctype, fixture.docname!);
      await expect(page.locator(".pdf-preview__page canvas").first()).toBeVisible();
    });
  }

  test("decodes Custom QR preview with exact field order and Unicode-safe bytes", async ({
    page,
  }, testInfo) => {
    test.skip(
      !invoice,
      "Set CRISPY_QR_E2E_SALES_INVOICE from seed_qr_acceptance",
    );
    await setLanguage(page, "en");
    await openBuilder(page, customFormat);
    await selectInvoice(page);

    const source = await page.evaluate(() => {
      return new Promise<string>((resolve) => {
        const handler = (event: Event) => {
          window.removeEventListener("crispy-preview:source", handler);
          resolve(String((event as CustomEvent).detail?.source || ""));
        };
        window.addEventListener("crispy-preview:source", handler);
        window.dispatchEvent(
          new CustomEvent("crispy-preview:request-source", { detail: {} }),
        );
      });
    });
    expect(source).toContain("crispy-qrcode");
    expect(source).toContain("ACC-SINV-2026-04956");

    const expected = await page.evaluate(
      async ({ docname }) => {
        const fields = [
          "name",
          "posting_date",
          "posting_time",
          "customer_name",
          "grand_total",
          "po_no",
        ];
        const response = await (window as any).frappe.call({
          method: "crispy_print.api.v1.get_formatted_doc",
          args: {
            doctype: "Sales Invoice",
            name: docname,
            fields,
          },
        });
        const doc = response.message;
        return fields
          .filter((fieldname) => fieldname === "name" || fieldname in doc)
          .map((fieldname) => `${fieldname}: ${doc[fieldname] ?? ""}`)
          .join("\n");
      },
      { docname: invoice! },
    );
    expect(source).toContain(JSON.stringify(expected).slice(1, -1));

    const compiled = await page.evaluate(async (payload) => {
      const response = await (window as any).frappe.call({
        method: "crispy_print.api.v1.compile_typst",
        args: {
          typst_source:
            '#set page(width: 80mm, height: 80mm, margin: 10mm)\n#image("acceptance-qr.svg", width: 50mm)',
          output_format: "pdf",
          qr_data: payload,
          qr_filename: "acceptance-qr.svg",
          barcode_options: { symbology: "QR Code", error_correction: "Medium" },
        },
      });
      return response.message;
    }, expected);
    expect(compiled.success).toBe(true);
    const pdfPath = testInfo.outputPath("custom-qr-final.pdf");
    const pngPrefix = testInfo.outputPath("custom-qr-final");
    const decoded = decodeQrPdf(compiled.pdf_data, pdfPath, pngPrefix);
    expect(decoded).toBe(expected);
  });

  test("resolves and validates the backend-owned regulatory profile", async ({
    page,
  }) => {
    test.skip(
      !invoice,
      "Set CRISPY_QR_E2E_SALES_INVOICE from seed_qr_acceptance",
    );
    await setLanguage(page, "en");
    await openBuilder(page, regulatoryFormat);
    await selectInvoice(page);
    await page.locator(".pane-toggle--settings").first().click();
    await page.locator(".settings-pane__section-header").nth(6).click();

    const summary = page.locator(".settings-pane__regulatory-summary");
    await expect(summary).toContainText("ZATCA");
    await expect(summary).toContainText("Configuration resolved");
    await expect(
      summary.getByRole("button", { name: "View profile" }),
    ).toBeVisible();
    await summary
      .getByRole("button", { name: "Validate configuration" })
      .click();
  });

  test("warns on editable legacy Basic QR and blocks save", async ({
    page,
  }) => {
    await setLanguage(page, "en");
    await openBuilder(page, legacyFormat);
    await page.locator(".pane-toggle--settings").first().click();
    await page.locator(".settings-pane__section-header").nth(6).click();
    await expect(page.locator(".settings-pane__qr-legacy")).toContainText(
      "Legacy Basic QR configuration",
    );
    await page.getByRole("button", { name: "Save", exact: true }).click();
    await expect(page.locator(".msgprint").last()).toContainText(
      "Custom Document QR",
    );
  });
});
