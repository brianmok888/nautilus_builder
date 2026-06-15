/**
 * Phase 6: ND evidence semantics test.
 * Verifies evidence panels render correct labels and do NOT render
 * forbidden action terms (Submit, Cancel, Modify, Approve, Force).
 */
import { describe, it, expect } from "vitest";
import { readFileSync, readdirSync, existsSync } from "fs";
import { join } from "path";

const COMPONENTS_DIR = join(process.cwd(), "components/tradehud");

function readFile(filename: string): string {
  return readFileSync(join(COMPONENTS_DIR, filename), "utf-8");
}

describe("SignalPreviewPanel evidence semantics", () => {
  it("renders NOT EXECUTABLE label", () => {
    const src = readFile("SignalPreviewPanel.tsx");
    expect(src).toContain("NOT EXECUTABLE");
  });

  it("does not render Submit, Cancel, Modify, Approve, Force as UI labels", () => {
    const src = readFile("SignalPreviewPanel.tsx");
    // These words must not appear as actionable button/label text
    const forbidden = [">Submit<", ">Cancel<", ">Modify<", ">Approve<", ">Force<"];
    for (const term of forbidden) {
      expect(src).not.toContain(term);
    }
  });
});

describe("TradeActionEvidencePanel evidence semantics", () => {
  it("renders RUNTIME-CONSUMED EVIDENCE ONLY label", () => {
    const src = readFile("TradeActionEvidencePanel.tsx");
    expect(src).toContain("RUNTIME-CONSUMED EVIDENCE");
  });

  it("does not render Submit, Cancel, Modify, Approve, Force", () => {
    const src = readFile("TradeActionEvidencePanel.tsx");
    const forbidden = [">Submit<", ">Cancel<", ">Modify<", ">Approve<", ">Force<"];
    for (const term of forbidden) {
      expect(src).not.toContain(term);
    }
  });
});

describe("ExecutionReportPanel evidence semantics", () => {
  it("renders EXCHANGE/RUNTIME EVIDENCE label", () => {
    const src = readFile("ExecutionReportPanel.tsx");
    expect(src).toContain("EXCHANGE/RUNTIME EVIDENCE");
  });

  it("displays execution status (not strategy confidence)", () => {
    const src = readFile("ExecutionReportPanel.tsx");
    expect(src).toContain("report.status");
    // Must NOT imply strategy confidence
    expect(src).not.toContain("strategy confidence");
    expect(src).not.toContain("Strategy Confidence");
  });
});

describe("GateDecisionPanel evidence semantics", () => {
  it("renders APPROVAL EVIDENCE label", () => {
    const src = readFile("GateDecisionPanel.tsx");
    // Must contain evidence-type label
    expect(src).toMatch(/APPROVAL|HOLD|REJECTION.*EVIDENCE/);
  });

  it("displays first_blocking_gate", () => {
    const src = readFile("GateDecisionPanel.tsx");
    expect(src).toContain("first_blocking_gate");
  });

  it("displays reason_code", () => {
    const src = readFile("GateDecisionPanel.tsx");
    expect(src).toContain("reason_code");
  });

  it("displays size_modifier", () => {
    const src = readFile("GateDecisionPanel.tsx");
    expect(src).toContain("size_modifier");
  });

  it("displays gate_decision_hash", () => {
    const src = readFile("GateDecisionPanel.tsx");
    expect(src).toContain("gate_decision_hash");
  });
});
