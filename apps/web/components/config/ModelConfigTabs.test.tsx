import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ModelConfigTabs } from "./ModelConfigTabs";

describe("ModelConfigTabs", () => {
  it("renders provider, model, guardrail, and audit tabs for advisory LLM configuration", () => {
    render(<ModelConfigTabs />);

    expect(screen.getByRole("tab", { name: "Providers" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("OpenAI-compatible chat completions")).toBeInTheDocument();
    expect(screen.getByText("OPENAI_API_KEY stays server-side only")).toBeInTheDocument();
    expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Models" }));
    expect(screen.getByLabelText("Draft model")).toHaveValue("strategy-draft-model");
    fireEvent.change(screen.getByLabelText("Draft model"), {
      target: { value: "local-qwen-strategy" },
    });
    expect(screen.getByText(/local-qwen-strategy/)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Guardrails" }));
    expect(screen.getByText("validate_strategy_spec() is mandatory")).toBeInTheDocument();
    expect(screen.getByText("submit_order / TradeAction blocked")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Audit" }));
    expect(screen.getByText("Prompt + response metadata audited")).toBeInTheDocument();
    expect(screen.getByText("No authorization headers or API keys are persisted")).toBeInTheDocument();
  });
});
