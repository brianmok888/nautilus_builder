import { describe, it, expect } from "vitest";
import { deriveStrategyLifecycle } from "./deriveStrategyLifecycle";
import type { LifecycleInput } from "./deriveStrategyLifecycle";

describe("deriveStrategyLifecycle", () => {
  const baseInput = (overrides: Partial<LifecycleInput> = {}): LifecycleInput => ({
    strategyId: "test-strategy-001",
    ...overrides,
  });

  it("returns draft when no evidence exists", () => {
    const result = deriveStrategyLifecycle(baseInput({ status: "draft" }));
    expect(result.currentStage).toBe("draft");
    expect(result.nextAction).toBe("validate_strategy_spec");
    expect(result.validationStatus).toBe("missing");
    expect(result.compileStatus).toBe("missing");
    expect(result.replayStatus).toBe("missing");
    expect(result.promotionStatus).toBe("missing");
  });

  it("returns validation_failed when validation has false fields", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "draft",
        validation: { bar_close_only: true, no_lookahead_required: false },
      }),
    );
    expect(result.currentStage).toBe("validation_failed");
    expect(result.validationStatus).toBe("failed");
    expect(result.nextAction).toBe("fix_validation_errors");
  });

  it("returns validated when backend status is validated", () => {
    const result = deriveStrategyLifecycle(baseInput({ status: "validated" }));
    expect(result.currentStage).toBe("validated");
    expect(result.validationStatus).toBe("passed");
    expect(result.nextAction).toBe("compile_preview_artifact");
  });

  it("returns replay_missing when compile exists but no replay", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "validated",
        compileHash: "a".repeat(64),
      }),
    );
    // Compile passed → now we need replay. Stage is replay_missing.
    expect(result.currentStage).toBe("replay_missing");
    expect(result.compileStatus).toBe("passed");
    expect(result.replayStatus).toBe("missing");
    expect(result.nextAction).toBe("run_replay");
  });

  it("returns replay_missing stage when compiled but no replay data", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "validated",
        compileHash: "a".repeat(64),
      }),
    );
    expect(result.replayStatus).toBe("missing");
    // Once compile is done, the stage advances to replay_missing
    expect(result.currentStage).toBe("replay_missing");
    expect(result.nextAction).toBe("run_replay");
  });

  it("returns replay_passed when backtest succeeded", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "backtested",
        backtestJobStatus: "succeeded",
        backtestResultArtifactRefs: { report: "report.json" },
      }),
    );
    expect(result.currentStage).toBe("replay_passed");
    expect(result.replayStatus).toBe("passed");
    expect(result.nextAction).toBe("request_promotion_review");
  });

  it("returns replay_failed when replay failed", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "validated",
        compileHash: "a".repeat(64),
        backtestJobStatus: "failed",
      }),
    );
    expect(result.currentStage).toBe("replay_failed");
    expect(result.replayStatus).toBe("failed");
    expect(result.nextAction).toBe("review_replay_errors");
  });

  it("returns promotion_ready when status is approved", () => {
    const result = deriveStrategyLifecycle(
      baseInput({ status: "approved" }),
    );
    expect(result.currentStage).toBe("promotion_ready");
    expect(result.promotionStatus).toBe("ready");
    expect(result.nextAction).toBe("inspect_evidence");
  });

  it("returns promotion_ready when status is execution_ready", () => {
    const result = deriveStrategyLifecycle(
      baseInput({ status: "execution_ready" }),
    );
    expect(result.currentStage).toBe("promotion_ready");
    expect(result.promotionStatus).toBe("ready");
  });

  it("returns promotion_requested when promotion requested but not approved", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "backtested",
        backtestJobStatus: "succeeded",
        backtestResultArtifactRefs: { report: "report.json" },
        promotionRequested: true,
      }),
    );
    expect(result.currentStage).toBe("promotion_requested");
    expect(result.promotionStatus).toBe("requested");
  });

  it("returns unknown for unrecognized status without other data", () => {
    const result = deriveStrategyLifecycle(
      baseInput({ status: "garbage_status" }),
    );
    expect(result.currentStage).toBe("unknown");
  });

  it("has correct blocking reasons for validation failure", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "draft",
        validation: { bar_close_only: false },
      }),
    );
    expect(result.blockingReasons).toContainEqual(
      expect.objectContaining({ code: "validation_failed" }),
    );
  });

  it("has correct blocking reasons for missing replay after compile", () => {
    const result = deriveStrategyLifecycle(
      baseInput({
        status: "validated",
        compileHash: "a".repeat(64),
      }),
    );
    const codes = result.blockingReasons.map((r) => r.code);
    expect(codes).toContain("replay_missing");
  });

  it("never marks missing as passed", () => {
    const result = deriveStrategyLifecycle(baseInput({ status: "draft" }));
    expect(result.validationStatus).toBe("missing");
    expect(result.compileStatus).toBe("missing");
    expect(result.replayStatus).toBe("missing");
    expect(result.promotionStatus).toBe("missing");
    expect(result.validationStatus).not.toBe("passed");
    expect(result.compileStatus).not.toBe("passed");
    expect(result.replayStatus).not.toBe("passed");
  });

  it("never marks unknown as passed", () => {
    const result = deriveStrategyLifecycle(
      baseInput({ status: "draft", validation: { bar_close_only: true } }),
    );
    expect(result.validationStatus).toBe("unknown");
    expect(result.validationStatus).not.toBe("passed");
  });
});
