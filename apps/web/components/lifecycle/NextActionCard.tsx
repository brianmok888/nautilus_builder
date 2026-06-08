"use client";

import { Alert, Button, Space, Typography } from "antd";
import { DashboardCard } from "../ui/DashboardCard";
import type {
  StrategyBlockingReason,
  StrategyNextAction,
} from "../../lib/lifecycle/types";
import {
  NEXT_ACTION_EXPLANATIONS,
  NEXT_ACTION_LABELS,
} from "../../lib/lifecycle/deriveStrategyLifecycle";

const { Text, Link: AntLink } = Typography;

export type NextActionCardProps = {
  action: StrategyNextAction;
  blockingReasons?: StrategyBlockingReason[];
  onValidate?: () => void;
  onCompile?: () => void;
  onRunReplay?: () => void;
  onRequestPromotion?: () => void;
  links?: {
    validation?: string;
    compile?: string;
    replay?: string;
    promotion?: string;
  };
};

export function NextActionCard({
  action,
  blockingReasons = [],
  onValidate,
  onCompile,
  onRunReplay,
  onRequestPromotion,
  links,
}: NextActionCardProps) {
  const hasError = blockingReasons.some((r) => r.severity === "error");

  const primaryButton = renderPrimaryButton({
    action,
    onValidate,
    onCompile,
    onRunReplay,
    onRequestPromotion,
    links,
  });

  return (
    <DashboardCard
      title="Next action"
      subtitle="The recommended next safe step in the Builder workflow"
      actions={
        <Text type="secondary" style={{ fontSize: 12 }}>
          Builder-only mode
        </Text>
      }
    >
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        <Alert
          type={hasError ? "error" : "info"}
          showIcon
          message={NEXT_ACTION_LABELS[action] ?? "Next action"}
          description={NEXT_ACTION_EXPLANATIONS[action] ?? ""}
        />

        {primaryButton && <div>{primaryButton}</div>}

        {blockingReasons.length > 0 && (
          <Space direction="vertical" size={4} style={{ width: "100%" }}>
            <Text strong>Blocking reasons</Text>
            {blockingReasons.map((reason) => (
              <Alert
                key={reason.code}
                type={
                  reason.severity === "error"
                    ? "error"
                    : reason.severity === "warning"
                      ? "warning"
                      : "info"
                }
                message={reason.title}
                description={reason.detail}
                style={{ padding: "6px 12px" }}
              />
            ))}
          </Space>
        )}

        {action === "no_action_available" && (
          <Text type="secondary">Action not available from current state.</Text>
        )}
      </Space>
    </DashboardCard>
  );
}

function renderPrimaryButton({
  action,
  onValidate,
  onCompile,
  onRunReplay,
  onRequestPromotion,
  links,
}: {
  action: StrategyNextAction;
  onValidate?: () => void;
  onCompile?: () => void;
  onRunReplay?: () => void;
  onRequestPromotion?: () => void;
  links?: NextActionCardProps["links"];
}) {
  switch (action) {
    case "validate_strategy_spec":
      return (
        <Button type="primary" onClick={onValidate}>
          {NEXT_ACTION_LABELS[action]}
        </Button>
      );
    case "fix_validation_errors":
      return (
        links?.validation ? (
          <AntLink href={links.validation}>{NEXT_ACTION_LABELS[action]}</AntLink>
        ) : (
          <Button onClick={onValidate}>{NEXT_ACTION_LABELS[action]}</Button>
        )
      );
    case "compile_preview_artifact":
      return (
        <Button type="primary" onClick={onCompile}>
          {NEXT_ACTION_LABELS[action]}
        </Button>
      );
    case "run_replay":
      return (
        <Button type="primary" onClick={onRunReplay}>
          {NEXT_ACTION_LABELS[action]}
        </Button>
      );
    case "review_replay_errors":
      return links?.replay ? (
        <AntLink href={links.replay}>{NEXT_ACTION_LABELS[action]}</AntLink>
      ) : (
        <Button onClick={onRunReplay}>{NEXT_ACTION_LABELS[action]}</Button>
      );
    case "request_promotion_review":
      return (
        <Button type="primary" onClick={onRequestPromotion}>
          {NEXT_ACTION_LABELS[action]}
        </Button>
      );
    case "review_promotion_blockers":
      return links?.promotion ? (
        <AntLink href={links.promotion}>
          {NEXT_ACTION_LABELS[action]}
        </AntLink>
      ) : (
        <Button onClick={onRequestPromotion}>
          {NEXT_ACTION_LABELS[action]}
        </Button>
      );
    case "inspect_evidence":
      return null; // Evidence is shown inline in the EvidenceSummaryGrid.
    default:
      return null;
  }
}
