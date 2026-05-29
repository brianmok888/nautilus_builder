"use client";

import { useEffect, useMemo, useState } from "react";
import { Alert, Button, Col, Form, Input, Row, Space, Tag, Typography } from "antd";
import { fetchAdapters } from "../../lib/api";
import { applyAiDraftToBuilder, generateAiDraft } from "../../lib/api";
import type { AiDraftApplication, AiDraftPayload, AiDraftResult, AdapterSummary } from "../../lib/types";

const DEFAULT_THREAD_ID = "thread_ui_default";
const DEFAULT_CYCLE_ID = "cycle_ui_default";
const DEFAULT_LINEAGE_ID = "lineage_strategy_001";
const DEFAULT_VERSION_ID = "strategy_001_v001";

function prettyJson(value: unknown) {
  return JSON.stringify(value, null, 2);
}

export const AiStrategyCopilot = () => {
  const [prompt, setPrompt] = useState("");
  const [aiThreadId, setAiThreadId] = useState(DEFAULT_THREAD_ID);
  const [improvementCycleId, setImprovementCycleId] = useState(DEFAULT_CYCLE_ID);
  const [strategyLineageId, setStrategyLineageId] = useState(DEFAULT_LINEAGE_ID);
  const [strategyVersionId, setStrategyVersionId] = useState(DEFAULT_VERSION_ID);
  const [draft, setDraft] = useState<AiDraftResult | null>(null);
  const [applied, setApplied] = useState<AiDraftApplication | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [showAdvancedIds, setShowAdvancedIds] = useState(false);

  // Adapter / venue selector for market context
  const [adapters, setAdapters] = useState<AdapterSummary[]>([]);
  const [adapterId, setAdapterId] = useState("");

  useEffect(() => {
    fetchAdapters()
      .then((list) => {
        setAdapters(list);
        if (list.length > 0) setAdapterId(list[0].adapter_id);
      })
      .catch(() => {});
  }, []);

  const payload = useMemo<AiDraftPayload>(
    () => ({
      prompt: prompt.trim(),
      ai_thread_id: aiThreadId.trim(),
      improvement_cycle_id: improvementCycleId.trim(),
      strategy_lineage_id: strategyLineageId.trim(),
      strategy_version_id: strategyVersionId.trim(),
    }),
    [aiThreadId, improvementCycleId, prompt, strategyLineageId, strategyVersionId],
  );

  async function onGenerateDraft() {
    if (!payload.prompt) {
      setError("Describe the strategy before asking AI to draft a StrategySpec.");
      return;
    }
    setError(null);
    setApplied(null);
    setIsBusy(true);
    try {
      const result = await generateAiDraft(payload);
      setDraft(result);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : String(nextError));
      setDraft(null);
    } finally {
      setIsBusy(false);
    }
  }

  async function onApplyDraft() {
    if (!draft?.accepted) return;
    setError(null);
    setIsBusy(true);
    try {
      const result = await applyAiDraftToBuilder(payload);
      setApplied(result);
    } catch (nextError) {
      setError(nextError instanceof Error ? nextError.message : String(nextError));
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="panel ai-copilot compact-ai-copilot" aria-label="ai strategy copilot">
      <Space direction="vertical" size="small" className="ai-copilot-stack">
        <div>
          <Typography.Title level={4} style={{ margin: 0 }}>
            Prompt to StrategySpec
          </Typography.Title>
          <Typography.Text type="secondary">
            Describe the strategy; AI generates a validated Builder draft.
          </Typography.Text>
        </div>

        {/* Adapter / Venue selector */}
        <div>
          <Typography.Text strong>Adapter / Venue</Typography.Text>
          <select
            aria-label="adapter venue"
            value={adapterId}
            onChange={(e) => setAdapterId(e.target.value)}
            style={{ width: "100%", padding: "4px 8px", marginTop: 4, borderRadius: 4 }}
          >
            {adapters.map((a) => (
              <option key={a.adapter_id} value={a.adapter_id}>
                {a.adapter_id} — {a.venue}
              </option>
            ))}
          </select>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            Select adapter so AI generates the correct spec (perp vs spot vs polymarket differ).
          </Typography.Text>
        </div>

        <Alert
          showIcon
          type="info"
          title="Validation gate"
          description="AI draft must pass validation before applying. Backtest remains separate from drafting and manual promotion stays a later gate."
        />

        <div className="prompt-examples compact-info-strip">
          <Typography.Text strong>Prompt examples</Typography.Text>
          <Typography.Text type="secondary">
            "EMA/RSI pullback on BTC perpetuals", "VWAP trend filter for ETH", or "mean-reversion bars with ATR risk".
          </Typography.Text>
        </div>

        <Form layout="vertical" className="ai-copilot-form">
          <Form.Item label="Strategy prompt">
            <Input.TextArea
              aria-label="Strategy prompt"
              rows={4}
              value={prompt}
              onChange={(event) => setPrompt(event.target.value)}
              placeholder="Example: Build an EMA/RSI pullback strategy for BTC perpetuals using 5 minute bars."
            />
          </Form.Item>

          <Button type="link" onClick={() => setShowAdvancedIds((current) => !current)}>
            Advanced lineage IDs
          </Button>
          <Typography.Text type="secondary">
            Lineage IDs are generated automatically for normal drafting; advanced editing is optional.
          </Typography.Text>

          {showAdvancedIds ? (
            <Row gutter={[8, 8]} className="ai-audit-grid" aria-label="AI audit identifiers">
              <Col xs={24} md={12} xl={6}>
                <Form.Item label="ai_thread_id">
                  <Input
                    aria-label="ai_thread_id"
                    value={aiThreadId}
                    onChange={(event) => setAiThreadId(event.target.value)}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12} xl={6}>
                <Form.Item label="improvement_cycle_id">
                  <Input
                    aria-label="improvement_cycle_id"
                    value={improvementCycleId}
                    onChange={(event) => setImprovementCycleId(event.target.value)}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12} xl={6}>
                <Form.Item label="strategy_lineage_id">
                  <Input
                    aria-label="strategy_lineage_id"
                    value={strategyLineageId}
                    onChange={(event) => setStrategyLineageId(event.target.value)}
                  />
                </Form.Item>
              </Col>
              <Col xs={24} md={12} xl={6}>
                <Form.Item label="strategy_version_id">
                  <Input
                    aria-label="strategy_version_id"
                    value={strategyVersionId}
                    onChange={(event) => setStrategyVersionId(event.target.value)}
                  />
                </Form.Item>
              </Col>
            </Row>
          ) : null}
        </Form>

        <Space wrap size="small" className="action-row compact-action-row">
          <Button type="primary" loading={isBusy} onClick={onGenerateDraft}>
            Generate StrategySpec
          </Button>
          <Button disabled={!draft?.accepted || isBusy} onClick={onApplyDraft}>
            Apply to Builder
          </Button>
          <Tag color="blue">validate_strategy_spec()</Tag>
        </Space>

        {error ? <Alert showIcon type="error" title="AI workflow error" description={error} /> : null}

        {draft ? (
          <section className="ai-draft-result" aria-label="AI draft result">
            <Alert
              showIcon
              type={draft.accepted ? "success" : "warning"}
              title={draft.accepted ? "Accepted draft" : "Rejected draft"}
              description={draft.explanation}
            />
            {draft.validation_errors.length ? (
              <ul className="config-checklist compact-error-list">
                {draft.validation_errors.map((validationError) => (
                  <li key={validationError}>{validationError}</li>
                ))}
              </ul>
            ) : null}
            <pre className="compact-spec-preview">{prettyJson(draft.spec)}</pre>
          </section>
        ) : null}

        {applied ? (
          <Alert
            showIcon
            type="success"
            title="Applied to Builder draft"
            description={`${applied.strategy_lineage_id} / ${applied.strategy_version_id} remains ${applied.mode}.`}
          />
        ) : null}
      </Space>
    </section>
  );
};
