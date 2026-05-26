import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ModelConfigTabs } from "./ModelConfigTabs";

function fetchCalls(fetchMock: ReturnType<typeof vi.fn>) {
  return fetchMock.mock.calls.map(([input, init]) => ({
    url: String(input),
    method: init?.method ?? "GET",
    body: init?.body ? JSON.parse(String(init.body)) : undefined,
  }));
}

describe("ModelConfigTabs", () => {
  it("loads and saves non-secret OpenAI-compatible model config through the backend contract", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        Response.json({
          provider_type: "openai-compatible",
          base_url: "https://api.openai.com/v1",
          roles: {
            draft_strategy_spec: "strategy-draft-model",
            validate_and_repair: "strategy-validate-model",
            explain_operator_feedback: "strategy-explain-model",
          },
          guardrails: { output_mode: "signal_preview_only" },
          credential_inputs_allowed: false,
          secrets_storage: "server_environment",
        }),
      )
      .mockResolvedValueOnce(
        Response.json({
          provider_type: "openai-compatible",
          base_url: "http://127.0.0.1:11434/v1",
          roles: {
            draft_strategy_spec: "local-qwen-strategy",
            validate_and_repair: "strategy-validate-model",
            explain_operator_feedback: "strategy-explain-model",
          },
          guardrails: { output_mode: "signal_preview_only" },
          credential_inputs_allowed: false,
          secrets_storage: "server_environment",
        }),
      );
    vi.stubGlobal("fetch", fetchMock);

    render(<ModelConfigTabs />);

    expect(await screen.findByDisplayValue("https://api.openai.com/v1")).toBeInTheDocument();
    expect(screen.getByText("OPENAI_API_KEY stays server-side only")).toBeInTheDocument();
    expect(screen.queryByLabelText(/api key/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: "Models" }));
    expect(await screen.findByLabelText("Draft model")).toHaveValue("strategy-draft-model");
    fireEvent.change(screen.getByLabelText("Draft model"), {
      target: { value: "local-qwen-strategy" },
    });

    fireEvent.click(screen.getByRole("tab", { name: "Providers" }));
    fireEvent.change(screen.getByLabelText("Base URL"), {
      target: { value: "http://127.0.0.1:11434/v1" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save LLM config" }));

    await waitFor(() => expect(screen.getByText("Saved LLM config")).toBeInTheDocument());
    const calls = fetchCalls(fetchMock);
    expect(calls[0]).toMatchObject({ url: "/api/config/llm", method: "GET" });
    expect(calls[1]).toMatchObject({
      url: "/api/config/llm",
      method: "POST",
      body: {
        provider_type: "openai-compatible",
        base_url: "http://127.0.0.1:11434/v1",
        draft_model: "local-qwen-strategy",
      },
    });
  });
});
