# Nautilus Builder Deep Review Findings

**Review date:** 2026-05-24  
**Target repository:** `/home/mok/projects/nautilus_builder`  
**Review mode:** `superpowers:code-review` + `superpowers:nt` routed primarily through `nt-review`, with `nt-architect`, `nt-adapters`, `nt-live`, and `nt-testing` checks.

## Verdict

**Recommendation: REQUEST CHANGES before claiming Builder MVP or NautilusTrader readiness.**

The repo is safe as a Builder-side scaffold/prototype, and the no-live-order boundary is mostly intact. It is not yet safe to claim that AI output, frontend profile validation, job/event audit trails, or NautilusTrader backtest integration are production-grade.

## Verification evidence

Commands run from `/home/mok/projects/nautilus_builder`:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Result: Pytest: 188 passed

cd apps/web
npm run typecheck
npm test
npm run build
# Result: typecheck passed, Vitest 12 passed, Next build passed

npm run test:e2e
# Result: failed because Playwright Chromium executable is not installed in ~/.cache/ms-playwright
```

Additional probes:

- UI-shaped profile-validation payload against the real `ApiApp` returned `422` with `requested data type unsupported: `.
- AI provider output containing nested `TradeAction` was accepted with `accepted=True` and no validation errors.
- Strategy validator accepted `api_key`, `secret_key`, `credential`, `broker_order`, and `exchange_order` references.

## Positive findings

- Builder-vs-Daedalus-vs-NautilusTrader boundaries are explicit in `doc/nautilus_builder_hardguards.md`, `doc/nautilus_builder_spec.md`, and `README.md`.
- Compile artifacts set `execution_authority=False` for both backtest and signal-preview profiles.
- Promotion payloads set `may_submit_order=False` and `may_create_trade_action=False`.
- Backtest config rejects explicit live credentials.
- The test suite is broad for a scaffold-stage repo and currently passes for Python contracts and frontend unit/build checks.
- API routes are mostly thin adapters over `packages/*`, which matches `services/api/AGENTS.md`.

## Findings by severity

### CRITICAL-1 — AI draft path can bypass StrategySpec schema and hard-rule validation

**Evidence**

- `doc/nautilus_builder_hardguards.md:347-357` says AI may not bypass schema/policy validators or generate direct live execution.
- `packages/ai_builder/service.py:29-31` only rejects a top-level `submit_order` key and non-signal output. It does not run `validate_strategy_spec()` and does not call `StrategySpec.model_validate()`.
- `packages/ai_builder/service.py:41-47` marks all non-`force_invalid` provider outputs accepted.
- Probe result: a provider returning nested `TradeAction` under `rules.entry.all[0].gt` was accepted with `accepted=True`, no validation errors.

**Risk**

A malicious or malformed advisory provider can produce invalid specs or nested live-execution references while Builder records the draft as accepted. This violates the central AI hardguard and makes downstream “accepted draft” state untrustworthy.

**Fix**

- Route every provider response through `validate_strategy_spec()` and `StrategySpec.model_validate()` before `accepted=True`.
- Store validation errors in `AiDraftResult.validation_errors`; never special-case only top-level keys.
- Add tests for nested `TradeAction`, nested `submit_order`, missing StrategySpec required fields, forbidden credential tokens, and malformed risk blocks.

### HIGH-1 — Forbidden StrategySpec token policy misses several hardguarded secrets/order references

**Evidence**

- `doc/nautilus_builder_hardguards.md:158-168` forbids `broker_order`, `exchange_order`, `api_key`, `secret_key`, and `credential` in specs.
- `packages/strategy_validation/policy.py:3-11` only includes submit/modify/cancel/close/set/place order and `TradeAction` references.
- `packages/strategy_validation/policy.py:13-24` raw-code patterns also omit those hardguarded secret/order terms.
- Probe result: validator returned `is_valid=True` for rules referencing `api_key`, `secret_key`, `credential`, `broker_order`, and `exchange_order`.

**Risk**

User or AI specs can carry credential/exchange-order concepts through validation despite the hardguard. Even if no live execution path exists, this weakens the core “Builder cannot access or encode secrets/live broker actions” guarantee.

**Fix**

- Add all hardguarded forbidden terms to policy coverage.
- Add regression tests matching each term from `doc/nautilus_builder_hardguards.md:158-178`.
- Prefer one canonical forbidden-token table generated from or checked against the hardguard doc to prevent drift.

### HIGH-2 — Frontend market-profile payload and types do not match the real backend API contract

**Evidence**

- Backend validation expects `data_type`, `timeframe`, `market_type`, and `date_range`: `services/api/routes/market_catalog.py:28-37`.
- Frontend sends `adapter_id`, `instrument_id`, `timeframe`, `start_date`, and `end_date`, omitting `data_type`, `market_type`, and `date_range`: `apps/web/components/market/MarketProfilePanel.tsx:143-155`.
- Backend `InstrumentSelection` returns `instrument_id`, `market_type`, `supported_data_types`, `supported_timeframes`, and string `available_date_ranges`: `packages/instrument_registry/service.py:8-16`.
- Frontend types expect `adapter_id`, `symbol`, and date-range objects with `{start,end}`: `apps/web/lib/types.ts:38-50`.
- Frontend adapter UI reads `adapter.name`, but backend `AdapterProfile` has no `name` field: `apps/web/components/market/MarketProfilePanel.tsx:19-22`, `packages/adapter_registry/models.py:6-12`.
- Probe result: sending the UI-shaped payload to `/api/backtest-profiles/validate` returned `422` / `requested data type unsupported: `.

**Risk**

A real operator cannot successfully validate a backtest profile through the current UI against the current backend. The existing component test mocks a different API shape than the backend exposes, so it misses the integration failure.

**Fix**

- Align frontend DTOs to backend payloads or add backend response mappers that intentionally expose UI-friendly fields.
- Submit `data_type`, `market_type`, and backend-formatted `date_range`.
- Update `AdapterSummary`, `InstrumentSummary`, and `DataAvailability` types to match actual API responses.
- Add a frontend/API contract test using the real `ApiApp` payload shape or a generated OpenAPI/schema fixture.

### HIGH-3 — BacktestJob and RuntimeEvent models are below the hardguard audit contract

**Evidence**

- Hardguard requires each long-running job to carry `job_id`, `status`, `created_by`, `created_at`, `updated_at`, `strategy_spec_version_id`, `adapter_profile_id`, `instrument_id`, `data_range`, `worker_id`, `result_artifact_refs`, and `event_stream_id`: `doc/nautilus_builder_hardguards.md:77-98`.
- Current `BacktestJob` only has `job_id`, `stage`, `strategy_spec_version`, `adapter_id`, `instrument_id`, `compile_hash`, `validation_report_id`, and `cancel_requested`: `packages/backtest_jobs/models.py:6-16`.
- Hardguard requires runtime events to include `event_id`, `job_id`, `actor_type`, `actor_id`, `stage`, `level`, `message`, `timestamp`, and `metadata`: `doc/nautilus_builder_hardguards.md:403-421`.
- Current `RuntimeEvent` only has `job_id`, `stage`, `level`, `message`, and `progress_pct`: `packages/runtime_events/models.py:6-13`.
- Spec success lifecycle ends at `SUCCEEDED`: `doc/nautilus_builder_spec.md:426-438`, but worker transitions to `COMPLETED`: `services/workers/nautilus_backtest_worker.py:54-59`.

**Risk**

The repo can pass current tests while failing its own auditability requirements. Job state and event replay are not yet sufficient for durable backend ownership, post-run review, worker attribution, or artifact lineage.

**Fix**

- Introduce explicit job and event Pydantic models/enums matching the hardguard fields.
- Use canonical lifecycle states (`SUCCEEDED`, `CANCELED`, `WORKER_LOST`, etc.) or update docs/tests if `COMPLETED` is intentionally canonical.
- Require event IDs, timestamps, actor identity, metadata, event stream ID, and artifact refs.
- Add tests for all hardguard-required fields and failure transitions.

### MEDIUM-1 — NautilusTrader is documented as a required engine dependency but is not pinned or wired as a real backtest engine

**Evidence**

- Dependency architecture says Builder should install NautilusTrader directly and pin the same version as Daedalus: `doc/nautilus_builder_repo_dependency_architecture.md:85-112`.
- `pyproject.toml:10-16` has FastAPI/Pydantic/Postgres/Redis/Uvicorn dependencies but no `nautilus_trader` dependency.
- `packages/backtest_runner/runner.py:7-37` returns fixture data.
- `packages/backtest_runner/nautilus_engine.py:10-44` defines an injected protocol boundary, but there is no concrete NautilusTrader engine adapter.
- Official NautilusTrader backtesting docs describe a `BacktestEngine` processing historical data and producing results/metrics; Builder currently does not exercise that path.

**Risk**

The product can overstate NautilusTrader alignment while only proving fixture/injected-engine behavior. Research/live parity and backtest semantics cannot be validated until Builder pins and executes the intended NautilusTrader version.

**Fix**

- Pin `nautilus_trader==<agreed version>` in `pyproject.toml` once Daedalus compatibility is selected.
- Add a minimal concrete NautilusTrader backtest smoke or clearly rename current runner to `fixture_runner` until real wiring exists.
- Keep fixture tests, but add a separate opt-in engine smoke that proves StrategySpec -> Nautilus config -> backtest result normalization.

### MEDIUM-2 — Allowed block docs and executable StrategySpec schema have drifted

**Evidence**

- Hardguard v1 allowed indicators include EMA, SMA, RSI, MACD, ATR, BollingerBands, and VWAP, and operators include `gte`, `lte`, `eq`, `and`, `or`, and `not`: `doc/nautilus_builder_hardguards.md:187-214`.
- Executable schema only permits `EMA` and `RSI`: `packages/strategy_spec/models.py:34-37`.
- Executable rule clauses only support `crossed_above`, `crossed_below`, `gt`, and `lt`: `packages/strategy_spec/models.py:53-64`.

**Risk**

Users and AI prompts can follow the source-truth docs and still be rejected by the current schema. This creates false negatives and makes the builder feel broken for documented v1 blocks.

**Fix**

- Either expand the schema to all documented v1 blocks or explicitly label the executable MVP subset in `doc/` and UI.
- Add tests for every documented allowed indicator/operator, or add tests proving omitted items are intentionally out of scope.

### MEDIUM-3 — Shadow promotion route fabricates readiness values without supplied evidence

**Evidence**

- Promotion hardguards require validation, backtest, out-of-sample/walk-forward, risk, gate, no-lookahead, runtime-boundary, and manual approval evidence for production approval: `doc/nautilus_builder_hardguards.md:372-399`.
- `services/api/routes/promotions.py:7-14` creates a shadow payload from only `strategy_version` and `compile_hash`, hardcoding `gate_compatibility=True`.
- `packages/promotions/service.py:28-47` returns evidence ref filenames without checking that referenced artifacts exist and sets `manual_approval=False` for shadow requests.

**Risk**

This does not grant live order authority, but it can make shadow-readiness appear stronger than the backend evidence actually proves.

**Fix**

- Keep `/api/promotions/request` as the safe user-facing route and treat `/api/promotions/shadow` as internal/test-only unless it verifies evidence IDs.
- Require result ID, validation report ID, backtest result ID, no-lookahead result, and gate compatibility evidence before setting positive readiness flags.

### LOW-1 — README limitations are stale relative to current repo shape

**Evidence**

- `README.md:70-76` says there is no package manifest, no real API server bootstrap, and no real frontend app shell/build pipeline.
- Current repo has `pyproject.toml`, `services/api/fastapi_app.py`, `apps/web/package.json`, Next app pages, TypeScript config, Vitest, Playwright config, and a passing `npm run build`.

**Risk**

Human and agent contributors may incorrectly treat existing surfaces as absent or planned-only, increasing duplicate or misplaced work.

**Fix**

- Update README limitations to distinguish what now exists from what remains scaffold/contract-only.

## NautilusTrader-specific notes

- No custom NautilusTrader adapter code exists in this repo, so `nt-adapters` DataTester/ExecTester gates are not directly applicable yet.
- If Builder later owns adapter profiles that claim real data/execution adapter compatibility, official NautilusTrader DataTester/ExecTester evidence should become mandatory.
- Live trading authority should remain outside Builder. Official NautilusTrader live docs emphasize research-to-live parity and live financial risk; Builder should continue to compile only to backtest or signal-preview paths.

## Closure progress — Segment 1 validation hardening

**Status:** completed on 2026-05-24.

Closed/changed findings:

- `CRITICAL-1` is remediated at code level: `AiBuilderService` now runs every provider draft through `validate_strategy_spec()` before returning `accepted=True`.
- `HIGH-1` is remediated at code level: forbidden references now include `broker_order`, `exchange_order`, `api_key`, `secret_key`, and `credential` in addition to execution-order verbs and `TradeAction`.

Evidence:

```bash
rtk pytest tests/strategy_validation/test_forbidden_execution_blocks.py tests/ai_builder/test_ai_output_must_validate.py -q
# Pytest: 11 passed

rtk pytest tests/strategy_validation tests/ai_builder tests/strategy_spec -q
# Pytest: 26 passed
```

Remaining open findings after Segment 1: frontend/backend market-profile DTO drift, audit-grade job/runtime fields, NautilusTrader dependency/backtest boundary, README/readiness drift.

## Closure progress — Segment 2 market-profile contract alignment

**Status:** completed on 2026-05-24.

Closed/changed findings:

- `HIGH-2` is remediated at code level: the market-profile UI now uses backend-real adapter and instrument shapes, sends `data_type`, `market_type`, and `date_range`, and renders validation from `instrument.instrument_id` instead of the removed `adapter_profile_id` path.
- Backend/API contract coverage now includes a `create_app()` regression for the same payload shape the frontend sends.
- Broader API route assertions were reconciled with Segment 1's validated StrategySpec output shape by checking `spec.validation.output_mode`.

Evidence:

```bash
cd apps/web && npm test -- components/market/MarketProfilePanel.test.tsx
# 1 passed

rtk pytest tests/api/test_backtest_profiles.py -q
# Pytest: 3 passed

cd apps/web && npm run typecheck
# tsc --noEmit passed

rtk pytest tests/api tests/instrument_registry tests/adapter_registry tests/web -q
# Pytest: 64 passed
```

Remaining open findings after Segment 2: audit-grade job/runtime fields, NautilusTrader dependency/backtest boundary, README/readiness drift, StrategySpec allowed-block doc/schema drift, and promotion evidence strictness.
