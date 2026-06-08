"use client";

import { Empty, Space, Typography } from "antd";
import { DashboardCard } from "./DashboardCard";

const { Text, Link: AntLink } = Typography;

export type EmptyStateCardProps = {
  title: string;
  message: string;
  detail?: string;
  actionLabel?: string;
  actionHref?: string;
  onAction?: () => void;
};

export function EmptyStateCard({
  title,
  message,
  detail,
  actionLabel,
  actionHref,
  onAction,
}: EmptyStateCardProps) {
  return (
    <DashboardCard title={title}>
      <Empty
        image={Empty.PRESENTED_IMAGE_SIMPLE}
        description={
          <Space direction="vertical" size={4}>
            <Text>{message}</Text>
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
