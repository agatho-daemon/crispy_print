import { defineConfig, devices } from "@playwright/test";

const baseURL = process.env.CRISPY_E2E_BASE_URL || "http://127.0.0.1:8000";

export default defineConfig({
  testDir: ".",
  timeout: 120_000,
  outputDir: "../test-results/playwright",
  snapshotDir: "./__screenshots__",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }], ["line"]] : "list",
  use: {
    baseURL,
    ignoreHTTPSErrors: true,
    viewport: { width: 1440, height: 1000 },
    timezoneId: "Asia/Kuwait",
    locale: "en-US",
    colorScheme: "light",
    reducedMotion: "reduce",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  expect: {
    toHaveScreenshot: {
      animations: "disabled",
      maxDiffPixelRatio: 0.01,
    },
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"], channel: "chromium" },
    },
  ],
});
