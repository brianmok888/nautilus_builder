"use client";

import type { SourceFreshnessMeta } from "../../lib/tradehud/types";

const STATUS_CLASS: Record<string, string> = {
  live: "tradehud-freshness-live",
  stale: "tradehud-freshness-stale",
  missing: "tradehud-freshness-missing",
  synthetic: "tradehud-freshness-synthetic",
  true_zero: "tradehud-freshness-true_zero",
  unavailable: "tradehud-freshness-unavailable",
  unknown: "tradehud-freshness-missing",
};

const STATUS_LABEL: Record<string, string> = {
  live: "LIVE",
  stale: "STALE",
  missing: "MISSING",
  synthetic: "MOCK",
  true_zero: "TRUE ZERO",
  unavailable: "UNAVAILABLE",
  unknown: "UNKNOWN",
};

export function FreshnessBadge({ meta }: { meta: SourceFreshnessMeta }) {
  const cls = STATUS_CLASS[meta.source_status] ?? STATUS_CLASS.unknown;
  const label = STATUS_LABEL[meta.source_status] ?? "UNKNOWN";
  const ageStr = meta.age_ms != null ? ` ${Math.round(meta.age_ms)}ms` : "";
  return (
    <span className={`tradehud-freshness-badge ${cls}`} title={`provenance: ${meta.provenance}`}>
      {label}{ageStr}
    </span>
  );
}
