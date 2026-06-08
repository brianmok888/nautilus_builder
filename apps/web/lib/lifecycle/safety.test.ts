/**
 * Frontend safety guard: scans source files for forbidden live-trading wording.
 *
 * Hits must fail unless they are explicit negative safety copy
 * (e.g., "No live order submission", "Builder-only mode").
 */
import { describe, it, expect } from "vitest";
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, resolve } from "node:path";

const ROOT = resolve(__dirname, "..");

const FORBIDDEN_PHRASES = [
  // These are positive/actionable phrases that should never appear in UI.
  // Negative safety copy like "No live order submission" is allowed.
  "Start live trading",
  "live trading enabled",
  "Auto execute",
  "Guaranteed profit",
  "Auto trade now",
  "Deploy to exchange",
];

const ALLOWED_NEGATIVE_CONTEXTS = [
  "no live order submission",
  "does not submit live orders",
  "may_submit_order: false",
  "submit_order access",
  "submit_order: false",
  "builder-only",
  "live credentials used",
  "live credentials",
  "no live credentials",
  "may_submit_order",
];

function listFiles(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      if (entry === "node_modules" || entry === ".next" || entry === "dist" || entry === ".ruff_cache") continue;
      out.push(...listFiles(full));
    } else if (/\.(ts|tsx)$/.test(entry) && !/\.test\.(ts|tsx)$/.test(entry)) {
      out.push(full);
    }
  }
  return out;
}

describe("frontend safety — forbidden live-trading wording", () => {
  const files = listFiles(ROOT);

  it("no source file contains forbidden actionable live-trading wording", () => {
    const hits: string[] = [];
    for (const file of files) {
      const content = readFileSync(file, "utf8");
      for (const phrase of FORBIDDEN_PHRASES) {
        let idx = 0;
        while ((idx = content.indexOf(phrase, idx)) !== -1) {
          const window = content.slice(Math.max(0, idx - 80), idx + phrase.length + 80);
          const isNegative = ALLOWED_NEGATIVE_CONTEXTS.some((ctx) =>
            window.toLowerCase().includes(ctx.toLowerCase()),
          );
          if (isNegative) {
            idx += phrase.length;
            continue;
          }
          hits.push(
            `"${phrase}" in ${file} at offset ${idx}: "${content.slice(Math.max(0, idx - 30), idx + phrase.length + 30)}"`,
          );
          idx += phrase.length;
        }
      }
    }
    if (hits.length > 0) {
      expect.fail(`Forbidden wording found:\n${hits.join("\n")}`);
    }
    expect(hits).toHaveLength(0);
  });
});
