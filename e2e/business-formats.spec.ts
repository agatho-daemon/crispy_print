import { expect, test, type Page } from "@playwright/test";

const user = process.env.CRISPY_E2E_USER;
const password = process.env.CRISPY_E2E_PASSWORD;
const deskPrefix = process.env.CRISPY_E2E_DESK_PREFIX || "/app";

const fixtures = [
  {
    label: "Payment Entry receipt",
    doctype: "Payment Entry",
    format: "Crispy V1 E2E 01 payment-entry-voucher",
    docname: process.env.CRISPY_V1_E2E_PAYMENT_RECEIVE,
  },
  {
    label: "Payment Entry supplier voucher",
    doctype: "Payment Entry",
    format: "Crispy V1 E2E 01 payment-entry-voucher",
    docname: process.env.CRISPY_V1_E2E_PAYMENT_PAY,
  },
  {
    label: "Supplier remittance advice",
    doctype: "Payment Entry",
    format: "Crispy V1 E2E 02 remittance-advice",
    docname: process.env.CRISPY_V1_E2E_PAYMENT_PAY,
  },
  {
    label: "Stock Entry movement",
    doctype: "Stock Entry",
    format: "Crispy V1 E2E 03 stock-entry-movement",
    docname: process.env.CRISPY_V1_E2E_STOCK_ENTRY,
  },
  {
    label: "Material Request requisition",
    doctype: "Material Request",
    format: "Crispy V1 E2E 04 material-request-requisition",
    docname: process.env.CRISPY_V1_E2E_MATERIAL_REQUEST,
  },
  {
    label: "Journal Entry voucher",
    doctype: "Journal Entry",
    format: "Crispy V1 E2E 05 journal-entry-voucher",
    docname: process.env.CRISPY_V1_E2E_JOURNAL_ENTRY,
  },
  {
    label: "Cash and petty-cash voucher",
    doctype: "Journal Entry",
    format: "Crispy V1 E2E 05 journal-entry-voucher",
    docname: process.env.CRISPY_V1_E2E_CASH_JOURNAL_ENTRY,
  },
  {
    label: "POS thermal receipt",
    doctype: "POS Invoice",
    format: "Crispy V1 E2E 09 pos-invoice-thermal",
    docname: process.env.CRISPY_V1_E2E_POS_INVOICE,
  },
  {
    label: "POS A4 invoice",
    doctype: "POS Invoice",
    format: "Crispy V1 E2E 10 pos-invoice-a4",
    docname: process.env.CRISPY_V1_E2E_POS_INVOICE,
  },
] as const;

const reportFixtures = [
  {
    label: "Statement of Account",
    format: "Crispy V1 E2E 06 statement-of-account",
  },
  {
    label: "Accounts Receivable aging",
    format: "Crispy V1 E2E 07 accounts-receivable-aging",
  },
  {
    label: "Accounts Payable aging",
    format: "Crispy V1 E2E 08 accounts-payable-aging",
  },
] as const;

async function login(page: Page) {
  const response = await page.request.post("/api/method/login", {
    form: { usr: user!, pwd: password! },
  });
  expect(response.ok(), await response.text()).toBe(true);
  await page.goto(`${deskPrefix}/crispy-studio`);
  await page.waitForFunction(
    () => Boolean((window as any).frappe?.session?.user),
  );
}

async function openAndRender(page: Page, fixture: (typeof fixtures)[number]) {
  await page.goto(
    `${deskPrefix}/crispy-format-builder/${encodeURIComponent(fixture.format)}`,
  );
  await page.locator("#crispy-print-app.crispy-layout").waitFor();
  const input = page.locator("#typst-sample-doc-input");
  await expect(input).toHaveAttribute("data-doctype", fixture.doctype);
  await input.fill(fixture.docname!);
  await input.evaluate((element) => {
    element.dispatchEvent(
      new CustomEvent("awesomplete-selectcomplete", { bubbles: true }),
    );
  });
  await page.locator(".pdf-preview__page canvas").first().waitFor({
    timeout: 90_000,
  });
}

test.describe("core v1 business-format acceptance", () => {
  test.skip(!user || !password, "Set CRISPY_E2E_USER and CRISPY_E2E_PASSWORD");

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  for (const fixture of fixtures) {
    test(`renders ${fixture.label}`, async ({ page }) => {
      test.skip(
        !fixture.docname,
        `Set the ${fixture.label} document returned by the business-format seed`,
      );
      await openAndRender(page, fixture);
      await expect(page.locator(".pdf-preview__page canvas").first()).toBeVisible();
    });
  }

  for (const fixture of reportFixtures) {
    test(`runs ${fixture.label}`, async ({ page }) => {
      await page.goto(
        `${deskPrefix}/crispy-format-builder/${encodeURIComponent(fixture.format)}`,
      );
      await page.locator("#crispy-print-app.crispy-layout").waitFor();
      await page
        .locator(
          ".report-preview-variables > .report-preview-variables__heading > .btn-primary",
        )
        .click();
      await page.locator(".pdf-preview__page canvas").first().waitFor({
        timeout: 90_000,
      });
      await expect(page.locator(".pdf-preview__page canvas").first()).toBeVisible();
      await expect(
        page.locator(".report-preview-variables__message.is-error"),
      ).toHaveCount(0);
    });
  }
});
