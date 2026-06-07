"use client";

import { ExecutionLaneFeaturePanel } from "../../components/config/ExecutionLaneFeaturePanel";
import { PageHeader } from "../../components/ui/PageHeader";
import { PlayCircleOutlined } from "@ant-design/icons";

export default function ExecutionPage() {
  return (
    <div>
      <PageHeader
        title="Execution Lane"
        subtitle="Paper / live TradingNode gate. Backend-owned credentials."
        icon={<PlayCircleOutlined />}
      />
      <ExecutionLaneFeaturePanel />
    </div>
  );
}
