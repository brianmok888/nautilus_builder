/**
 * Derive a StrategyLifecycleSummary from existing backend data.
 *
 * PURE FRONTEND DERIVATION. This function does not call any backend, does not
 * change backend meaning, and never invents completed states. Missing data is
 * treated as missing; unknown data is treated as unknown.
 *
 * Source data:
 *   - StrategySummary / StrategyDetail.status (draft|validated|backtested|approved|execution_ready)
 *   - StrategySpec.validation fields (bar_close_only, no_lookahead_required, etc.)
 *   - BacktestJobStatus (status, stage, lifecycle_status, compile_hash, result_artifact_refs)
 *   - PromotionRequestResult / strategy.status (approved|execution_ready)
 */

import type {
  StrategyBlockingReason,
  StrategyLifecycleStage,
  StrategyLifecycleSummary,
  StrategyNextAction,
  LifecycleSubStatus,
  PromotionSubStatus,
} from "./types";

// ── Input type (loose, derived from existing API responses) ──────────

export type LifecycleInput = {
  strategyId: string;
  strategyName?: string;
  /** Backend strategy status (draft|validated|backtested|approved|execution_ready). */
  status?: string;
  /** StrategySpec validation block (bar_close_only, no_lookahead_required, etc.). */
  validation?: Record<string, unknown>;
  /** Compile artifact presence. */
  compileHash?: string;
  compileArtifactId?: string;
  /** Replay/backtest evidence. */
  backtestJobId?: string;
  backtestJobStatus?: string;
  backtestJobStage?: string;
  backtestJobLifecycleStatus?: string;
  backtestResultArtifactRefs?: Record<string, string>;
  backtestJobUpdatedAt?: string;
  /** Promotion state. */
  promotionRequested?: boolean;
  promotionApproved?: boolean;
  updatedAt?: string;
};

// ── Helpers ──────────────────────────────────────────────────────────

function normalize(value: string | undefined): string {
  return (value ?? "").toString().toLowerCase();
}

function hasValidationPassed(
  status: string,
  validation: Record<string, unknown> | undefined,
): LifecycleSubStatus {
  // Backend status "validated"|"backtested"|"approved"|"execution_ready" implies
  // validation passed at some point. "draft" with a validation block that has
  // no falsy fields is also considered passed. A validation block with a falsy
  // field is "failed". Absence of both is "missing".
  const norm = normalize(status);
  if (["validated", "backtested", "approved", "execution_ready"].includes(norm)) {
    return "passed";
  }
  if (!validation) return "missing";
  const values = Object.values(validation);
  if (values.length === 0) return "missing";
  const hasFalse = values.some((v) => v === false);
  if (hasFalse) return "failed";
  // Has validation block with no failures but backend status is draft/unknown.
  return norm === "draft" ? "unknown" : "passed";
}

function deriveCompileStatus(
  status: string,
  compileHash: string | undefined,
  compileArtifactId: string | undefined,
): LifecycleSubStatus {
  const norm = normalize(status);
  if (["backtested", "approved", "execution_ready"].includes(norm)) {
    // Backend statuses >= backtested imply a compile artifact existed at some
    // point (compile is a prerequisite). But only mark "passed" if a hash is
    // actually present; otherwise "unknown" — never fake it.
    if (compileHash || compileArtifactId) return "passed";
    return "unknown";
  }
  if (compileHash || compileArtifactId) return "passed";
  return "missing";
}

function deriveReplayStatus(input: LifecycleInput): LifecycleSubStatus {
  const norm = normalize(input.status);
  const jobNorm = normalize(input.backtestJobStatus);
  const stageNorm = normalize(input.backtestJobStage);
  const lifecycleNorm = normalize(input.backtestJobLifecycleStatus);
  const combined = `${jobNorm} ${stageNorm} ${lifecycleNorm}`;
  const artifactRefs = input.backtestResultArtifactRefs ?? {};
  const hasArtifacts = Object.keys(artifactRefs).length > 0;
  const hasStatusOnlyReplay = Boolean(input.backtestJobId || jobNorm || stageNorm || lifecycleNorm) ||
    ["backtested", "approved", "execution_ready"].includes(norm);

  if (combined.includes("fail")) return "failed";
  if (hasArtifacts) return "passed";
  if (hasStatusOnlyReplay) return "unknown";
  return "missing";
}

function derivePromotionStatus(
  status: string,
  promotionRequested: boolean | undefined,
  promotionApproved: boolean | undefined,
): PromotionSubStatus {
  const norm = normalize(status);
  if (promotionApproved) return "ready";
  if (promotionRequested) return "requested";
  if (["approved", "execution_ready"].includes(norm)) return "unknown";
  return "missing";
}

// ── Stage resolution ─────────────────────────────────────────────────

function resolveStage(
  validation: LifecycleSubStatus,
  compile: LifecycleSubStatus,
  replay: LifecycleSubStatus,
  promotion: PromotionSubStatus,
  status: string,
): StrategyLifecycleStage {
  // Promotion takes priority when ready/requested.
  if (promotion === "ready") return "promotion_ready";
  if (promotion === "blocked") return "promotion_blocked";
  if (promotion === "requested") return "promotion_requested";

  // Replay failures take priority.
  if (replay === "failed") return "replay_failed";

  // Passed replay → show replay_passed unless compile missing (shouldn't happen
  // since compile is a prerequisite, but we don't fake it).
  if (replay === "passed") {
    return "replay_passed";
  }

  // Replay-missing only when there IS a compile artifact (otherwise we are
  // still at compile / validated stage — not missing replay yet).
  if (replay === "missing" && compile === "passed") {
    return "replay_missing";
  }

  // Compile present.
  if (compile === "passed") return "compiled";

  // Validation.
  if (validation === "failed") return "validation_failed";
  if (validation === "passed") return "validated";

  // Draft fallback.
  if (status === "draft" || status === "") return "draft";
  return "unknown";
}

function resolveNextAction(
  validation: LifecycleSubStatus,
  compile: LifecycleSubStatus,
  replay: LifecycleSubStatus,
  promotion: PromotionSubStatus,
): StrategyNextAction {
  if (validation === "missing") return "validate_strategy_spec";
  if (validation === "failed") return "fix_validation_errors";
  if (compile === "missing") return "compile_preview_artifact";
  if (replay === "missing") return "run_replay";
  if (replay === "failed") return "review_replay_errors";
  if (promotion === "missing") return "request_promotion_review";
  if (promotion === "blocked") return "review_promotion_blockers";
  if (promotion === "ready" || promotion === "requested") return "inspect_evidence";
  return "inspect_evidence";
}

function deriveBlockingReasons(
  validation: LifecycleSubStatus,
  compile: LifecycleSubStatus,
  replay: LifecycleSubStatus,
  promotion: PromotionSubStatus,
): StrategyBlockingReason[] {
  const reasons: StrategyBlockingReason[] = [];
  if (validation === "failed") {
    reasons.push({
      code: "validation_failed",
      title: "Validation failed",
      detail: "One or more StrategySpec validation checks failed.",
      severity: "error",
    });
  }
  if (validation === "missing") {
    reasons.push({
      code: "validation_missing",
      title: "Validation evidence missing",
      detail: "Run validation before compiling or replaying.",
      severity: "info",
    });
  }
  if (compile === "missing" && validation === "passed") {
    reasons.push({
      code: "compile_missing",
      title: "Compile artifact missing",
      detail: "Compile a preview artifact before running replay.",
      severity: "warning",
    });
  }
  if (replay === "failed") {
    reasons.push({
      code: "replay_failed",
      title: "Replay failed",
      detail: "Review replay errors before requesting promotion.",
      severity: "error",
    });
  }
  if (replay === "missing" && compile === "passed") {
    reasons.push({
      code: "replay_missing",
      title: "Replay evidence missing",
      detail: "Run a replay to generate backtest evidence.",
      severity: "warning",
    });
  }
  if (promotion === "blocked") {
    reasons.push({
      code: "promotion_blocked",
      title: "Promotion blocked",
      detail: "Review promotion blockers before retrying.",
      severity: "error",
    });
  }
  return reasons;
}

// ── Public entry point ───────────────────────────────────────────────

export function deriveStrategyLifecycle(
  input: LifecycleInput,
): StrategyLifecycleSummary {
  const norm = normalize(input.status);
  const validationStatus = hasValidationPassed(norm, input.validation);
  const compileStatus = deriveCompileStatus(
    norm,
    input.compileHash,
    input.compileArtifactId,
  );
  const replayStatus = deriveReplayStatus(input);
  const promotionStatus = derivePromotionStatus(
    norm,
    input.promotionRequested,
    input.promotionApproved,
  );

  const currentStage = resolveStage(
    validationStatus,
    compileStatus,
    replayStatus,
    promotionStatus,
    norm,
  );
  const nextAction = resolveNextAction(
    validationStatus,
    compileStatus,
    replayStatus,
    promotionStatus,
  );
  const blockingReasons = deriveBlockingReasons(
    validationStatus,
    compileStatus,
    replayStatus,
    promotionStatus,
  );

  return {
    strategyId: input.strategyId,
    strategyName: input.strategyName ?? input.strategyId,
    currentStage,
    validationStatus,
    compileStatus,
    replayStatus,
    promotionStatus,
    nextAction,
    blockingReasons,
    evidenceRefs: [],
    updatedAt: input.updatedAt,
  };
}

// ── Display helpers ──────────────────────────────────────────────────

export const LIFECYCLE_STAGE_LABELS: Record<StrategyLifecycleStage, string> = {
  draft: "Draft",
  validation_failed: "Validation failed",
  validated: "Validated",
  compiled: "Compiled",
  replay_missing: "Replay missing",
  replay_failed: "Replay failed",
  replay_passed: "Replay passed",
  promotion_missing: "Promotion pending",
  promotion_requested: "Promotion requested",
  promotion_blocked: "Promotion blocked",
  promotion_ready: "Ready for review",
  execution_profile_pending: "Execution profile pending",
  unknown: "Unknown",
};

export const NEXT_ACTION_LABELS: Record<StrategyNextAction, string> = {
  create_draft: "Create a strategy draft",
  validate_strategy_spec: "Validate the StrategySpec",
  fix_validation_errors: "Fix validation errors",
  compile_preview_artifact: "Compile a preview artifact",
  run_replay: "Run replay",
  review_replay_errors: "Review replay errors",
  request_promotion_review: "Request promotion review",
  review_promotion_blockers: "Review promotion blockers",
  inspect_evidence: "Inspect the collected evidence",
  no_action_available: "No action available",
};

export const NEXT_ACTION_EXPLANATIONS: Record<StrategyNextAction, string> = {
  create_draft: "Start by drafting a StrategySpec in the Strategy Builder.",
  validate_strategy_spec:
    "Run validation to confirm the StrategySpec is internally consistent.",
  fix_validation_errors:
    "One or more validation checks failed. Edit the StrategySpec and re-run validation.",
  compile_preview_artifact:
    "Compile a preview artifact before running replay evidence.",
  run_replay:
    "Run a historical replay to generate backtest evidence.",
  review_replay_errors:
    "The replay run failed. Review the errors before retrying.",
  request_promotion_review:
    "Replay evidence exists. Request a manual promotion review.",
  review_promotion_blockers:
    "Promotion is blocked. Resolve the blockers before retrying.",
  inspect_evidence:
    "Evidence has been collected. Inspect it before any manual review.",
  no_action_available: "Action not available from current state.",
};
