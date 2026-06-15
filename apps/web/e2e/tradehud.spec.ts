import { test, expect } from "@playwright/test";

test.describe("TradeHUD observability route", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/tradehud");
    await page.waitForLoadState("networkidle");
  });

  test("page loads successfully", async ({ page }) => {
    await expect(page).toHaveURL(/\/tradehud$/);
  });

  test("NO BROWSER ORDER AUTHORITY visible", async ({ page }) => {
    await expect(page.locator("text=NO BROWSER ORDER AUTHORITY")).toBeVisible();
  });

  test("Strategy Signal Preview visible and labeled NOT EXECUTABLE", async ({ page }) => {
    const panel = page.locator("text=Strategy Signal Preview").locator("..");
    await expect(panel).toBeVisible();
    await expect(page.locator("text=NOT EXECUTABLE")).toBeVisible();
  });

  test("Gate Decision visible", async ({ page }) => {
    await expect(page.locator("text=Gate Decision").first()).toBeVisible();
  });

  test("Bookmap heatmap canvas visible", async ({ page }) => {
    await expect(page.locator("text=Bookmap Heatmap").first()).toBeVisible();
    const canvas = page.locator("canvas").first();
    await expect(canvas).toBeVisible();
  });

  test("Order Book visible", async ({ page }) => {
    await expect(page.locator("text=Order Book").first()).toBeVisible();
  });

  test("Trade Tape visible", async ({ page }) => {
    await expect(page.locator("text=Trade Tape").first()).toBeVisible();
  });

  test("Runtime Health visible", async ({ page }) => {
    await expect(page.locator("text=Runtime Health").first()).toBeVisible();
  });
});
