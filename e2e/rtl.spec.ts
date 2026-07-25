import { expect, test, type Page } from "@playwright/test";

const user = process.env.CRISPY_E2E_USER;
const password = process.env.CRISPY_E2E_PASSWORD;
const formatName = process.env.CRISPY_E2E_FORMAT || "Crispy RTL E2E";
let originalUserLanguage: string | undefined;
let originalPresentationSettings: string | undefined;

async function login(page: Page) {
  await page.goto("/login");
  await page.locator("#login_email").fill(user!);
  await page.locator("#login_password").fill(password!);
  await page.locator(".btn-login").click();
  await page.waitForURL(/\/app(?:\/|$)/);
}

async function openBuilder(page: Page, language: "ar" | "fa" | "en") {
  await page.goto("/app");
  await page.evaluate(async (lang) => {
    const frappeGlobal = (window as any).frappe;
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
  await page.goto(
    `/app/crispy-format-builder/${encodeURIComponent(formatName)}`,
  );
  await page.locator("#crispy-print-app.crispy-layout").waitFor();
}

async function setPrintLanguage(page: Page, language: "ar-KW" | "fa-IR" | "en") {
  await page.evaluate(
    async ({ name, lang }) => {
      const frappeGlobal = (window as any).frappe;
      const response = await frappeGlobal.call({
        method: "frappe.client.get",
        args: { doctype: "Crispy Format", name },
      });
      const settings = JSON.parse(response.message.presentation_settings || "{}");
      settings.language = lang;
      await frappeGlobal.call({
        method: "frappe.client.set_value",
        args: {
          doctype: "Crispy Format",
          name,
          fieldname: "presentation_settings",
          value: JSON.stringify(settings),
        },
      });
    },
    { name: formatName, lang: language },
  );
  await page.reload();
  await page.locator("#crispy-print-app.crispy-layout").waitFor();
}

async function captureOriginalState(page: Page) {
  if (originalUserLanguage !== undefined) return;
  const state = await page.evaluate(async (name) => {
    const frappeGlobal = (window as any).frappe;
    const response = await frappeGlobal.call({
      method: "frappe.client.get",
      args: { doctype: "Crispy Format", name },
    });
    return {
      userLanguage: String(frappeGlobal.boot?.lang || "en"),
      presentationSettings: String(response.message.presentation_settings || "{}"),
    };
  }, formatName);
  originalUserLanguage = state.userLanguage;
  originalPresentationSettings = state.presentationSettings;
}

test.describe("RTL builder acceptance matrix", () => {
  test.skip(!user || !password, "Set CRISPY_E2E_USER and CRISPY_E2E_PASSWORD");
  test.beforeEach(async ({ page }) => {
    await login(page);
    await captureOriginalState(page);
  });
  test.afterAll(async ({ browser }) => {
    if (originalUserLanguage === undefined || originalPresentationSettings === undefined) {
      return;
    }
    const page = await browser.newPage();
    await login(page);
    await page.evaluate(
      async ({ name, userLanguage, presentationSettings }) => {
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
        await frappeGlobal.call({
          method: "frappe.client.set_value",
          args: {
            doctype: "Crispy Format",
            name,
            fieldname: "presentation_settings",
            value: presentationSettings,
          },
        });
      },
      {
        name: formatName,
        userLanguage: originalUserLanguage,
        presentationSettings: originalPresentationSettings,
      },
    );
    await page.close();
  });

  for (const entry of [
    { name: "arabic-ui-arabic-document", ui: "ar", print: "ar-KW" },
    { name: "english-ui-arabic-document", ui: "en", print: "ar-KW" },
    { name: "arabic-ui-english-document", ui: "ar", print: "en" },
    { name: "persian-ui-persian-document", ui: "fa", print: "fa-IR" },
  ] as const) {
    test(entry.name, async ({ page }) => {
      await openBuilder(page, entry.ui);
      await setPrintLanguage(page, entry.print);
      const root = page.locator("#crispy-print-root");
      const uiDirection = entry.ui === "en" ? "ltr" : "rtl";
      await expect(root).toHaveAttribute("dir", uiDirection);
      await expect(root).toHaveAttribute("lang", new RegExp(`^${entry.ui}`));

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
    await openBuilder(page, "ar");
    await expect(page.locator(".preview-stage")).toHaveCSS("direction", "ltr");
    await page.locator(".pane-toggle--settings").first().click();
    await page.locator(".settings-pane__section-header").nth(2).click();
    await expect(page.locator('input[type="number"]').first()).toHaveCSS(
      "direction",
      "ltr",
    );
  });

  test("supports keyboard and drag interactions in RTL", async ({ page }) => {
    await openBuilder(page, "ar");
    const firstFieldMenu = page.locator(".field-card__menu-btn").first();
    await firstFieldMenu.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator(".field-card__menu").last()).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.locator(".field-card__menu").last()).toBeHidden();
  });
});
