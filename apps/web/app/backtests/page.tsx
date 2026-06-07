"use client";

import Link from "next/link";
import { PageHeader } from "../../components/ui/PageHeader";
import { ExperimentOutlined } from "@ant-design/icons";

export default function BacktestsPage() {
  return (
    <div>
      <PageHeader
        title="Backtest Center"
        subtitle="Select a backtest job from the dashboard or create a new run."
        icon={<ExperimentOutlined />}
        actions={
          <Link href="/" style={{ color: "#1d9bf0" }}>
            ← Back to Strategy Builder
          </Link>
        }
      />
    </div>
  );
}
