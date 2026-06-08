import { chromium } from "playwright";
import { mkdirSync } from "fs";
import path from "path";

const OUT_DIR = path.resolve("../../docs/screenshots");
mkdirSync(OUT_DIR, { recursive: true });

const SHOTS = [
  { name: "01-overview", url: "/", label: "Overview / Dashboard" },
  { name: "02-strategy-builder", url: "/builder", label: "Strategy Builder" },
  { name: "03-backtest-center", url: "/backtests", label: "Backtest Center" },
  { name: "04-execution-lane", url: "/execution", label: "Execution Lane" },
  { name: "05-strategy-specs", url: "/strategies", label: "Strategy Specs" },
  { name: "06-settings", url: "/config", label: "Settings" },
  { name: "07-results", url: "/results", label: "Results" },
  { name: "08-pipeline", url: "/pipeline", label: "Pipeline" },
];

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  deviceScaleFactor: 2,
});

for (const shot of SHOTS) {
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("requestfailed", (r) => {
    const url = r.url();
    // Ignore expected API failures (no backend running); only log non-API
    if (!url.includes("/api/") && !url.includes("/health")) {
      errors.push(`requestfailed: ${url}`);
    }
  });
  try {
    await page.goto(`http://localhost:3457${shot.url}`, {
      waitUntil: "domcontentloaded",
      timeout: 15000,
    });
    await page.waitForTimeout(1200);
    const outPath = path.join(OUT_DIR, `${shot.name}.png`);
    await page.screenshot({ path: outPath, fullPage: false });
    console.log(`✓ ${shot.name}.png (${shot.label}) — ${shot.url}`);
  } catch (e) {
    console.error(`✗ ${shot.name} FAILED: ${e.message}`);
  } finally {
    await page.close();
  }
}

await browser.close();
console.log(`\nScreenshots saved to ${OUT_DIR}`);
