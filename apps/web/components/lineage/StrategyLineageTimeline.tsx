/**
 * StrategyLineageTimeline — shows the traceability spine from draft to promotion.
 *
 * Displays: Draft → Validation → Compile → Backtest → Evidence → Promotion
 * Safety: No live action buttons. Uses "request", "view", "verify" wording only.
 */
import React from "react";

export interface LineageStep {
  label: string;
  status: "pending" | "in_progress" | "completed" | "blocked";
  hash?: string;
  evidenceId?: string;
  blockingReason?: string;
}

export interface StrategyLineageTimelineProps {
  steps: LineageStep[];
  strategyId: string;
}

export default function StrategyLineageTimeline({ steps, strategyId }: StrategyLineageTimelineProps) {
  return (
    <div data-testid="lineage-timeline" className="lineage-timeline">
      <h3>Strategy Lineage: {strategyId}</h3>
      <ol>
        {steps.map((step, i) => (
          <li key={i} data-testid={`lineage-step-${i}`} className={`step-${step.status}`}>
            <span className="step-label">{step.label}</span>
            <span className="step-status">{step.status}</span>
            {step.hash && (
              <code className="step-hash" title="Copy hash">{step.hash.slice(0, 16)}...</code>
            )}
            {step.blockingReason && (
              <span className="blocking-reason">{step.blockingReason}</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  );
}
