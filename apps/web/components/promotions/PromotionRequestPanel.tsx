"use client";

import { useState } from "react";
import { Alert, Button, Descriptions, Space, Tag, Typography } from "antd";
import { requestShadowPromotion } from "../../lib/api";
import type { StrategySummary } from "../../lib/types";

export const PromotionRequestPanel = ({
  strategy,
}: {
  strategy?: StrategySummary | null;
}) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ target: string; manual_approval_required: boolean } | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!strategy) {
    return (
      <section className="panel" aria-label="promotion request">
        <Typography.Paragraph type="secondary">
          Select a strategy from the table above to request promotion review.
        </Typography.Paragraph>
      </section>
    );
  }

  async function onRequestPromotion() {
    if (!strategy) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await requestShadowPromotion({
        strategy_version_id: strategy.strategy_id,
        result_id: "res_pending",
        target: "shadow",
      });
      setResult({ target: res.target, manual_approval_required: res.manual_approval_required });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel" aria-label="promotion request">
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="Strategy">{strategy.strategy_id}</Descriptions.Item>
        <Descriptions.Item label="Status">
          <Tag color="blue">{strategy.status.replace("_", " ")}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Promotion target">
          <Space>
            <Tag color="purple">shadow</Tag>
            <Tag color="cyan">signal-preview</Tag>
          </Space>
        </Descriptions.Item>
        <Descriptions.Item label="Authority">
          <Space>
            <Tag color="red">may_submit_order: false</Tag>
            <Tag color="red">may_create_trade_action: false</Tag>
          </Space>
        </Descriptions.Item>
      </Descriptions>
      <Space style={{ marginTop: 12 }}>
        <Button
          type="primary"
          loading={loading}
          onClick={onRequestPromotion}
          disabled={strategy.status === "approved" || strategy.status === "execution_ready"}
        >
          Request shadow promotion
        </Button>
        <Typography.Text type="secondary">Requires manual approval before any downstream change.</Typography.Text>
      </Space>
      {result && (
        <Alert
          showIcon
          type="success"
          style={{ marginTop: 12 }}
          title="Promotion request submitted"
          description={
            <Space orientation="vertical" size={4}>
              <Typography.Text>Target: {result.target}</Typography.Text>
              <Typography.Text>Manual approval required: {String(result.manual_approval_required)}</Typography.Text>
              <Tag color="warning">approval_state: manual_approval_pending</Tag>
            </Space>
          }
        />
      )}
      {error && (
        <Alert showIcon type="error" style={{ marginTop: 12 }} title="Promotion request failed" description={error} />
      )}
    </section>
  );
};
