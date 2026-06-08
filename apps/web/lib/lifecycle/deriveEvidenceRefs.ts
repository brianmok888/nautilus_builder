/**
 * Derive evidence references from existing backend data.
 *
 * Uses only fields that already exist in API responses.
 * Never invents evidence. Missing data is marked as missing.
 */

import type { StrategyEvidenceRef } from "./types";

export type EvidenceInput = {
  strategyId: string;
  /** StrategySpec validation block. */
  validation?: Record<string, unknown>;
  /** Compile hash / artifact ID. */
  compileHash?: string;
  compileArtifactId?: string;
  /** Replay / backtest evidence. */
  backtestJobId?: string;
  backtestJobStatus?: string;
  backtestResultArtifactRefs?: Record<string, string>;
  /** Promotion. */
  promotionRequested?: boolean;
  promotionApproved?: boolean;
  /** Strategy status. */
  status?: string;
};

function normalize(v: string | undefined): string {
  return (v ?? "").toLowerCase();
}

export function deriveEvidenceRefs(input: EvidenceInput): StrategyEvidenceRef[] {
  const refs: StrategyEvidenceRef[] = [];
  const norm = normalize(input.status);

  // ── StrategySpec ────────────────────────────────────────────────
  refs.push({
    kind: "strategy_spec",
    status: "present",
    label: "StrategySpec",
    refId: input.strategyId,
    href: `/strategies/${input.strategyId}`,
  });

  // ── Validation ─────────────────────────────────────────────────
  const hasValidation = input.validation && Object.keys(input.validation).length > 0;
  const validationFailed =
    hasValidation && Object.values(input.validation!).some((v) => v === false);
  refs.push({
    kind: "validation",
    status: !hasValidation
      ? "missing"
      : validationFailed
        ? "failed"
        : "passed",
    label: "Validation evidence",
    refId: input.strategyId,
  });

  // ── Compile artifact ───────────────────────────────────────────
  const hasCompile = Boolean(input.compileHash || input.compileArtifactId);
  refs.push({
    kind: "compile_artifact",
    status: hasCompile ? "present" : "missing",
    label: "Compile artifact",
    hash: input.compileHash,
    refId: input.compileArtifactId,
  });

  // ── Replay / backtest report ───────────────────────────────────
  const combined = `${normalize(input.backtestJobStatus)}`;
  const hasReplayArtifacts =
    (input.backtestResultArtifactRefs &&
      Object.keys(input.backtestResultArtifactRefs).length > 0) ||
    combined.includes("succeed") ||
    combined.includes("completed");
  const replayFailed = combined.includes("fail");
  refs.push({
    kind: "replay_report",
    status: replayFailed
      ? "failed"
      : hasReplayArtifacts
        ? "passed"
        : "missing",
    label: "Replay / backtest evidence",
    refId: input.backtestJobId,
    href: input.backtestJobId ? `/backtests/${input.backtestJobId}` : undefined,
  });

  // ── Promotion request ──────────────────────────────────────────
  const hasPromotion =
    input.promotionRequested ||
    input.promotionApproved ||
    ["approved", "execution_ready"].includes(norm);
  refs.push({
    kind: "promotion_request",
    status: !hasPromotion
      ? "missing"
      : input.promotionApproved || ["approved", "execution_ready"].includes(norm)
        ? "passed"
        : "present",
    label: "Promotion request",
  });

  return refs;
}
