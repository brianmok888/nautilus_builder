"use client";

import { Empty, Tag, Timeline, Typography } from "antd";
import { DashboardCard } from "../ui/DashboardCard";
import type { StrategyAuditEvent } from "../../lib/lifecycle/types";

const { Text } = Typography;

const STATUS_DOT_COLORS: Record<string, string> = {
  success: "green",
  warning: "orange",
  error: "red",
  info: "blue",
};

type Props = {
  events: StrategyAuditEvent[];
  title?: string;
};

export function AuditTimeline({ events, title = "Audit timeline" }: Props) {
  if (!events || events.length === 0) {
    return (
      <DashboardCard title={title}>
        <Empty
          description="No audit events yet. Builder events will appear here after validation, compile, replay, or promotion actions."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </DashboardCard>
    );
  }

  return (
    <DashboardCard title={title} subtitle="Major events in this strategy's lifecycle">
      <Timeline
        items={events.map((event) => ({
          color: STATUS_DOT_COLORS[event.status ?? "info"] ?? "blue",
          children: (
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Text strong style={{ fontSize: 13 }}>
                  {event.title}
                </Text>
                {event.status === "error" && (
                  <Tag color="red" style={{ fontSize: 11 }}>failed</Tag>
                )}
                {event.status === "success" && (
                  <Tag color="green" style={{ fontSize: 11 }}>passed</Tag>
                )}
              </div>
              {event.detail && (
                <Text type="secondary" style={{ fontSize: 12, display: "block", marginTop: 2 }}>
                  {event.detail}
                </Text>
              )}
              {event.timestamp && event.timestamp !== "degraded-mode" && (
                <Text
                  type="secondary"
                  style={{ fontSize: 11, display: "block", marginTop: 2 }}
                >
                  {new Date(event.timestamp).toLocaleString()}
                </Text>
              )}
            </div>
          ),
        }))}
      />
    </DashboardCard>
  );
}
