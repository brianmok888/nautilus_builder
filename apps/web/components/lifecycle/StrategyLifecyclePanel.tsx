"use client";

import { Space, Tag } from "antd";
import { DashboardCard } from "../ui/DashboardCard";
import type {
  StrategyLifecycleStage,
  StrategyLifecycleSummary,
} from "../../lib/lifecycle/types";
import { LIFECYCLE_STAGE_LABELS } from "../../lib/lifecycle/deriveStrategyLifecycle";

/** Visual lifecycle chain — ordered stages the UI shows as a timeline. */
const LIFECYCLE_CHAIN: StrategyLifecycleStage[] = [
  "draft",
  "validated",
  "compiled",
  "replay_passed",
  "promotion_ready",
  "execution_profile_pending",
];

/** Map sub-stages back to chain index for "reached" calculation. */
function chainIndex(stage: StrategyLifecycleStage): number {
  if (stage === "validation_failed") return 0;
  if (stage === "replay_missing" || stage === "replay_failed") return 2;
  if (
    stage === "promotion_missing" ||
    stage === "promotion_requested" ||
    stage === "promotion_blocked"
  )
    return 3;
  return LIFECYCLE_CHAIN.indexOf(stage);
}

const STAGE_COLORS: Record<string, string> = {
  draft: "default",
  validation_failed: "red",
  validated: "blue",
  compiled: "blue",
  replay_missing: "orange",
  replay_failed: "red",
  replay_passed: "green",
  promotion_missing: "default",
  promotion_requested: "purple",
  promotion_blocked: "red",
  promotion_ready: "green",
  execution_profile_pending: "gold",
  unknown: "default",
};

type Props = {
  summary: StrategyLifecycleSummary;
};

export function StrategyLifecyclePanel({ summary }: Props) {
  const currentIdx = chainIndex(summary.currentStage);

  return (
    <DashboardCard title="Lifecycle" subtitle="Strategy progress through the Builder pipeline">
      <Space wrap size={[8, 12]}>
        {LIFECYCLE_CHAIN.map((stage, idx) => {
          const reached = idx <= currentIdx;
          const isCurrent = stage === summary.currentStage;
          const isFailed = [
            "validation_failed",
            "replay_failed",
            "promotion_blocked",
          ].includes(summary.currentStage) && idx === currentIdx;

          return (
            <Tag
              key={stage}
              color={
                isFailed
                  ? "red"
                  : isCurrent
                    ? STAGE_COLORS[stage] ?? "blue"
                    : reached
                      ? "blue"
                      : "default"
              }
              style={{
                opacity: reached || isFailed ? 1 : 0.4,
                fontWeight: isCurrent ? 600 : 400,
              }}
            >
              {isCurrent ? "● " : reached ? "✓ " : "○ "}
              {LIFECYCLE_STAGE_LABELS[stage]}
            </Tag>
          );
        })}
      </Space>
      {/* Show the derived stage when it doesn't match a main-chain step. */}
      {!LIFECYCLE_CHAIN.includes(summary.currentStage) && (
        <div style={{ marginTop: 8 }}>
          <Tag
            color={STAGE_COLORS[summary.currentStage] ?? "default"}
            style={{ fontWeight: 600 }}
          >
            ● {LIFECYCLE_STAGE_LABELS[summary.currentStage] ?? summary.currentStage}
          </Tag>
        </div>
      )}
    </DashboardCard>
  );
}
