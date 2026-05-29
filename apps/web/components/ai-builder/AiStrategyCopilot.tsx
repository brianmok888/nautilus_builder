"use client";

import { useEffect, useState } from "react";
import { Alert, Button, Form, Input, Select, Space, Steps, Typography } from "antd";
import { generateAiDraft, applyAiDraftToBuilder, createStrategy } from "../../lib/api";
import type { AiDraftResult, StrategyRecord } from "../../lib/types";

const { Text } = Typography;

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

type StepStatus = "wait" | "process" | "finish" | "error";

export const AiStrategyCopilot = () => {
  const [prompt, setPrompt] = useState("");
  const [adapterId, setAdapterId] = useState("");
  const [adapters, setAdapters] = useState<{ adapter_id: string; venue: string }[]>([]);
  const [isBusy, setIsBusy] = useState(false);

  // Step statuses
  const [steps, setSteps] = useState<StepStatus[]>(["wait", "wait", "wait"]);
  const [stepError, setStepError] = useState<string | null>(null);
  const [draft, setDraft] = useState<AiDraftResult | null>(null);
  const [strategy, setStrategy] = useState<StrategyRecord | null>(null);

  useEffect(() => {
    fetch("/api/adapters")
      .then((r) => r.json())
      .then((list) => {
        setAdapters(list);
        if (list.length > 0) setAdapterId(list[0].adapter_id);
      })
      .catch(() => {});
  }, []);

  function setStep(index: number, status: StepStatus) {
    setSteps((prev) => {
      const next = [...prev];
      next[index] = status;
      return next;
    });
  }

  async function onGenerate() {
    if (!prompt.trim()) {
      setStepError("Describe the strategy before generating.");
      return;
    }
    setStepError(null);
    setDraft(null);
    setStrategy(null);
    setSteps(["process", "wait", "wait"]);
    setIsBusy(true);

    try {
      // Step 1: Generate StrategySpec via AI
      const result = await generateAiDraft({
        prompt: prompt.trim(),
        ai_thread_id: `thread_${Date.now()}`,
        improvement_cycle_id: `cycle_${Date.now()}`,
        strategy_lineage_id: `lineage_${Date.now()}`,
        strategy_version_id: `v_${Date.now()}`,
      });
      setDraft(result);

      if (!result.accepted) {
        setStep(0, "error");
        setStepError(result.validation_errors.join("; ") || result.explanation);
        return;
      }
      setStep(0, "finish");

      // Step 2: Validate via backend
      setStep(1, "process");
      await applyAiDraftToBuilder({
        prompt: prompt.trim(),
        ai_thread_id: `thread_${Date.now()}`,
        improvement_cycle_id: `cycle_${Date.now()}`,
        strategy_lineage_id: `lineage_${Date.now()}`,
        strategy_version_id: `v_${Date.now()}`,
      });
      setStep(1, "finish");

      // Step 3: Save strategy as draft (pending backtest)
      setStep(2, "process");
      try {
        const saved = await createStrategy({
          spec: result.spec,
          adapter_id: adapterId,
          status: "draft",
        });
        setStrategy(saved);
      } catch {
        // Best-effort save
      }
      setStep(2, "finish");
    } catch (err) {
      // Find which step failed
      const failedIdx = steps.indexOf("process");
      if (failedIdx >= 0) setStep(failedIdx, "error");
      setStepError(err instanceof Error ? err.message : String(err));
    } finally {
      setIsBusy(false);
    }
  }

  const hasResult = draft !== null;

  return (
    <section className="panel ai-copilot compact-ai-copilot" aria-label="strategy editor">
      <Space direction="vertical" size="middle" style={{ width: "100%" }}>
        {/* Prompt */}
        <Form layout="vertical" style={{ marginBottom: 0 }}>
          <Form.Item label="Strategy prompt" style={{ marginBottom: 8 }}>
            <Input.TextArea
              rows={4}
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Example: Build an EMA/RSI pullback strategy for BTC perpetuals using 5 minute bars."
              disabled={isBusy}
            />
          </Form.Item>
        </Form>

        {/* Adapter / Venue */}
        <div>
          <Text strong>Adapter / Venue</Text>
          <Select
            value={adapterId || undefined}
            onChange={setAdapterId}
            style={{ width: "100%", marginTop: 4 }}
            options={adapters.map((a) => ({
              value: a.adapter_id,
              label: `${a.adapter_id} — ${a.venue}`,
            }))}
            placeholder="Select adapter"
            disabled={isBusy}
          />
          <Text type="secondary" style={{ fontSize: 12, display: "block", marginTop: 4 }}>
            Select adapter so AI generates the correct spec for the market type.
          </Text>
        </div>

        {/* Single action button */}
        <Button type="primary" size="large" block loading={isBusy} onClick={onGenerate}>
          {hasResult && !stepError ? "Regenerate" : "Generate & Build Strategy"}
        </Button>

        {/* Live status steps */}
        {(isBusy || hasResult) && (
          <Steps
            size="small"
            current={steps.indexOf("process") >= 0 ? steps.indexOf("process") : 3}
            items={[
              { title: "Generate", status: steps[0] },
              { title: "Validate", status: steps[1] },
              { title: "Save draft", status: steps[2] },
            ]}
          />
        )}

        {/* Error */}
        {stepError && <Alert showIcon type="error" title="Failed" description={stepError} />}

        {/* Success summary */}
        {draft?.accepted && !stepError && (
          <Alert
            showIcon
            type="success"
            title="Strategy built & saved"
            description={
              strategy
                ? `Strategy ${strategy.strategy_id} saved as draft — pending backtest.`
                : draft.explanation
            }
          />
        )}

        {/* Validation warnings */}
        {draft && draft.validation_errors.length > 0 && (
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {draft.validation_errors.map((e) => (
              <li key={e}><Text type="warning">{e}</Text></li>
            ))}
          </ul>
        )}

        {/* Spec JSON */}
        {draft?.spec && (
          <details>
            <summary><Text strong>StrategySpec JSON</Text></summary>
            <pre style={{ fontSize: 11, maxHeight: 300, overflow: "auto", marginTop: 8 }}>{prettyJson(draft.spec)}</pre>
          </details>
        )}
      </Space>
    </section>
  );
};
