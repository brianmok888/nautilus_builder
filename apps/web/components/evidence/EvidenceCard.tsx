"use client";

import { Tag, Typography } from "antd";
import type { StrategyEvidenceRef } from "../../lib/lifecycle/types";
import Link from "next/link";

const { Text, Link: AntLink } = Typography;

const STATUS_COLORS: Record<string, string> = {
  present: "blue",
  passed: "green",
  missing: "orange",
  failed: "red",
  unknown: "default",
};

const STATUS_LABELS: Record<string, string> = {
  present: "Present",
  passed: "Passed",
  missing: "Missing",
  failed: "Failed",
  unknown: "Unknown",
};

const KIND_ICONS: Record<string, string> = {
  strategy_spec: "📄",
  validation: "✅",
  compile_artifact: "🔧",
  replay_report: "📊",
  promotion_request: "🔒",
  audit_event: "📝",
};

type Props = {
  evidence: StrategyEvidenceRef;
};

export function EvidenceCard({ evidence }: Props) {
  return (
    <div
      className="nb-card nb-card-padded"
      style={{
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        gap: 12,
        minHeight: 48,
      }}
    >
      <span style={{ fontSize: 18 }}>
        {KIND_ICONS[evidence.kind] ?? "📋"}
      </span>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <Text strong style={{ fontSize: 13 }}>
            {evidence.label}
          </Text>
          <Tag
            color={STATUS_COLORS[evidence.status]}
            style={{ fontSize: 11, lineHeight: "18px" }}
          >
            {STATUS_LABELS[evidence.status]}
          </Tag>
        </div>
        <div style={{ marginTop: 2 }}>
          {evidence.hash && (
            <Text
              code
              style={{ fontSize: 11 }}
            >
              {evidence.hash.slice(0, 16)}...
            </Text>
          )}
          {evidence.refId && !evidence.hash && (
            <Text type="secondary" style={{ fontSize: 11 }}>
              {evidence.refId}
            </Text>
          )}
          {evidence.createdAt && (
            <Text type="secondary" style={{ fontSize: 11, marginLeft: 8 }}>
              {new Date(evidence.createdAt).toLocaleDateString()}
            </Text>
          )}
        </div>
      </div>
      {evidence.href && (
        <AntLink href={evidence.href} style={{ fontSize: 12 }}>
          View
        </AntLink>
      )}
    </div>
  );
}
