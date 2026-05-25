"use client";

import { useMemo, useState } from "react";

type ConfigTab = "providers" | "models" | "guardrails" | "audit";

const tabs: { id: ConfigTab; label: string }[] = [
  { id: "providers", label: "Providers" },
  { id: "models", label: "Models" },
  { id: "guardrails", label: "Guardrails" },
  { id: "audit", label: "Audit" },
];

export function ModelConfigTabs() {
  const [activeTab, setActiveTab] = useState<ConfigTab>("providers");
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
      <div className="result-tabs config-tabs" role="tablist" aria-label="configuration tabs">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            aria-controls={`${tab.id}-panel`}
            id={`${tab.id}-tab`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === "providers" ? (
        <section
          className="config-tab-panel"
          role="tabpanel"
          id="providers-panel"
          aria-labelledby="providers-tab"
        >
          <h2>LLM provider configuration</h2>
          <p>
            Configure advisory model endpoints for StrategySpec drafting without
            moving secrets into the browser.
          </p>
          <div className="form-grid">
            <label>
              Provider type
              <select
                aria-label="provider type"
                value={providerType}
                onChange={(event) => setProviderType(event.target.value)}
              >
                <option value="openai-compatible">
                  OpenAI-compatible chat completions
                </option>
                <option value="local-openai-compatible">
                  Local OpenAI-compatible gateway
                </option>
                <option value="advisory-fixture">
                  Offline advisory fixture
                </option>
              </select>
            </label>
            <label>
              Base URL
              <input
                aria-label="base url"
                value={baseUrl}
                onChange={(event) => setBaseUrl(event.target.value)}
              />
            </label>
          </div>
          <ul className="config-checklist">
            <li>OPENAI_API_KEY stays server-side only</li>
            <li>OPENAI_BASE_URL maps to the configured provider endpoint</li>
            <li>OPENAI_MODEL provides the default draft model</li>
          </ul>
        </section>
      ) : null}

      {activeTab === "models" ? (
        <section
          className="config-tab-panel"
          role="tabpanel"
          id="models-panel"
          aria-labelledby="models-tab"
        >
          <h2>Model roles</h2>
          <p>
            Separate draft, validation, and explanation roles so later backend
            config can route each advisory task independently.
          </p>
          <div className="form-grid">
            <label>
              Draft model
              <input
                aria-label="Draft model"
                value={draftModel}
                onChange={(event) => setDraftModel(event.target.value)}
              />
            </label>
            <label>
              Validation model
              <input
                aria-label="Validation model"
                value={validationModel}
                onChange={(event) => setValidationModel(event.target.value)}
              />
            </label>
            <label>
              Explanation model
              <input
                aria-label="Explanation model"
                value={explanationModel}
                onChange={(event) => setExplanationModel(event.target.value)}
              />
            </label>
          </div>
          <p className="status-badge warning">
            UI draft only — backend env/config store remains source of truth.
          </p>
        </section>
      ) : null}

      {activeTab === "guardrails" ? (
        <section
          className="config-tab-panel"
          role="tabpanel"
          id="guardrails-panel"
          aria-labelledby="guardrails-tab"
        >
          <h2>StrategySpec guardrails</h2>
          <ul className="config-checklist">
            <li>validate_strategy_spec() is mandatory</li>
            <li>signal_preview_only output mode only</li>
            <li>submit_order / TradeAction blocked</li>
            <li>No credentials in prompts, specs, or audit payloads</li>
            <li>Backtest evidence and manual promotion remain required</li>
          </ul>
        </section>
      ) : null}

      {activeTab === "audit" ? (
        <section
          className="config-tab-panel"
          role="tabpanel"
          id="audit-panel"
          aria-labelledby="audit-tab"
        >
          <h2>Audit and runtime metadata</h2>
          <ul className="config-checklist">
            <li>Prompt + response metadata audited</li>
            <li>No authorization headers or API keys are persisted</li>
            <li>Response ID, finish reason, usage, and model name are recorded</li>
            <li>Malformed provider responses become rejected drafts</li>
          </ul>
        </section>
      ) : null}

      <section className="config-preview" aria-label="configuration preview">
        <h3>Draft config preview</h3>
        <pre>{JSON.stringify(preview, null, 2)}</pre>
      </section>
    </section>
  );
}
