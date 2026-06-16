/**
 * Phase 12: Hardened safety grep for TradeHUD — Redis Stream Adapter.
 *
 * Scans all TradeHUD frontend + backend files for forbidden patterns that would indicate
 * executable order authority, gate approval, or credential exposure.
 */
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync } from "fs";
import { join } from "path";

const TRADEHUD_DIRS = [
  join(process.cwd(), "lib/tradehud"),
  join(process.cwd(), "components/tradehud"),
  join(process.cwd(), "app/tradehud"),
];

const FORBIDDEN_PATTERNS: { pattern: RegExp; label: string }[] = [
  { pattern: /submit_order\s*\(/i, label: "submit_order() call" },
  { pattern: /submit_order\s*;/i, label: "submit_order statement" },
  { pattern: /createTradeAction\s*\(/i, label: "createTradeAction() call" },
  { pattern: /create_trade_action\s*\(/i, label: "create_trade_action() call" },
  { pattern: /force_approve\s*\(/i, label: "force_approve() call" },
  { pattern: /forceApprove\s*\(/i, label: "forceApprove() call" },
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
  { pattern: /NEXT_PUBLIC_REDIS_URL/i, label: "Redis URL in browser env" },
  { pattern: /NEXT_PUBLIC_DATABASE_URL/i, label: "Database URL in browser env" },
  { pattern: /NEXT_PUBLIC_EXCHANGE_SECRET/i, label: "Exchange secret in browser env" },
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

function stripNonCode(content: string): string {
  return content
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\/\/.*$/gm, "")
    .replace(/"[^"]*"/g, '""')
    .replace(/'[^']*'/g, '""')
    .replace(/`[^`]*`/g, '""');
}

describe("TradeHUD safety grep — Redis adapter hardened", () => {
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
          violations.push(`${file.replace(process.cwd(), ".")}: ${label}`);
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

// Backend safety grep — covers Redis adapter + seeder
const BACKEND_DIRS = [
  join(process.cwd(), "..", "..", "packages", "tradehud_contracts"),
  join(process.cwd(), "..", "..", "scripts"),
];

const BACKEND_FORBIDDEN = [
  { pattern: /submit_order\s*\(/i, label: "submit_order() call" },
  { pattern: /force_approve\s*\(/i, label: "force_approve() call" },
  { pattern: /\.xadd\s*\(/i, label: "Redis XADD write" },
  { pattern: /\.set\s*\(/i, label: "Redis SET write" },
  { pattern: /exchange_api_key\s*[:=]/i, label: "exchange_api_key assignment" },
  { pattern: /secret_key\s*[:=]/i, label: "secret_key assignment" },
  { pattern: /private_key\s*[:=]/i, label: "private_key assignment" },
  { pattern: /BINANCE_SECRET/i, label: "BINANCE_SECRET reference" },
  { pattern: /BYBIT_SECRET/i, label: "BYBIT_SECRET reference" },
  { pattern: /NEXT_PUBLIC_REDIS_URL/i, label: "Redis URL in browser env" },
  { pattern: /NEXT_PUBLIC_DATABASE_URL/i, label: "Database URL in browser env" },
];

describe("Redis adapter backend safety grep", () => {
  it("no forbidden patterns in Redis adapter files", () => {
    const violations: string[] = [];
    for (const dir of BACKEND_DIRS) {
      if (!existsSync(dir)) continue;
      for (const entry of readdirSync(dir, { withFileTypes: true })) {
        const full = join(dir, entry.name);
        if (!entry.isFile() || !entry.name.endsWith(".py")) continue;
        // Only scan TradeHUD-related files, not all .py in scripts/
        if (!entry.name.includes("tradehud") && !entry.name.includes("redis")) continue;
        // Seeder is allowed to use XADD — skip it for write checks
        const isSeeder = entry.name === "tradehud_seed_redis.py"
          || entry.name === "tradehud_replay_nd_fixtures.py";
        const content = readFileSync(full, "utf-8");
        for (const { pattern, label } of BACKEND_FORBIDDEN) {
          if (isSeeder && (label === "Redis XADD write" || label === "submit_order() call")) continue;
          if (pattern.test(content)) {
            violations.push(`${entry.name}: ${label}`);
          }
        }
      }
    }
    expect(violations, `Forbidden patterns in Redis adapter backend:\n${violations.join("\n")}`).toEqual([]);
  });

  it("seeder is documented local-only", () => {
    const seederPath = join(process.cwd(), "..", "..", "scripts", "tradehud_seed_redis.py");
    if (!existsSync(seederPath)) return;
    const content = readFileSync(seederPath, "utf-8");
    expect(content).toContain("LOCAL DEVELOPMENT ONLY");
  });
});

// SSE backend safety grep
const SSE_BACKEND_FILES = [
  join(process.cwd(), "..", "..", "services", "api", "routes", "tradehud_sse.py"),
  join(process.cwd(), "..", "..", "services", "api", "routes", "tradehud.py"),
];

const SSE_FORBIDDEN = [
  { pattern: /submit_order\s*\(/i, label: "submit_order() call" },
  { pattern: /force_approve\s*\(/i, label: "force_approve() call" },
  { pattern: /exchange_api_key\s*[:=]/i, label: "exchange_api_key assignment" },
  { pattern: /secret_key\s*[:=]/i, label: "secret_key assignment" },
  { pattern: /private_key\s*[:=]/i, label: "private_key assignment" },
  { pattern: /BINANCE_SECRET/i, label: "BINANCE_SECRET reference" },
  { pattern: /BYBIT_SECRET/i, label: "BYBIT_SECRET reference" },
  { pattern: /NEXT_PUBLIC_REDIS_URL/i, label: "Redis URL in browser env" },
  { pattern: /NEXT_PUBLIC_DATABASE_URL/i, label: "Database URL in browser env" },
];

describe("SSE backend safety grep", () => {
  it("no forbidden patterns in SSE backend files", () => {
    const violations: string[] = [];
    for (const file of SSE_BACKEND_FILES) {
      if (!existsSync(file)) continue;
      const content = readFileSync(file, "utf-8");
      for (const { pattern, label } of SSE_FORBIDDEN) {
        if (pattern.test(content)) {
          violations.push(`${file.split("/").slice(-2).join("/")}: ${label}`);
        }
      }
    }
    expect(violations, `Forbidden patterns in SSE backend:\n${violations.join("\n")}`).toEqual([]);
  });

  it("no POST route definitions in SSE route files", () => {
    for (const file of SSE_BACKEND_FILES) {
      if (!existsSync(file)) continue;
      const content = readFileSync(file, "utf-8");
      expect(content).not.toMatch(/@app\.(post|put|patch|delete)/i);
    }
  });
});
