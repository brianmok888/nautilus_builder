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
