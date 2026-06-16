"use client";

import { PageHeader } from "../../../components/ui/PageHeader";
import { FileTextOutlined } from "@ant-design/icons";
import { StrategyListClient } from "../../../components/strategies/StrategyListClient";

export default function StrategiesPage() {
  return (
    <div>
      <PageHeader
        title="Strategy Specs"
        subtitle="All strategies across every status. Edit draft/validated, clone, or send to Backtest Center."
        icon={<FileTextOutlined />}
      />
      <StrategyListClient />
    </div>
  );
}
