/**
 * Map the backend evidence summary response into normalized lifecycle inputs.
 *
 * This is a pure mapping function. It does not invent evidence, change backend
 * meaning, or create new authority. Missing fields remain missing.
 */

import type { StrategyEvidenceSummary } from "../types";
import type { LifecycleInput } from "./deriveStrategyLifecycle";
import type { EvidenceInput } from "./deriveEvidenceRefs";
import type { AuditInput } from "./deriveAuditEvents";

/**
 * Normalize a string to lowercase, returning undefined for empty/non-strings.
 */
function asString(value: unknown): string | undefined {
  if (typeof value === "string" && value.length > 0) return value;
  return undefined;
}

function normalizeStatus(value: unknown): string {
  if (typeof value === "string") return value.toLowerCase();
  return "";
}

/**
 * Map the evidence summary into the lifecycle derivation input.
 */
export function mapLifecycleInput(
  summary: StrategyEvidenceSummary,
): LifecycleInput {
  const replayJob =
    summary.replay.jobs.length > 0
      ? summary.replay.jobs[summary.replay.jobs.length - 1]
      : undefined;

  return {
    strategyId: summary.strategyId,
    strategyName: summary.strategyVersionId,
    status: summary.strategyStatus,
    validation: summary.validation.flags as Record<string, unknown>,
    compileHash:
      summary.compile.hash ??
      replayJob?.compileHash ??
      undefined,
    compileArtifactId:
      summary.compile.artifactId ??
      replayJob?.compileArtifactId ??
      undefined,
    backtestJobId: replayJob?.jobId,
    backtestJobStatus: replayJob?.status,
    backtestJobStage: replayJob?.stage,
    backtestJobLifecycleStatus: replayJob?.lifecycleStatus,
    backtestResultArtifactRefs: replayJob?.resultArtifactRefs,
    backtestJobUpdatedAt: replayJob?.updatedAt,
    promotionRequested:
      summary.promotion.status === "requested" ||
      summary.promotion.status === "ready",
    promotionApproved:
      summary.promotion.status === "ready" ||
      summary.promotion.status === "approved",
    updatedAt: replayJob?.updatedAt,
  };
}

/**
 * Map the evidence summary into the evidence refs derivation input.
 */
export function mapEvidenceInput(
  summary: StrategyEvidenceSummary,
): EvidenceInput {
  const replayJob =
    summary.replay.jobs.length > 0
      ? summary.replay.jobs[summary.replay.jobs.length - 1]
      : undefined;

  return {
    strategyId: summary.strategyId,
    validation: summary.validation.flags as Record<string, unknown>,
    compileHash: summary.compile.hash ?? undefined,
    compileArtifactId: summary.compile.artifactId ?? undefined,
    backtestJobId: replayJob?.jobId,
    backtestJobStatus: replayJob?.status,
    backtestResultArtifactRefs: replayJob?.resultArtifactRefs,
    status: summary.strategyStatus,
    promotionRequested:
      summary.promotion.status === "requested" ||
      summary.promotion.status === "ready",
    promotionApproved:
      summary.promotion.status === "ready" ||
      summary.promotion.status === "approved",
  };
}

/**
 * Map the evidence summary into the audit events derivation input.
 */
export function mapAuditInput(
  summary: StrategyEvidenceSummary,
): AuditInput {
  return {
    strategyId: summary.strategyId,
    strategyLineageId: summary.strategyVersionId,
    status: summary.strategyStatus,
    validation: summary.validation.flags as Record<string, unknown>,
    compileHash: summary.compile.hash ?? undefined,
    backtestJobId:
      summary.replay.jobs.length > 0
        ? summary.replay.jobs[summary.replay.jobs.length - 1].jobId
        : undefined,
    backtestJobStatus:
      summary.replay.jobs.length > 0
        ? summary.replay.jobs[summary.replay.jobs.length - 1].status
        : undefined,
    backtestJobStage:
      summary.replay.jobs.length > 0
        ? summary.replay.jobs[summary.replay.jobs.length - 1].stage
        : undefined,
    backtestUpdatedAt:
      summary.replay.jobs.length > 0
        ? summary.replay.jobs[summary.replay.jobs.length - 1].updatedAt
        : undefined,
    promotionApproved:
      summary.promotion.status === "ready" ||
      summary.promotion.status === "approved",
    promotionRequested:
      summary.promotion.status === "requested" ||
      summary.promotion.status === "ready",
  };
}
