import { describe, it, expect } from "vitest";
import { deriveEvidenceRefs } from "./deriveEvidenceRefs";
import type { EvidenceInput } from "./deriveEvidenceRefs";

describe("deriveEvidenceRefs", () => {
  const baseInput = (overrides: Partial<EvidenceInput> = {}): EvidenceInput => ({
    strategyId: "test-001",
    ...overrides,
  });

  it("marks strategy_spec as present even when everything else is missing", () => {
    const refs = deriveEvidenceRefs(baseInput());
    const spec = refs.find((r) => r.kind === "strategy_spec");
    expect(spec).toBeDefined();
    expect(spec!.status).toBe("present");
  });

  it("marks validation as missing when no validation block", () => {
    const refs = deriveEvidenceRefs(baseInput());
    const validation = refs.find((r) => r.kind === "validation");
    expect(validation!.status).toBe("missing");
  });

  it("marks validation as failed when validation has false fields", () => {
    const refs = deriveEvidenceRefs(
      baseInput({ validation: { bar_close_only: true, no_lookahead: false } }),
    );
    const validation = refs.find((r) => r.kind === "validation");
    expect(validation!.status).toBe("failed");
  });

  it("marks validation as passed when all fields are truthy", () => {
    const refs = deriveEvidenceRefs(
      baseInput({ validation: { bar_close_only: true, no_lookahead: true } }),
    );
    const validation = refs.find((r) => r.kind === "validation");
    expect(validation!.status).toBe("passed");
  });

  it("marks compile artifact as present when hash exists", () => {
    const refs = deriveEvidenceRefs(
      baseInput({ compileHash: "a".repeat(64) }),
    );
    const compile = refs.find((r) => r.kind === "compile_artifact");
    expect(compile!.status).toBe("present");
  });

  it("marks replay as failed when job status includes fail", () => {
    const refs = deriveEvidenceRefs(
      baseInput({ backtestJobStatus: "failed", backtestJobId: "job-1" }),
    );
    const replay = refs.find((r) => r.kind === "replay_report");
    expect(replay!.status).toBe("failed");
  });

  it("marks replay as passed when artifacts exist", () => {
    const refs = deriveEvidenceRefs(
      baseInput({
        backtestJobStatus: "succeeded",
        backtestResultArtifactRefs: { report: "report.json" },
      }),
    );
    const replay = refs.find((r) => r.kind === "replay_report");
    expect(replay!.status).toBe("passed");
  });

  it("marks promotion as missing when no promotion data", () => {
    const refs = deriveEvidenceRefs(baseInput());
    const promotion = refs.find((r) => r.kind === "promotion_request");
    expect(promotion!.status).toBe("missing");
  });

  it("marks promotion as passed when status is approved", () => {
    const refs = deriveEvidenceRefs(baseInput({ status: "approved" }));
    const promotion = refs.find((r) => r.kind === "promotion_request");
    expect(promotion!.status).toBe("passed");
  });

  it("always returns exactly 5 evidence refs", () => {
    const refs = deriveEvidenceRefs(baseInput());
    expect(refs).toHaveLength(5);
  });
});
