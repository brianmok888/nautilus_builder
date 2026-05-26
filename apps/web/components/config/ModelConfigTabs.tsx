"use client";

import { useMemo, useState } from "react";
import { Alert, Badge, Card, Form, Input, Select, Space, Tabs, Tag, Typography } from "antd";

const providerOptions = [
  {
    label: "OpenAI-compatible chat completions",
    value: "openai-compatible",
  },
  {
    label: "Local OpenAI-compatible gateway",
    value: "local-openai-compatible",
  },
  {
    label: "Offline advisory fixture",
    value: "advisory-fixture",
  },
];

const guardrailItems = [
  "validate_strategy_spec() is mandatory",
  "signal_preview_only output mode only",
  "submit_order / TradeAction blocked",
  "No credentials in prompts, specs, or audit payloads",
  "Backtest evidence and manual promotion remain required",
];

const auditItems = [
  "Prompt + response metadata audited",
  "No authorization headers or API keys are persisted",
  "Response ID, finish reason, usage, and model name are recorded",
  "Malformed provider responses become rejected drafts",
];

export function ModelConfigTabs() {
  const [providerType, setProviderType] = useState("openai-compatible");
  const [baseUrl, setBaseUrl] = useState("https://api.openai.com/v1");
  const [draftModel, setDraftModel] = useState("strategy-draft-model");
  const [validationModel, setValidationModel] = useState("strategy-draft-model");
  const [explanationModel, setExplanationModel] = useState("strategy-draft-model");

  const preview = useMemo(
    () => ({
      provider_type: providerType,
      env: {
        OPENAI_BASE_URL: baseUrl,
        OPENAI_MODEL: draftModel,
        OPENAI_API_KEY: "server-side only / not collected by UI",
      },
      roles: {
        draft_strategy_spec: draftModel,
        validate_and_repair: validationModel,
        explain_operator_feedback: explanationModel,
      },
      guardrails: {
        output_mode: "signal_preview_only",
        validation_gate: "validate_strategy_spec()",
        promotion: "manual only",
        live_order_authority: false,
      },
    }),
    [baseUrl, draftModel, explanationModel, providerType, validationModel],
  );

  return (
    <section className="panel config-panel" aria-label="llm model configuration">
      <Space orientation="vertical" size="large" className="config-stack">
        <Alert
          showIcon
          type="info"
          title="LLM settings are an operator-facing draft surface"
          description="Provider secrets stay on the backend environment/config store. The browser can inspect intended provider/model roles but cannot collect API keys."
        />
        <Tabs
          className="config-tabs"
          defaultActiveKey="providers"
          items={[
            {
              key: "providers",
              label: "Providers",
              children: (
                <Card title="LLM provider configuration">
                  <Typography.Paragraph>
                    Configure advisory model endpoints for StrategySpec drafting
                    without moving secrets into the browser.
                  </Typography.Paragraph>
                  <Form layout="vertical" className="form-grid">
                    <Form.Item label="Provider type">
                      <Select
                        aria-label="provider type"
                        options={providerOptions}
                        value={providerType}
                        onChange={setProviderType}
                      />
                    </Form.Item>
                    <Form.Item label="Base URL">
                      <Input
                        aria-label="base url"
                        value={baseUrl}
                        onChange={(event) => setBaseUrl(event.target.value)}
                      />
                    </Form.Item>
                  </Form>
                  <ul className="config-checklist">
                    {[
                      "OPENAI_API_KEY stays server-side only",
                      "OPENAI_BASE_URL maps to the configured provider endpoint",
                      "OPENAI_MODEL provides the default draft model",
                    ].map((item) => (
                      <li key={item}>
                        <Badge status="processing" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ),
            },
            {
              key: "models",
              label: "Models",
              children: (
                <Card title="Model roles">
                  <Typography.Paragraph>
                    Separate draft, validation, and explanation roles so later
                    backend config can route each advisory task independently.
                  </Typography.Paragraph>
                  <Form layout="vertical" className="form-grid">
                    <Form.Item label="Draft model">
                      <Input
                        aria-label="Draft model"
                        value={draftModel}
                        onChange={(event) => setDraftModel(event.target.value)}
                      />
                    </Form.Item>
                    <Form.Item label="Validation model">
                      <Input
                        aria-label="Validation model"
                        value={validationModel}
                        onChange={(event) => setValidationModel(event.target.value)}
                      />
                    </Form.Item>
                    <Form.Item label="Explanation model">
                      <Input
                        aria-label="Explanation model"
                        value={explanationModel}
                        onChange={(event) => setExplanationModel(event.target.value)}
                      />
                    </Form.Item>
                  </Form>
                  <Tag color="warning">
                    UI draft only — backend env/config store remains source of truth.
                  </Tag>
                </Card>
              ),
            },
            {
              key: "guardrails",
              label: "Guardrails",
              children: (
                <Card title="StrategySpec guardrails">
                  <ul className="config-checklist">
                    {guardrailItems.map((item) => (
                      <li key={item}>
                        <Badge status="success" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ),
            },
            {
              key: "audit",
              label: "Audit",
              children: (
                <Card title="Audit and runtime metadata">
                  <ul className="config-checklist">
                    {auditItems.map((item) => (
                      <li key={item}>
                        <Badge status="warning" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </Card>
              ),
            },
          ]}
        />
        <Card title="Draft config preview" className="config-preview">
          <pre>{JSON.stringify(preview, null, 2)}</pre>
        </Card>
      </Space>
    </section>
  );
}
