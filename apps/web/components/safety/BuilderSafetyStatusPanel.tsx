"use client";

import { Row, Col, Tag, Typography } from "antd";
import {
  SafetyCertificateOutlined,
  StopOutlined,
  EyeOutlined,
} from "@ant-design/icons";
import { DashboardCard } from "../ui/DashboardCard";

const { Text } = Typography;

type SafetyItem = {
  label: string;
  value: string;
  status: "safe" | "disabled";
};

const SAFETY_ITEMS: SafetyItem[] = [
  {
    label: "Execution authority",
    value: "Disabled",
    status: "disabled",
  },
  {
    label: "Live credentials used",
    value: "No",
    status: "safe",
  },
  {
    label: "TradeAction generation",
    value: "No",
    status: "disabled",
  },
  {
    label: "submit_order access",
    value: "No",
    status: "disabled",
  },
  {
    label: "AI authority",
    value: "Advisory only",
    status: "safe",
  },
  {
    label: "Builder mode",
    value: "Draft / validation / replay / promotion review only",
    status: "safe",
  },
];

export function BuilderSafetyStatusPanel() {
  return (
    <DashboardCard
      title="Builder safety status"
      subtitle="Static Builder guarantees — this workspace does not submit live orders"
      actions={
        <Tag color="green" style={{ fontSize: 12 }}>
          <SafetyCertificateOutlined /> Builder-only mode
        </Tag>
      }
    >
      <Row gutter={[12, 8]}>
        {SAFETY_ITEMS.map((item) => (
          <Col key={item.label} xs={24} sm={12} md={8}>
            <div
              style={{
                padding: "8px 12px",
                borderRadius: 10,
                border: "1px solid var(--nb-border)",
                display: "flex",
                alignItems: "center",
                gap: 8,
              }}
            >
              {item.status === "disabled" ? (
                <StopOutlined style={{ color: "var(--nb-green)", fontSize: 14 }} />
              ) : (
                <EyeOutlined style={{ color: "var(--nb-active)", fontSize: 14 }} />
              )}
              <div>
                <Text type="secondary" style={{ fontSize: 11, display: "block" }}>
                  {item.label}
                </Text>
                <Text strong style={{ fontSize: 13 }}>
                  {item.value}
                </Text>
              </div>
            </div>
          </Col>
        ))}
      </Row>
      <div style={{ marginTop: 12 }}>
        <Text type="secondary" style={{ fontSize: 12 }}>
          This workspace does not submit live orders. Execution remains outside
          Builder authority. These are static Builder guarantees.
        </Text>
      </div>
    </DashboardCard>
  );
}
