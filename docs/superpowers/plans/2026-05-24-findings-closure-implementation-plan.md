# Nautilus Builder Findings Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:test-driven-development for every behavior change. This plan is executed inline in this session by segment, with an autopilot-style plan -> implement -> review loop and reconciliation after each segment.

**Goal:** Close the top review findings in `findings.md` without weakening Builder-only authority boundaries.

**Architecture:** Four isolated TDD segments harden validation, align frontend/backend DTOs, enrich audit models, and pin/wire the NautilusTrader boundary. Each segment updates code, tests, and the three review markdown files before the next segment starts.

**Tech Stack:** Python 3.12, Pydantic v2, pytest/rtk, FastAPI route seams, Next.js/React/TypeScript, Vitest, NautilusTrader pinned as a Python dependency.

---

## File structure

- Modify `packages/strategy_validation/policy.py` — canonical forbidden token list.
- Modify `packages/strategy_validation/validators.py` — keep recursive validation behavior and expose all tokens through reports.
- Modify `packages/ai_builder/service.py` — gate provider drafts through schema/hard-rule validation.
- Modify `tests/strategy_validation/test_forbidden_execution_blocks.py` — regression coverage for all forbidden terms.
- Modify `tests/ai_builder/test_ai_output_must_validate.py` — AI nested invalid-output regressions.
- Modify `apps/web/lib/types.ts` — backend-aligned DTOs.
- Modify `apps/web/components/market/MarketProfilePanel.tsx` — payload and display alignment.
- Modify `apps/web/components/market/MarketProfilePanel.test.tsx` — real payload-shape expectations.
- Modify `tests/api/test_backtest_profiles.py` or add integration coverage — UI-shaped payload acceptance.
- Modify `packages/backtest_jobs/models.py` and `packages/backtest_jobs/service.py` — job audit fields and canonical status.
- Modify `packages/runtime_events/models.py`, `packages/runtime_events/service.py`, and streams if needed — audit fields.
- Modify `services/workers/nautilus_backtest_worker.py` and tests — `SUCCEEDED` status and richer events.
- Modify `pyproject.toml` — pin `nautilus_trader==1.223.0`.
- Modify `packages/backtest_runner/*` tests/docs naming where needed — explicit fixture-vs-engine boundary.
- Update `structure.md`, `findings.md`, `handguard.md` after each segment.

## Segment 1 — Validation hardening

- [ ] Write failing tests in `tests/strategy_validation/test_forbidden_execution_blocks.py` for `api_key`, `secret_key`, `credential`, `broker_order`, and `exchange_order`.
- [ ] Write failing tests in `tests/ai_builder/test_ai_output_must_validate.py` proving nested `TradeAction` provider output returns `accepted=False`, and malformed provider output returns validation errors.
- [ ] Run focused tests and confirm expected failures.
- [ ] Expand forbidden-token policy and route AI provider output through `validate_strategy_spec()`.
- [ ] Run focused tests to green, then run validation/AI slices.
- [ ] Update `structure.md`, `findings.md`, `handguard.md` with Segment 1 evidence.

## Segment 2 — Frontend/backend market-profile contract

- [ ] Write failing component/API tests proving `MarketProfilePanel` sends `data_type`, `market_type`, and `date_range` and displays backend response fields.
- [ ] Add or adjust a backend contract test showing a UI-equivalent payload succeeds.
- [ ] Run focused Python/frontend tests and confirm failures.
- [ ] Align TypeScript DTOs and `MarketProfilePanel.tsx` payload construction/display.
- [ ] Run focused tests to green, then API + frontend market slices.
- [ ] Update `structure.md`, `findings.md`, `handguard.md` with Segment 2 evidence.

## Segment 3 — Audit-grade job/runtime events

- [ ] Write failing tests for required `BacktestJob` audit fields and canonical `SUCCEEDED` worker completion.
- [ ] Write failing tests for `RuntimeEvent` audit fields: `event_id`, `actor_type`, `actor_id`, `timestamp`, and `metadata`.
- [ ] Run focused tests and confirm failures.
- [ ] Add defaulted fields and deterministic event IDs without breaking simple callers.
- [ ] Update worker completion stage to `SUCCEEDED` and status mapping as needed.
- [ ] Run focused tests to green, then backtest/runtime slices.
- [ ] Update `structure.md`, `findings.md`, `handguard.md` with Segment 3 evidence.

## Segment 4 — Nautilus dependency/backtest boundary

- [ ] Write failing test or metadata check proving `pyproject.toml` includes `nautilus_trader==1.223.0`.
- [ ] Write a backtest-boundary test proving fixture runner output is explicitly fixture/scaffold evidence and injected engine boundary remains separate.
- [ ] Run focused tests and confirm failures.
- [ ] Pin dependency and update result/config metadata to mark fixture evidence.
- [ ] Run focused tests to green, then backtest-runner slices.
- [ ] Update `structure.md`, `findings.md`, `handguard.md` with Segment 4 evidence.

## Master reconciliation

- [ ] Run `python3 -m compileall -q packages services tests`.
- [ ] Run full Python test suite with `rtk pytest ... -q`.
- [ ] Run `cd apps/web && npm run typecheck && npm test && npm run build`.
- [ ] Run `cd apps/web && npm run test:e2e` if browsers are installed; otherwise record the provisioning blocker.
- [ ] Review `git diff` for unintended authority creep (`submit_order`, `TradeAction`, credentials, shell access).
- [ ] Final-update `structure.md`, `findings.md`, and `handguard.md` with master reconciliation evidence.
