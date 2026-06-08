"use client";

import { Col, Empty, Row, Typography } from "antd";
import { DashboardCard } from "../ui/DashboardCard";
import { EvidenceCard } from "./EvidenceCard";
import type { StrategyEvidenceRef } from "../../lib/lifecycle/types";

const { Text } = Typography;

type Props = {
  evidenceRefs: StrategyEvidenceRef[];
  title?: string;
};

export function EvidenceSummaryGrid({
  evidenceRefs,
  title = "Evidence",
}: Props) {
  if (!evidenceRefs || evidenceRefs.length === 0) {
    return (
      <DashboardCard title={title}>
        <Empty
          description="No evidence references available."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      </DashboardCard>
    );
  }

  const missingCount = evidenceRefs.filter(
    (e) => e.status === "missing",
  ).length;
  const failedCount = evidenceRefs.filter(
    (e) => e.status === "failed",
  ).length;
  const passedCount = evidenceRefs.filter(
    (e) => e.status === "passed" || e.status === "present",
  ).length;

  return (
    <DashboardCard
      title={title}
      subtitle="What evidence exists, is missing, or failed"
      actions={
        <Text type="secondary" style={{ fontSize: 12 }}>
          {passedCount} present · {missingCount} missing
          {failedCount > 0 ? ` · ${failedCount} failed` : ""}
        </Text>
      }
    >
      <Row gutter={[12, 12]}>
        {evidenceRefs.map((ref, idx) => (
          <Col key={`${ref.kind}-${idx}`} xs={24} sm={12} lg={8}>
            <EvidenceCard evidence={ref} />
          </Col>
        ))}
      </Row>
    </DashboardCard>
  );
}
