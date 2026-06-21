import { ResultsDashboard } from "../../../components/results/ResultsDashboard";
import { fetchResultSummary } from "../../../lib/api";

export default async function ResultPage({ params }: { params: Promise<{ resultId: string }> }) {
  const { resultId } = await params;
  const payload = await fetchResultSummary(resultId);
  return <ResultsDashboard resultId={resultId} payload={payload} />;
}
