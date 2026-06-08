import { describe, it, expect } from "vitest";
import { mapLifecycleInput, mapEvidenceInput, mapAuditInput } from "./mapEvidenceSummary";
import type { StrategyEvidenceSummary } from "../../lib/types";

function makeSummary(overrides: Partial<StrategyEvidenceSummary> = {}): StrategyEvidenceSummary {
  return {
    strategyId: "strategy_001",
    strategyVersionId: "strategy_001_v001",
    strategyStatus: "draft",
    validation: { status: "missing", flags: {} },
    compile: { status: "missing", hash: null, artifactId: null },
    replay: { status: "missing", jobs: [] },
    promotion: { status: "missing" },
    audit: [],
    ...overrides,
  };
}

describe("mapLifecycleInput", () => {
  it("maps draft strategy with no evidence", () => {
    const input = mapLifecycleInput(makeSummary());
    expect(input.strategyId).toBe("strategy_001");
    expect(input.status).toBe("draft");
    expect(input.validation).toEqual({});
    expect(input.compileHash).toBeUndefined();
    expect(input.backtestJobId).toBeUndefined();
    expect(input.promotionRequested).toBe(false);
    expect(input.promotionApproved).toBe(false);
  });

  it("maps validated strategy with validation flags", () => {
    const input = mapLifecycleInput(
      makeSummary({
        strategyStatus: "validated",
        validation: { status: "passed", flags: { bar_close_only: true, no_lookahead_required: true } },
      }),
    );
    expect(input.status).toBe("validated");
    expect(input.validation).toEqual({ bar_close_only: true, no_lookahead_required: true });
  });

  it("maps compile hash from evidence summary", () => {
    const input = mapLifecycleInput(
      makeSummary({
        compile: { status: "passed", hash: "a".repeat(64), artifactId: "art_001" },
      }),
    );
    expect(input.compileHash).toBe("a".repeat(64));
    expect(input.compileArtifactId).toBe("art_001");
  });

  it("maps replay job from evidence summary", () => {
    const input = mapLifecycleInput(
      makeSummary({
        replay: {
          status: "passed",
          jobs: [
            {
              jobId: "bt_abc123",
              status: "passed",
              stage: "SUCCEEDED",
              lifecycleStatus: "SUCCEEDED",
              createdAt: "2025-01-01T00:00:00Z",
              updatedAt: "2025-01-01T01:00:00Z",
              compileHash: "a".repeat(64),
              compileArtifactId: "art_001",
              resultArtifactRefs: { report: "report.json" },
              datasetId: "ds_001",
            },
          ],
        },
      }),
    );
    expect(input.backtestJobId).toBe("bt_abc123");
    expect(input.backtestJobStatus).toBe("passed");
    expect(input.backtestResultArtifactRefs).toEqual({ report: "report.json" });
    expect(input.compileHash).toBe("a".repeat(64));
  });

  it("maps promotion ready from evidence summary", () => {
    const input = mapLifecycleInput(
      makeSummary({
        strategyStatus: "approved",
        promotion: { status: "ready" },
      }),
    );
    expect(input.promotionApproved).toBe(true);
    expect(input.promotionRequested).toBe(true);
  });

  it("maps promotion requested", () => {
    const input = mapLifecycleInput(
      makeSummary({ promotion: { status: "requested" } }),
    );
    expect(input.promotionRequested).toBe(true);
    expect(input.promotionApproved).toBe(false);
  });

  it("uses the last replay job when multiple exist", () => {
    const input = mapLifecycleInput(
      makeSummary({
        replay: {
          status: "failed",
          jobs: [
            {
              jobId: "bt_first",
              status: "passed",
              stage: "SUCCEEDED",
              lifecycleStatus: "SUCCEEDED",
              createdAt: "2025-01-01T00:00:00Z",
              updatedAt: "2025-01-01T01:00:00Z",
              compileHash: "a".repeat(64),
              compileArtifactId: null,
              resultArtifactRefs: {},
              datasetId: "ds_001",
            },
            {
              jobId: "bt_second",
              status: "failed",
              stage: "FAILED",
              lifecycleStatus: "FAILED",
              createdAt: "2025-01-02T00:00:00Z",
              updatedAt: "2025-01-02T01:00:00Z",
              compileHash: "b".repeat(64),
              compileArtifactId: null,
              resultArtifactRefs: {},
              datasetId: "ds_001",
            },
          ],
        },
      }),
    );
    expect(input.backtestJobId).toBe("bt_second");
    expect(input.backtestJobStatus).toBe("failed");
  });
});

describe("mapEvidenceInput", () => {
  it("maps all evidence fields", () => {
    const input = mapEvidenceInput(
      makeSummary({
        compile: { status: "passed", hash: "c".repeat(64), artifactId: "art_002" },
        replay: {
          status: "passed",
          jobs: [
            {
              jobId: "bt_xyz",
              status: "passed",
              stage: "SUCCEEDED",
              lifecycleStatus: "SUCCEEDED",
              createdAt: "2025-01-01T00:00:00Z",
              updatedAt: "2025-01-01T01:00:00Z",
              compileHash: "c".repeat(64),
              compileArtifactId: "art_002",
              resultArtifactRefs: { report: "report.json" },
              datasetId: "ds_001",
            },
          ],
        },
        promotion: { status: "ready" },
      }),
    );
    expect(input.strategyId).toBe("strategy_001");
    expect(input.compileHash).toBe("c".repeat(64));
    expect(input.backtestJobId).toBe("bt_xyz");
    expect(input.promotionApproved).toBe(true);
  });
});

describe("mapAuditInput", () => {
  it("maps audit input with replay job", () => {
    const input = mapAuditInput(
      makeSummary({
        validation: { status: "passed", flags: { bar_close_only: true } },
        compile: { status: "passed", hash: "d".repeat(64), artifactId: null },
        replay: {
          status: "passed",
          jobs: [
            {
              jobId: "bt_audit",
              status: "passed",
              stage: "SUCCEEDED",
              lifecycleStatus: "SUCCEEDED",
              createdAt: "2025-01-01T00:00:00Z",
              updatedAt: "2025-01-01T01:00:00Z",
              compileHash: "d".repeat(64),
              compileArtifactId: null,
              resultArtifactRefs: {},
              datasetId: "ds_001",
            },
          ],
        },
      }),
    );
    expect(input.strategyId).toBe("strategy_001");
    expect(input.compileHash).toBe("d".repeat(64));
    expect(input.backtestJobId).toBe("bt_audit");
    expect(input.validation).toEqual({ bar_close_only: true });
  });
});
