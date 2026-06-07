import type { ReactNode } from "react";

type MetricCardTone =
  | "blue"
  | "green"
  | "purple"
  | "warning"
  | "danger"
  | "neutral";

type MetricCardProps = {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  helper?: ReactNode;
  tone?: MetricCardTone;
};

export function MetricCard({
  label,
  value,
  icon,
  helper,
  tone = "blue",
}: MetricCardProps) {
  return (
    <div className={`nb-metric-card nb-metric-card-${tone}`}>
      {icon ? <div className="nb-metric-icon">{icon}</div> : null}
      <div className="nb-metric-content">
        <div className="nb-metric-label">{label}</div>
        <div className="nb-metric-value">{value}</div>
        {helper ? <div className="nb-metric-helper">{helper}</div> : null}
      </div>
    </div>
  );
}
