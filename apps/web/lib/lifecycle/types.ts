/**
 * Strategy lifecycle types for Builder-only UI.
 *
 * These types represent *derived* frontend state from existing backend data.
 * They do not change backend meaning, validation logic, or promotion authority.
 *
 * ND (non-negotiable directive):
 *   - missing is not zero
 *   - unknown is not passed
 *   - preview is not approved
 *   - replay is not live execution
 */

// ── Lifecycle stage ──────────────────────────────────────────────────

export type StrategyLifecycleStage =
  | "draft"
  | "validation_failed"
  | "validated"
  | "compiled"
  | "replay_missing"
  | "replay_failed"
  | "replay_passed"
  | "promotion_missing"
  | "promotion_requested"
  | "promotion_blocked"
  | "promotion_ready"
  | "execution_profile_pending"
  | "unknown";

// ── Sub-statuses ─────────────────────────────────────────────────────

export type LifecycleSubStatus = "missing" | "failed" | "passed" | "unknown";
export type PromotionSubStatus =
  | "missing"
  | "blocked"
  | "requested"
  | "ready"
  | "unknown";

// ── Next action ──────────────────────────────────────────────────────

export type StrategyNextAction =
  | "create_draft"
  | "validate_strategy_spec"
  | "fix_validation_errors"
  | "compile_preview_artifact"
  | "run_replay"
  | "review_replay_errors"
  | "request_promotion_review"
  | "review_promotion_blockers"
  | "inspect_evidence"
  | "no_action_available";

// ── Blocking reason ──────────────────────────────────────────────────

export type StrategyBlockingReason = {
  code: string;
  title: string;
  detail?: string;
  severity: "info" | "warning" | "error";
};

// ── Evidence reference ───────────────────────────────────────────────

export type StrategyEvidenceRef = {
  kind:
    | "strategy_spec"
    | "validation"
    | "compile_artifact"
    | "replay_report"
    | "promotion_request"
    | "audit_event";
  status: "missing" | "present" | "failed" | "passed" | "unknown";
  label: string;
  refId?: string;
  hash?: string;
  createdAt?: string;
  href?: string;
};

// ── Lifecycle summary ────────────────────────────────────────────────

export type StrategyLifecycleSummary = {
  strategyId: string;
  strategyName: string;
  currentStage: StrategyLifecycleStage;
  validationStatus: LifecycleSubStatus;
  compileStatus: LifecycleSubStatus;
  replayStatus: LifecycleSubStatus;
  promotionStatus: PromotionSubStatus;
  nextAction: StrategyNextAction;
  blockingReasons: StrategyBlockingReason[];
  evidenceRefs: StrategyEvidenceRef[];
  updatedAt?: string;
};

// ── Audit event ──────────────────────────────────────────────────────

export type StrategyAuditEvent = {
  id: string;
  kind:
    | "created"
    | "updated"
    | "validated"
    | "validation_failed"
    | "compiled"
    | "compile_failed"
    | "replay_started"
    | "replay_completed"
    | "replay_failed"
    | "promotion_requested"
    | "promotion_blocked"
    | "promotion_ready"
    | "unknown";
  title: string;
  detail?: string;
  timestamp?: string;
  actor?: string;
  status?: "success" | "warning" | "error" | "info";
  refId?: string;
  hash?: string;
};

// ── Lifecycle chain (for display) ────────────────────────────────────

export type LifecycleChainStep = {
  key: StrategyLifecycleStage;
  label: string;
  description: string;
};
