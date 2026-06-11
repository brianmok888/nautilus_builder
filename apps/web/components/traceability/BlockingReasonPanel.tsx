"use client";

import React from "react";

interface BlockingReason {
  code: string;
  message: string;
  evidenceRequired?: string;
}

interface BlockingReasonPanelProps {
  reasons: BlockingReason[];
  onDismiss?: () => void;
}

export default function BlockingReasonPanel({
  reasons,
  onDismiss,
}: BlockingReasonPanelProps) {
  if (!reasons.length) return null;

  return (
    <div className="blocking-reason-panel" data-testid="blocking-reason-panel">
      <h4>Blocking Reasons</h4>
      <ul>
        {reasons.map((reason, i) => (
          <li key={i} data-testid={`blocking-reason-${reason.code}`}>
            <span className="reason-code">{reason.code}</span>
            <span className="reason-message">{reason.message}</span>
            {reason.evidenceRequired && (
              <span className="evidence-required">
                Required: {reason.evidenceRequired}
              </span>
            )}
          </li>
        ))}
      </ul>
      {onDismiss && (
        <button onClick={onDismiss} data-testid="dismiss-blocking">
          Dismiss
        </button>
      )}
    </div>
  );
}
