/**
 * Phase 7: Hardened safety grep for TradeHUD.
 *
 * Scans all TradeHUD frontend files for forbidden patterns that would indicate
 * executable order authority, gate approval, or credential exposure.
 *
 * Uses allowlist to avoid false positives on safety-warning docstrings.
 */
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync } from "fs";
import { join } from "path";

const TRADEHUD_DIRS = [
  join(process.cwd(), "lib/tradehud"),
  join(process.cwd(), "components/tradehud"),
  join(process.cwd(), "app/tradehud"),
];

/** Patterns that indicate executable authority or credential access.
 *  These must NEVER appear in TradeHUD source code (outside docstrings). */
const FORBIDDEN_PATTERNS: { pattern: RegExp; label: string }[] = [
  // Order execution authority
  { pattern: /submit_order\s*\(/i, label: "submit_order() call" },
  { pattern: /submit_order\s*;/i, label: "submit_order statement" },
  { pattern: /createTradeAction\s*\(/i, label: "createTradeAction() call" },
  { pattern: /create_trade_action\s*\(/i, label: "create_trade_action() call" },
  { pattern: /force_approve\s*\(/i, label: "force_approve() call" },
  { pattern: /forceApprove\s*\(/i, label: "forceApprove() call" },
  // Credential access
  { pattern: /exchange_api_key/i, label: "exchange_api_key reference" },
  { pattern: /exchangeApiKey/i, label: "exchangeApiKey reference" },
  { pattern: /secret_key\s*[:=]/i, label: "secret_key assignment" },
  { pattern: /secretKey\s*[:=]/i, label: "secretKey assignment" },
  { pattern: /private_key\s*[:=]/i, label: "private_key assignment" },
  { pattern: /privateKey\s*[:=]/i, label: "privateKey assignment" },
  { pattern: /BINANCE_SECRET/i, label: "BINANCE_SECRET env reference" },
  { pattern: /BYBIT_SECRET/i, label: "BYBIT_SECRET env reference" },
  { pattern: /OKX_SECRET/i, label: "OKX_SECRET env reference" },
  { pattern: /DERIBIT_SECRET/i, label: "DERIBIT_SECRET env reference" },
  { pattern: /POLYMARKET_PRIVATE_KEY/i, label: "POLYMARKET_PRIVATE_KEY reference" },
  // Direct backend connections from browser
  { pattern: /process\.env\.REDIS_URL/i, label: "Redis URL in browser" },
  { pattern: /process\.env\.POSTGRES/i, label: "Postgres env in browser" },
  { pattern: /new\s+Redis\s*\(/i, label: "Redis client instantiation" },
  { pattern: /new\s+Pool\s*\(/i, label: "pg Pool instantiation" },
];

function collectSourceFiles(dir: string): string[] {
  const results: string[] = [];
  if (!existsSync(dir)) return results;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...collectSourceFiles(full));
    } else if (
      (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx")) &&
      !entry.name.includes(".test.")
    ) {
      results.push(full);
    }
  }
  return results;
}

/**
 * Strip comments and string literals to avoid false positives on
 * safety-warning text like "No submit_order authority".
 */
function stripNonCode(content: string): string {
  return content
    .replace(/\/\*[\s\S]*?\*\//g, "") // block comments
    .replace(/\/\/.*$/gm, "") // line comments
    .replace(/"[^"]*"/g, '""') // double-quoted strings
    .replace(/'[^']*'/g, '""') // single-quoted strings
    .replace(/`[^`]*`/g, '""'); // template literals
}

describe("TradeHUD safety grep — hardened", () => {
  const allFiles: string[] = [];
  for (const dir of TRADEHUD_DIRS) {
    allFiles.push(...collectSourceFiles(dir));
  }

  it("scans at least 10 TradeHUD source files", () => {
    expect(allFiles.length).toBeGreaterThanOrEqual(10);
  });

  it("no forbidden order authority or credential patterns in code", () => {
    const violations: string[] = [];
    for (const file of allFiles) {
      const raw = readFileSync(file, "utf-8");
      const code = stripNonCode(raw);

      for (const { pattern, label } of FORBIDDEN_PATTERNS) {
        if (pattern.test(code)) {
          violations.push(
            `${file.replace(process.cwd(), ".")}: ${label}`,
          );
        }
      }
    }

    expect(
      violations,
      `Forbidden patterns found in TradeHUD:\n${violations.join("\n")}`,
    ).toEqual([]);
  });

  it("no browser-side fetch/axios POST to order endpoints", () => {
    const violations: string[] = [];
    for (const file of allFiles) {
      const code = stripNonCode(readFileSync(file, "utf-8"));
      // POST to anything that looks like order/execute/approve
      if (/fetch\s*\([^)]*method\s*:\s*["']POST/i.test(code) && /order|execute|approve/i.test(code)) {
        violations.push(file);
      }
      if (/axios\.post/i.test(code) && /order|execute|approve/i.test(code)) {
        violations.push(file);
      }
    }
    expect(violations).toEqual([]);
  });
});
