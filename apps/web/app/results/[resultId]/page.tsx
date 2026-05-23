import { ResultsDashboard } from "../../../components/results/ResultsDashboard";

export default function ResultPage({ params }: { params: { resultId: string } }) {
  return <ResultsDashboard resultId={params.resultId} />;
}
