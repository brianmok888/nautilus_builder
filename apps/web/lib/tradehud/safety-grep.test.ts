/**
 * Safety contract test — ensures TradeHUD code has NO order execution authority.
 * Scans all TradeHUD files for forbidden terms.
 */
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync } from "fs";
import { join } from "path";

const TRADEHUD_DIRS = [
  join(process.cwd(), "lib/tradehud"),
  join(process.cwd(), "components/tradehud"),
];

const FORBIDDEN_TERMS = [
  "submit_order(",
  "submit_order;",
  "submit_order ",
  "submit_order\n",
  "createTradeAction",
  "create_trade_action",
  "force_approve",
  "exchange_api_key",
  "secret_key",
  "private_key",
  "binance_secret",
];

// Terms that are OK in documentation/comments but NOT in code
const DOCS_CONTEXT_TERMS = [
  "submit_order",
];

function collectFiles(dir: string, ext: string): string[] {
  if (!existsSync(dir)) return [];
  return readdirSync(dir)
    .filter((f) => f.endsWith(ext))
    .map((f) => join(dir, f));
}

describe("TradeHUD safety contract", () => {
  it("no TradeHUD file calls submit_order or creates TradeAction", () => {
    const files = [
      ...collectFiles(TRADEHUD_DIRS[0], ".ts"),
      ...collectFiles(TRADEHUD_DIRS[1], ".tsx"),
    ];

    expect(files.length).toBeGreaterThan(0);

    for (const file of files) {
      // Skip test files
      if (file.includes(".test.")) continue;

      const content = readFileSync(file, "utf-8");

      // Strip comments and string literals that contain "forbidden" in docs context
      const stripped = content
        .replace(/\/\*[\s\S]*?\*\//g, "") // block comments
        .replace(/\/\/.*$/gm, "") // line comments
        .replace(/"[^"]*"/g, '""') // double-quoted strings
        .replace(/'[^']*'/g, '""') // single-quoted strings
        .replace(/`[^`]*`/g, '""'); // template literals

      for (const term of FORBIDDEN_TERMS) {
        const lower = stripped.toLowerCase();
        expect(lower).not.toContain(term.toLowerCase());
      }
    }
  });

  it("no TradeHUD file references exchange credentials or secrets", () => {
    const files = [
      ...collectFiles(TRADEHUD_DIRS[0], ".ts"),
      ...collectFiles(TRADEHUD_DIRS[1], ".tsx"),
    ];

    for (const file of files) {
      if (file.includes(".test.")) continue;
      const content = readFileSync(file, "utf-8").toLowerCase();
      for (const term of [
        "exchange_api_key",
        "binance_secret",
        "secret_key =",
        "private_key =",
        "process.env.redis_url",
        "process.env.postgres",
      ]) {
        expect(content).not.toContain(term);
      }
    }
  });
});
