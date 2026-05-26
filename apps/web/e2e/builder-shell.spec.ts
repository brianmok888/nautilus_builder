import { expect, test } from "@playwright/test";

test("Nautilus Builder shell exposes authoring, terminal, and advisory surfaces", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Nautilus Builder" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Strategy draft authoring" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Observational runtime console" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Advisory AI drafting" })).toBeVisible();
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
  await expect(page.getByRole("heading", { name: "Safe promotion request" }).first()).toBeVisible();
});

test("operator can traverse composed observational journey with stable IDs and no execution authority", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("navigation", { name: "Operator workflow" })).toBeVisible();
  await page.getByRole("link", { name: "Strategies" }).click();
  await expect(page).toHaveURL(/\/strategies$/);
  await expect(page.getByText("No saved strategies yet.")).toBeVisible();
  await page.getByRole("button", { name: "Create draft" }).click();
  await expect(page.getByRole("link", { name: "strategy_001" })).toBeVisible();
  await expect(page.getByText("lineage_strategy_001")).toBeVisible();

  await page.goto("/");
  await page.getByRole("link", { name: "Backtest job bt_job_001" }).click();
  await expect(page).toHaveURL(/\/backtests\/bt_job_001$/);
  await expect(page.getByText("Allowed command: request cancel")).toBeVisible();

  await page.goto("/");
  await page.getByRole("link", { name: "Results res_001" }).click();
  await expect(page).toHaveURL(/\/results\/res_001$/);
  await expect(page.getByText("Result: res_001")).toBeVisible();
  await expect(page.getByText("strategy_version_id")).toBeVisible();

  await page.goto("/");
  await expect(page.getByText("Lineage IDs are automatic by default and available only under Advanced.")).toBeVisible();
  await expect(page.getByText("approval_state: manual_approval_pending")).toBeVisible();
  await expect(page.getByText("Order authority remains disabled in Builder.")).toBeVisible();
  await expect(page.getByText("Trade-action creation remains disabled in Builder.")).toBeVisible();
});
