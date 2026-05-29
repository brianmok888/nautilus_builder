import { expect, test } from "@playwright/test";

test("Nautilus Builder shell exposes the three-section workflow", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Nautilus Builder" })).toBeVisible();
  await expect(page.getByText("Strategy Builder → Backtest Center → Execution Lane").first()).toBeVisible();
  await expect(page.getByRole("tab", { name: "1. Strategy Builder" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "2. Backtest Center" })).toBeVisible();
  await expect(page.getByRole("tab", { name: "3. Execution Lane" })).toBeVisible();
});

test("results dashboard route is observational", async ({ page }) => {
  await page.goto("/results/res_001");
  await expect(page.getByRole("heading", { name: "Backtest results" })).toBeVisible();
  await expect(page.getByText("Result: res_001")).toBeVisible();
  await expect(page.getByText("no execution authority")).toBeVisible();
});

test("operator MVP routes expose strategies, backtest console, AI, and promotion surfaces", async ({ page }) => {
  await page.goto("/strategies");
  await expect(page.getByRole("heading", { name: "Strategy list" })).toBeVisible();

  await page.goto("/backtests/bt_job_001");
  await expect(page.getByRole("heading", { name: "Observational runtime console" })).toBeVisible();
  await expect(page.getByText("Allowed command: request cancel")).toBeVisible();

  await page.goto("/");
  await expect(page.getByText("Apply to Builder")).toBeVisible();
  await expect(page.getByText("Manual promotion before paper/live")).toBeVisible();
  await expect(page.getByRole("tab", { name: "2. Backtest Center" })).toBeVisible();
});

test("operator can traverse Strategy Builder, Backtest Center, and Execution Lane without browser authority", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("navigation", { name: "Operator workflow" })).toBeVisible();
  await page.getByRole("link", { name: "Strategy records" }).click();
  await expect(page).toHaveURL(/\/strategies$/);
  await expect(page.getByText("No saved strategies yet.")).toBeVisible();
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(page.getByRole("link", { name: "strategy_001" })).toBeVisible();
  await expect(page.getByText("lineage_strategy_001")).toBeVisible();

  await page.goto("/");
  await page.getByRole("link", { name: "Backtest Center" }).click();
  await expect(page).toHaveURL(/\/backtests\/bt_job_001$/);
  await expect(page.getByText("Allowed command: request cancel")).toBeVisible();

  await page.goto("/");
  await page.getByRole("link", { name: "Results / Reports" }).click();
  await expect(page).toHaveURL(/\/results\/res_001$/);
  await expect(page.getByText("Result: res_001")).toBeVisible();
  await expect(page.getByText("strategy_version_id")).toBeVisible();

  await page.goto("/");
  await expect(page.getByText("Lineage IDs are generated automatically for normal drafting; advanced editing is optional.")).toBeVisible();
  await page.getByRole("link", { name: "Execution Lane" }).click();
  await expect(page).toHaveURL(/\/config$/);
  await page.waitForTimeout(2000);
  await expect(page.getByText("Execution lane feature flags are backend-owned")).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("may submit order").first()).toBeVisible({ timeout: 10000 });
});
