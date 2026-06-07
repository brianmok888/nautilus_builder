"use client";

import { ResultsListClient } from "../../components/results/ResultsListClient";
import { PageHeader } from "../../components/ui/PageHeader";
import { BarChartOutlined } from "@ant-design/icons";

export default function ResultsPage() {
  return (
    <div>
      <PageHeader
        title="Results"
        subtitle="Backtest results and reports."
        icon={<BarChartOutlined />}
      />
      <ResultsListClient />
    </div>
  );
}
