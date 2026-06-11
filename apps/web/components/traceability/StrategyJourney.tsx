"use client";

import React from "react";

interface JourneyStep {
  status: "pending" | "in_progress" | "completed" | "blocked";
  label: string;
  artifactId?: string;
  hash?: string;
  createdAt?: string;
  actor?: string;
  blockingReason?: string;
}

interface StrategyJourneyProps {
  steps: JourneyStep[];
  strategyId: string;
}

const statusColors: Record<JourneyStep["status"], string> = {
  pending: "#d9d9d9",
  in_progress: "#1890ff",
  completed: "#52c41a",
  blocked: "#ff4d4f",
};

export default function StrategyJourney({ steps, strategyId }: StrategyJourneyProps) {
  return (
    <div className="strategy-journey" data-strategy-id={strategyId}>
      <h3>Strategy Journey</h3>
      <div className="journey-steps">
        {steps.map((step, i) => (
          <div
            key={i}
            className="journey-step"
            data-status={step.status}
            data-testid={`journey-step-${step.label}`}
          >
            <div
              className="step-indicator"
              style={{ backgroundColor: statusColors[step.status] }}
            />
            <div className="step-content">
              <span className="step-label">{step.label}</span>
              {step.artifactId && (
                <span className="step-artifact-id" data-testid="artifact-id">
                  {step.artifactId}
                </span>
              )}
              {step.hash && (
                <span className="step-hash" data-testid="artifact-hash">
                  {step.hash.slice(0, 12)}...
                </span>
              )}
              {step.actor && (
                <span className="step-actor">by {step.actor}</span>
              )}
              {step.blockingReason && (
                <div className="blocking-reason" data-testid="blocking-reason">
                  Blocked: {step.blockingReason}
                </div>
              )}
            </div>
            {i < steps.length - 1 && <div className="step-connector" />}
          </div>
        ))}
      </div>
      {/* Safety: never show live execution CTA */}
    </div>
  );
}
