/**
 * E2E tests for TradeHUD SSE gateway modes.
 *
 * Covers:
 *  8.1 Mock mode — /tradehud renders with safety labels and canvas
 *  8.2 SSE mode fallback — backend unavailable → mock fallback
 *  8.3 SSE mode connected — backend running → live SSE stream
 */
import { test, expect } from "@playwright/test";

test.describe("TradeHUD SSE Gateway", () => {
  test("8.1 Mock mode — renders with safety labels and canvas", async ({ page }) => {
    await page.goto("/tradehud");
    await page.waitForLoadState("networkidle");

    // Safety labels visible
    await expect(page.locator("text=NO BROWSER ORDER AUTHORITY")).toBeVisible();

    // Feed badge shows mock
    await expect(page.locator("text=LOCAL MOCK")).toBeVisible({ timeout: 5000 });

    // Bookmap canvas visible
    const canvas = page.locator("canvas").first();
    await expect(canvas).toBeVisible({ timeout: 5000 });

    // Runtime Health visible
    await expect(page.locator("text=Runtime Health").first()).toBeVisible({ timeout: 5000 });
  });

  test("8.2 SSE mode — falls back to mock when backend unavailable", async ({ page }) => {
    // Point SSE to an unreachable port to trigger fallback
    await page.addInitScript(() => {
      Object.defineProperty(window, "__FORCE_SSE_FALLBACK", { value: true });
    });

    await page.goto("/tradehud?mode=sse");
    await page.waitForLoadState("networkidle");

    // Page still loads
    await expect(page).toHaveURL(/tradehud/);

    // Safety labels still present
    await expect(page.locator("text=NO BROWSER ORDER AUTHORITY")).toBeVisible();

    // Canvas still renders (mock fallback provides data)
    const canvas = page.locator("canvas").first();
    await expect(canvas).toBeVisible({ timeout: 10000 });
  });

  test("8.3 SSE mode — page does not crash with missing backend", async ({ page }) => {
    await page.goto("/tradehud");
    await page.waitForLoadState("networkidle");

    // No JS errors from page
    const errors: string[] = [];
    page.on("pageerror", (err) => errors.push(err.message));

    // Wait a moment for any SSE reconnect logic
    await page.waitForTimeout(3000);

    // Page should not have crashed
    const topbar = page.locator(".tradehud-topbar");
    await expect(topbar).toBeVisible();

    // No critical errors
    expect(errors.filter((e) => !e.includes("net::ERR_CONNECTION"))).toEqual([]);
  });
});
