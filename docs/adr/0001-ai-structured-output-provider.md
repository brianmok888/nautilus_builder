# ADR 0001: AI structured output provider (instructor)

- **Status:** Accepted
- **Date:** 2026-06-22
- **Adoption Report reference:** §3.1

## Context

The AI builder lane produces strategy-spec drafts from operator prompts. The
previous flow parsed raw chat-completion JSON via string extraction and
`json.loads`, which was fragile and required hand-rolled validation of output
shape.

## Decision

Use `instructor` for typed LLM draft extraction behind the existing
`DraftProviderProtocol` abstraction. `InstructorDraftProvider` produces a
Pydantic-validated `StrategySpecDraftModel` (`extra="forbid"`, Literal-locked
advisory fields) and returns it as a JSON dict.

## Guardrails (non-negotiable)

- Output remains **advisory-only**. `validate_strategy_spec`, static safety
  scan, manual approval, and promotion evidence gates remain authoritative.
- No tools, no agent invocation, no order authority, no runtime mutation.
- The model output cannot set provider, model, base URL, or tools.
- Forbidden credential/order prompts are rejected BEFORE the provider is called.
- Output stays `stage="draft"`, `status="draft"`, `created_from="ai_builder"`.

## Rejected alternatives

- **Vendor agent SDKs with tool authority** (claude-agent-sdk, google-genai as
  architecture): rejected — these grant execution agency that conflicts with the
  advisory-only rule. Provider clients are allowed only behind
  `DraftProviderProtocol` with extraction-only behavior.

## Verification

15 contract tests in `tests/ai_builder/test_instructor_provider_contract.py`.
Authority scan PASSED. basedpyright 0 errors.
