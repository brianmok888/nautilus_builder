"use client";

import type { GateDecisionType, ExecutionStatusType } from "../../lib/tradehud/types";

export function StatusChip({ status }: { status: string }) {
  const lower = status.toLowerCase();
  const cls = `tradehud-status-${lower}` in STATUS_MAP
    ? STATUS_MAP[lower]
    : "tradehud-status-default";
  return <span className={`tradehud-status-chip ${cls}`}>{status}</span>;
}

const STATUS_MAP: Record<string, string> = {
  approved: "tradehud-status-approved",
  hold: "tradehud-status-hold",
  rejected: "tradehud-status-rejected",
  live: "tradehud-status-live",
  filled: "tradehud-status-filled",
  canceled: "tradehud-status-canceled",
  partial_fill: "tradehud-status-partial_fill",
  submitted: "tradehud-status-submitted",
  acked: "tradehud-status-acked",
  expired: "tradehud-status-expired",
};
