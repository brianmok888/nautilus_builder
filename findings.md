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

## Closure update — Segment AI-UI-1 prompt-to-StrategySpec UI and compact workflow

**Status:** CLOSED locally on 2026-05-26 pending final verification/commit.

### Finding

- **HIGH-UX-2026-05-26-1:** Natural-language strategy input was not implemented in the web UI. The backend AI draft/apply endpoints existed, but `AiStrategyCopilot` only displayed placeholder copy and an inert Apply button.
- **MEDIUM-UX-2026-05-26-2:** The dashboard workflow was visually overwhelming; too many surfaces had equal weight before the user reached the actual AI → StrategySpec path.

### Resolution

- Added a real prompt-to-StrategySpec UI with `Input.TextArea`, Generate StrategySpec, accepted/rejected status, validation errors, JSON preview, and accepted-only Apply to Builder.
- Defaulted the main dashboard workspace to the AI prompt tab and made downstream tabs numbered: AI prompt → StrategySpec → Runtime → Promotion.
- Reduced AntD density through `componentSize="small"`, smaller theme tokens, smaller card bodies, compact steps, and compact spec preview styling.

### Review verdict

**Recommendation:** APPROVE after final verification. **Architectural Status:** CLEAR for this frontend segment.

The change is UI/API-client scoped. It does not add live order authority, Daedalus execution coupling, automatic backtest, automatic promotion, browser-side LLM secrets, or backend policy bypasses.

### Evidence so far

```bash
cd apps/web && npm test -- --run components/ai-builder/AiStrategyCopilot.test.tsx
# 1 file / 2 tests passed

pytest tests/web/test_ai_copilot_frontend.py -q
# 3 passed
```

### Reference review addendum — QuantDinger / QuantDinger-Vue

**Checked:** 2026-05-26.

The reference project confirms the direction: users need a product information architecture, not a raw contract-demo screen. QuantDinger-Vue divides the frontend into analysis/research, strategy/IDE/backtesting, execution/portfolio, and user/platform areas, with source folders for API modules, layouts, router, store, utilities, and page-level views.

For Nautilus Builder, the useful carry-over is the page/workflow organization and compact operator layout. The unsafe carry-over is execution UX: QuickTradePanel, exchange account binding, portfolio execution, and live trading output do not belong in Builder. Builder should keep a narrower prompt-first workflow: AI prompt → StrategySpec draft → validation → backtest evidence → manual promotion.

This segment implements the first concrete step of that mapping by making AI prompt input the default workspace and shrinking the dashboard density.

### Final verification — Segment AI-UI-1

```bash
git diff --check
# passed

pytest tests/web/test_ai_copilot_frontend.py -q
# 3 passed

cd apps/web && npm test -- --run components/ai-builder/AiStrategyCopilot.test.tsx
# 1 file / 2 tests passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 285 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 11 files / 20 tests passed; Next build passed; Playwright: 4 passed

cd apps/web && npm audit --omit=dev --audit-level=high
# exit 0; only moderate Next/PostCSS advisory remains with a breaking force-fix path
```

## Implementation queue update — PMBT/QuantDinger adoption segment BT-1

**Started:** 2026-05-26 10:05:52Z

The previously discussed PMBT adoption is being decomposed into safe Builder-owned segments. BT-1 targets high-leverage backend contracts first: run manifests, artifact refs, report summaries, and dataset provenance. This closes part of the gap between the current fixture/injected runner and a user-friendly Backtest Center without adding live execution authority or copying external project code.

Risk boundary: this segment does **not** implement optimizer execution, arbitrary strategy module loading, direct data downloads, or live/paper trading controls.

## Closure update — PMBT/QuantDinger adoption slice

**Completed:** 2026-05-26 10:27:08Z

Closed or reduced findings:

- Backtest runner contracts are no longer implicit fixture-only dictionaries; they now have explicit run request/manifest/report models.
- Artifact/report policy now has a strict typed surface requiring safe URI scope, checksum, and media type.
- Dataset source/cache modes are inventory-first and policy-checked before later worker/data-source expansion.
- Strategy module selection now has a metadata-only allowlisted registry rather than arbitrary import execution.
- Optimizer/research work now has an offline-only job model with manual promotion and no live order authority.
- Result UI can render report sections/chart metadata without introducing a chart dependency or execution controls.

Residual risk:

- Worker persistence still uses existing result artifact refs; future work should persist `BacktestRunManifest` alongside actual artifacts once non-fixture outputs are durable.
- `research_jobs` is a backend contract package only in this slice; API and UI wiring are still future work.
- Chart payloads are metadata-only until real equity/drawdown series storage is added.

## Closure update — Segment PLATFORM-1 standalone Builder control-plane schema

**Status:** CLOSED locally on 2026-05-26 pending final verification/commit.

### Finding

- **HIGH-ARCH-2026-05-26-1:** Builder was still architecturally framed as a companion to Nautilus-Daedalus for live/paper/control-plane responsibilities. That conflicts with the new product direction: Nautilus Builder should be the standalone open-source AI strategy builder + NautilusTrader platform, while ND becomes private reference only.
- **HIGH-DATA-2026-05-26-1:** The existing Builder DB migration only stored a minimal workflow spine (`strategy_identities`, `strategy_versions`, `test_jobs`, `test_results`, `ai_suggestions`, `runtime_events`). It could not durably model StrategySpec lineage, dataset manifests, backtest artifacts, research/optimizer trials, AI improvement cycles, promotion packages, runtime profiles, paper/live runs, execution reports, or Telegram delivery.

### Resolution

- Added `docs/superpowers/specs/2026-05-26-standalone-builder-platform-design.md` as the clean-room standalone platform design.
- Added `infra/migrations/002_builder_standalone_platform.sql` under only the `builder` schema; no ND/private schema names are created.
- Added schema coverage for Builder-owned AI, data, backtest, research, promotion, paper/live runtime, execution report, Telegram notification, and enriched runtime-event records.
- Live and execution authority remain disabled by default and require explicit mode/profile/risk/reconciliation/activation/checksum fields before they can be represented.
- Added `tests/infrastructure/test_builder_standalone_platform_migration.py` to lock the migration inventory and safety gates.
- Updated `doc/nautilus_builder_hardguards.md` to express the new mode-gated standalone Builder authority model while preserving no-live-authority for existing authoring/backtest/research/UI surfaces.

### Review verdict

**Recommendation:** APPROVE for PLATFORM-1 after full verification. **Architectural Status:** CLEAR for the schema/design segment.

This segment is control-plane schema and documentation only. It does not add order-submission code, exchange credentials, broker API calls, browser-side secrets, LangChain/LangGraph/EvoMap runtime dependencies, or automatic promotion.

### TDD evidence so far

```bash
rtk pytest tests/infrastructure/test_builder_standalone_platform_migration.py -q
# RED before migration: 0 passed, 6 failed because infra/migrations/002_builder_standalone_platform.sql did not exist
# GREEN after migration: 6 passed
```

### Residual risk

- No live/paper service code is implemented yet; future segments must add services and tests before any runtime claim.
- The migration is SQL-contract tested but not applied against a running PostgreSQL instance in this segment unless final environment verification adds one.
- Older docs still contain Daedalus-companion history; future doc cleanup should rewrite those sections into standalone Builder wording once code catches up.

### Final verification — Segment PLATFORM-1

```bash
git diff --check
# passed

rtk pytest tests/infrastructure/test_builder_standalone_platform_migration.py -q
# 6 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 316 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 11 files / 21 tests passed; Next build passed; Playwright 4 passed

cd apps/web && npm audit --omit=dev --audit-level=high
# exited 0; existing moderate Next/PostCSS advisory remains with a breaking force-fix path
```

Additional migration syntax verification:

```bash
docker run postgres:16-alpine ...
psql -U postgres -d nautilus_builder -v ON_ERROR_STOP=1 -f /tmp/001.sql -f /tmp/002.sql
# 001 + 002 migrations applied successfully in a disposable PostgreSQL 16 container
```

### Code-review reconciliation — Segment PLATFORM-1

**Recommendation:** APPROVE. **Architectural Status:** CLEAR.

Review notes:

- Migration is Builder-owned and creates only `builder.*` schema objects.
- Dangerous runtime authority defaults false and is constrained by profile/run/action activation predicates.
- Artifact scope now matches the existing `BacktestArtifactRef` contract (`project_artifact` / `fixture_dev_only`) and requires Builder artifact or fixture URI prefixes.
- No service/API/frontend code path was added for live order submission.
- Remaining risk is intentionally deferred: future services must add FK/application-level enforcement when paper/live runtime code is introduced.

## Closure update — Segment EXEC-1 standalone execution lane scaffold

**Status:** CLOSED locally on 2026-05-26 pending final verification/commit.

### Finding

- **HIGH-ARCH-2026-05-26-2:** Builder had platform tables for future paper/live execution, but no package/API/worker contract for running execution independently from strategy authoring/research lanes. Without an explicit lane queue, strategy code could become coupled to order lifecycle and block ongoing strategy iteration.

### Resolution

- Added strict execution-lane contracts and service in `packages/execution_lane`.
- Added independent execution-lane API routes for status, profile registration, and command enqueueing.
- Added backend worker scaffold with no strategy imports.
- Added `003_builder_execution_lane.sql` for durable lane runs, commands, reports, and heartbeats.
- Added tests proving paper command claim/report flow, idempotency, secret/coupling rejection, live-gate rejection, live-gate acceptance, API policy reuse, worker import separation, and migration inventory.

### Review verdict

**Recommendation:** APPROVE for EXEC-1 after full verification. **Architectural Status:** CLEAR for the scaffold/contract segment.

This segment decouples execution-lane contracts without adding real broker order submission, browser credentials, exchange API calls, or a Nautilus live-node process. Live command authority is representable only behind explicit risk/reconciliation/credential/approval gates.

### TDD evidence so far

```bash
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/infrastructure/test_builder_execution_lane_migration.py -q
# RED before implementation: package/migration missing
# GREEN after implementation: 10 passed
```

### Final verification — Segment EXEC-1

```bash
git diff --check
# passed

rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/infrastructure/test_builder_execution_lane_migration.py -q
# 10 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 326 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 11 files / 21 tests passed; Next build passed; Playwright 4 passed

cd apps/web && npm audit --omit=dev --audit-level=high
# exited 0; existing moderate Next/PostCSS advisory remains with a breaking force-fix path

psql -U postgres -d nautilus_builder -v ON_ERROR_STOP=1 -f /tmp/001.sql -f /tmp/002.sql -f /tmp/003.sql
# migrations 001 + 002 + 003 applied successfully in disposable PostgreSQL 16 container
```

### Code-review reconciliation — Segment EXEC-1

**Recommendation:** APPROVE. **Architectural Status:** CLEAR.

Review notes:

- Execution lane now has a separate package, API contract, worker scaffold, migration, and tests.
- Strategy-lane coupling is explicitly rejected at model level and checked on the worker scaffold.
- Paper lane remains simulated/no-order. Live command authority remains gated and disabled unless both profile and command meet risk/reconciliation/credential/approval predicates.
- No Nautilus live-node or broker adapter submission code was added; that remains a later implementation segment with ExecTester/reconciliation evidence.

Worker smoke:

```bash
python3 -m services.workers.execution_lane_worker --runtime-profile-id rp_paper_001 --worker-id exec_worker_smoke
# emitted execution_lane JSON with strategy_lane_coupled=false and may_submit_order=false
```

## Closure update — Segment EXEC-2 venue-bound execution lane and UI feature flags

**Status:** CLOSED locally on 2026-05-26 after full verification.

### Finding

- **HIGH-ARCH-2026-05-26-3:** Execution lane commands could be queued independently, but the lane was not yet bound to a venue/adapter/account. That left a future risk that execution workers could accept commands for the wrong Nautilus venue or that UI controls could appear without a backend-selected venue.
- **MEDIUM-UX-2026-05-26-4:** The web app had no explicit feature-flag surface for showing/hiding execution-lane controls. Operators needed a visible config panel that explains which execution features are enabled while still blocking browser-side credentials.

### Resolution

- Added adapter/venue/account fields to execution profiles, commands, reports, status snapshots, route tests, and focused policy tests.
- Enforced profile/command adapter and venue matching before command enqueueing.
- Enforced enabled-profile venue binding and live-control authority gates.
- Added migration `004_builder_execution_lane_venue_ui.sql` with columns, constraints, and indexes for venue binding and UI flags.
- Added frontend `ExecutionLaneFeaturePanel` and `fetchExecutionLaneStatus()` typed helper. The panel displays venue bindings and backend UI flags but intentionally contains no password/API-key fields.

### Review verdict

**Recommendation:** APPROVE for EXEC-2. **Architectural Status:** CLEAR for venue binding and UI feature visibility.

The change links execution lanes to approved adapter venues and gives the UI a read-only feature-control surface. It does not add real broker submission, browser credential capture, exchange account setup, automatic promotion, or strategy-lane coupling.

### Evidence

```bash
rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/web/test_execution_lane_ui_contract.py tests/infrastructure/test_builder_execution_lane_venue_migration.py -q
# Pytest: 17 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 334 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 21 tests passed; Next build passed; Playwright 4 passed

psql -U postgres -d nautilus_builder -v ON_ERROR_STOP=1 -f /tmp/001.sql -f /tmp/002.sql -f /tmp/003.sql -f /tmp/004.sql
# migration chain applied successfully in disposable PostgreSQL 16
```

### Remaining watch items

- Real Nautilus `LiveNode`/adapter submission is still a future segment and must require ExecTester/reconciliation evidence before live-readiness claims.
- The `/config` execution panel currently reads backend status; future mutation APIs for toggling flags must remain backend-auth-derived and must not accept browser-supplied credentials or live authority.
- `npm audit --omit=dev --audit-level=moderate` still reports the known moderate Next/PostCSS advisory with a breaking `npm audit fix --force` path; this segment kept the high-severity gate clean and did not apply the unsafe force-fix.

## Closure update — Segment UI-SECTIONS-1 sectioned operator UI

**Status:** CLOSED locally on 2026-05-26 after full verification, pending commit/push.

### Finding

- **MEDIUM-UX-2026-05-26-5:** The frontend operator workflow was too scaffold-like and overwhelming. Users needed a smaller, clearer QuantDinger-inspired command-center flow where natural-language strategy intent leads to StrategySpec, market setup, backtest evidence, review, and execution-lane visibility.
- **MEDIUM-UX-2026-05-26-6:** Execution-lane and promotion information was mixed into the dashboard in developer-token form. That made the UI less user-friendly and risked blurring the dedicated manual-promotion/evidence surfaces.

### Resolution

- Added TDD contract coverage for all seven requested sections and a dashboard render test before implementation.
- Reworked the dashboard into a compact command center with “Describe strategy,” the full AI-to-execution-lane workflow trail, prompt-first CTAs, and execution-lane status copy.
- Added explicit AI Builder, StrategySpec Editor, Market + Dataset Setup, Backtest Center, Results / Research, and Execution Lane / Config labels/copy.
- Kept promotion `may_submit_order=false` / `may_create_trade_action=false` in the dedicated promotion panel and removed those strings from the dashboard source.
- Updated the Playwright journey to open the Promotion tab before asserting promotion evidence strings.

### Review verdict

**Recommendation:** APPROVE for UI-SECTIONS-1 after final verification. **Architectural Status:** CLEAR for UI organization.

This segment improves information architecture and visual density only. It does not add real broker submission, browser credential capture, live venue connectivity, automatic promotion, or strategy-lane/execution-lane coupling.

### TDD / focused evidence so far

```bash
pytest tests/web/test_sectioned_operator_ui.py -q
# RED before implementation: 7 failed
# GREEN after implementation: 7 passed

cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx
# RED before implementation: 1 failed
# GREEN after implementation: 1 passed

pytest tests/web/test_sectioned_operator_ui.py tests/web/test_execution_lane_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_antd_operator_ui_contract.py tests/web/test_promotion_frontend.py tests/web/test_results_dashboard_frontend.py tests/web/test_frontend_data_wiring.py tests/web/test_ai_copilot_frontend.py -q
# 25 passed

cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx components/ai-builder/AiStrategyCopilot.test.tsx components/strategy-builder/StrategyBuilderWorkspace.test.tsx components/market/MarketProfilePanel.test.tsx components/results/ResultsDashboard.test.tsx components/config/ModelConfigTabs.test.tsx
# 6 files / 9 tests passed
```

### Remaining watch items

- Results charts remain placeholders until a chart library is explicitly chosen and tested.
- The execution config panel is read-only; future mutation APIs must remain backend-auth-derived and must not accept browser-supplied secrets or live authority.
- Real NautilusTrader live/backtest readiness remains governed by pinned NT engine evidence and DataTester/ExecTester/reconciliation gates.

### Final verification — Segment UI-SECTIONS-1

```bash
git diff --check
# passed

python3 -m compileall -q packages services tests
# passed

rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 341 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 12 files / 22 tests passed; Next build passed; Playwright 4 passed

cd apps/web && npm audit --omit=dev --audit-level=high
# exited 0 for high severity; existing moderate Next/PostCSS advisory remains with a breaking force-fix path
```

### Code-review reconciliation — Segment UI-SECTIONS-1

**Recommendation:** APPROVE. **Architectural Status:** CLEAR.

Review notes:

- The new UI sections are copy/layout changes plus tests; no backend live-order or adapter execution path was added.
- Dashboard source remains free of raw `submit_order` / `TradeAction` tokens; raw promotion evidence remains isolated to the promotion panel and backend/API contracts.
- Execution config remains a read-only status/visibility panel with server-side credential-slot language and no browser secret fields.
- The E2E journey now checks user-friendly dashboard authority language while static promotion tests continue to guard promotion evidence fields.

### Architecture clarification — NautilusTrader as backend pip dependency

The backend dependency direction is explicit and remains in force:

- `pyproject.toml` owns the pip dependency pin: `nautilus_trader==1.223.0`.
- Backend code imports official `nautilus_trader` modules directly for real-engine smoke and catalog replay seams.
- Backend package structure should follow NautilusTrader domains and lifecycle concepts first, while using Nautilus-Daedalus only as a read-only/reference architecture for clean-room adoption.
- Do not replace the pip dependency with a vendored NautilusTrader checkout, frontend-only API proxy, or ND runtime dependency.


## Closure update — Segment HEADLESS-BACKEND-1 headless backend runtime

**Status:** CLOSED locally on 2026-05-26 after focused, full Python, and web verification.

### Finding

- **MEDIUM-RUNTIME-2026-05-26-7:** Builder had API and worker modules that could be run manually, but no single backend-owned contract proved the system can operate without the web UI or a Nautilus-Daedalus checkout. This made it too easy to conflate UI readiness with backend readiness.

### Resolution

- Added a `backend_runtime` package with a strict `HeadlessBackendRuntimeReport`.
- Added a CLI (`services.backend_runtime`) and installed script entrypoint (`nautilus-builder-backend-check`) that emits JSON evidence.
- Added headless entrypoint scripts for `services.api.dev_server` and `services.workers.execution_lane_worker`.
- Added an integration test that verifies dependency-free API health/adapters, FastAPI factory mounting under `uv run`, execution-lane decoupling, NautilusTrader pin status, and absence of web/Daedalus imports.
- Documented backend-only commands in `README.md`.

### Review verdict

**Recommendation:** APPROVE for HEADLESS-BACKEND-1. **Architectural Status:** CLEAR for headless backend contracts.

The segment does not add live order authority, browser credentials, Nautilus-Daedalus imports, or new live adapter connectivity. It adds runtime evidence and command surfaces for backend-only operation.

### Focused evidence so far

```bash
rtk pytest tests/integration/test_headless_backend_runtime.py -q
# 6 passed

uv run python -c "from services.api.fastapi_app import create_fastapi_app; app=create_fastapi_app(); print(app.title, len(app.routes))"
# Nautilus Builder API 32
```

### Final verification — Segment HEADLESS-BACKEND-1

```bash
rtk pytest tests/integration/test_headless_backend_runtime.py tests/api/test_fastapi_app.py tests/api/test_route_mounts.py tests/execution_lane tests/backtest_runner/test_runtime_dependency_check.py tests/backtest_runner/test_real_nautilus_engine_smoke.py -q
# Pytest: 38 passed

git diff --check
# passed

python3 -m compileall -q packages services tests
# passed

rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 347 passed

uv run nautilus-builder-backend-check --runtime-profile-id rp_paper_001
# emitted JSON with web_ui_required=false, nautilus_daedalus_required=false, FastAPI mounted true / 32 routes, and nautilus_trader==1.223.0

python3 -m services.workers.execution_lane_worker --runtime-profile-id rp_paper_001 --worker-id exec_worker_smoke
# emitted execution_lane JSON with strategy_lane_coupled=false and may_submit_order=false

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 12 files / 22 tests passed; Next build passed; Playwright 4 passed

cd apps/web && npm audit --omit=dev --audit-level=high
# exited 0 for high severity; existing moderate Next/PostCSS advisory remains with a breaking force-fix path
```

### Remaining watch items

- The dependency-free dev server is a local contract server; production FastAPI service supervision remains deployment work.
- Running `services.backend_runtime` outside `uv` may report FastAPI as missing while still proving dependency-free API/worker contracts.


## Deep review findings — NT/AI/backend alignment (2026-05-26)

**Review verdict:** REQUEST CHANGES for production/beta-readiness claims. COMMENT/APPROVE only for the current contract-prototype scope. No critical issue found that adds live order authority today, but several high-priority gaps would mislead users if the system is described as a fully working AI-to-Nautilus backtesting builder.

### CRITICAL

- None found in the current reviewed tree. No direct `submit_order` path, browser credential field, or Nautilus-Daedalus runtime import was found in Builder implementation code.

### HIGH

1. **StrategySpec validation accepts unsafe or incoherent backtest semantics.**
   - Evidence: `packages/strategy_validation/validators.py` checks `bar_close_only` and `no_lookahead_required`, but not `requires_backtest_before_shadow`; `packages/strategy_spec/models.py` treats `DataRange.start/end` as unconstrained strings and `RuleClause` operands as arbitrary-length lists.
   - Reproduced locally: `requires_backtest_before_shadow=false`, reversed/invalid dates, and one-/three-operand `gt` clauses all validate as `is_valid=True`.
   - Risk: AI-generated StrategySpecs can pass the primary validation gate while bypassing stated backtest-before-shadow policy or carrying rules/date ranges that cannot map cleanly to Nautilus backtests.
   - Fix: add validators/tests for ISO datetime parsing, start < end, exact operator arity, indicator/rule reference resolution, and `requires_backtest_before_shadow is True`.

2. **StrategySpec-generated Nautilus replay does not execute the StrategySpec logic yet.**
   - Evidence: `packages/nautilus_rule_graph/strategy.py` only loads the instrument, subscribes to quote ticks, and increments `observed_quote_ticks`; `packages/backtest_runner/strategy_spec_replay.py` passes the spec into config but returns zero-order/zero-position observational evidence.
   - Risk: the current replay proves NT catalog/runtime wiring, not whether the user/AI strategy works. Promotion/research UX must not treat these results as strategy-performance backtests.
   - Fix: implement a rule-graph signal evaluator/indicator bridge or relabel the current replay as catalog/runtime smoke only until signals/metrics are actually derived from StrategySpec rules.

3. **The web UI has no bearer-auth propagation for protected FastAPI routes.**
   - Evidence: `services/api/fastapi_app.py` requires bearer auth for strategies, backtest jobs, runtime replay, AI draft/apply, promotion, workflow results, and execution-lane routes. `apps/web/lib/api.ts` never attaches `Authorization`, and frontend tests mock `fetch` rather than exercising the real FastAPI auth boundary.
   - Risk: live VM deployments using FastAPI will return `401 auth_required` for many interactive UI flows even when the proxy/base URL is correct.
   - Fix: add an auth/session bootstrap, server-side token exchange or dev-token injection for local mode, typed auth errors in UI, and integration tests that run the Next proxy against FastAPI with a real bearer context.

4. **Unauthenticated dependency-free API docs/diagnostics advertise public binding.**
   - Evidence: `services/api/dev_server.py` defaults to `127.0.0.1`, but `README.md` and `packages/backend_runtime/service.py` list `python3 -m services.api.dev_server --host 0.0.0.0 --port 8000`; `services/api/app.py` routes are dependency-free and unauthenticated by design.
   - Risk: a remote VM can expose contract/dev routes without auth if operators copy the documented command.
   - Fix: document `127.0.0.1` as the default for the dev server, add explicit “not production / do not bind publicly” warnings, and reserve `0.0.0.0` examples for the FastAPI path with real auth/proxy controls.

### MEDIUM

1. **`PostgresWorkflowRepository` is SQLite-style despite the Postgres name and migrations.**
   - Evidence: `packages/workflow_spine/postgres_repository.py` imports `sqlite3.Connection`, creates flattened `builder_*` tables, and uses `insert or replace`; tests use `sqlite3.connect(":memory:")`. The repo also ships psycopg and Postgres-shaped SQL migrations under `infra/migrations`.
   - Risk: database setup is not production-ready or actually aligned with the declared Postgres/ND-like storage direction.
   - Fix: rename this to a SQLite contract repository or implement a real psycopg repository against `infra/migrations` tables.

2. **Strategy module registry metadata points to a missing config class.**
   - Evidence: `packages/strategy_registry/service.py` registers `packages.nautilus_rule_graph.config:RuleGraphStrategyConfig`, but `packages/nautilus_rule_graph/config.py` defines only `RuleGraphProfile`; resolving the metadata raises `AttributeError`.
   - Risk: future registry-to-backtest resolution will fail despite current metadata-only tests passing.
   - Fix: change the registry to `packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategyConfig` or add the missing config class and test import resolution in a safe allowlisted mode.

3. **Backtest job creation treats `compile_artifact_id` as `compile_hash` without digest validation.**
   - Evidence: `services/api/routes/backtest_jobs.py` requires `compile_artifact_id` and stores it as `compile_hash`; tests use values like `compile_001`.
   - Risk: job/run/evidence lineage can claim a compile hash that is not the compiler’s deterministic SHA-256 hash, weakening promotion binding and reproducibility.
   - Fix: accept an explicit `compile_hash`, validate 64 hex chars, and keep any artifact ID in a separate field.

4. **Artifact URI schemes are not consistent across result paths.**
   - Evidence: `packages/artifact_store` and strict promotion require `artifact://builder/...`; `packages/backtest_runner/result_normalizer.py` emits `artifact://backtests/{job_id}/result.json` for non-fixture injected-engine results; `services/api/routes/workflow_results.py` still has explicit `fixture://` fallback for the lightweight API.
   - Risk: non-fixture results may not be consumable by strict promotion evidence checks, while dev fixture refs can remain accidentally reachable in compatibility flows.
   - Fix: normalize all project artifacts to `artifact://builder/<project>/<user>/<type>/<id>` and gate fixture fallback behind an explicit dev flag.

5. **Catalog root policy is optional outside strict FastAPI paths.**
   - Evidence: `CatalogDatasetRegistryService(catalog_root=None)` returns datasets without path normalization/root checks unless strict mode is requested; the lightweight API path accepts caller-supplied catalog fields.
   - Risk: package consumers or dev routes can bypass the rooted/allowlisted catalog policy already used by strict FastAPI backtest creation.
   - Fix: require a root policy by default for any write/replay path, and keep no-root registries read-only/test-only.

6. **AI audit persistence defaults to process memory.**
   - Evidence: `create_fastapi_app()` builds `AiBuilderService.from_env(store=RecordedAiDraftStore())` unless an audit store is injected.
   - Risk: prompt/response metadata needed for continuous improvement, incident analysis, and EvoMap-style auditable evolution disappears on restart.
   - Fix: wire the default FastAPI app to a durable DB-backed audit store or fail closed when production mode lacks one.

7. **Semantic import closure is too broad.**
   - Evidence: schema allows `CreatedFrom.IMPORTED`, but `validate_strategy_spec()` scans all strings for the substring `import`, so a valid imported draft is rejected as raw code.
   - Risk: clean-room imports from existing strategy registries will fail or require bypassing the main validator.
   - Fix: distinguish raw code tokens from safe enum values; use token/AST-ish matching instead of substring matching across all schema fields.

### LOW / WATCH

1. **NautilusTrader pin drift watch.**
   - Evidence: Builder pins `nautilus_trader==1.223.0`, while official latest docs describe installing the latest release and current docs may reflect newer APIs.
   - Risk: docs/skill guidance may drift from the pinned runtime. This is acceptable only if the Daedalus-matched pin is intentional and claims say “pinned 1.223.0,” not “latest NT.”
   - Fix: keep a version-compatibility note and retest before upgrading.

2. **Frontend remains an operator shell, not a polished production app.**
   - Evidence: UI has AntD shell/tabs and prompt controls, but tests are mostly mocked/contract-level, chart sections are placeholders, and protected API/auth E2E is absent.
   - Risk: VM demos can look interactive while backend-driven flows are still incomplete.
   - Fix: add end-to-end tests with real FastAPI + auth + proxy + seeded data before calling it user-ready.

### Architecture watchlist

- Execution lane contracts are useful, but there is no Nautilus `LiveNode`/`TradingNode`, adapter factory, DataTester, ExecTester, or reconciliation evidence. Treat it as a decoupled execution-lane model only.
- LangChain/LangGraph/EvoMap alignment is conceptual today: Builder has an OpenAI-compatible provider and audit records, but no stateful graph/checkpointed AI improvement lane yet.
- The DB direction should converge: either keep explicit in-memory/SQLite contract storage for open-source demo mode or implement the Postgres migrations end to end. Do not call the current SQLite repository production Postgres.

### Closure update — DR-CLOSURE-1 StrategySpec validation hardening (2026-05-26)

Status: **CLOSED for validation scope**.

- HIGH finding "StrategySpec validation accepts unsafe or incoherent backtest semantics" is closed for the documented validator gaps: backtest-before-shadow, ISO datetime parsing/order, exact rule arity, rule operand reference resolution, and imported provenance false positives.
- Remaining related work is covered by DR-CLOSURE-2: StrategySpec replay must now prove no-order rule evaluation evidence under Nautilus replay.

Evidence:

```bash
rtk pytest tests/strategy_validation/test_deep_review_closure_validation.py -q
# 7 passed
rtk pytest tests/strategy_validation tests/strategy_spec tests/ai_builder -q
# 44 passed
```

### Closure update — DR-CLOSURE-2 StrategySpec no-order rule replay (2026-05-26)

Status: **CLOSED for no-order replay semantics**.

- HIGH finding "StrategySpec-generated Nautilus replay does not execute the StrategySpec logic yet" is closed for the safe Builder scope: replay now includes deterministic StrategySpec indicator/rule evaluation evidence while still emitting zero orders, zero positions, no credentials, no live authority, and `may_submit_order=false`.
- This is not a live trading implementation and does not replace future full Nautilus strategy/order parity work.

Evidence:

```bash
rtk pytest tests/nautilus_rule_graph/test_rule_graph_evaluator.py tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
# 6 passed
rtk pytest tests/nautilus_rule_graph tests/backtest_runner tests/strategy_validation tests/strategy_spec -q
# 58 passed
```

### Closure update — DR-CLOSURE-3 web/API auth and dev-server exposure (2026-05-26)

Status: **CLOSED for local/VM auth propagation and unsafe dev-server docs**.

- HIGH finding "The web UI has no bearer-auth propagation for protected FastAPI routes" is closed for the local/VM route: web API helpers propagate configured bearer tokens and auth failures now include setup guidance.
- HIGH finding "Unauthenticated dependency-free API docs/diagnostics advertise public binding" is closed: dependency-free dev server examples now use `127.0.0.1` and document local-only scope.

Evidence:

```bash
cd apps/web && npm run typecheck && npm test -- --run lib/api.test.ts
# typecheck passed; 8 tests passed
rtk pytest tests/api/test_fastapi_app.py tests/integration/test_readme_readiness_hygiene.py tests/integration/test_headless_backend_runtime.py -q
# 22 passed
```

### Closure update — DR-CLOSURE-4 medium-risk evidence and persistence closure (2026-05-26)

Status: **CLOSED for repo-contract scope**.

- MEDIUM finding "Strategy module registry metadata points to a missing config class" is closed: default metadata resolves to `packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategyConfig` and tests import both allowlisted symbols.
- MEDIUM finding "Backtest job creation treats `compile_artifact_id` as `compile_hash`" is closed for strict FastAPI paths: strict creation requires a 64-character SHA-256 `compile_hash`, preserves `compile_artifact_id` separately, and legacy non-strict compatibility derives a deterministic hash instead of mislabeling the artifact ID.
- MEDIUM finding "Artifact URI schemes are not consistent across result paths" is closed for non-fixture result normalization: injected-engine results now use scoped `artifact://builder/{project_id}/{user_id}/backtest_result/{job_id}` refs.
- MEDIUM finding "Catalog root policy is optional outside strict FastAPI paths" is closed for registry write/selection defaults: unrooted registries raise unless explicitly constructed as test compatibility.
- MEDIUM finding "AI audit persistence defaults to process memory" is closed for production FastAPI bootstrap: production mode requires a durable injected store or `BUILDER_AI_AUDIT_SQLITE_PATH`.
- MEDIUM finding "`PostgresWorkflowRepository` is SQLite-style despite the Postgres name" is controlled: `SqliteWorkflowRepository` is now the honest public name and the old Postgres name is a compatibility alias, not a production-readiness claim.

Evidence:

```bash
rtk pytest tests/catalog_datasets tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py tests/backtest_jobs tests/backtest_runner/test_result_normalizer.py tests/strategy_registry tests/workflow_spine tests/ai_builder -q
# Pytest: 112 passed
```

### Master reconciliation — 2026-05-26 deep-review findings closure

Status: **CLOSED for the named repository-contract findings; WATCH for production/runtime maturity claims**.

All named HIGH/MEDIUM findings in this pass have concrete code/tests/docs closure. The closure does not claim full production trading readiness: Builder remains an advisory authoring/backtest system with no live order authority, no browser credentials, and no `submit_order`/`TradeAction` path.

Final verification:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 363 passed

cd apps/web
npm run typecheck
npm test
npm run build
# Typecheck passed; Vitest 25 passed; Next.js build passed
```

Remaining watch items before stronger claims:

- production Postgres repository against `infra/migrations`, not the SQLite compatibility repository;
- Playwright/browser E2E for full frontend readiness;
- future Nautilus live execution node/adapter reconciliation and ExecTester evidence before any live-trading readiness claim.

## Closure progress — 2026-05-26 Segment 1 UI StrategySpec serialization

**Status:** completed.

Closed/changed findings:

- `HIGH-1` from the UI recheck is remediated at frontend contract level: `graphToStrategySpec()` now emits a full backend-shaped draft StrategySpec rather than the previous partial `{status, stage, indicators, graph_edges}` scaffold.
- `strategySpecToGraph()` now understands canonical object-shaped StrategySpec indicators so persisted/backend draft specs can reopen as editable graph nodes.

Evidence:

```bash
cd apps/web && npm test -- --run lib/strategySpec.test.ts
# RED first: 2 failed for missing backend fields and indicator round-trip
# GREEN: 3 passed
```

## Closure progress — 2026-05-26 Segment 2 Backtest Center runtime rendering

**Status:** completed.

Closed/changed findings:

- `HIGH-2` from the UI recheck is remediated at frontend route level: `/backtests/[jobId]` now fetches and renders backend job status, runtime events, artifact refs, worker identity, strategy version, and cancel-request state.
- The Backtest Center remains observational-only: the browser action is limited to `cancelBacktestJob()` / request cancel, with `may_submit_order: false` visible.

Evidence:

```bash
cd apps/web && npm test -- --run app/backtests/'[jobId]'/page.test.tsx
# RED first: no backend fetch calls
# GREEN: 1 passed
```

## Closure progress — 2026-05-26 Segment 3 Dashboard navigation and builder route

**Status:** completed.

Closed/changed findings:

- `MEDIUM-3` Dashboard CTA buttons are no longer inert: they switch the main workspace between AI prompt and StrategySpec/market setup sections.
- `MEDIUM-4` broken Builder route is closed by adding `/builder/[strategyId]`, preserving the existing strategy-detail link while keeping the page draft-only and non-authoritative.

Evidence:

```bash
cd apps/web && npm test -- --run components/dashboard/BuilderDashboard.test.tsx app/builder/'[strategyId]'/page.test.tsx
# RED first: inert CTA and missing route
# GREEN: 3 passed
```

## Closure progress — 2026-05-26 Segment 4 LLM config persistence and AI ID simplification

**Status:** completed.

Closed/changed findings:

- `MEDIUM-5` LLM config is no longer local draft state only: `/api/config/llm` now provides a backend load/save contract for non-secret OpenAI-compatible provider and model-role settings.
- Browser secret collection is explicitly rejected by backend config routes and absent from the UI.
- `MEDIUM-6` AI copilot technical lineage IDs are hidden for normal users and only rendered under `Advanced lineage IDs`; default generated IDs still flow through the advisory API payload.

Evidence:

```bash
rtk pytest tests/api/test_llm_config_routes.py -q
# 2 passed after RED/GREEN cycle

cd apps/web && npm test -- --run components/config/ModelConfigTabs.test.tsx components/ai-builder/AiStrategyCopilot.test.tsx
# 3 passed after RED/GREEN cycle
```

## Master reconciliation — 2026-05-26 UI workflow closure

**Status:** completed.

Closed current UI findings:

- HIGH: StrategySpec editor no longer emits partial scaffold-only StrategySpec output.
- HIGH: Backtest Center no longer renders a static contract list; it fetches job/event contracts and exposes artifact/cancel state.
- MEDIUM: Dashboard CTA buttons now switch the intended workflow sections.
- MEDIUM: `/builder/[strategyId]` now exists for strategy-detail links.
- MEDIUM: LLM config now has backend load/save validation for non-secret provider/model settings.
- MEDIUM: AI copilot technical lineage IDs are hidden by default under an Advanced affordance.

Remaining risk / non-claim:

- Backtest Center has an observational degraded fallback for fixture/development IDs that are absent from the backend; this keeps the UI navigable but does not prove the job exists.
- LLM config persists non-secret routing settings only. API keys remain server-environment concerns and are not accepted by browser config payloads.
- These changes improve UI workflow readiness; they do not create live order authority or real Nautilus engine proof beyond existing backend contracts.

Verification:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 365 passed
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 29 passed; build passed; Playwright 4 passed
```

## Closure progress — 2026-05-26 Segment 5 Backtest launch manifest

**Status:** completed.

Closed/changed findings:

- The dashboard no longer jumps from StrategySpec editing to a generic runtime terminal only; it now has a dedicated `3. Backtest` section with an explicit validated run manifest.
- Backtest job creation is gated on required evidence fields and a 64-character SHA-256 `compile_hash` shape before the browser calls `/api/backtest-jobs`.
- Successful job creation surfaces the backend `job_id`, status, dataset, worker, event stream, and an `Open job console` link for observational review.

Remaining risk / non-claim:

- The panel uses operator-visible manifest fields until a deeper state pipeline passes actual validated StrategySpec/dataset/compile evidence between sections.
- FastAPI strict-mode dataset selection can still reject the manifest if the referenced dataset is not registered in the authenticated project scope; the UI shows that backend error instead of bypassing it.
- This segment does not add live/paper execution authority, browser credentials, or automatic promotion.

Evidence:

```bash
cd apps/web && npm test -- --run components/backtests/BacktestLaunchPanel.test.tsx components/dashboard/BuilderDashboard.test.tsx
# RED first: missing component/import and missing Backtest tab
# GREEN: 5 passed
```

### Reconciliation — Segment 5 Backtest launch manifest

Verification before commit:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 365 passed
cd apps/web && npm run typecheck && npm test
# 15 files / 32 Vitest tests passed
cd apps/web && npm run build && npm run test:e2e
# Next build passed; Playwright 4 passed
```

## Segment closure — BacktestNode execution trigger

**Status:** Closed for the current backend-owned local/dev run segment on 2026-05-26.

Closed / improved findings:

- **HIGH: Backtest Center/API did not execute real backend job path.** Added `POST /api/backtest-jobs/{job_id}/run` to execute an already-created scoped job through the backend worker and the real `BacktestNode` catalog replay path.
- **HIGH: StrategySpec replay evidence needed to prove user-selected catalog ingestion.** The new route resolves the stored `StrategySpec`, selects the registry-approved `CatalogDataset`, passes the registry `catalog_root`, and persists replay evidence with `dataset_source == "user_catalog"` and `engine_mode == "strategy_spec_catalog_replay"`.
- **MEDIUM: Compile lineage needed binding before run.** The run helper recomputes the stored StrategySpec backtest compile hash and rejects jobs whose `compile_hash` does not match the saved StrategySpec lineage.
- **MEDIUM: Runtime events were mounted as empty observational payloads only.** Event replay can now return actual RUNNING/SUCCEEDED/FAILED/CANCEL_REQUESTED worker events for the injected runtime-event service, with FastAPI bearer-auth/project-scope checks before event disclosure.

Safety notes:

- Browser/UI still does not own worker shell, credentials, or order authority.
- The route is backend-owned and scoped by bearer auth in FastAPI.
- The `cancel_requested` state is honored before worker start and does not require catalog/artifact dependencies; started replay failures move the job to `FAILED` and emit an ERROR event.
- Artifacts remain project/user-scoped `artifact://builder/...` JSON records.
- This is still BacktestNode/historical replay, not TradingNode paper or live execution.

Remaining actionable risks:

- Add asynchronous worker queue/claiming when moving beyond local/dev synchronous runs.
- Add durable job/event persistence for production deployments; current FastAPI injection can still be in-memory depending on boot configuration.
- Add UI wiring to call the run route only after validation/compile/job creation evidence exists.
- Add result-dashboard artifact read/display wiring for the persisted `strategy_spec_replay` artifact.

## Closure progress — 2026-05-26 TradingNode paper/live execution lane

**Status:** implementation segment completed locally; verification evidence recorded below.

Closed / improved findings:

- **HIGH: TradingNode paper/live was only a conceptual future lane.** Added a backend-owned TradingNode runtime-plan contract under `packages/execution_lane` and exposed it via `/api/execution-lane/runtime-plan`.
- **HIGH: Paper/live risk could couple back into StrategySpec/backtest flow.** Runtime plans and worker reports preserve `strategy_lane_coupled=false`; the worker claims execution-lane commands only and does not import strategy-lane packages.
- **HIGH: Live authority needed stronger evidence gates.** Live profiles/commands now require matching manual review, risk profile, server-side credential-slot ref, activation identity/time, config checksum, DataTester evidence, ExecTester evidence, reconciliation evidence, and risk approval before order authority can be represented.
- **MEDIUM: Python TradingNode vs Rust LiveNode labeling risk.** Runtime plans explicitly label `node_runtime=python_trading_node` and `runtime_label=python_live_integration_specific`, with `future_runtime=rust_live_node` for the Rust-backed path.
- **MEDIUM: Browser credential leakage risk.** Runtime plans and reports set `browser_credentials_allowed=false` and reject secret-shaped payload fields.

Remaining non-claims / risks:

- This segment does **not** start a real Nautilus `TradingNode`, connect a venue adapter, or submit/cancel/modify orders.
- Paper mode is a sandbox/forward-execution contract, not historical replay; BacktestNode remains the repeatable historical evidence lane.
- Live mode remains fail-closed unless all gates and evidence refs are present; real venue readiness still requires adapter-specific DataTester/ExecTester/reconciliation proof.
- Rust `LiveNode` implementation remains future work; the current implementation records the Python TradingNode path as integration-specific.

Segment verification:

```bash
rtk pytest tests/execution_lane/test_tradingnode_runtime_contract.py tests/api/test_execution_lane_tradingnode_routes.py -q
# RED first: missing packages.execution_lane.nautilus_runtime
# GREEN: 7 passed

rtk pytest tests/execution_lane tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/api/test_execution_lane_tradingnode_routes.py tests/infrastructure -q
# 31 passed
```

### Reconciliation — TradingNode paper/live execution lane

Master verification after implementation:

```bash
git diff --check
# passed
python3 - <<'PY'
from nautilus_trader.common import Environment
from nautilus_trader.config import LiveExecEngineConfig, LiveRiskEngineConfig, TradingNodeConfig
from nautilus_trader.live.node import TradingNode
exec_cfg = LiveExecEngineConfig(reconciliation=True, reconciliation_lookback_mins=60, reconciliation_startup_delay_secs=10.0)
risk_cfg = LiveRiskEngineConfig(bypass=False)
node_cfg = TradingNodeConfig(environment=Environment.SANDBOX, trader_id='BUILDER-001', exec_engine=exec_cfg, risk_engine=risk_cfg, data_clients={}, exec_clients={})
print({'environment': node_cfg.environment.value, 'reconciliation': node_cfg.exec_engine.reconciliation, 'lookback': node_cfg.exec_engine.reconciliation_lookback_mins, 'startup_delay': node_cfg.exec_engine.reconciliation_startup_delay_secs, 'trading_node_methods': [m for m in ('build','run','stop','dispose') if hasattr(TradingNode, m)]})
PY
# {'environment': 'sandbox', 'reconciliation': True, 'lookback': 60, 'startup_delay': 10.0, 'trading_node_methods': ['build', 'run', 'stop', 'dispose']}
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 380 passed
```

## Closure progress — 2026-05-26 Execution lane full web wire

**Status:** implementation segment completed locally; final master verification recorded after the verification gate.

Closed / improved findings:

- **HIGH: TradingNode paper/live execution lane was not runnable from web UI.** The `/config` UI now wires the paper lane through backend contracts: profile registration, runtime-plan fetch, command enqueue, worker run-once, and report rendering.
- **HIGH: Browser/API boundary needed explicit worker separation.** The UI calls a backend-owned `POST /api/execution-lane/worker/run-once` adapter that delegates to `services.workers.execution_lane_worker.run_execution_lane_worker_once()`; it does not expose shell/process controls or raw worker internals.
- **MEDIUM: Runtime-plan evidence was API-only.** The UI now displays `Runtime plan READY`, `python_live_integration_specific`, sandbox/paper status, credential restrictions, and `Worker report: tradingnode_runtime_plan` after the backend seam reports.
- **MEDIUM: Full-wire UI lacked contract tests.** Added Vitest coverage for the fetch sequence and Python source-scan coverage for API wrappers/types/buttons/routes.

Remaining non-claims / risks:

- This is a paper/sandbox contract wire only. It does not start a real Nautilus `TradingNode`, connect to a venue, or submit/cancel/modify orders.
- The browser still supplies only a paper command request shape; real paper/live venue readiness still requires adapter-specific DataTester, ExecTester, reconciliation, credential-slot, and manual approval evidence.
- Worker run-once is synchronous/local-dev scaffolding; production execution still needs durable queue/claim/retry semantics and persistent event/report storage.
- Live mode remains fail-closed and is not exposed as a browser order-submission path.

Implementation evidence:

```bash
rtk pytest tests/api/test_execution_lane_tradingnode_routes.py tests/web/test_execution_lane_ui_contract.py -q
# Pytest: 5 passed
cd apps/web && npm test -- --run components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts components/dashboard/BuilderDashboard.test.tsx
# 12 passed
cd apps/web && npm run typecheck
# passed
rtk pytest tests/api/test_execution_lane_tradingnode_routes.py tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/execution_lane tests/web/test_execution_lane_ui_contract.py -q
# 26 passed
```

### Reconciliation — Execution lane full web wire

Verification gate evidence:

```bash
git diff --check
# passed
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# Pytest: 382 passed
cd apps/web && npm run typecheck && npm test && npm run build
# typecheck passed; Vitest 33 passed; Next build passed
cd apps/web && npm run test:e2e
# Playwright 4 passed
```

Master status for this segment: closed for paper/sandbox full-wire UI contracts. Do not escalate this into a live-trading readiness claim without real venue adapter evidence, credential-slot integration, durable worker persistence, and operator approval gates.

## Closure progress — 2026-05-26 BacktestNode web run full wire

**Status:** implementation segment completed locally; final verification pending master gate.

Closed / improved findings:

- **HIGH: Web UI could create a backtest job but could not actually call the backend run route.** `BacktestLaunchPanel` now exposes a `Run BacktestNode` action after job creation and calls `POST /api/backtest-jobs/{job_id}/run` through the typed frontend API client.
- **HIGH: Backtest run evidence was not visible in the launch workflow.** The panel now renders returned `RUNNING` / `SUCCEEDED` / `FAILED` events, BacktestNode mode, replay engine mode, dataset source, artifact refs, worker identity, and no-order evidence flags.
- **MEDIUM: Frontend API contract lacked a typed run response.** Added `BacktestRunResponse` / `RuntimeEvent` types and `runBacktestJob()` wrapper tests.
- **MEDIUM: UI source-scan coverage did not enforce the run trigger.** Added Python web contract coverage for the route wrapper and section surface.

Preserved non-claims / risks:

- This does **not** give the browser shell, worker-process, catalog-path, StrategySpec-payload, credential, paper, live, or order authority.
- The run remains a backend-owned local/dev synchronous trigger over the existing worker seam; production deployment still needs durable queue/claim/retry/event persistence.
- Artifacts are displayed by ref only; full artifact read/detail dashboards remain a later Results/Research wiring task.
- TradingNode paper/live remains separate from BacktestNode historical replay and stays behind manual promotion and execution-lane gates.

Implementation evidence:

```bash
cd apps/web && npm test -- --run components/backtests/BacktestLaunchPanel.test.tsx lib/api.test.ts
# 2 files / 12 tests passed
rtk pytest tests/web/test_frontend_data_wiring.py tests/web/test_sectioned_operator_ui.py -q
# 11 passed
```

### Reconciliation — BacktestNode web run full wire

Verification gate evidence:

```bash
git diff --check
# passed
rtk pytest tests/api/test_backtest_job_execution_routes.py tests/backtest_runner/test_worker_integration.py tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
# 15 passed
python3 -m compileall -q packages services tests
# passed
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 383 passed
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 35 passed; Next build passed; Playwright 4 passed
```

Master status for this segment: closed for the browser-to-backend BacktestNode run trigger and observational evidence display. Remaining work is production worker queue/durable persistence and richer artifact detail views, not this segment's core web/run contract.

## Closure progress — 2026-05-26 Execution credential-slot bootstrap

**Status:** implementation segment completed locally; master verification gate pending after documentation reconciliation.

Closed / improved findings:

- **HIGH: Execution lane needed a safe path from UI intent to server-side credential slot.** Added `POST /api/execution-lane/credential-slots` and a UI credential-slot bootstrap card. The route writes a gitignored `.env.execution.local` and returns only redacted slot metadata.
- **HIGH: Raw credentials must not flow through StrategySpec/profile/command/worker payloads.** Runtime profiles and commands still reject secret-shaped fields; credential bootstrap is isolated in `packages/execution_lane/credentials.py` and response models set `browser_secret_echo=false`.
- **HIGH: FastAPI credential bootstrap needed bearer scope.** FastAPI now requires bearer auth for credential-slot creation and rejects project mismatches with `project_scope_mismatch`.
- **MEDIUM: Runtime plans did not show bound credential evidence for paper/sandbox venue connectivity.** READY paper/live runtime plans can now include a server-side `credential_slot_ref` while paper still keeps `may_submit_order=false`.
- **MEDIUM: Worker reports did not expose risk-gate/credential-slot evidence.** The execution-lane worker report now emits `risk_gate_status`, `credential_slot_bound`, and `secrets_storage` without secret values.

Remaining non-claims / risks:

- This does **not** start a real venue-connected Nautilus `TradingNode` from the browser.
- This does **not** make live trading production-ready; live remains fail-closed without all manual/risk/testing/reconciliation gates.
- `.env.execution.local` is local/dev storage. Production needs an operator-managed secret store or deployment-specific environment injection.
- Existing `credslot://server/...` refs are accepted as externally managed server-side slots; only Builder-created `credslot://local-env/...` refs are scope-validated against the in-memory store.

Targeted verification captured:

```bash
rtk pytest tests/execution_lane/test_credential_slots.py tests/api/test_execution_lane_credentials_routes.py tests/api/test_fastapi_app.py::test_fastapi_execution_lane_credential_slot_requires_auth_and_project_scope -q
# 7 passed
rtk pytest tests/execution_lane/test_tradingnode_runtime_contract.py::test_worker_report_includes_credential_slot_and_risk_gate_without_secrets -q
# 1 passed
rtk pytest tests/execution_lane tests/api/test_execution_lane_credentials_routes.py tests/api/test_execution_lane_tradingnode_routes.py tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/api/test_fastapi_app.py::test_fastapi_execution_lane_credential_slot_requires_auth_and_project_scope tests/web/test_execution_lane_ui_contract.py -q
# 34 passed
cd apps/web && npm test -- --run components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts
# 12 passed
cd apps/web && npm run typecheck
# passed
```

### Master reconciliation — Execution credential-slot bootstrap

Verification gate evidence:

```bash
git diff --check
# passed
python3 -m compileall -q packages services tests
# passed
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 391 passed
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 16 files / 37 tests passed; Next build passed; Playwright 4 passed
```

Master status for this segment: closed for safe local/dev credential-slot bootstrap and redacted execution-lane evidence. Remaining work is real operator-managed secret-store integration and venue-specific paper/live node startup after adapter evidence gates, not browser-side credential or order authority.

## Closure progress — 2026-05-27 Paper TradingNode session lifecycle full wire

Closed / improved findings:

- **HIGH: Web UI could not start a paper TradingNode lifecycle.** Added backend session start/get/stop APIs and UI controls that move a queued paper command into `RUNNING` and then `DISPOSED` lifecycle states.
- **HIGH: Credential slot needed backend-side resolution for paper session startup.** The worker now resolves `credential_slot_ref` from `.env.execution.local` and exposes only `credential_env_keys`, `credential_slot_ref`, and `credential_values_resolved=true`.
- **HIGH: Paper session needed Nautilus-native config evidence.** The worker builds a Nautilus `TradingNodeConfig` with reconciliation enabled, risk bypass disabled, official Binance config/factory classes where applicable, and no-order promoted strategy lineage attachment.
- **MEDIUM: UI lacked stop/dispose controls and lifecycle evidence.** The config panel now shows session ID, runner mode, runtime environment, credential slot ref, attached strategy version, lifecycle tags, and a `Stop / Dispose` control.
- **MEDIUM: FastAPI session routes needed project-scope checks.** Session start/get/stop routes now require bearer auth and reject cross-project access.

Remaining non-claims / risks:

- The default runner is `contract_dry_run`; it proves config/lifecycle wiring without opening venue sockets. Real Python `TradingNode` startup requires operator opt-in with `BUILDER_EXECUTION_LANE_TRADINGNODE_RUNNER=native`.
- Paper remains sandbox/no-order: `live_trading_enabled=false`, `execution_authority=false`, and `may_submit_order=false`.
- Live TradingNode/LiveNode authority remains fail-closed behind manual review, risk, DataTester, ExecTester, reconciliation, config checksum, and credential gates.
- Production secret storage should move from local `.env.execution.local` to an operator-managed secret store.

Verification captured:

```bash
rtk pytest tests/execution_lane tests/api/test_execution_lane_tradingnode_routes.py tests/api/test_execution_lane_credentials_routes.py tests/api/test_execution_lane_routes.py tests/api/test_execution_lane_venue_features.py tests/api/test_fastapi_app.py::test_fastapi_execution_lane_credential_slot_requires_auth_and_project_scope tests/api/test_fastapi_app.py::test_fastapi_execution_lane_session_start_requires_auth_and_project_scope tests/web/test_execution_lane_ui_contract.py tests/web/test_sectioned_operator_ui.py -q
# 47 passed
cd apps/web && npm run typecheck && npm test -- --run components/config/ExecutionLaneFeaturePanel.test.tsx lib/api.test.ts
# typecheck passed; 14 passed
```

### Master reconciliation — Paper TradingNode session lifecycle full wire

Verification gate evidence:

```bash
git diff --check
# passed
python3 -m compileall -q packages services tests
# passed
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/execution_lane tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/infrastructure -q
# 397 passed
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 39 passed; Next build passed; Playwright 4 passed
```

Master status for this segment: closed for UI → backend worker → server-side credential resolution → TradingNodeConfig build → promoted strategy attachment → paper lifecycle start/stop evidence. Remaining work is operator-managed native runner deployment/monitoring and live authority gates, not browser-side execution authority.

## Findings closure update — UI-3 three-section workflow

**Date:** 2026-05-27
**Status:** CLOSED for the current UI-organization segment.

Closed/advanced findings:

- The home dashboard no longer presents the operator journey as many competing surfaces. It is organized into the three product sections requested by the user:
  1. Strategy Builder — prompt-first natural language to guarded StrategySpec draft.
  2. Backtest Center — selected strategy/data run manifest to backend-owned BacktestNode evidence.
  3. Execution Lane — promoted strategy to backend-owned TradingNode paper/live lifecycle controls.
- Dashboard and shell navigation now use product-language labels instead of demo IDs as primary labels.
- Manual promotion remains in the Backtest Center review path, not in the strategy drafting lane.
- Execution Lane UI is visible from the command center and config route, but stays backend-owned and server-credential-slot based.

Residual non-blocking notes:

- The home page still embeds large components; future UX passes can split Strategy Builder, Backtest Center, and Execution Lane into dedicated routes while retaining the same labels.
- The Backtest Center form still uses a compact manifest-first flow; a future route can replace free-text IDs with backend-loaded strategy/dataset selectors.
- Execution Lane currently exposes a dev/local credential-slot bootstrap. Production deployment should replace local env writes with the intended secret backend without changing browser authority.

Verification:

```bash
cd apps/web && npm test
# 16 passed / 39 tests

cd apps/web && npm run typecheck && npm run build
# passed

cd apps/web && npm run test:e2e
# 4 passed

rtk pytest tests/web -q
# Pytest: 49 passed
```

## UI status/polish closure — 2026-05-27

### CLOSED / IMPROVED

1. **Shell looked like a scaffold instead of a usable app**
   - Fixed by stabilizing the AntD/Next layout with a left sidebar, sticky header, compact content spacing, and card/grid fallbacks.
   - `OperatorAppShell` now uses one navigation surface instead of duplicate quick links plus menu.

2. **AntD component rendering was visually degraded in local/dev screenshots**
   - Added repo-local fallbacks for grid columns, cards, tabs, steps, alerts, tags, descriptions, forms, inputs, and v6 select DOM.
   - Config and Backtest pages now render readable controls/status sections instead of collapsed/default browser controls.

3. **Design decisions were implicit**
   - Added `DESIGN.md` as the UI source of truth for the current Strategy Builder / Backtest Center / Execution Lane product shape.

### REMAINING UI RISKS

- The UI is now usable/polished enough for the current MVP shell, but result charts/equity curves still need a charting decision.
- Config and execution pages are still contract-heavy; future work should progressively disclose IDs/artifact refs behind advanced panels.
- Visual polish is CSS-fallback based because current AntD v6 runtime styling in dev was insufficient; revisit if the frontend adopts a stronger theme extraction/build setup.
