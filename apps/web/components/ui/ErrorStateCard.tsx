"use client";

import { Alert, Space, Typography } from "antd";
import { DashboardCard } from "./DashboardCard";

const { Text, Link: AntLink } = Typography;

export type ErrorStateCardProps = {
  title?: string;
  message: string;
  detail?: string;
  retryLabel?: string;
  onRetry?: () => void;
  retryHref?: string;
};

export function ErrorStateCard({
  title = "Error",
  message,
  detail,
  retryLabel,
  onRetry,
  retryHref,
}: ErrorStateCardProps) {
  return (
    <DashboardCard>
      <Alert
        type="error"
        showIcon
        message={title}
        description={
          <Space direction="vertical" size={4}>
            <Text>{message}</Text>
            {detail && <Text type="secondary">{detail}</Text>}
            {retryLabel &&
              (retryHref ? (
                <AntLink href={retryHref}>{retryLabel}</AntLink>
              ) : onRetry ? (
                <a onClick={onRetry} style={{ cursor: "pointer" }}>
                  {retryLabel}
                </a>
              ) : null)}
          </Space>
        }
      />
    </DashboardCard>
  );
}
