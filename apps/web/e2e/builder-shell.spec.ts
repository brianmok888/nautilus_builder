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
  await expect(page.getByText("request cancel")).toBeVisible();

  await page.goto("/");
  await expect(page.getByText("Apply to Builder")).toBeVisible();
  await expect(page.getByText("Safe promotion request")).toBeVisible();
});
