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

## Closure progress — Segment 3 audit-grade jobs and runtime events

**Status:** completed on 2026-05-24.

Closed/changed findings:

- `HIGH-3` is remediated at code level for current Builder seams: `BacktestJob` now exposes the hardguard audit fields, route payloads return them, and worker transitions update `worker_id`, `result_artifact_refs`, and timestamps.
- `RuntimeEvent` now carries `event_id`, `actor_type`, `actor_id`, `timestamp`, and `metadata` in addition to the existing stage/level/message/progress fields.
- Worker success lifecycle now uses `SUCCEEDED` instead of `COMPLETED`.

Evidence:

```bash
rtk pytest tests/backtest_jobs/test_create_job.py tests/runtime_events/test_replay.py tests/backtest_runner/test_worker_integration.py -q
# RED captured expected failures before implementation; GREEN: Pytest: 6 passed

rtk pytest tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/api/test_backtest_job_routes.py tests/api/test_route_mounts.py tests/web/test_job_terminal_replay.py -q
# Pytest: 36 passed

python3 -m compileall -q packages/backtest_jobs packages/runtime_events services/workers services/api/routes/backtest_jobs.py
# compileall passed
```

Remaining open findings after Segment 3: NautilusTrader dependency/backtest boundary, README/readiness drift, StrategySpec allowed-block doc/schema drift, and promotion evidence strictness.

## Closure progress — Segment 4 NautilusTrader dependency and backtest boundary

**Status:** completed on 2026-05-24.

Closed/changed findings:

- `MEDIUM-1` is partially remediated at code level: Builder now pins `nautilus_trader==1.223.0`, matching the Daedalus runtime pin found read-only in `/home/mok/projects/Nautilus-Daedalus/pyproject.toml`.
- Fixture runner results and injected engine boundary results are now explicitly labeled by `engine_mode`, and both carry the pinned NautilusTrader version.
- Backtest configs continue to reject credentials and now also state `live_trading_enabled=False` and `execution_authority=False`.

Remaining limitation:

- This segment does not install or execute a concrete NautilusTrader `BacktestEngine`; it prevents hidden fixture-overclaiming while preserving the injected engine seam for future real-engine wiring.

Evidence:

```bash
rtk pytest tests/backtest_runner/test_nautilus_dependency_contract.py -q
# RED captured missing pin/labels; GREEN: Pytest: 3 passed

rtk pytest tests/backtest_runner -q
# Pytest: 10 passed

python3 -m compileall -q packages/backtest_runner tests/backtest_runner
# compileall passed
```

Remaining open findings after Segment 4: README/readiness drift, StrategySpec allowed-block doc/schema drift, promotion evidence strictness, and a future real NautilusTrader engine smoke beyond the current injected boundary.

## Master reconciliation — findings closure

**Status:** completed on 2026-05-24.

Top findings closed in this implementation loop:

- AI draft provider output cannot be accepted unless StrategySpec schema and recursive hard-rule validation pass.
- Forbidden token coverage includes hardguarded credential and broker/exchange-order terms.
- Market-profile frontend payloads match backend validation API shape.
- Backtest jobs and runtime events carry audit fields and worker success uses `SUCCEEDED`.
- `nautilus_trader==1.223.0` is pinned to match Daedalus runtime, while fixture and injected-engine evidence stay explicitly labeled.

Master evidence:

```bash
python3 -m compileall -q packages services tests
# passed

rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 197 passed

cd apps/web && npm run typecheck && npm test && npm run build
# tsc --noEmit passed; Vitest: 8 files / 12 tests passed; Next build passed

cd apps/web && npm run test:e2e
# Playwright: 4 passed
```

Residual non-top findings remain tracked for later work: README/readiness drift, StrategySpec allowed-block doc/schema drift, promotion evidence strictness, and a future concrete NautilusTrader `BacktestEngine` smoke beyond the current injected boundary.

## Deep review refresh — NT/Daedalus alignment pass

**Reviewed:** 2026-05-24 12:50 UTC
**Mode:** `superpowers:code-review` + `superpowers:nt` routed through `nt-review`, with `nt-architect`, `nt-adapters`, `nt-live`, and `nt-testing` checks.
**Scope:** `/home/mok/projects/nautilus_builder` only; `/home/mok/projects/Nautilus-Daedalus` was read-only reference.

### Refresh verdict

**Recommendation: COMMENT for the current Builder contract scaffold; REQUEST CHANGES before claiming NautilusTrader backtest/runtime readiness.**

**Architectural status: WATCH.** The no-live-order and Builder/Daedalus split is intact, and the prior top findings remain closed by tests. The main blocker to stronger approval is that the active Python environment is not actually running the recorded NautilusTrader pin and no concrete NautilusTrader `BacktestEngine` smoke exists yet.

### Fresh verification evidence

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 197 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed
```

Targeted probes:

```text
forbidden_terms_rejected: 12/12
AI nested TradeAction draft accepted: False
market profile validation through create_app(): 200 valid=True
Builder pyproject pin: nautilus_trader==1.223.0
Daedalus pyproject pin: nautilus_trader==1.223.0
local python import: nautilus_trader 1.222.0 from /home/mok/.local/lib/python3.12/site-packages
```

### Positive findings after refresh

- `packages/ai_builder/service.py:35-49` now gates `accepted=True` on `validate_strategy_spec()`.
- `packages/strategy_validation/policy.py:3-15` covers execution verbs, `TradeAction`, broker/exchange order references, and credential terms.
- `apps/web/components/market/MarketProfilePanel.tsx:150-162` sends backend-required market-profile fields; `services/api/routes/market_catalog.py:28-40` validates those fields against backend registries.
- `packages/backtest_jobs/models.py:6-24` and `packages/runtime_events/models.py:6-18` carry the hardguard audit fields.
- `packages/backtest_runner/engine_contract.py:3-5` labels the intended NautilusTrader version and fixture/injected evidence modes.
- Daedalus reference keeps live authority outside Builder: `/home/mok/projects/Nautilus-Daedalus/README.md:15-19` and `AGENTS.md:17-27` define advisory systems as non-authoritative and isolate order submission under the execution lane.

### Current findings by severity

#### HIGH-4 — Active environment is not synchronized to the Builder/Daedalus NautilusTrader pin

**Evidence**

- `pyproject.toml:10-13` pins `nautilus_trader==1.223.0`.
- `/home/mok/projects/Nautilus-Daedalus/pyproject.toml:7` also pins `nautilus_trader==1.223.0`.
- `packages/backtest_runner/engine_contract.py:3` records `NAUTILUS_TRADER_VERSION = "1.223.0"`.
- Fresh probe from this cwd: default `python3` imports `nautilus_trader` version `1.222.0` from `/home/mok/.local/lib/python3.12/site-packages`.
- Builder has no `uv.lock` or requirements lock, and the passing tests do not import a concrete NautilusTrader `BacktestEngine`.

**Risk**

The repository now records the correct Daedalus-matched pin, but local/runtime verification can still run against a different NautilusTrader package or no synchronized package at all. This can produce false confidence in version-sensitive model, adapter, fill, and backtest semantics.

**Fix**

- Add a dependency sync/lock policy for Builder (`uv.lock` or equivalent) and document the expected install command.
- Add a test that checks `importlib.metadata.version("nautilus_trader") == packages.backtest_runner.engine_contract.NAUTILUS_TRADER_VERSION` in the intended test environment.
- Add at least one minimal concrete NautilusTrader backtest smoke, or keep all readiness language explicitly fixture/injected-only until that exists.

#### MEDIUM-4 — Shadow promotion route still fabricates gate compatibility and evidence refs

**Evidence**

- `services/api/app.py:44-45` still mounts both `/api/promotions/shadow` and `/api/promotions/request`.
- `services/api/routes/promotions.py:7-14` creates `/api/promotions/shadow` with `gate_compatibility=True` regardless of supplied evidence.
- `packages/promotions/service.py:28-47` returns fixed `validation_report.md` and `backtest_result.json` refs without checking artifact existence.
- Hardguards require validation, backtest, no-lookahead, risk, gate, runtime-boundary, and manual approval evidence before production approval (`doc/nautilus_builder_hardguards.md:372-399`, `547-558`).

**Risk**

This does not create live order authority, but it can overstate readiness and weaken the audit trail for shadow/promotion decisions.

**Fix**

Prefer `/api/promotions/request` for user-facing flows. Gate `/api/promotions/shadow` behind explicit evidence IDs or mark it internal/test-only until it verifies stored artifacts and gate compatibility.

#### MEDIUM-5 — StrategySpec allowed-block docs still exceed executable schema

**Evidence**

- `doc/nautilus_builder_hardguards.md:187-214` lists v1 indicators/operators including `SMA`, `MACD`, `ATR`, `BollingerBands`, `VWAP`, `gte`, `lte`, `eq`, `and`, `or`, and `not`.
- `packages/strategy_spec/models.py:34-57` currently accepts only `EMA`, `RSI`, `crossed_above`, `crossed_below`, `gt`, and `lt`.

**Risk**

Users and agents may build specs that docs call valid but the executable schema rejects. This is acceptable only if the repo explicitly labels the current implementation as an MVP subset.

**Fix**

Either implement/tests the documented v1 block set, or update `doc/`/UI wording to say the current executable subset is EMA/RSI plus crossed/gt/lt only.

#### LOW-2 — README limitations are stale relative to current repo shape

**Evidence**

- `README.md:70-75` still says there is no package manifest, real API server bootstrap, real frontend app shell, or frontend build pipeline.
- Current repo has `pyproject.toml`, `services/api/fastapi_app.py`, `services/api/dev_server.py`, a Next app shell under `apps/web/app`, Vitest, Playwright, and a passing build/E2E run.

**Risk**

Contributor orientation can drift toward planned-only assumptions and duplicate already-present surfaces.

**Fix**

Refresh the limitations section to distinguish current contract/MVP implementation from remaining production integration gaps.

#### LOW-3 — Pydantic warning from `schema` field shadows `BaseModel.schema`

**Evidence**

- Playwright web-server startup emitted: `UserWarning: Field name "schema" in "BuilderPostgresConfig" shadows an attribute in parent "BaseModel"`.
- `packages/workflow_spine/storage_config.py:6-13` defines `BuilderPostgresConfig.schema`.

**Risk**

Low immediate risk, but warning noise can hide more important runtime startup warnings and may become a compatibility problem under stricter Pydantic versions.

**Fix**

Rename the field to `db_schema` with a backwards-compatible alias if external payload compatibility matters, and update tests to assert no warning during import/config construction.

## Production blocker closure pass — 2026-05-24

**Status:** completed. The five main production blockers identified after the refresh are closed at the Builder contract/MVP level.

### Closed blockers

1. **Runtime dependency mismatch — CLOSED**
   - Builder now has `uv.lock` and an active-runtime check in `packages/backtest_runner/runtime_check.py`.
   - Builder, read-only Daedalus, and active `python3` all resolve `nautilus_trader==1.223.0`.

2. **No real NautilusTrader backtest smoke — CLOSED for engine lifecycle smoke**
   - `packages/backtest_runner/real_engine_smoke.py` runs a real pinned `BacktestEngine` lifecycle and returns `engine_mode=real_nautilus_engine_smoke`.
   - Fixture and injected-engine evidence are still labeled separately; this is not overclaimed as a full data/strategy replay.

3. **Promotion evidence too weak — CLOSED**
   - `PromotionEvidenceRefs` requires validation, backtest, no-lookahead, gate-compatibility, runtime-boundary, and risk-review refs.
   - `/api/promotions/shadow` now rejects missing evidence (`422`) and no longer fabricates refs, coerces evidence values, accepts empty refs, accepts missing strategy/compile identity, or accepts non-boolean gate compatibility.
   - FastAPI and dependency-free `ApiApp` bootstraps share the hardened route helper.

4. **Docs/schema drift — CLOSED for executable MVP truth**
   - StrategySpec schema, generated JSON schema, frontend allowed blocks, and hardguard docs now align on the executable indicator/operator set.
   - Direct `not` is explicitly documented as outside the MVP executable schema.

5. **Readiness hygiene — CLOSED**
   - README limitations reflect the current package/API/frontend/E2E reality.
   - `BuilderPostgresConfig` uses `db_schema` with `schema` as an input alias, removing the Pydantic shadow-field warning.

### Segment and master evidence

```bash
rtk pytest tests/api/test_fastapi_app.py -q
# RED: 0 passed, 4 failed because FastAPI still imported removed _create_shadow_promotion

rtk pytest tests/api/test_fastapi_app.py tests/api/test_route_mounts.py tests/promotions -q
# Pytest: 29 passed

python3 -m compileall -q packages/backtest_runner packages/promotions packages/strategy_spec packages/workflow_spine services/api tests/backtest_runner tests/promotions tests/strategy_spec tests/workflow_spine tests/integration
rtk pytest tests/backtest_runner tests/promotions tests/api tests/strategy_spec tests/strategy_validation tests/workflow_spine tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 113 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 215 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed
```

### Current verdict after closure

**Recommendation: COMMENT / conditional Builder-MVP approval, not full trading-production approval.** The named blockers are closed and the no-live-order boundary remains intact. Remaining production work is now broader deployment maturity: catalog-backed real backtest worker, persisted artifact store, production authz/tenant controls, CI-provisioned browser/runtime environment, and operational rollout evidence.

## Catalog-backed replay closure start — 2026-05-24

Planning artifacts added for the remaining NautilusTrader readiness blocker: `docs/superpowers/specs/2026-05-24-catalog-backed-nautilus-replay-design.md` and `docs/superpowers/plans/2026-05-24-catalog-backed-nautilus-replay-implementation-plan.md`. The chosen design is a deterministic ParquetDataCatalog + BacktestNode replay using an official no-order SubscribeStrategy, preserving Builder's no-live-order boundary.

## Catalog-backed replay Segment 1 closure

**Status:** completed on 2026-05-24.

Closed/changed finding:

- The prior remaining blocker is remediated at smoke-evidence level: Builder now has a real catalog-backed Nautilus replay smoke, not only an empty `BacktestEngine` lifecycle check.
- The smoke writes historical quote ticks to `ParquetDataCatalog`, runs `BacktestNode` with official `SubscribeStrategy`, and verifies iterations/data count, metrics sections, zero orders, zero positions, and no credentials/execution authority.

Evidence:

```bash
rtk pytest tests/backtest_runner/test_catalog_backed_nautilus_replay_smoke.py -q
# RED: missing catalog-backed replay function; GREEN: Pytest: 1 passed

rtk pytest tests/backtest_runner -q
# Pytest: 15 passed
```

Remaining limitation: this is still a deterministic smoke over synthetic historical quote ticks, not a production-scale catalog-backed worker over user-selected datasets and StrategySpec-generated strategies.

## Catalog-backed replay Segment 2 closure

**Status:** completed on 2026-05-24.

Closed/changed finding:

- README/readiness language now reflects the stronger catalog-backed replay evidence and still avoids overclaiming full trading-production readiness.
- The old limitation saying Builder only had a minimal empty lifecycle smoke is removed.

Evidence:

```bash
rtk pytest tests/integration/test_readme_readiness_hygiene.py -q
# RED: README lacked catalog-backed replay wording; GREEN: Pytest: 2 passed

rtk pytest tests/backtest_runner tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 17 passed
```

## Master reconciliation — catalog-backed Nautilus replay

**Status:** completed on 2026-05-24.

The specific remaining blocker from the last review is closed: Builder no longer relies only on an empty BacktestEngine lifecycle smoke. The new `catalog_backed_replay_smoke` writes synthetic historical quote ticks to a Nautilus `ParquetDataCatalog`, runs a real Nautilus `BacktestNode` / BacktestEngine-backed replay with official `SubscribeStrategy`, and records result/metric evidence while keeping orders, positions, credentials, and execution authority at zero.

Verdict: **COMMENT / conditional Builder-MVP approval** for this blocker. This is not full trading-production readiness; full readiness still requires production-scale StrategySpec-generated replay over durable user-selected datasets with persisted artifacts and deployment/CI evidence.

Segment 3 focused evidence:

```bash
rtk pytest tests/backtest_runner tests/integration/test_readme_readiness_hygiene.py tests/integration/test_catalog_replay_ledger_updates.py -q
# Pytest: 18 passed
```

## Final verification — catalog-backed Nautilus replay closure

**Completed:** 2026-05-24.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 218 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed
```

Authority grep for live-order/credential/Daedalus execution terms found only guard tables, negative tests, false authority booleans, and credential-rejection paths. No Builder live-order path was introduced.

## Production runtime readiness Segment 1 — durable artifact storage

**Status:** completed on 2026-05-24.

Closed part of the durable-artifact blocker: Builder now has a concrete local JSON artifact store with persisted payloads, checksums, artifact refs, and user/project-scoped reads. This is durable local storage evidence, not a claim that object-store/S3 production deployment is finished.

Evidence:

```bash
rtk pytest tests/artifact_store/test_local_json_artifact_store.py -q
# RED: missing packages.artifact_store import
# GREEN: Pytest: 3 passed
```

## Production runtime readiness Segment 2 — user-selected catalog datasets

**Status:** completed on 2026-05-24.

Closed part of the user-selected dataset blocker: Builder now has an explicit catalog dataset registry and selection contract. Dataset selection is tenant-scoped and validates adapter, instrument, data type, timeframe, market type, and date range before a dataset can be used as backtest evidence. Backtest jobs now carry dataset identity and catalog path fields.

Remaining boundary: this establishes the dataset-selection contract and local catalog path handoff; production object-storage/catalog provisioning still requires deployment evidence.

Evidence:

```bash
rtk pytest tests/catalog_datasets tests/backtest_jobs -q
# Pytest: 8 passed
```

## Production runtime readiness Segment 3 — StrategySpec-generated catalog replay

**Status:** completed on 2026-05-24.

Closed the StrategySpec-generated replay blocker at deterministic local evidence level: Builder can now run a validated StrategySpec through a real Nautilus `BacktestNode` with a Builder-owned no-order `RuleGraphBacktestStrategy`, using a real `ParquetDataCatalog` and a user-selected dataset contract. Worker output is persisted as a scoped artifact ref.

Evidence fields include engine mode, NautilusTrader version, dataset ID, catalog path, Builder/NT instrument IDs, rule-graph strategy path/config path, StrategySpec version, compile hash, catalog data count, iterations, run timestamps, zero orders, zero positions, and false live authority/credential booleans.

Remaining boundary: this is still deterministic local replay with synthetic quote ticks; production data ingestion/provisioning and deployment object storage require CI/deployment evidence.

Evidence:

```bash
rtk pytest tests/backtest_runner -q
# Pytest: 17 passed
```

## Production runtime readiness Segment 4 — authz/tenant controls

**Status:** completed on 2026-05-24.

Closed part of the authz/tenant blocker: job and artifact/dataset contracts now carry user/project scope, and backtest job service/API reads/cancels can enforce that scope. Cross-project access returns `ProjectScopeError` at package level and `403 forbidden` at API-contract level.

Remaining boundary: this is a package/API contract for scoped access. A production deployment still needs real auth middleware/token propagation in front of these seams.

Evidence:

```bash
rtk pytest tests/auth tests/backtest_jobs tests/api/test_backtest_job_routes.py -q
# Pytest: 21 passed
```

## Production runtime readiness Segment 5 — CI/deployment evidence

**Status:** completed on 2026-05-24.

Closed the CI/deployment-evidence blocker at repository-template level: the CI template now lists Python compile checks, Nautilus runtime pin verification, full Python contract suites including artifact/dataset seams, and frontend type/unit/build/e2e checks. Deployment evidence now names closed seams and explicitly preserves the no-live-order boundary.

Remaining boundary: the workflow is still under `infra/ci/` as a template. Repository activation under `.github/workflows/`, real secrets-free environment provisioning, and object-storage deployment remain rollout steps.

Evidence:

```bash
rtk pytest tests/integration/test_operability_baseline.py tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 8 passed
```

## Master reconciliation — production runtime readiness closure

**Status:** completed on 2026-05-24.

Recommendation changes from **not production ready** to **conditional Builder-runtime readiness for the named blockers**. The repository now has durable local artifact evidence, user-selected tenant-scoped catalog datasets, StrategySpec-generated Nautilus catalog replay, scoped backtest job access, and CI/deployment evidence templates.

This is still not a full live trading-production claim. Remaining rollout work is cloud/object-storage provisioning, real auth middleware/token injection, production dataset ingestion/curation, and activation of the CI template in the hosting repository.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/artifact_store tests/catalog_datasets -q
# Pytest: 234 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 12 passed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

Code-review synthesis: APPROVE for the scoped repository-contract closure, architectural status WATCH because deployment activation and real middleware/object-store rollout remain outside this local repo pass.

## Deep review refresh — 2026-05-25 inventory-first semantic legacy/deprecation closure

### Verdict

**Recommendation:** REQUEST CHANGES before any stronger production-readiness claim. **Architectural Status:** WATCH for the repo-local Builder contract, BLOCK for production claims that imply real user-selected catalog replay, production auth, or resolved promotion evidence.

No critical live-order authority breach was found. The strongest positive result is that Builder source still has no Daedalus execution-lane import, no live order API call, no direct EvoMap/LangChain/LangGraph execution coupling, and no aiogram/Telegram runtime surface. The highest-risk gaps are evidence provenance and production boundary gaps rather than failing tests.

### Fresh verification evidence

```bash
git ls-remote --symref https://github.com/nautechsystems/nautilus_trader.git HEAD
# refs/heads/develop @ e43ecef7b395e2a5372198d0c8c0565de2209177

git ls-remote --symref https://github.com/EvoMap/evolver.git HEAD
# refs/heads/main @ 3d5386cfe16660de05ef8ff5cbe9749b032e782c

git ls-remote --symref https://github.com/langchain-ai/langchain.git HEAD
# refs/heads/master @ 33875fde2acf6ffb717915a895638274a6098ec2

git ls-remote --symref https://github.com/langchain-ai/langgraph.git HEAD
# refs/heads/main @ d1e2ff0561a8b0b09212d0795c9d7b390a5de23a

python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 234 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
print(status.message)
assert status.is_match
PY
# nautilus_trader runtime matches pinned version 1.223.0

cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

Inventory grep notes:

- Source-only authority grep over `packages/`, `services/`, and `apps/web` found no live order authority implementation. Hits are guard tables, negative tests, `may_submit_order=False`, or forbidden-token policy.
- No Builder source imports `nautilus_brain`, `nautilus_runtime`, `langchain`, `langgraph`, `EvoMap`, `evolver`, `TradingNode`, `LiveNode`, `DataTesterConfig`, or `ExecTesterConfig`.
- No Builder aiogram-dialog implementation exists; the only Builder hit is a derived plan note saying the skill is loaded but no Telegram dialog work is in scope.

### Findings by severity — 2026-05-25 refresh

#### CRITICAL

None found.

#### HIGH-2026-05-25-1 — StrategySpec catalog replay writes synthetic data into the selected catalog path

**Evidence:** `packages/backtest_runner/strategy_spec_replay.py:46-66` creates `Path(dataset.catalog_path)`, initializes `ParquetDataCatalog`, builds `TestDataStubs.quote_tick(...)` rows, writes the instrument and ticks, and then runs `BacktestNode` over those newly written rows.

**Risk:** This can overstate readiness. The path is named `user_selected_catalog`, and evidence carries `dataset_id`, but the replay does not prove that existing user-selected catalog data was ingested. Official Nautilus catalog-backed replay patterns make the catalog the source of historical data; synthetic test-kit writes are valid smoke evidence only when clearly labeled as synthetic.

**Fix:** Split modes explicitly:

1. keep synthetic smoke as `strategy_spec_synthetic_catalog_smoke` or similar;
2. add a production/user-dataset replay mode that fails if the selected catalog is missing/empty/mismatched;
3. record `dataset_source`, row counts before replay, and a read-only catalog checksum/manifest;
4. add tests proving user-dataset mode does not call `TestDataStubs` or write synthetic rows.

#### HIGH-2026-05-25-2 — API scope is client-supplied, not auth-derived

**Evidence:** `services/api/routes/backtest_jobs.py:19-22` accepts `user_id`, `project_id`, `dataset_id`, and `catalog_path` from job creation payloads. `services/api/routes/backtest_jobs.py:110-115` reconstructs `UserProjectContext` from query values for scoped read/cancel. `packages/auth/service.py:12-37` exists but is an in-memory test token service and is not wired into `services/api/fastapi_app.py`.

**Risk:** Route-level scope tests are useful, but a deployed API that trusts request body/query identity lets callers impersonate another user/project. This directly weakens artifact, dataset, and job isolation even though package-level `assert_same_project()` is correct when a trusted context is supplied.

**Fix:** Introduce FastAPI auth middleware/dependency that verifies a bearer token and injects `UserProjectContext`; remove or dev-gate client-provided `user_id`/`project_id`; add 401/403 tests for missing, malformed, cross-project, and mismatched job/dataset contexts.

#### HIGH-2026-05-25-3 — Catalog dataset paths are not rooted or allowlisted before worker writes

**Evidence:** `packages/catalog_datasets/models.py:25-28` only expands `catalog_path`. `packages/backtest_runner/strategy_spec_replay.py:46-65` creates directories and writes catalog data under that path. Unlike `LocalJsonArtifactStore`, there is no configured catalog root, scoped path derivation, path traversal check, symlink guard, or read-only user-dataset mode.

**Risk:** Any future route/registry path that accepts user-controlled catalog metadata can cause the worker to write files anywhere the process account can access. This is a security and operability risk independent of live trading authority.

**Fix:** Make catalog paths registry-owned: derive them from a configured safe root plus scoped dataset IDs, resolve and assert `path.is_relative_to(root)`, reject symlinks/out-of-root paths, and make production replay read-only unless a controlled ingestion job owns writes.

#### MEDIUM-2026-05-25-1 — Registry/replay data-type semantics disagree

**Evidence:** `packages/instrument_registry/service.py:20-25` exposes `BTCUSDT-PERP` with `supported_data_types=["historical_bars", "funding", "liquidation"]`. `packages/backtest_runner/strategy_spec_replay.py:143-144` requires `dataset.data_type == "quote_ticks"`, and the catalog dataset tests create `quote_ticks` datasets for the same Builder instrument.

**Risk:** A user can see a market profile that rejects quote ticks while the worker requires quote ticks for StrategySpec replay. This drift makes readiness and UX guidance inconsistent and can create hard-to-debug job failures or false data-availability claims.

**Fix:** Pick one canonical replay data type for MVP. Either add `quote_ticks` to the instrument registry and UI contracts, or change StrategySpec replay to consume the registry-approved historical bars. Add a contract test that every StrategySpec replay-supported dataset type is visible in the market catalog.

#### MEDIUM-2026-05-25-2 — `backtest_order_intent` is a legacy semantic hazard for a no-order replay path

**Evidence:** `packages/strategy_compiler/compiler.py:21-31` emits `output_mode="backtest_order_intent"` for the `backtest` profile while `execution_authority=False`. The canonical StrategySpec output mode remains `signal_preview_only` (`packages/strategy_spec/models.py:48-50`).

**Risk:** The phrase "order intent" is easy to confuse with Daedalus `TradeAction`/execution intent. It does not currently grant authority, but it undermines semantic closure around the no-order Builder boundary.

**Fix:** Rename the output mode to something like `backtest_signal_observation` or `backtest_rule_graph_observation`, update tests, and reserve any future order-intent terminology for Daedalus-owned execution/gate contracts only.

#### MEDIUM-2026-05-25-3 — Promotion evidence refs are shape-checked but not resolved against scoped artifacts

**Evidence:** `packages/promotions/models.py:11-19` requires string refs only. `packages/promotions/service.py:44-58` validates shape and returns the refs unchanged. Existing tests use unscoped examples such as `artifact://backtests/...` and `artifact://validation/...`, while new durable artifacts use `artifact://builder/{project_id}/{user_id}/...`.

**Risk:** A shadow promotion can carry syntactically complete but nonexistent, wrong-scope, stale, or checksum-mismatched evidence refs. This weakens the audit chain between backtest results, runtime boundary evidence, and promotion readiness.

**Fix:** Require scoped Builder artifact refs for production promotion requests, resolve them through `LocalJsonArtifactStore` or the production artifact backend, verify checksum/scope/evidence type, and keep legacy unscoped refs restricted to fixture tests.

#### MEDIUM-2026-05-25-4 — Backtest job creation bypasses profile validation and returns unhandled errors for malformed payloads

**Evidence:** `services/api/routes/backtest_jobs.py:9-25` copies payload fields directly into `BacktestJobService.create_job()` and does not call `InstrumentRegistryService.validate_selection()` or the catalog dataset registry. Missing required fields use direct indexes (`payload["strategy_version_id"]`, etc.), which raise `KeyError` instead of returning a typed 4xx API response.

**Risk:** Job audit payloads can claim an adapter/instrument/dataset combination that market-profile validation would reject. In FastAPI, malformed payloads can escape the route helper as server errors rather than clear client errors.

**Fix:** Add a request model/validator for backtest job creation, validate market profile and dataset selection before job creation, and return explicit 400/422 responses for missing or mismatched fields.

#### LOW-2026-05-25-1 — Dataset mismatch error text reverses expected/actual values

**Evidence:** `packages/catalog_datasets/service.py:55-60` raises `dataset field mismatch: {field_name} expected {actual_value}, got {expected_value}`; the actual and expected values are reversed in the message.

**Risk:** Low runtime risk, but it slows incident triage and test-debugging around dataset/profile mismatches.

**Fix:** Swap the values in the message and add a focused test for diagnostic wording.

#### LOW-2026-05-25-2 — Frontend test stack emits a Vite CJS deprecation warning

**Evidence:** `npm test -- --run` passes but prints `The CJS build of Vite's Node API is deprecated`.

**Risk:** Low immediate risk; it is a future maintenance warning for the frontend toolchain.

**Fix:** Track Vite/Vitest config upgrade work separately; do not mix it with trading/runtime safety changes.

### Positive findings retained

- `pyproject.toml` pins `nautilus_trader==1.223.0`, and the runtime check passed in the active environment.
- The no-live-order boundary is still enforced by source shape, tests, and UI strings.
- The StrategySpec replay strategy subscribes/observes quote ticks and does not submit orders.
- Worker context enforcement exists and rejects cross-project mutation when a trusted context is supplied.
- LangChain/LangGraph/EvoMap remain advisory references only in Builder; no source dependency or direct execution coupling was found.
- aiogram-dialog is not present in Builder source, so no Telegram menu/runtime boundary is currently at risk in this repo.

## Segment 1 closure — catalog trust and read-only user replay (2026-05-25)

Closed findings:

- **HIGH-2026-05-25-1:** StrategySpec user-catalog replay no longer writes synthetic data into the selected catalog path. Synthetic data generation is isolated in `strategy_spec_synthetic_catalog_smoke` and evidence is labeled `dataset_source=synthetic_test_kit`.
- **HIGH-2026-05-25-3:** StrategySpec replay and dataset registry paths now require safe-root validation through `CatalogPathPolicy`, reject out-of-root paths, and reject symlink traversal.
- **LOW-2026-05-25-1:** Dataset mismatch diagnostics now report `expected <requested>, got <dataset>`.

New evidence guarantees:

- user replay requires `catalog_root`;
- user replay fails on missing/empty matching quote ticks;
- user replay does not call `TestDataStubs` after the catalog is seeded;
- user replay records catalog manifest checksum and file count;
- worker StrategySpec replay requires the same root.

Verification:

```bash
rtk pytest tests/catalog_datasets/test_catalog_dataset_registry.py tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/backtest_runner/test_worker_integration.py -q
# RED: missing safe-root/synthetic split behavior, then GREEN: Pytest: 13 passed

rtk pytest tests/catalog_datasets tests/backtest_runner -q
# Pytest: 26 passed
```

Remaining from 2026-05-25 list after Segment 1: auth-derived API scope, validated job creation, promotion artifact resolution, registry/replay `quote_ticks` alignment, and no-order output-mode rename.

## Segment 2 closure — auth-derived API scope and validated job creation (2026-05-25)

Closed findings:

- **HIGH-2026-05-25-2:** Strict FastAPI backtest job routes now derive scope from verified bearer auth via `AuthTokenService`; client-supplied body/query scope is ignored in strict mode.
- **MEDIUM-2026-05-25-4:** Strict backtest job creation now validates adapter/instrument/data type/timeframe/market/date range through the instrument registry and validates scoped catalog dataset selection before `BacktestJobService.create_job()`.

New evidence guarantees:

- strict job creation returns `401 auth_required` without context;
- spoofed `user_id`/`project_id` and `catalog_path` in request payloads do not control job scope/path;
- malformed strict payloads return deterministic `422 invalid_backtest_job_request` instead of `KeyError`;
- strict read/cancel ignores spoofed query scope and enforces the auth-derived context;
- job audit payloads persist `data_type`, `timeframe`, and `market_type`.

Verification:

```bash
rtk pytest tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py tests/backtest_jobs -q
# RED: strict auth/context and profile-validation behavior missing, then GREEN: Pytest: 21 passed

rtk pytest tests/auth tests/api tests/backtest_jobs tests/catalog_datasets -q
# Pytest: 59 passed
```

Remaining from 2026-05-25 list after Segment 2: promotion artifact/checksum/scope verification, registry/replay `quote_ticks` alignment, and no-order output-mode rename.

## Segment 3 closure — promotion artifact/checksum/scope verification (2026-05-25)

Closed finding:

- **MEDIUM-2026-05-25-3:** Promotion evidence refs can now be resolved through scoped Builder artifact storage in strict mode. The service verifies Builder ref shape, user/project scope, artifact checksum, and artifact type per evidence key before returning a promotion request.

New evidence guarantees:

- strict shadow promotion rejects legacy unscoped refs;
- strict shadow promotion rejects cross-project refs through `ProjectScopeError`;
- strict shadow promotion rejects checksum-tampered artifacts;
- strict shadow promotion rejects artifact-type mismatches;
- successful strict promotion carries `evidence_checksums` for audit.

Verification:

```bash
rtk pytest tests/promotions/test_shadow_evidence_contract.py -q
# RED: artifact-backed promotion verification missing, then GREEN: Pytest: 16 passed

rtk pytest tests/promotions tests/artifact_store tests/api -q
# Pytest: 65 passed
```

Remaining from 2026-05-25 list after Segment 3: registry/replay `quote_ticks` alignment and no-order output-mode rename.

## Segment 4 closure — registry/replay semantics and no-order output naming (2026-05-25)

Closed findings:

- **MEDIUM-2026-05-25-1:** Market catalog and StrategySpec replay now agree that `BTCUSDT-PERP` supports `quote_ticks`, and registry validation rejects adapter data modes that the instrument itself does not support.
- **MEDIUM-2026-05-25-2:** Builder no-order backtest compile artifacts now use `backtest_signal_observation` instead of `backtest_order_intent`; source-truth docs use `BacktestSignalObservation` wording.

New evidence guarantees:

- `STRATEGY_SPEC_REPLAY_DATA_TYPE == "quote_ticks"` is visible in `InstrumentRegistryService.data_availability()`;
- `InstrumentRegistryService.validate_selection()` accepts the replay-supported quote-tick profile and rejects unsupported instrument-level modes;
- semantic legacy closure tests prevent `backtest_order_intent`/`BacktestOrderIntent` from returning to Builder no-order source truth.

Verification:

```bash
rtk pytest tests/instrument_registry tests/strategy_compiler tests/integration/test_semantic_legacy_closure.py -q
# RED: registry/replay and output-mode drift, then GREEN: Pytest: 9 passed

rtk pytest tests/instrument_registry tests/strategy_compiler tests/api tests/backtest_runner tests/integration/test_semantic_legacy_closure.py -q
# Pytest: 67 passed
```

All named 2026-05-25 HIGH/MEDIUM findings are now closed at repo-contract level. Master reconciliation remains before final readiness reporting.

## Master reconciliation — 2026-05-25 findings closure

### Verdict

**Recommendation:** local repo-contract closure achieved for the named 2026-05-25 HIGH/MEDIUM findings. **Architectural Status:** CLEAR for the implemented Builder repository contracts; WATCH remains for external production rollout items not implemented in this repo (real production token issuer, production catalog ingestion/curation, object-store deployment, and downstream Daedalus promotion consumption).

### Closed items

- **HIGH-2026-05-25-1:** Closed by read-only user-catalog replay and separate synthetic smoke mode.
- **HIGH-2026-05-25-2:** Closed by strict auth-derived FastAPI scope for backtest jobs, with spoofed body/query scope ignored.
- **HIGH-2026-05-25-3:** Closed by catalog safe-root/symlink path policy and removal of user-replay writes.
- **MEDIUM-2026-05-25-1:** Closed by `quote_ticks` registry/replay alignment and instrument-level data-type validation.
- **MEDIUM-2026-05-25-2:** Closed by `backtest_signal_observation` no-order output wording.
- **MEDIUM-2026-05-25-3:** Closed by strict scoped artifact/checksum/type promotion evidence verification.
- **MEDIUM-2026-05-25-4:** Closed by strict profile/dataset validation before backtest job creation.
- **LOW-2026-05-25-1:** Closed by corrected dataset mismatch diagnostics.

### Remaining watch items

- The in-memory `AuthTokenService` is still a local/test issuer; deployment must connect a real token issuer/middleware before production exposure.
- `LocalJsonArtifactStore` is a durable local seam; production object storage remains a deployment concern.
- Catalog data ingestion/curation remains explicit; the repo now fails closed rather than synthesizing user-catalog evidence.
- Legacy non-strict route/helper compatibility remains for fixture/dev tests and must not be cited as production readiness evidence.

Master verification:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 256 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
print(status.message)
assert status.is_match, status.message
PY
# nautilus_trader runtime matches pinned version 1.223.0

cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

## Deep review refresh — 2026-05-25 post-closure inventory review

### Verdict

**Recommendation:** REQUEST CHANGES before production-readiness or promotion-readiness claims. **Architectural Status:** BLOCK for production exposure; CLEAR for no live-order authority. The prior named 2026-05-25 findings remain locally closed, but this inventory found new actionable gaps around evidence semantics, catalog traversal, tenant scoping, and advisory provenance.

### Fresh verification evidence

```bash
git ls-remote --symref https://github.com/nautechsystems/nautilus_trader HEAD
# refs/heads/develop @ 107b9c707cae70bb8ea8580df86235b305754ceb

git ls-remote --symref https://github.com/EvoMap/evolver HEAD
# refs/heads/main @ 3d5386cfe16660de05ef8ff5cbe9749b032e782c

git ls-remote --symref https://github.com/langchain-ai/langchain HEAD
# refs/heads/master @ 33875fde2acf6ffb717915a895638274a6098ec2

git ls-remote --symref https://github.com/langchain-ai/langgraph HEAD
# refs/heads/main @ d1e2ff0561a8b0b09212d0795c9d7b390a5de23a

python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 256 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
print(status.message)
assert status.is_match, status.message
PY
# nautilus_trader runtime matches pinned version 1.223.0

cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

### Findings by severity — 2026-05-25 post-closure review

#### CRITICAL

None found. No Builder source path currently calls `submit_order`, creates `TradeAction`, imports Daedalus execution internals, or adds LangChain/LangGraph/EvoMap/aiogram runtime dependencies.

#### HIGH-2026-05-25-R2-1 — Strict promotion evidence is artifact-backed but not promotion-bound, and missing artifacts can escape as 500s

- **Evidence:** `packages/promotions/service.py:51-58` validates `strategy_version` and `compile_hash` independently, then calls `_validate_evidence()` without passing either value. `packages/promotions/service.py:117-126` verifies artifact ref prefix, scope via the artifact store, artifact type, and checksum, but never checks that artifact payload/metadata belongs to the requested `compile_hash`, `strategy_version`, result, or job. `packages/artifact_store/service.py:65-80` calls `path.read_text()` for the scoped ref and only checksum-validates after the file is read; missing files raise `FileNotFoundError`, which `services/api/routes/promotions.py:30-33` does not catch.
- **Proof:** a strict request using all six valid scoped artifact refs whose payloads contain `compile_hash=old_compile_hash` is accepted for `compile_hash=new_compile_hash`. A strict request using well-shaped but absent scoped refs raises `FileNotFoundError` instead of returning a typed 422.
- **Risk:** stale or unrelated evidence can support a shadow promotion request, and missing evidence can become a route-level server error. This weakens the manual/evidence gate expected before Daedalus shadow/signal-preview handoff.
- **Fix:** bind strict evidence to the request by checking stored artifact payload/metadata for `compile_hash`, `strategy_version`, `result_id`/`job_id`, and evidence role; convert missing/corrupt artifact reads into typed domain `ValueError`s that FastAPI maps to 422.

#### HIGH-2026-05-25-R2-2 — User-catalog manifest hashing follows nested symlinks inside an allowed catalog

- **Evidence:** `packages/catalog_datasets/service.py:16-24` validates that the selected catalog path itself resolves under the configured root and `packages/catalog_datasets/service.py:26-34` rejects symlinks in that path. However, `packages/backtest_runner/strategy_spec_replay.py:248-253` builds the evidence manifest with `catalog_path.rglob("*")`, `file.is_file()`, and `file.read_bytes()`; `Path.is_file()` follows symlinked files.
- **Proof:** creating `catalog/linked_secret.txt -> ../outside_secret.txt` causes `_catalog_manifest(catalog)` to hash `linked_secret.txt` by reading the outside target.
- **Risk:** a user-selected catalog can make Builder read and checksum files outside the catalog tree during replay evidence collection. Even if only hashes are returned, this violates the root/allowlist boundary and can create sensitive-file hash disclosure or denial-of-service paths.
- **Fix:** reject or skip symlinks during manifest traversal; resolve every manifest candidate and require it to remain under the resolved catalog path/root before reading; add regression tests for nested file symlinks and symlinked subdirectories.

#### HIGH-2026-05-25-R2-3 — Tenant/project scoping is incomplete across non-backtest API routes

- **Evidence:** `services/api/fastapi_app.py:69-128` enforces bearer-derived context for backtest jobs and `services/api/fastapi_app.py:166-179` does the same for strict shadow promotion. In contrast, strategy routes (`services/api/fastapi_app.py:142-160`), AI draft/apply (`services/api/fastapi_app.py:162-164`), promotion request (`services/api/fastapi_app.py:181-183`), workflow result/suggestion/lineage routes (`services/api/fastapi_app.py:185-199`), and runtime replay (`services/api/fastapi_app.py:130-136`) do not require auth context. `packages/workflow_spine/repository.py:38-61` returns results and suggestions by IDs only, and `services/api/routes/workflow_results.py:7-18` / `:35-69` expose them without a `UserProjectContext`.
- **Proof:** an in-memory result with `project_id=project_beta` and its AI suggestion are returned by `workflow_result_payload()` and `workflow_result_suggestions_payload()` with no caller context.
- **Risk:** once real multi-tenant repositories are injected, strategy drafts, result metrics, artifact refs, and AI suggestions can leak across users/projects despite the backtest-job strict-scope closure.
- **Fix:** extend `UserProjectContext` enforcement and repository filters to strategies, workflow results, suggestions, lineage status, runtime event replay, and promotion request routes; keep the lightweight `ApiApp` explicitly fixture/dev-only.

#### MEDIUM-2026-05-25-R2-1 — Strict catalog root policy is optional at registry construction

- **Evidence:** `packages/catalog_datasets/service.py:40-42` only creates a `CatalogPathPolicy` when `catalog_root` is supplied. `packages/catalog_datasets/service.py:94-98` returns datasets unchanged when no root policy exists.
- **Proof:** `CatalogDatasetRegistryService().register_dataset()` accepts an absolute `/tmp/outside/catalog` path unchanged.
- **Risk:** strict API code can receive a registry that has scoped datasets but no root policy, then record unallowlisted catalog paths into jobs. Later replay requires `catalog_root`, but job creation has already claimed dataset selection.
- **Fix:** expose/require a root-policy flag for strict selection, make `catalog_root` mandatory for registries used by strict FastAPI/worker paths, or reject absolute paths unless a root has been configured.

#### MEDIUM-2026-05-25-R2-2 — Storage schema and namespace identifiers are not constrained to safe shapes

- **Evidence:** `packages/workflow_spine/storage_config.py:6-13` accepts arbitrary `db_schema` strings and returns them in table names. `packages/workflow_spine/postgres_repository.py:15-19` and `packages/runtime_events/stream.py:9-17` interpolate schema names into SQL identifiers. `packages/workflow_spine/storage_config.py:16-30` accepts Redis namespaces such as `builder:evil` or strings with whitespace.
- **Proof:** `BuilderPostgresConfig(db_schema="builder;drop table x--")` and `BuilderRedisConfig(namespace="builder:evil")` validate successfully.
- **Risk:** configuration mistakes or untrusted deployment input can produce invalid SQL, namespace collisions, or injection-shaped strings in storage infrastructure.
- **Fix:** validate schema/table/namespace identifiers with a strict regex; quote SQL identifiers through the real database driver when Postgres replaces the SQLite test seam; reject namespace separators unless explicitly intended.

#### MEDIUM-2026-05-25-R2-3 — AI apply route accepts blank provenance IDs and route-level audit is ephemeral

- **Evidence:** `services/api/routes/ai_builder.py:11-19` coerces missing `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id` to empty strings. `packages/ai_builder/service.py:61-83` stores those IDs without validation. The API route constructs a fresh `AiBuilderService()` per call, so the default audit store is in-memory and discarded after the request.
- **Proof:** `AiBuilderService().apply_draft_to_strategy(..., ai_thread_id="", improvement_cycle_id="", strategy_lineage_id="", strategy_version_id="")` returns an accepted advisory record with all four IDs blank.
- **Risk:** future LangChain/LangGraph/EvoMap-style advisory loops need durable thread/cycle provenance and explicit human-in-the-loop traceability. Blank IDs make AI suggestions hard to reconcile to Builder strategy lineage.
- **Fix:** require non-empty provenance IDs at the route/model boundary and inject a durable audit store for API usage; keep direct AI provider output advisory-only and validation-gated.

#### MEDIUM-2026-05-25-R2-4 — Legacy fixture artifact refs still appear in externally reachable result/promotion compatibility paths

- **Evidence:** `packages/backtest_runner/result_normalizer.py:35-40` emits unscoped `artifact://backtests/...` refs for fixture results. `services/api/routes/workflow_results.py:21-28` fabricates `artifact://backtests/{result_id}/result.json` for the default dashboard fallback. Legacy promotion tests still exercise unscoped refs through non-strict `ApiApp` paths.
- **Risk:** this is acceptable for fixture/dev compatibility, but external callers can confuse these refs with strict Builder artifacts if the route is not explicitly fixture-scoped or auth-gated.
- **Fix:** label fallback result payloads as fixture/dev evidence, prefer scoped `artifact://builder/...` refs for real stored results, and prevent non-strict refs from reaching production FastAPI routes.

#### LOW-2026-05-25-R2-1 — Frontend/tooling warnings remain in otherwise passing verification

- **Evidence:** `npm test -- --run` still emits the Vite CJS Node API deprecation warning. Playwright's web server still emits a `NO_COLOR` ignored warning because `FORCE_COLOR` is set.
- **Risk:** not a runtime correctness issue, but it keeps verification output noisy and can hide future warnings.
- **Fix:** update Vitest/Vite config to avoid the CJS Node API path and normalize color environment handling in the Playwright web server command.

### Positive findings retained

- No live trading/order-authority source path was found in Builder implementation. `submit_order`/`TradeAction` hits are guard text, negative tests, or explicit `may_submit_order=False` contract fields.
- No executable Builder source imports LangChain, LangGraph, EvoMap/evolver, aiogram, or Telegram.
- `BacktestNode` and `ParquetDataCatalog` are used for the current Nautilus backtest replay seam; no `TradingNode`/`LiveNode` claims are made by Builder code.
- The no-order semantic rename remains closed: `backtest_order_intent` and `BacktestOrderIntent` are absent from Builder no-order source truth except historical closure-plan text and negative tests.

## R2 Segment 1 closure — promotion evidence lineage binding (2026-05-25)

Closed finding:

- **HIGH-2026-05-25-R2-1:** Strict promotion evidence is now artifact-backed **and** promotion-bound. Each strict evidence artifact must resolve in the caller scope, match its evidence role, pass checksum validation, and carry matching `compile_hash` plus `strategy_version` / `strategy_version_id` binding. Missing or invalid artifact envelopes now fail as typed domain errors that route helpers map to 422.

New evidence guarantees:

- wrong-compile artifacts cannot support a new promotion request;
- wrong strategy-version artifacts cannot support a new promotion request;
- missing scoped refs fail as `ValueError("artifact not found: ...")`, not raw `FileNotFoundError`;
- strict FastAPI shadow-promotion fixtures now include lineage metadata in stored artifacts.

Verification:

```bash
rtk pytest tests/promotions/test_shadow_evidence_contract.py -q
# Pytest: 19 passed

rtk pytest tests/promotions tests/artifact_store tests/api/test_fastapi_app.py -q
# Pytest: 37 passed
```

Remaining R2 findings after Segment 1: catalog manifest traversal/root-policy, tenant/project scoping across non-backtest routes, storage identifier validation, AI provenance/audit durability, fixture artifact exposure, and frontend warning cleanup.

## R2 Segment 2 closure — catalog traversal and root-policy enforcement (2026-05-25)

Closed findings:

- **HIGH-2026-05-25-R2-2:** User-catalog manifest hashing no longer follows nested symlinks inside selected catalogs. Symlinked files and directories are rejected before read, and each resolved manifest candidate must remain under the selected catalog path.
- **MEDIUM-2026-05-25-R2-1:** Strict catalog dataset use now has an executable root-policy requirement. Registries can still be used in fixture/dev compatibility mode without a root, but strict registration/selection and strict backtest job creation fail closed unless `catalog_root` was configured.

New evidence guarantees:

- nested symlinked files cannot be hashed as catalog evidence;
- symlinked directories inside catalogs are rejected;
- strict backtest job creation returns `422 invalid_backtest_job_request` for unrooted catalog registries;
- compatibility no-root registry behavior remains limited to non-strict/dev paths.

Verification:

```bash
rtk pytest tests/catalog_datasets/test_catalog_dataset_registry.py tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/api/test_backtest_job_routes.py -q
# Pytest: 22 passed

rtk pytest tests/catalog_datasets tests/backtest_runner tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py -q
# Pytest: 46 passed
```

Remaining R2 findings after Segment 2: tenant/project scoping across non-backtest routes, storage identifier validation, AI provenance/audit durability, fixture artifact exposure, and frontend warning cleanup.

## R2 Segment 3 closure — tenant/project scoping across FastAPI routes (2026-05-25)

Closed finding:

- **HIGH-2026-05-25-R2-3:** Strict FastAPI auth-derived scope now applies beyond backtest jobs. Strategy routes, workflow result/suggestion/lineage routes, runtime-event replay, AI draft, and promotion-request routes require bearer auth in the FastAPI bootstrap. Strategy records created through strict routes are user/project-owned, and workflow result/suggestion reads enforce project boundaries.

New evidence guarantees:

- missing auth returns `401 auth_required` for production-facing non-backtest FastAPI routes;
- strategies created in `project_alpha` are not visible/readable from `project_beta` strict context;
- workflow result/suggestion/lineage reads deny cross-project access with 403;
- `ApiApp` compatibility remains explicit fixture/dev behavior and is not production authorization evidence.

Verification:

```bash
rtk pytest tests/api/test_fastapi_app.py -q
# Pytest: 9 passed

rtk pytest tests/api tests/workflow_spine tests/strategy_spec tests/runtime_events -q
# Pytest: 98 passed
```

Remaining R2 findings after Segment 3: storage identifier validation, AI provenance/audit durability, fixture artifact exposure, and frontend warning cleanup.

## R2 Segment 4 closure — storage identifiers and AI provenance/audit (2026-05-25)

Closed findings:

- **MEDIUM-2026-05-25-R2-2:** Builder-owned storage schema/table and Redis namespace identifiers now require safe identifier shapes before use in SQL table names or stream namespaces.
- **MEDIUM-2026-05-25-R2-3:** AI draft apply now rejects blank `ai_thread_id`, `improvement_cycle_id`, `strategy_lineage_id`, and `strategy_version_id`. FastAPI AI apply uses a reused app-level service with an injectable audit store, so route-level apply records are not discarded after each request.

New evidence guarantees:

- `builder;drop table x--`, `builder:evil`, and whitespace namespace shapes are rejected;
- runtime durable stream schema names are validated before SQL construction;
- AI apply cannot record blank provenance IDs;
- FastAPI `/api/ai-builder/apply` persists apply audit records through an injected `SqliteAiDraftAuditStore`.

Verification:

```bash
rtk pytest tests/workflow_spine/test_storage_config.py tests/runtime_events/test_durable_stream.py tests/ai_builder/test_persistent_audit_store.py tests/api/test_fastapi_app.py -q
# Pytest: 24 passed

rtk pytest tests/workflow_spine tests/runtime_events tests/ai_builder tests/api -q
# Pytest: 101 passed
```

Remaining R2 findings after Segment 4: fixture artifact exposure and frontend warning cleanup.

## R2 Segment 5 closure — fixture evidence exposure and frontend warnings (2026-05-25)

Closed findings:

- **MEDIUM-2026-05-25-R2-4:** Fixture/dev compatibility artifact refs are now explicitly labeled and moved to `fixture://` in fixture result normalization and dashboard fallback payloads. Strict FastAPI result routes do not expose the fallback as a production repository result.
- **LOW-2026-05-25-R2-1:** Frontend test config now uses ESM Vitest config (`vitest.config.mts`) and Playwright's web server command unsets `FORCE_COLOR`/`NO_COLOR` to avoid the observed warnings.

New evidence guarantees:

- fixture backtest result refs carry `fixture_evidence_only=true`;
- dashboard fallback payloads carry `evidence_mode=fixture_dev_only` and `fixture_evidence_only=true`;
- strict FastAPI `/api/results/res_001` returns 404 without a repository-owned result;
- Vitest runs through the ESM config without the Vite CJS warning in the targeted verification run.

Verification:

```bash
rtk pytest tests/backtest_runner/test_result_normalizer.py tests/backtest_runner/test_runner_dummy_data.py tests/api/test_workflow_results.py tests/api/test_fastapi_app.py tests/web/test_frontend_infrastructure.py tests/integration/test_browser_e2e_contract.py -q
# Pytest: 29 passed

rtk pytest tests/backtest_runner tests/api tests/web tests/integration -q
# Pytest: 121 passed

cd apps/web && npm test -- --run
# Vitest: 12 passed; no Vite CJS warning observed
```

All named R2 findings are now closed at repo-contract level. Master reconciliation remains before final readiness reporting.

## Master reconciliation — 2026-05-25 R2 findings closure

### Verdict

**Recommendation:** local repo-contract closure achieved for all named R2 findings. **Architectural Status:** CLEAR for the implemented Builder contracts and no-live-order boundary. **WATCH** remains for external production rollout items that are outside this repo change: real token issuer/middleware, object-store deployment, catalog ingestion operations, and downstream Daedalus promotion consumption.

### Closed R2 findings

- **HIGH-2026-05-25-R2-1:** Closed by lineage-bound strict promotion evidence and typed artifact errors.
- **HIGH-2026-05-25-R2-2:** Closed by symlink-safe catalog manifest traversal.
- **HIGH-2026-05-25-R2-3:** Closed by auth-derived FastAPI scoping across non-backtest routes.
- **MEDIUM-2026-05-25-R2-1:** Closed by executable strict catalog root-policy guards.
- **MEDIUM-2026-05-25-R2-2:** Closed by safe SQL schema/table and Redis namespace validation.
- **MEDIUM-2026-05-25-R2-3:** Closed by non-empty AI apply provenance and reusable/injected FastAPI audit storage.
- **MEDIUM-2026-05-25-R2-4:** Closed by explicit fixture-only evidence labels and production FastAPI fallback denial.
- **LOW-2026-05-25-R2-1:** Closed by ESM Vitest config and Playwright color-env cleanup.

### Master verification

```bash
python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 278 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
print(status.message)
assert status.is_match, status.message
PY
# nautilus_trader runtime matches pinned version 1.223.0

cd apps/web && npm run typecheck && npm test -- --run && npm run build && npm run test:e2e
# typecheck passed; Vitest: 12 passed with no Vite CJS warning observed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

### Remaining watch items

- Production auth still depends on integrating a real issuer/middleware with `AuthTokenService`'s current in-memory seam.
- Production artifact storage remains a deployment concern beyond `LocalJsonArtifactStore`.
- Catalog data ingestion/curation remains explicit; Builder now fails closed rather than proving data it does not own.
- Daedalus consumption of strict Builder promotion artifacts remains an external integration step.

## Post-implementation code review — 2026-05-25 R2 closure

**Files reviewed:** implementation diff across promotion/artifact, catalog/backtest, FastAPI scope, workflow/strategy repositories, storage config, AI builder, workflow result fallback, frontend verification config, and regression tests.
**Architectural Status:** CLEAR.
**Recommendation:** APPROVE for local repo-contract closure.

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None open after the implementation pass.

### LOW / WATCH

- Production rollout still needs real auth middleware/issuer, object storage, catalog data curation, and Daedalus-side consumption of strict promotion artifacts. These are deployment/integration watch items, not merge blockers for this repo-contract closure.

### Review evidence

```bash
grep -R "submit_order\|TradeAction\|Daedalus\|langchain\|langgraph\|EvoMap\|evolver\|aiogram\|telegram" -n packages services apps/web --exclude-dir=node_modules --exclude-dir=.next --exclude='*.pyc'
# Hits are guard text, negative tests, false-authority fields, or docs only; no live-order/Daedalus/AI-runtime dependency path was introduced.

python3 -m compileall -q packages services tests
rtk pytest tests -q
# Pytest: 278 passed

git diff --check
# passed
```

## Closure update — Segment UI-1 API JSON/proxy hardening

**Status:** CLOSED for the reported `JSON.parse: unexpected character at line 1 column 1` class of frontend failures.

Resolution:

- `apiFetch()` no longer unconditionally calls `response.json()`.
- Non-JSON API/proxy responses now produce an `ApiError` naming the status, URL, received content type, and VM/API base URL guidance.
- Empty error bodies and network failures no longer leak low-level JSON parser errors.

Evidence:

```bash
cd apps/web && npm test -- --run lib/api.test.ts
# Result: 5 passed
```

## Closure update — Segment UI-2 no-dependency polished shell

**Status:** CLOSED for the reported VM symptom where the app rendered as mostly plain text.

Resolution:

- Root layout imports `apps/web/app/globals.css`.
- The home shell now renders a hero, workflow navigation, dashboard grid, cards, panels, terminal card, form grids, and status badges.
- Styling is dependency-free; no Tailwind, MUI, Chakra, or UI framework dependency was added.
- Existing copy still reinforces Builder-only draft/advisory/observational boundaries and does not introduce live order authority.

Evidence:

```bash
rtk pytest tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py -q
# Result: 9 passed
```

## Master reconciliation — frontend staging findings

**Final status:** REQUESTED FINDINGS CLOSED LOCALLY.

Closed findings:

- API JSON failure: `apiFetch()` now handles non-JSON, empty, malformed, and network responses with Builder-specific diagnostics.
- Plain text UI: root layout imports global CSS and the app shell/components now render with dashboard, card, panel, form, terminal, and status-badge styling.
- Frontend contract checks: global CSS import, no-dependency visual shell, and API error handling are covered by tests.

Verification evidence:

```bash
rtk pytest tests/web tests/integration -q
# Result: 54 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Result: 271 passed

cd apps/web && npm run typecheck && npm test && npm run build
# Result: typecheck passed; Vitest 17 passed; Next build passed
```

Residual deployment check: VM02 should set `BUILDER_API_BASE_URL` for server-side rendering and/or `NEXT_PUBLIC_API_BASE_URL` for browser direct API calls to the reachable API origin. If routes still return HTML/text, the new diagnostics should identify the exact URL/content type.

## Post-implementation code review — 2026-05-25 frontend UI/API hardening

**Files reviewed:** frontend API boundary, Next app shell/routes, strategy/market/results/promotions UI components, web contract tests, and review artifacts.
**Architectural Status:** CLEAR.
**Recommendation:** APPROVE for local VM-staging UI/API hardening.

### CRITICAL

None.

### HIGH

None.

### MEDIUM

None open after review. A review-discovered JSON-error nuance was fixed during this pass: JSON error payloads are preserved and no longer mislabeled as empty response bodies.

### LOW / WATCH

- Full browser E2E remains a deployment/provisioning watch item; this pass verified typecheck, Vitest, Next production build, and Python contract suites, but did not rerun Playwright after removing `.next` artifacts.
- VM02 still needs correct `BUILDER_API_BASE_URL` / `NEXT_PUBLIC_API_BASE_URL` environment wiring for its network topology.

### Review evidence

```bash
rg -n "submit_order|TradeAction|tailwindcss|@mui/material|@chakra-ui/react|response\.json\(" apps/web tests/web
# Hits are negative tests, false-authority display fields, or e2e guard text; no new live authority or UI framework dependency was introduced.

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Result: 271 passed

cd apps/web && npm run typecheck && npm test && npm run build
# Result: typecheck passed; Vitest 17 passed; Next build passed

git diff --check
# passed
```

## Closure update — Segment DEP-1 PyYAML test-extra closure

**Status:** CLOSED for the VM02 `ModuleNotFoundError: No module named 'yaml'` failures observed after `uv sync --extra test`.

### Finding

- **MEDIUM-DEP-2026-05-25-1:** The test environment was not reproducible because StrategySpec YAML example tests import `yaml`, and API contract tests indirectly import that module via `make_valid_spec`, but the repo test extra/lockfile did not declare PyYAML.

### Resolution

- Added `PyYAML>=6.0` to `[project.optional-dependencies].test` in `pyproject.toml`.
- Regenerated `uv.lock`, locking `pyyaml==6.0.3`.
- Added an operability baseline assertion that the test extra declares PyYAML so future clean VM/CI syncs do not regress.

### Review verdict

**Recommendation:** APPROVE. **Architectural Status:** CLEAR.

The change is test/deployment-environment scoped only. It does not add runtime YAML parsing, live order authority, Daedalus coupling, LangChain/LangGraph/EvoMap runtime dependencies, or frontend UI dependencies.

### Evidence

```bash
uv sync --extra test
# Installed pyyaml==6.0.3

rtk pytest tests/integration/test_operability_baseline.py::test_python_project_declares_runtime_and_test_dependencies tests/api/test_fastapi_app.py::test_fastapi_bootstrap_reuses_strategy_repository_helpers tests/api/test_fastapi_app.py::test_fastapi_strategy_routes_require_auth_and_filter_by_project tests/strategy_spec/test_schema_valid.py::test_example_yaml_loads_as_valid_strategy_spec -q
# Pytest: 4 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 271 passed

cd apps/web && npm run typecheck && npm test && npm run build
# typecheck passed; Vitest: 17 passed; Next build passed
```

## Planned closure — Segment AI-2 OpenAI-compatible StrategySpec draft provider

**Status:** IN PROGRESS on 2026-05-25.

### Finding

- **MEDIUM-AI-2026-05-25-2:** Builder can validate AI-shaped drafts, but there is no real OpenAI-compatible draft provider behind `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL`. The app therefore cannot yet perform the intended user-prompt-to-StrategySpec workflow except through the deterministic advisory scaffold.

### Required closure criteria

- Provider is activated only when the three env vars are present; otherwise existing deterministic advisory drafting remains the default.
- Provider sends an OpenAI-compatible chat-completions request and accepts only a JSON object StrategySpec from the model content.
- `AiBuilderService` still runs `validate_strategy_spec()` before `accepted=True`.
- Audit records include the user prompt and response metadata, but never the API key or full credential-bearing request headers.
- Forbidden `submit_order`, `TradeAction`, and credential references remain rejected.

## Closure update — Segment AI-2 OpenAI-compatible StrategySpec draft provider

**Status:** CLOSED on 2026-05-25.

### Resolution

- Added an optional OpenAI-compatible chat-completions draft provider activated by complete `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` env configuration.
- Kept deterministic advisory drafting as the fallback when env is incomplete.
- The provider requests JSON output, parses only JSON-object model content, and returns that object to the existing Builder validation gate.
- `AiBuilderService` now audits prompt text, provider identity, provider response metadata, validation errors, and spec payloads without persisting API keys.
- Prompt inputs mentioning credentials are rejected before audit persistence; model outputs containing `api_key`, `submit_order`, `TradeAction`, or other forbidden references remain rejected by `validate_strategy_spec()`.
- FastAPI app construction now wires the service through `AiBuilderService.from_env()` while preserving injected audit stores.

### Review verdict

**Recommendation:** APPROVE. **Architectural Status:** CLEAR.

The diff is narrow to the AI draft provider seam, FastAPI bootstrap wiring, tests, and guard docs. It does not add live order authority, Daedalus execution coupling, OpenAI SDK dependency, LangChain/LangGraph/EvoMap runtime dependency, automatic promotion, or frontend dependency changes.

### Evidence

```bash
rtk pytest tests/ai_builder/test_openai_compatible_provider.py -q
# Pytest: 7 passed

rtk pytest tests/ai_builder -q
# Pytest: 17 passed

rtk pytest tests/api/test_fastapi_app.py tests/api/test_route_mounts.py -q
# Pytest: 18 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 278 passed

cd apps/web && npm run typecheck && npm test && npm run build
# typecheck passed; Vitest: 17 passed; Next build passed

git diff --check
# passed
```

## Closure update — Segment VM-API-1 live web/API proxy and CONFIG-1 LLM config UI

**Status:** CLOSED locally on 2026-05-25.

### Findings

- **HIGH-UI-2026-05-25-1:** VM02 browser traffic through `http://192.168.4.82:3000/api/*` returned 500s even though direct API calls to `http://192.168.4.82:8000/api/*` returned JSON. The Next rewrite config only read `NEXT_PUBLIC_API_BASE_URL`, while the documented VM guard says server-side proxying should use `BUILDER_API_BASE_URL` when the API is reachable from the web process.
- **MEDIUM-UX-2026-05-25-1:** Operators had no UI-based configuration section for AI/LLM provider and model-role settings after the OpenAI-compatible provider was added.

### Resolution

- Next rewrites now prefer `BUILDER_API_BASE_URL` before `NEXT_PUBLIC_API_BASE_URL`, preserving browser-direct mode as optional and making VM server-side proxying explicit.
- Added `/config` with multiple tabs: Providers, Models, Guardrails, and Audit.
- The config UI shows OpenAI-compatible/local/offline provider choices, model-role fields, draft JSON preview, and audit/guardrail status without collecting API keys.
- E2E-visible guard text for backtest cancel and promotion manual approval was made contiguous so Playwright can assert the no-live-authority journey reliably.

### Review verdict

**Recommendation:** APPROVE. **Architectural Status:** CLEAR for the repo diff.

The change is frontend/proxy/config-surface scoped. It does not add backend secret persistence, live trading authority, Daedalus coupling, LangChain/LangGraph/EvoMap runtime dependency, UI framework dependency, or automatic promotion.

### Evidence

```bash
rtk pytest tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py tests/web/test_frontend_data_wiring.py -q
# Pytest: 10 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 280 passed

cd apps/web && npm run typecheck && npm test && BUILDER_API_BASE_URL=http://192.168.4.82:8000 npm run build && npm run test:e2e
# typecheck passed; Vitest: 18 passed; Next build passed; Playwright: 4 passed

BUILDER_API_BASE_URL=http://192.168.4.82:8000 npm run start -- --hostname 127.0.0.1 --port 3100
curl -i http://127.0.0.1:3100/api/adapters
# HTTP/1.1 200 OK; JSON adapter list
curl -i http://127.0.0.1:3100/api/strategies
# HTTP/1.1 200 OK; [] JSON

git diff --check
# passed
```

### Deployment note

The live VM02 web service still needs to pull this commit, rebuild, set `BUILDER_API_BASE_URL=http://192.168.4.82:8000` for `next build/start`, and restart before the remote `:3000/api/*` endpoints reflect the local fix.

## Closure update — Segment UI-ANTD-1 Ant Design operator console

**Status:** CLOSED locally on 2026-05-26.

### Finding

- **MEDIUM-UX-2026-05-26-1:** The web UI was still scaffold-like and substantially less user-friendly than mature trading/admin frontends such as QuantDinger / QuantDinger-Vue. The custom CSS shell proved contracts, but it did not provide a polished operator-console experience.

### Resolution

- Added the approved React pre-built UI stack: `antd` and `@ant-design/icons`.
- Rebuilt the app around an AntD operator shell with sidebar navigation, top status bar, backend/proxy status affordances, and always-visible advisory-only/no-live-authority warnings.
- Added a richer AntD dashboard with KPI cards, AI → StrategySpec → Validate → Backtest → Manual promotion steps, visible workflow cards, and tabbed operator workspaces.
- Reworked the LLM config section into AntD tabs/forms/cards/alerts/badges while preserving backend-only secret handling.
- Kept the frontend React/Next-based; no Vue migration and no QuantDinger code copy.

### Review verdict

**Recommendation:** APPROVE with bundle/audit watch. **Architectural Status:** CLEAR for this frontend segment.

The change is UI-layer scoped. It does not add live order authority, Daedalus execution coupling, backend secret persistence, automatic promotion, LangChain/LangGraph/EvoMap runtime dependency, or browser-side provider keys.

### Evidence

```bash
rtk pytest tests/web/test_antd_operator_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py -q
# Pytest: 15 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 18 passed; Next build passed; Playwright: 4 passed
```

### Remaining watch items

- `npm audit --omit=dev --audit-level=moderate` reports a moderate `next`/`postcss` advisory and suggests a breaking `npm audit fix --force` path that would downgrade/replace Next; this segment did not apply that unsafe fix.
- AntD increased first-load JS size (`/` around 249 kB, `/config` around 280 kB in the verified build); future charting should be lazy-loaded or route-split.

### Final reconciliation refresh — Segment UI-ANTD-1

**Status:** READY TO COMMIT/PUSH after fresh local verification on 2026-05-26.

- Focused AntD/operator UI contracts: 15 passed.
- Full targeted Python contract suite: 284 passed after `compileall`.
- Frontend gates: TypeScript, Vitest, Next production build, and Playwright E2E passed.
- Guardrail grep remains expected-only: live-order, credential, LangChain/LangGraph/EvoMap, and Vue terms appear in guard docs, negative tests, explicit false authority fields, or approved dependency-denial tests; no runtime authority path was added.
- `npm audit --omit=dev --audit-level=high` exits 0. The remaining Next/PostCSS advisory is moderate and still points to a breaking `npm audit fix --force`; this segment intentionally does not apply that unsafe force-fix.
