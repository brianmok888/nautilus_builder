"use client";

import { ApiOutlined } from "@ant-design/icons";
import { Badge, Space, Tag } from "antd";
import { useHealthCheck } from "../../hooks/useHealthCheck";

function HealthIndicator() {
  const health = useHealthCheck();
  const color =
    health.status === "healthy"
      ? "success"
      : health.status === "degraded"
        ? "warning"
        : "error";
  const label =
    health.status === "healthy"
      ? "API healthy"
      : health.status === "degraded"
        ? "API degraded"
        : "API down";
  return (
    <Tag color={color}>
      {label}
      {health.latencyMs != null ? ` (${health.latencyMs}ms)` : ""}
    </Tag>
  );
}

export function BuilderTopBar() {
  return (
    <header className="nb-top-bar">
      <Space wrap size="small">
        <Badge status="processing" text="FastAPI / worker contracts" />
        <Tag color="blue" icon={<ApiOutlined />}>
          server-side API base
        </Tag>
      </Space>
      <HealthIndicator />
    </header>
  );
}
