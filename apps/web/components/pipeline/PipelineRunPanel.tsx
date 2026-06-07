"use client";

import { useState } from "react";
import {
  CheckCircleOutlined,
  CodeOutlined,
  ExperimentOutlined,
  FileSearchOutlined,
  LoadingOutlined,
  PlayCircleOutlined,
  SafetyCertificateOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { Button, Card, Descriptions, Input, message, Modal, Space, Steps, Tag, Typography } from "antd";
import { apiFetch } from "../../lib/api";

const { Text, Paragraph } = Typography;

type PipelineStepKey = "validate" | "compile" | "backtest" | "results";

const PIPELINE_STEPS: { key: PipelineStepKey; title: string; icon: React.ReactNode }[] = [
  { key: "validate", title: "Validate", icon: <FileSearchOutlined /> },
  { key: "compile", title: "Compile", icon: <CodeOutlined /> },
  { key: "backtest", title: "Run Backtest", icon: <ExperimentOutlined /> },
  { key: "results", title: "Results", icon: <CheckCircleOutlined /> },
];

type StrategySpecPayload = {
  strategy_name: string;
  entry_signal: Record<string, unknown>;
  exit_signal: Record<string, unknown>;
  [key: string]: unknown;
};

type PipelineStepResult = {
  step: string;
  status: string;
  [key: string]: unknown;
};

type PromotionEvidence = {
  validation_report_ref?: string;
  backtest_result_ref?: string;
  gate_compatibility?: string;
  [key: string]: unknown;
};

type PipelineRunResponse = {
  success: boolean;
  steps: PipelineStepResult[];
  validation_report: Record<string, unknown> | null;
  compile_artifact: {
    compile_hash?: string;
    spec_version?: string;
    strategy_version?: string;
    [key: string]: unknown;
  } | null;
  backtest_result: {
    trade_count: number;
    total_pnl: number;
    win_rate: number;
    [key: string]: unknown;
  } | null;
  promotion_evidence: PromotionEvidence | null;
  promotion_status: string;
  error?: string;
};

type PromotionResponse = {
  success: boolean;
  promotion_status: string;
  promotion_request: Record<string, unknown> | null;
  error: string | null;
};

const DEFAULT_SPEC: StrategySpecPayload = {
  strategy_name: "",
  entry_signal: { type: "cross", fast_period: 10, slow_period: 20 },
  exit_signal: { type: "opposite_signal" },
};

function specFromJson(raw: string): StrategySpecPayload | null {
  try {
    const parsed = JSON.parse(raw);
    if (typeof parsed === "object" && parsed !== null && !Array.isArray(parsed)) {
      return parsed as StrategySpecPayload;
    }
    return null;
  } catch {
    return null;
  }
}

export function PipelineRunPanel() {
  const [specJson, setSpecJson] = useState(JSON.stringify(DEFAULT_SPEC, null, 2));
  const [currentStep, setCurrentStep] = useState(-1);
  const [stepStatuses, setStepStatuses] = useState<Record<PipelineStepKey, "wait" | "process" | "finish" | "error">>({
    validate: "wait",
    compile: "wait",
    backtest: "wait",
    results: "wait",
  });
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<PipelineRunResponse | null>(null);
  const [promotionStatus, setPromotionStatus] = useState<string | null>(null);
  const [isPromoting, setIsPromoting] = useState(false);

  const spec = specFromJson(specJson);
  const specValid = spec !== null && spec.strategy_name.trim().length > 0;

  async function runPipeline() {
    if (!spec) {
      message.error("Invalid strategy spec JSON");
      return;
    }

    setIsRunning(true);
    setResult(null);
    setCurrentStep(0);
    setStepStatuses({ validate: "process", compile: "wait", backtest: "wait", results: "wait" });

    try {
      const response = await apiFetch<PipelineRunResponse>("/api/pipeline/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(spec),
      });

      if (!response.success) {
        const errorMsg = response.error ?? "Pipeline execution failed";
        message.error(errorMsg);
        setStepStatuses((prev) => ({
          ...prev,
          [PIPELINE_STEPS[Math.max(0, currentStep)].key]: "error",
        }));
        return;
      }

      const stepKeys: PipelineStepKey[] = ["validate", "compile", "backtest", "results"];
      const nextStatuses = { ...stepStatuses };
      for (const key of stepKeys) {
        nextStatuses[key] = "finish";
      }
      setStepStatuses(nextStatuses);
      setCurrentStep(stepKeys.length - 1);
      setResult(response);
      message.success("Pipeline completed successfully");
    } catch (caught) {
      const errorMsg = caught instanceof Error ? caught.message : String(caught);
      message.error(errorMsg);
      setStepStatuses((prev) => {
        const updated = { ...prev };
        for (const step of PIPELINE_STEPS) {
          if (updated[step.key] === "process") {
            updated[step.key] = "error";
            break;
          }
        }
        return updated;
      });
    } finally {
      setIsRunning(false);
    }
  }

  function requestPromotion() {
    if (!result?.compile_artifact) return;

    const compileHash = result.compile_artifact.compile_hash ?? "";
    const strategyVersion = result.compile_artifact.strategy_version ?? result.compile_artifact.spec_version ?? "";
    const evidenceRefs: Record<string, string> = {};
    if (result.promotion_evidence?.validation_report_ref) {
      evidenceRefs.validation_report = result.promotion_evidence.validation_report_ref;
    }
    if (result.promotion_evidence?.backtest_result_ref) {
      evidenceRefs.backtest_result = result.promotion_evidence.backtest_result_ref;
    }
    if (result.promotion_evidence?.gate_compatibility) {
      evidenceRefs.gate_compatibility = result.promotion_evidence.gate_compatibility;
    }

    const gateSummary = [
      "Target: shadow (observational only)",
      "may_submit_order: false",
      "may_create_trade_action: false",
      `Evidence refs: ${Object.keys(evidenceRefs).length > 0 ? Object.entries(evidenceRefs).map(([k, v]) => `${k}=${v}`).join(", ") : "none"}`,
    ].join("\n");

    Modal.confirm({
      title: "Confirm Shadow Promotion Request",
      content: (
        <div>
          <p>This will request a shadow promotion for strategy version <strong>{strategyVersion}</strong>.</p>
          <p>The promotion gate enforces observational-only mode:</p>
          <pre style={{ fontSize: 12, background: "var(--ant-color-bg-container)", padding: 8, borderRadius: 4 }}>{gateSummary}</pre>
        </div>
      ),
      okText: "Confirm Promotion",
      cancelText: "Cancel",
      onOk: async () => {
        setIsPromoting(true);
        try {
          const response = await apiFetch<PromotionResponse>("/api/pipeline/promote", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              strategy_version: strategyVersion,
              compile_hash: compileHash,
              target: "shadow",
              evidence_refs: evidenceRefs,
            }),
          });
          if (response.success) {
            setPromotionStatus(response.promotion_status);
            message.success("Shadow promotion request submitted");
          } else {
            message.error(response.error ?? "Promotion request failed");
          }
        } catch (caught) {
          const errorMsg = caught instanceof Error ? caught.message : String(caught);
          message.error(errorMsg);
        } finally {
          setIsPromoting(false);
        }
      },
    });
  }

  const antdSteps = PIPELINE_STEPS.map((step, idx) => {
    const status = stepStatuses[step.key];
    let icon: React.ReactNode = step.icon;
    if (status === "process") {
      icon = <LoadingOutlined />;
    } else if (status === "finish") {
      icon = <CheckCircleOutlined style={{ color: "var(--ant-color-success)" }} />;
    } else if (status === "error") {
      icon = <CheckCircleOutlined style={{ color: "var(--ant-color-error)" }} />;
    }
    return { key: step.key, title: step.title, icon, status: status as "wait" | "process" | "finish" | "error", description: undefined as string | undefined };
  });

  const backtestResult = result?.backtest_result;

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Card
        size="small"
        title={
          <Space>
            <ThunderboltOutlined />
            <span>Pipeline Runner</span>
            <Tag color="blue">One-click flow</Tag>
          </Space>
        }
      >
        <Paragraph type="secondary" style={{ marginBottom: 16 }}>
          Chain: validate → compile → run backtest → show results. A single &quot;Run Pipeline&quot; call triggers the full sequence.
        </Paragraph>

        <Text strong style={{ display: "block", marginBottom: 8 }}>
          Strategy Spec (JSON)
        </Text>
        <Input.TextArea
          value={specJson}
          onChange={(e) => setSpecJson(e.target.value)}
          rows={10}
          style={{ fontFamily: "monospace", fontSize: 12 }}
          disabled={isRunning}
          status={specValid ? undefined : "error"}
        />
        {!specValid && (
          <Text type="danger" style={{ fontSize: 12, marginTop: 4, display: "block" }}>
            Must be valid JSON with a non-empty &quot;strategy_name&quot; field.
          </Text>
        )}

        <div style={{ marginTop: 16 }}>
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            loading={isRunning}
            disabled={!specValid || isRunning}
            onClick={runPipeline}
            size="large"
            block
          >
            {isRunning ? "Running Pipeline…" : "Run Pipeline"}
          </Button>
        </div>
      </Card>

      <Card size="small" title="Pipeline Progress">
        <Steps
          current={currentStep}
          items={antdSteps}
          direction="horizontal"
          size="small"
        />

        {result?.steps && result.steps.length > 0 && (
          <div style={{ marginTop: 16 }}>
            <Descriptions
              size="small"
              bordered
              column={1}
              title="Step Details"
            >
              {result.steps.map((step, idx) => (
                <Descriptions.Item key={idx} label={step.step}>
                  <Tag color={step.status === "completed" ? "success" : step.status === "failed" ? "error" : "processing"}>
                    {step.status}
                  </Tag>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </div>
        )}
      </Card>

      {backtestResult && (
        <Card
          size="small"
          title={
            <Space>
              <CheckCircleOutlined style={{ color: "var(--ant-color-success)" }} />
              <span>Backtest Results</span>
            </Space>
          }
        >
          <Descriptions size="small" bordered column={3}>
            <Descriptions.Item label="Trade Count">
              <Text strong>{backtestResult.trade_count}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Total PnL">
              <Text strong style={{ color: backtestResult.total_pnl >= 0 ? "var(--ant-color-success)" : "var(--ant-color-error)" }}>
                {backtestResult.total_pnl >= 0 ? "+" : ""}
                {backtestResult.total_pnl.toFixed(2)}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Win Rate">
              <Text strong>{(backtestResult.win_rate * 100).toFixed(1)}%</Text>
            </Descriptions.Item>
          </Descriptions>
        </Card>
      )}

      {result?.success && result.promotion_evidence && (
        <Card
          size="small"
          title={
            <Space>
              <SafetyCertificateOutlined style={{ color: "var(--ant-color-info)" }} />
              <span>Promotion Evidence</span>
              <Tag color={promotionStatus ? "success" : "blue"}>
                {promotionStatus ?? result.promotion_status}
              </Tag>
            </Space>
          }
        >
          <Descriptions size="small" bordered column={1}>
            {result.promotion_evidence.validation_report_ref && (
              <Descriptions.Item label="Validation Report">
                <Tag>{result.promotion_evidence.validation_report_ref}</Tag>
              </Descriptions.Item>
            )}
            {result.promotion_evidence.backtest_result_ref && (
              <Descriptions.Item label="Backtest Result">
                <Tag>{result.promotion_evidence.backtest_result_ref}</Tag>
              </Descriptions.Item>
            )}
            {result.promotion_evidence.gate_compatibility && (
              <Descriptions.Item label="Gate Compatibility">
                <Tag color="success">{result.promotion_evidence.gate_compatibility}</Tag>
              </Descriptions.Item>
            )}
            <Descriptions.Item label="Execution Constraints">
              <Space size={4}>
                <Tag>may_submit_order: false</Tag>
                <Tag>may_create_trade_action: false</Tag>
              </Space>
            </Descriptions.Item>
          </Descriptions>

          <div style={{ marginTop: 16 }}>
            {promotionStatus === "manual_approval_pending" ? (
              <Space>
                <Tag color="success" style={{ fontSize: 14, padding: "4px 12px" }}>
                  <CheckCircleOutlined /> Promotion Submitted
                </Tag>
              </Space>
            ) : (
              <Button
                type="primary"
                icon={<SafetyCertificateOutlined />}
                loading={isPromoting}
                disabled={isPromoting || result.promotion_status !== "pending_approval"}
                onClick={requestPromotion}
                size="large"
                block
              >
                Request Shadow Promotion
              </Button>
            )}
          </div>
        </Card>
      )}
    </Space>
  );
}
