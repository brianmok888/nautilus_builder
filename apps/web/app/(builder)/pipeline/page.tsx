"use client";

import { PipelineRunPanel } from "../../../components/pipeline/PipelineRunPanel";
import { PageHeader } from "../../../components/ui/PageHeader";
import { ThunderboltOutlined } from "@ant-design/icons";

export default function PipelinePage() {
  return (
    <div>
      <PageHeader
        title="Pipeline"
        subtitle="Manage strategy/test workflow lineage."
        icon={<ThunderboltOutlined />}
      />
      <PipelineRunPanel />
    </div>
  );
}
