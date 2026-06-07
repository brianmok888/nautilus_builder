import { describe, expect, it } from "vitest";
import fs from "fs";
import path from "path";

const WEB_ROOT = path.resolve(__dirname);

function readSourceFiles(dir: string): string[] {
  const results: string[] = [];
  if (!fs.existsSync(dir)) return results;
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory() && entry.name !== "node_modules" && entry.name !== ".next") {
      results.push(...readSourceFiles(full));
    } else if (
      entry.isFile() &&
      (entry.name.endsWith(".ts") || entry.name.endsWith(".tsx")) &&
      !entry.name.includes(".test.") &&
      !entry.name.includes("safety-contract")
    ) {
      results.push(full);
    }
  }
  return results;
}

describe("Frontend safety contract", () => {
  it("has no submit_order function calls in frontend source", () => {
    const files = readSourceFiles(WEB_ROOT);
    const violations: string[] = [];
    for (const file of files) {
      const content = fs.readFileSync(file, "utf-8");
      const lines = content.split("\n");
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (
          /(?<!may_|_|\w)submit_order\s*\(/.test(line) &&
          !line.includes("blocked") &&
          !line.includes("unsupported strategy block")
        ) {
          violations.push(`${path.relative(WEB_ROOT, file)}:${i + 1}: ${line.trim()}`);
        }
      }
    }
    expect(violations, `Found submit_order calls:\n${violations.join("\n")}`).toEqual([]);
  });

  it("has no TradeAction creation in frontend source", () => {
    const files = readSourceFiles(WEB_ROOT);
    const violations: string[] = [];
    for (const file of files) {
      const content = fs.readFileSync(file, "utf-8");
      if (/new\s+TradeAction|TradeAction\s*\(/.test(content) && !content.includes("blocked")) {
        violations.push(path.relative(WEB_ROOT, file));
      }
    }
    expect(violations, `Found TradeAction creation:\n${violations.join("\n")}`).toEqual([]);
  });

  it("has no forbidden live trading wording", () => {
    const files = readSourceFiles(WEB_ROOT);
    const forbidden = [
      "Start live trading",
      "Auto trade now",
      "Execute strategy",
      "Live bot running",
      "Guaranteed profit",
    ];
    const violations: string[] = [];
    for (const file of files) {
      const content = fs.readFileSync(file, "utf-8");
      for (const phrase of forbidden) {
        if (content.includes(phrase)) {
          violations.push(`${path.relative(WEB_ROOT, file)}: "${phrase}"`);
        }
      }
    }
    expect(violations, `Found forbidden wording:\n${violations.join("\n")}`).toEqual([]);
  });
});
