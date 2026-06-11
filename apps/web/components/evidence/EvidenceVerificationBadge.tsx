/**
 * EvidenceVerificationBadge — shows evidence verification status.
 *
 * Displays: verified, failed, unverified, hash_mismatch states.
 * Safety: Read-only display, no action buttons.
 */
import React from "react";

export type VerificationStatus = "unverified" | "verified" | "failed" | "hash_mismatch" | "expired" | "missing";

export interface EvidenceVerificationBadgeProps {
  status: VerificationStatus;
  artifactType: string;
  sha256?: string;
  blockingReason?: string;
}

const STATUS_LABELS: Record<VerificationStatus, string> = {
  unverified: "Unverified",
  verified: "Verified",
  failed: "Failed",
  hash_mismatch: "Hash Mismatch",
  expired: "Expired",
  missing: "Missing",
};

export default function EvidenceVerificationBadge({
  status,
  artifactType,
  sha256,
  blockingReason,
}: EvidenceVerificationBadgeProps) {
  return (
    <span data-testid="evidence-badge" className={`evidence-badge status-${status}`}>
      {artifactType}: {STATUS_LABELS[status]}
      {blockingReason && <span className="blocking-reason">{blockingReason}</span>}
    </span>
  );
}
