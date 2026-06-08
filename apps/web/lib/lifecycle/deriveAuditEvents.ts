/**
 * Derive audit events from existing backend data.
 *
 * Only shows events backed by existing records. Does NOT invent historical
 * events. If the backend provides no timestamps or state, only a generic
 * "created" event is emitted (since the strategy exists, it was created).
 */

import type { StrategyAuditEvent } from "./types";

export type AuditInput = {
  strategyId: string;
  strategyLineageId?: string;
  /** Backend strategy status. */
  status?: string;
  /** StrategySpec creation provenance. */
  createdBy?: string;
  createdAt?: string;
  /** Validation block. */
  validation?: Record<string, unknown>;
  /** Compile info. */
  compileHash?: string;
  /** Replay info. */
  backtestJobId?: string;
  backtestJobStatus?: string;
  backtestJobStage?: string;
  backtestUpdatedAt?: string;
  /** Promotion. */
  promotionRequested?: boolean;
  promotionApproved?: boolean;
};

function normalize(v: string | undefined): string {
  return (v ?? "").toLowerCase();
}

export function deriveAuditEvents(input: AuditInput): StrategyAuditEvent[] {
  const events: StrategyAuditEvent[] = [];
  const norm = normalize(input.status);
  let idx = 0;

  // ── Created ─────────────────────────────────────────────────────
  // If the strategy exists, it was created. This is the only safe
  // synthetic event.
  events.push({
    id: `${input.strategyId}_evt_${idx++}`,
    kind: "created",
    title: "Strategy draft created",
    detail: input.createdBy ? `Created by ${input.createdBy}` : undefined,
    timestamp: input.createdAt,
    actor: input.createdBy,
    status: "info",
  });

  // ── Validation ──────────────────────────────────────────────────
  if (input.validation && Object.keys(input.validation).length > 0) {
    const failed = Object.values(input.validation).some((v) => v === false);
    events.push({
      id: `${input.strategyId}_evt_${idx++}`,
      kind: failed ? "validation_failed" : "validated",
      title: failed ? "Validation failed" : "Validation passed",
      detail: failed
        ? "One or more validation checks failed"
        : "All validation checks passed",
      status: failed ? "error" : "success",
    });
  }

  // ── Compiled ────────────────────────────────────────────────────
  if (input.compileHash) {
    events.push({
      id: `${input.strategyId}_evt_${idx++}`,
      kind: "compiled",
      title: "Preview artifact compiled",
      detail: `Compile hash: ${input.compileHash.slice(0, 16)}...`,
      status: "success",
      hash: input.compileHash,
    });
  }

  // ── Replay / Backtest ───────────────────────────────────────────
  if (input.backtestJobId) {
    const combined = `${normalize(input.backtestJobStatus)} ${normalize(input.backtestJobStage)}`;
    if (combined.includes("fail")) {
      events.push({
        id: `${input.strategyId}_evt_${idx++}`,
        kind: "replay_failed",
        title: "Replay failed",
        detail: `Job ${input.backtestJobId}`,
        refId: input.backtestJobId,
        timestamp: input.backtestUpdatedAt,
        status: "error",
      });
    } else if (
      combined.includes("succeed") ||
      combined.includes("completed")
    ) {
      events.push({
        id: `${input.strategyId}_evt_${idx++}`,
        kind: "replay_completed",
        title: "Replay completed",
        detail: `Job ${input.backtestJobId}`,
        refId: input.backtestJobId,
        timestamp: input.backtestUpdatedAt,
        status: "success",
      });
    } else {
      events.push({
        id: `${input.strategyId}_evt_${idx++}`,
        kind: "replay_started",
        title: "Replay started",
        detail: `Job ${input.backtestJobId}`,
        refId: input.backtestJobId,
        timestamp: input.backtestUpdatedAt,
        status: "info",
      });
    }
  }

  // ── Promotion ───────────────────────────────────────────────────
  if (input.promotionApproved || ["approved", "execution_ready"].includes(norm)) {
    events.push({
      id: `${input.strategyId}_evt_${idx++}`,
      kind: "promotion_ready",
      title: "Promotion approved",
      status: "success",
    });
  } else if (input.promotionRequested) {
    events.push({
      id: `${input.strategyId}_evt_${idx++}`,
      kind: "promotion_requested",
      title: "Promotion requested",
      detail: "Pending manual review",
      status: "info",
    });
  }

  return events;
}
