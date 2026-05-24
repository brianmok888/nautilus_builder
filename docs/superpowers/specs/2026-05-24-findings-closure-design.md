# Nautilus Builder Findings Closure Design

**Date:** 2026-05-24  
**Approved approach:** Approach A — TDD segment closure  
**Target repo:** `/home/mok/projects/nautilus_builder`  
**Out of scope:** editing Nautilus-Daedalus, live order submission, Telegram dialog implementation, adopting EvoMap/LangChain/LangGraph runtime dependencies.

## Goal

Close the top findings from `findings.md` while preserving Nautilus Builder's core boundary: Builder is an authoring, validation, backtest, and signal-preview product; live order authority remains outside Builder.

## External reference posture

- NautilusTrader remains authoritative for backtest/replay/live terminology and should be pinned to match the Daedalus runtime version: `nautilus_trader==1.223.0`.
- EvoMap/Evolver, LangChain, and LangGraph are referenced as advisory/evolution/agent ecosystem context only. They do not become runtime dependencies in this closure pass.
- Any future EvoMap/LangChain/LangGraph integration must treat LLM/advisory output as untrusted input and keep Builder validation as the hard gate.

## Architecture

The closure is split into four implementation segments plus a master reconciliation:

1. **Validation hardening** — make AI draft acceptance depend on the same schema and hard-rule validator used by user specs; expand forbidden references to cover all hardguarded secret/order terms.
2. **Market-profile contract alignment** — make frontend profile-validation payloads and types match the backend registry contract.
3. **Audit-grade job/runtime events** — add required audit fields, canonical lifecycle status, and deterministic event identity while preserving existing simple callers.
4. **Nautilus dependency/backtest boundary** — pin NautilusTrader to the Daedalus runtime version and make fixture-vs-real-engine backtest boundaries explicit.

## Component design

### Validation hardening

- `packages/strategy_validation/policy.py` owns canonical forbidden tokens.
- `packages/strategy_validation/validators.py` remains the recursive payload validator.
- `packages/ai_builder/service.py` calls the validator for every provider draft and returns `accepted=False` with errors instead of raising for ordinary invalid drafts.
- Direct prompt requests for live execution still raise `ValueError` because they are unsafe requests, not merely invalid specs.

### Market-profile contract alignment

- Backend keeps the source contract in `packages/instrument_registry/service.py` and `services/api/routes/market_catalog.py`.
- Frontend types in `apps/web/lib/types.ts` match actual backend response fields.
- `MarketProfilePanel.tsx` submits `data_type`, `market_type`, and backend-formatted `date_range`.
- Component tests stop mocking a fantasy DTO and assert the real payload shape.

### Audit-grade job/runtime events

- `BacktestJob` grows optional/defaulted audit fields required by hardguards.
- `RuntimeEvent` grows `event_id`, `actor_type`, `actor_id`, `timestamp`, and `metadata` defaults so existing callers remain lightweight.
- Worker success status becomes `SUCCEEDED` to match docs.
- Event stream persistence stores the richer payload unchanged.

### Nautilus dependency/backtest boundary

- `pyproject.toml` pins `nautilus_trader==1.223.0` to match Daedalus runtime.
- Backtest runner naming/docs make clear that fixture runner is not real Nautilus backtest evidence.
- Existing `NautilusBacktestEngineBoundary` remains the injection seam for real engine smoke tests.

## Data flow

```text
AI/User draft
  -> StrategySpec model validation
  -> recursive hard-rule validator
  -> accepted draft or validation errors
  -> compile artifact with execution_authority=False
  -> durable BacktestJob with audit fields
  -> RuntimeEvent stream with event_id/timestamp/actor metadata
  -> fixture or injected Nautilus backtest boundary
  -> result normalization
  -> promotion request remains signal-preview/shadow only
```

## Error handling

- Invalid AI output returns `AiDraftResult(accepted=False, validation_errors=[...])` for normal validation failures.
- Explicit live-order prompts still raise `ValueError("forbidden execution request")`.
- Invalid market-profile submissions return the current 422 route contract.
- Missing job IDs remain 404 at route boundaries.
- Real Nautilus engine absence is not hidden; fixture results remain labeled fixture/scaffold evidence.

## Testing strategy

Each segment follows TDD:

1. Write failing tests.
2. Run focused tests and verify the expected failure.
3. Implement minimal production changes.
4. Run focused tests to green.
5. Run the segment reconciliation slice.
6. Update `structure.md`, `findings.md`, and `handguard.md`.

Master reconciliation runs Python compile, full Python tests, frontend typecheck/unit/build, and records Playwright status.

## Acceptance criteria

- AI nested forbidden references cannot be accepted as valid drafts.
- All forbidden terms listed in hardguards are rejected recursively.
- UI-shaped market-profile validation succeeds against the real backend contract.
- Backtest jobs/events include hardguard audit fields and use canonical success status.
- `nautilus_trader==1.223.0` is pinned and documented as Daedalus-matched.
- `structure.md`, `findings.md`, and `handguard.md` include segment completion evidence.
