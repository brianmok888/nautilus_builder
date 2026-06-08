"use client";

import { Alert, Space, Typography } from "antd";
import { DashboardCard } from "./DashboardCard";

const { Text, Link: AntLink } = Typography;

export type BlockedStateCardProps = {
  title: string;
  reason: string;
  detail?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
};

export function BlockedStateCard({
  title,
  reason,
  detail,
  actionLabel,
  actionHref,
  onAction,
}: BlockedStateCardProps) {
  return (
    <DashboardCard>
      <Alert
        type="warning"
        showIcon
        message={title}
        description={
          <Space direction="vertical" size={4}>
            <Text>{reason}</Text>
            {detail && <Text type="secondary">{detail}</Text>}
            {actionLabel &&
              (actionHref ? (
                <AntLink href={actionHref}>{actionLabel}</AntLink>
              ) : onAction ? (
                <a onClick={onAction} style={{ cursor: "pointer" }}>
                  {actionLabel}
                </a>
              ) : null)}
          </Space>
        }
      />
    </DashboardCard>
  );
}
