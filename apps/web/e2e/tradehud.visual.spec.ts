import { test, expect } from "@playwright/test";

/**
 * Visual QA screenshots for TradeHUD at 4 viewport sizes.
 *
 * Pre-screenshot assertions verify safety labels and key panels are visible.
 * Screenshots saved to test-results/ (not committed to git).
 */

const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "1920x1080", width: 1920, height: 1080 },
  { name: "1280x720", width: 1280, height: 720 },
  { name: "mobile-390x844", width: 390, height: 844 },
];

test.describe("TradeHUD visual QA screenshots", () => {
  for (const vp of VIEWPORTS) {
    test(`renders TradeHUD at ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await page.goto("/tradehud");
      // Wait for TradeHUD root to mount
      await page.waitForSelector(".tradehud-root", { timeout: 15_000 });
      // Allow mock data to populate
      await page.waitForTimeout(2000);

      // ── Safety label assertions (desktop only — mobile may reflow) ──────────
      if (vp.width >= 1280) {
        await expect(page.locator("body")).toContainText("NO BROWSER ORDER AUTHORITY");
        await expect(page.locator("body")).toContainText("NOT EXECUTABLE");
        await expect(page.locator("body")).toContainText("Gate Decision");
        await expect(page.locator("body")).toContainText("Bookmap Heatmap");
        await expect(page.locator("body")).toContainText("Order Book");
        await expect(page.locator("body")).toContainText("Trade Tape");
        await expect(page.locator("body")).toContainText("Runtime Health");

        // ── Canvas element exists ───────────────────────────────────────────────
        const canvas = page.locator("canvas.tradehud-heatmap-canvas");
        await expect(canvas).toHaveCount(1);
      }

      // ── Capture screenshot ──────────────────────────────────────────────────
      await page.screenshot({
        path: `test-results/tradehud-${vp.name}.png`,
        fullPage: vp.width >= 1280,
      });
    });
  }
});
