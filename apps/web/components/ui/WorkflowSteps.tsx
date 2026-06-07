"use client";

import type { ReactNode } from "react";

export type WorkflowStep = {
  key: string;
  num: number;
  icon: ReactNode;
  title: string;
  subtitle: string;
};

type WorkflowStepsProps = {
  steps: WorkflowStep[];
  activeKey: string;
  onSelect: (key: string) => void;
};

export function WorkflowSteps({ steps, activeKey, onSelect }: WorkflowStepsProps) {
  return (
    <div className="nb-workflow-steps" role="tablist">
      {steps.map((step) => {
        const active = step.key === activeKey;
        return (
          <button
            key={step.key}
            type="button"
            role="tab"
            aria-selected={active}
            className={
              active
                ? "nb-workflow-step nb-workflow-step-active"
                : "nb-workflow-step"
            }
            onClick={() => onSelect(step.key)}
          >
            <span className="nb-workflow-step-num">{step.num}</span>
            <span>
              <div className="nb-workflow-step-title">
                {step.icon} {step.title}
              </div>
              <div className="nb-workflow-step-subtitle">{step.subtitle}</div>
            </span>
          </button>
        );
      })}
    </div>
  );
}
