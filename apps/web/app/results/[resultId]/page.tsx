import { ResultsDashboard } from "../../../components/results/ResultsDashboard";

export default async function ResultPage({ params }: { params: Promise<{ resultId: string }> }) {
  const { resultId } = await params;
  return <ResultsDashboard resultId={resultId} />;
}
