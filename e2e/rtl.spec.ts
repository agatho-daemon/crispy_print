import { expect, test, type Page } from "@playwright/test";

const user = process.env.CRISPY_E2E_USER;
const password = process.env.CRISPY_E2E_PASSWORD;
const formatNames = {
  ar:
    process.env.CRISPY_E2E_FORMAT_AR ||
    process.env.CRISPY_E2E_FORMAT ||
    "Crispy RTL E2E Arabic",
  fa: process.env.CRISPY_E2E_FORMAT_FA || "Crispy RTL E2E Persian",
  en: process.env.CRISPY_E2E_FORMAT_EN || "Crispy RTL E2E English",
  multipage:
    process.env.CRISPY_E2E_FORMAT_MULTIPAGE || "Crispy RTL E2E Multipage",
  report: process.env.CRISPY_E2E_FORMAT_REPORT || "Crispy RTL E2E Report",
};
const fixtureDocname = process.env.CRISPY_E2E_DOCNAME;
const fixtureTemplate = process.env.CRISPY_E2E_TEMPLATE;
let originalUserLanguage: string | undefined;

async function login(page: Page) {
  await page.goto("/login");
  await page.locator("#login_email").fill(user!);
  await page.locator("#login_password").fill(password!);
  await page.locator(".btn-login").click();
  await page.waitForURL(/\/app(?:\/|$)/);
}

async function openBuilder(
  page: Page,
  language: "ar" | "fa" | "en",
  formatName: string,
) {
  await page.goto("/app");
  await page.evaluate(async (lang) => {
    const frappeGlobal = (window as any).frappe;
    if (String(frappeGlobal.boot?.lang || "en").startsWith(lang)) {
      return;
    }
    await frappeGlobal.call({
      method: "frappe.client.set_value",
      args: {
        doctype: "User",
        name: frappeGlobal.session.user,
        fieldname: "language",
        value: lang,
      },
    });
  }, language);
  await page.waitForLoadState("networkidle");
  await page.goto(
    `/app/crispy-format-builder/${encodeURIComponent(formatName)}`,
  );
  await page.locator("#crispy-print-app.crispy-layout").waitFor();
  await expect(page).toHaveURL(
    new RegExp(`/app/crispy-format-builder/${encodeURIComponent(formatName)}$`),
  );
}

async function captureOriginalState(page: Page) {
  if (originalUserLanguage !== undefined) return;
  originalUserLanguage = await page.evaluate(() => {
    const frappeGlobal = (window as any).frappe;
    return String(frappeGlobal.boot?.lang || "en");
  });
}

async function selectInvoice(page: Page) {
  if (!fixtureDocname) {
    throw new Error("CRISPY_E2E_DOCNAME is required for document preview tests");
  }
  const input = page.locator("#typst-sample-doc-input");
  await expect(input).toHaveAttribute("data-doctype", "Sales Invoice");
  await input.fill(fixtureDocname);
  await input.dispatchEvent("awesomplete-selectcomplete");
  await page.locator(".pdf-preview__page").first().waitFor({ timeout: 60_000 });
}

test.describe("RTL builder acceptance matrix", () => {
  test.skip(!user || !password, "Set CRISPY_E2E_USER and CRISPY_E2E_PASSWORD");
  test.beforeEach(async ({ page }) => {
    await login(page);
    await captureOriginalState(page);
  });
  test.afterAll(async ({ browser }) => {
    if (originalUserLanguage === undefined) {
      return;
    }
    const page = await browser.newPage();
    await login(page);
    await page.evaluate(async (userLanguage) => {
      const frappeGlobal = (window as any).frappe;
      await frappeGlobal.call({
        method: "frappe.client.set_value",
        args: {
          doctype: "User",
          name: frappeGlobal.session.user,
          fieldname: "language",
          value: userLanguage,
        },
      });
    }, originalUserLanguage);
    await page.close();
  });

  for (const entry of [
    {
      name: "arabic-ui-arabic-document",
      ui: "ar",
      format: formatNames.ar,
      label: "فاتورة تجريبية",
    },
    {
      name: "english-ui-arabic-document",
      ui: "en",
      format: formatNames.ar,
      label: "فاتورة تجريبية",
    },
    {
      name: "arabic-ui-english-document",
      ui: "ar",
      format: formatNames.en,
      label: "Test Invoice",
    },
    {
      name: "persian-ui-persian-document",
      ui: "fa",
      format: formatNames.fa,
      label: "فاکتور آزمایشی",
    },
  ] as const) {
    test(entry.name, async ({ page }) => {
      await openBuilder(page, entry.ui, entry.format);
      const root = page.locator("#crispy-print-root");
      const uiDirection = entry.ui === "en" ? "ltr" : "rtl";
      await expect(root).toHaveAttribute("dir", uiDirection);
      await expect(root).toHaveAttribute("lang", new RegExp(`^${entry.ui}`));
      const sectionTitle = page.locator(".section-title-input").first();
      await expect(sectionTitle).toHaveValue(entry.label);
      await expect(sectionTitle).not.toHaveValue(/ \/ /);

      await page.locator(".field-card").first().hover();
      await page.locator(".field-card__menu-btn").first().click();
      await expect(page.locator(".field-card__menu").last()).toHaveAttribute(
        "dir",
        uiDirection,
      );
      await expect(page).toHaveScreenshot(`${entry.name}.png`, {
        fullPage: true,
      });
    });
  }

  test("keeps preview canvas and physical controls LTR", async ({ page }) => {
    await openBuilder(page, "ar", formatNames.ar);
    await expect(page.locator(".preview-stage")).toHaveCSS("direction", "ltr");
    await page.locator(".pane-toggle--settings").first().click();
    await page.locator(".settings-pane__section-header").nth(2).click();
    await expect(page.locator('input[type="number"]').first()).toHaveCSS(
      "direction",
      "ltr",
    );
  });

  test("supports keyboard and drag interactions in RTL", async ({ page }) => {
    await openBuilder(page, "ar", formatNames.ar);
    const firstFieldMenu = page.locator(".field-card__menu-btn").first();
    await firstFieldMenu.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(".field-card__menu").last()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.locator(".field-card__menu").last()).toBeHidden();

    await page.locator(".layout-pane__help-btn").click();
    await expect(page.locator("#layout-help")).toBeVisible();
    await expect(page.locator("#layout-help")).toHaveCSS("direction", "rtl");

    const fieldCards = page.locator(".field-card");
    const firstLabelInput = fieldCards.nth(0).locator(".field-card__label-input");
    const secondLabelInput = fieldCards.nth(1).locator(".field-card__label-input");
    const firstLabel = await firstLabelInput.inputValue();
    const secondLabel = await secondLabelInput.inputValue();
    await fieldCards
      .nth(0)
      .locator(".field-grip")
      .dragTo(fieldCards.nth(1));
    await expect(
      fieldCards.nth(0).locator(".field-card__label-input"),
    ).not.toHaveValue(firstLabel);
    await expect(
      fieldCards.nth(0).locator(".field-card__label-input"),
    ).toHaveValue(secondLabel);
    await page.reload();
    await page.locator("#crispy-print-app.crispy-layout").waitFor();
  });

  test("renders deterministic multipage RTL output with retained LTR values", async ({
    page,
  }) => {
    await openBuilder(page, "ar", formatNames.multipage);
    await selectInvoice(page);
    await expect
      .poll(() => page.locator(".pdf-preview__page").count(), {
        timeout: 60_000,
      })
      .toBeGreaterThan(1);
    await expect(page.locator(".preview-stage")).toHaveCSS("direction", "ltr");
  });

  test("runs the deterministic RTL report fixture", async ({ page }) => {
    await openBuilder(page, "ar", formatNames.report);
    const runButton = page.locator(
      ".report-preview-variables > .report-preview-variables__heading > .btn-primary",
    );
    await runButton.click();
    await page
      .locator(".pdf-preview__page")
      .first()
      .waitFor({ timeout: 90_000 });
    await expect(
      page.locator(".report-preview-variables__message.is-ready"),
    ).toBeVisible();
  });

  test("renders the published Arabic fixture through standalone final preview", async ({
    page,
  }) => {
    test.skip(
      !fixtureDocname || !fixtureTemplate,
      "Set CRISPY_E2E_DOCNAME and CRISPY_E2E_TEMPLATE from an opt-in published fixture",
    );
    await openBuilder(page, "ar", formatNames.ar);
    await page.goto(
      `/app/crispy-print-preview/Sales%20Invoice/${encodeURIComponent(
        fixtureDocname!,
      )}/${encodeURIComponent(formatNames.ar)}`,
    );
    await page
      .locator(".pdf-preview__page")
      .first()
      .waitFor({ timeout: 60_000 });
    await expect(page.locator("#crispy-preview-root")).toHaveAttribute(
      "dir",
      "rtl",
    );
  });
});
