# Nautilus Builder Structure Review

**Review date:** 2026-05-24
**Target repository:** `/home/mok/projects/nautilus_builder`
**Scope correction:** this review targets **Nautilus Builder**, not `/home/mok/projects/Nautilus-Daedalus`.

## Authoritative references used

Local source truth:

- `AGENTS.md`
- `doc/README.md`
- `doc/nautilus_builder_spec.md`
- `doc/nautilus_builder_hardguards.md`
- `doc/nautilus_builder_repo_dependency_architecture.md`
- `packages/`, `services/`, `apps/web/`, and `tests/`

Official NautilusTrader references:

- <https://github.com/nautechsystems/nautilus_trader>
- <https://nautilustrader.io/docs/latest/developer_guide>
- <https://nautilustrader.io/docs/latest/developer_guide/adapters/>
- <https://nautilustrader.io/docs/latest/developer_guide/spec_data_testing/>
- <https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/>
- <https://nautilustrader.io/docs/latest/concepts/backtesting/>
- <https://nautilustrader.io/docs/latest/concepts/live/>

## Repository shape

```text
nautilus_builder/
├── doc/                    # Builder source-truth product, hardguard, lifecycle, dependency docs
├── docs/                   # Derived superpowers/spec/audit/verification artifacts
├── packages/               # Canonical Python domain layer
├── services/api/           # Thin API adapters over packages/*
├── services/workers/       # Backend-owned worker entrypoint stubs
├── apps/web/               # Minimal Next.js app shell and TSX components
├── tests/                  # Pytest contract suite mirrored by feature seam
├── infra/                  # Local docker-compose, migrations, CI template
├── README.md               # High-level current-shape summary
└── pyproject.toml          # Python packaging/test manifest
```

## Builder authority boundary

The local docs consistently define this product as Builder-only:

```text
UX / AI          -> authoring, drafting, explanation, observation
Validator        -> hard safety enforcement
Compiler         -> safe StrategySpec translation
NautilusTrader   -> backtest/replay truth engine
Daedalus gate    -> live gate authority
Daedalus execution lane -> only live submit_order authority
```

Current implementation mostly preserves the no-live-order boundary:

- `packages/strategy_compiler/compiler.py` sets `execution_authority=False` for both `backtest` and `signal_preview_only` profiles.
- `packages/promotions/service.py` returns `may_submit_order=False` and `may_create_trade_action=False`.
- `packages/lifecycle/models.py` exposes `live_trading_authority=False`.
- `apps/web/components/*` text is observational/advisory rather than live-ordering UI.

## Domain package map

| Package | Role | Key files |
|---|---|---|
| `strategy_spec` | Strict Pydantic StrategySpec schema and in-memory repository | `models.py`, `repository.py`, `schema.py`, `examples/ema_rsi_pullback.yaml` |
| `strategy_validation` | Hard-rule checks before compile/backtest | `policy.py`, `validators.py`, `reports.py` |
| `strategy_compiler` | StrategySpec -> compile artifact/profile metadata | `compiler.py`, `artifacts.py` |
| `nautilus_rule_graph` | Placeholder strategy classes/profiles | `config.py`, `strategy.py` |
| `adapter_registry` | Backend-approved adapter profiles | `models.py`, `service.py` |
| `instrument_registry` | Backend-approved instruments, data/timeframe/date checks | `service.py` |
| `backtest_jobs` | Durable-job contract scaffold | `models.py`, `service.py` |
| `backtest_runner` | Backtest config, engine boundary, fixture result normalization | `config_builder.py`, `nautilus_engine.py`, `runner.py`, `result_normalizer.py` |
| `runtime_events` | In-memory, SQLite, and Redis event stream seams | `models.py`, `stream.py`, `redis_stream.py`, `service.py` |
| `workflow_spine` | Strategy/test workflow lineage, persistence, projections, ND stream compatibility | `models.py`, `service.py`, `repository.py`, `postgres_repository.py`, `event_stream.py` |
| `lifecycle` | Draft -> Testing -> Beta -> Final policy | `models.py`, `state_machine.py`, `promotion_policy.py`, `versioning.py` |
| `promotions` | Builder-side promotion/shadow request contracts | `models.py`, `service.py` |
| `ai_builder` | Advisory draft provider/service and audit stores | `models.py`, `provider.py`, `service.py` |
| `strategy_registry` | Read-only external strategy registry/import-as-draft policy | `models.py`, `service.py` |
| `ui_contracts` | Python-backed executable UI contract helpers | `strategy_builder.py`, `job_terminal.py`, `results_dashboard.py` |
| `auth` | In-memory test token/project-scope model | `models.py`, `policy.py`, `service.py` |
| `system_verification` | Composed MVP verification report | `e2e.py` |

## API/service map

- `services/api/app.py` mounts the dependency-free `ApiApp` contract routes used by tests.
- `services/api/fastapi_app.py` mounts equivalent FastAPI routes when FastAPI is installed.
- `services/api/routes/market_catalog.py` exposes adapter/instrument/profile validation payloads.
- `services/api/routes/backtest_jobs.py` exposes job creation/status/cancel/event handles.
- `services/api/routes/promotions.py` exposes shadow/promotion payloads.
- `services/api/routes/ai_builder.py` exposes advisory draft/apply payloads.
- `services/workers/nautilus_backtest_worker.py` is a worker stub using fixture backtest results.

## Frontend map

- `apps/web/app/` contains the Next.js app shell and route pages.
- `apps/web/lib/api.ts` defines typed fetch wrappers and uses Next rewrites in `next.config.mjs`.
- `apps/web/components/strategy-builder/` holds the draft graph/spec workspace.
- `apps/web/components/market/` holds adapter/instrument/profile-selection UI.
- `apps/web/components/terminal/` holds observational terminal command parsing.
- `apps/web/components/results/`, `strategies/`, `ai-builder/`, and `promotions/` expose the operator MVP surfaces.

## Test map

- Python contract tests: `tests/**` — 188 tests currently pass.
- Frontend type/unit tests: `apps/web` — `tsc --noEmit` and Vitest currently pass.
- Playwright E2E exists at `apps/web/e2e/builder-shell.spec.ts`, but it could not run in this environment because the Playwright Chromium binary is not installed.

## Current maturity assessment

Nautilus Builder is a contract-heavy, scaffold-to-MVP repository. Its strongest areas are boundary language, no-live-order framing, and broad contract tests. The main readiness gaps are enforcement drift: AI draft validation, forbidden token coverage, frontend/backend DTO alignment, audit-grade job/event fields, and real NautilusTrader backtest dependency/wiring.

## Implementation progress — Segment 1 validation hardening

**Completed:** 2026-05-24

Files changed:

- `packages/strategy_validation/policy.py` — expanded canonical forbidden references to include hardguarded credential and broker/exchange-order terms.
- `packages/strategy_validation/validators.py` — aligned missing-risk wording with existing UI contract language.
- `packages/ai_builder/provider.py` — default advisory provider now emits a full StrategySpec-shaped draft.
- `packages/ai_builder/service.py` — provider output now passes through recursive Builder validation before `accepted=True`.
- `tests/strategy_validation/test_forbidden_execution_blocks.py` — added hardguard token coverage.
- `tests/ai_builder/test_ai_output_must_validate.py` — added nested forbidden and malformed-provider regressions.

Verification:

```bash
rtk pytest tests/strategy_validation/test_forbidden_execution_blocks.py tests/ai_builder/test_ai_output_must_validate.py -q
# Pytest: 11 passed

rtk pytest tests/strategy_validation tests/ai_builder tests/strategy_spec -q
# Pytest: 26 passed
```

## Implementation progress — Segment 2 market-profile contract alignment

**Completed:** 2026-05-24

Files changed:

- `apps/web/lib/types.ts` — frontend DTO types now mirror backend adapter, instrument, availability, and profile-validation payloads.
- `apps/web/components/market/MarketProfilePanel.tsx` — profile validation now submits backend-required `data_type`, `market_type`, and `date_range` fields and renders backend response identifiers.
- `apps/web/components/market/MarketProfilePanel.test.tsx` — component test now mocks the real backend route shape instead of the old UI-only DTOs.
- `tests/api/test_backtest_profiles.py` — API regression proves frontend-shaped validation payloads are accepted by `create_app()`.
- `tests/web/test_market_profile_frontend.py` — contract scan now guards `date_range` and `validation.instrument` rather than removed `adapter_profile_id` output.
- `tests/api/test_fastapi_app.py` and `tests/api/test_route_mounts.py` — API route assertions now align with the Segment 1 StrategySpec shape (`validation.output_mode`).

Verification:

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

## Implementation progress — Segment 3 audit-grade jobs and runtime events

**Completed:** 2026-05-24

Files changed:

- `packages/backtest_jobs/models.py` — `BacktestJob` now carries hardguard audit fields: `status`, timestamps, creator, strategy version ID, adapter profile ID, data range, worker ID, artifact refs, and event stream ID.
- `packages/backtest_jobs/service.py` — job creation canonicalizes old/new payload names, preserves idempotency, sets audit defaults, updates timestamps, and records worker/artifact transitions.
- `packages/runtime_events/models.py` and `packages/runtime_events/service.py` — runtime events now include event ID, actor identity, timestamp, metadata, and deterministic per-job event sequencing.
- `packages/runtime_events/redis_stream.py` — Redis stream payloads are JSON-wrapped so nested metadata remains durable and replayable.
- `services/api/routes/backtest_jobs.py` — create/read/cancel payloads expose backend-owned audit fields while preserving status labels.
- `services/workers/nautilus_backtest_worker.py` — worker transitions successful jobs to canonical `SUCCEEDED`, records worker identity, persists artifact refs, and emits actor-attributed events.
- Tests under `tests/backtest_jobs/`, `tests/runtime_events/`, `tests/backtest_runner/`, and `tests/api/test_backtest_job_routes.py` lock the audit contract.

Verification:

```bash
rtk pytest tests/backtest_jobs/test_create_job.py tests/runtime_events/test_replay.py tests/backtest_runner/test_worker_integration.py -q
# Initial RED: 3 passed, 3 failed for missing audit fields, actor fields, and COMPLETED/SUCCEEDED mismatch

rtk pytest tests/backtest_jobs/test_create_job.py tests/runtime_events/test_replay.py tests/backtest_runner/test_worker_integration.py -q
# GREEN: Pytest: 6 passed

python3 -m compileall -q packages/backtest_jobs packages/runtime_events services/workers services/api/routes/backtest_jobs.py
# compileall passed

rtk pytest tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/api/test_backtest_job_routes.py tests/api/test_route_mounts.py tests/web/test_job_terminal_replay.py -q
# Pytest: 36 passed
```

## Implementation progress — Segment 4 NautilusTrader dependency and engine-boundary labeling

**Completed:** 2026-05-24

Files changed:

- `pyproject.toml` — pins `nautilus_trader==1.223.0`, matching the read-only Daedalus runtime pin observed in `/home/mok/projects/Nautilus-Daedalus/pyproject.toml`.
- `packages/backtest_runner/engine_contract.py` — centralizes the pinned NautilusTrader version and engine-mode labels.
- `packages/backtest_runner/config_builder.py` — includes `nautilus_trader_version`, `engine_mode`, `live_trading_enabled=False`, and `execution_authority=False` in backtest configs.
- `packages/backtest_runner/artifacts.py` and `result_normalizer.py` — result artifacts now record NautilusTrader version and fixture/injected-engine evidence mode.
- `packages/backtest_runner/runner.py` — fixture backtests are explicitly labeled `fixture`.
- `packages/backtest_runner/nautilus_engine.py` — injected engine boundary results are explicitly labeled `injected_engine`, separate from fixture evidence.
- `tests/backtest_runner/test_nautilus_dependency_contract.py` — locks the exact dependency pin and fixture-vs-injected boundary labels.

Verification:

```bash
rtk pytest tests/backtest_runner/test_nautilus_dependency_contract.py -q
# Initial RED: 0 passed, 3 failed for missing dependency pin and engine labels
# GREEN: Pytest: 3 passed

rtk pytest tests/backtest_runner -q
# Pytest: 10 passed

python3 -m compileall -q packages/backtest_runner tests/backtest_runner
# compileall passed
```

## Master reconciliation — findings closure

**Completed:** 2026-05-24

Additional reconciliation changes after Segment 4:

- `packages/system_verification/e2e.py` now checks the validated StrategySpec shape (`validation.output_mode`) and canonical `SUCCEEDED` worker state.
- `apps/web/lib/api.ts` resolves server-side API fetches through `BUILDER_API_BASE_URL` / `127.0.0.1:8000` while preserving browser-side relative rewrites.
- `services/api/dev_server.py` adds a dependency-free local API server for Playwright and operator-shell smoke tests.
- `apps/web/playwright.config.ts` now starts the local API dev server alongside Next.
- `apps/web/components/strategies/StrategyListClient.tsx` posts a full StrategySpec-shaped draft, so real backend validation accepts the operator journey.
- `services/api/routes/workflow_results.py` includes `strategy_version_id` in default result artifacts for result-route traceability.
- `apps/web/e2e/builder-shell.spec.ts` now exercises the real create-draft path and backend-backed result route without strict-locator ambiguity.

Master verification:

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

Forbidden-authority reconciliation:

- Diff grep for `submit_order`, `TradeAction`, `api_key`, `secret_key`, `credential`, `broker_order`, and `exchange_order` found only guard tables, negative/denied booleans, credential-rejection config, tests, and documentation references.
- No Builder path gained live order authority, Daedalus imports, shell execution, or credential acceptance.

## Deep review refresh — NT/Daedalus alignment pass

**Reviewed:** 2026-05-24 12:50 UTC
**Skills/routing:** `superpowers:code-review` with `superpowers:nt`; primary `nt-review`, supporting `nt-architect`, `nt-adapters`, `nt-live`, and `nt-testing`.
**Scope:** current cwd `/home/mok/projects/nautilus_builder`; `/home/mok/projects/Nautilus-Daedalus` was read-only reference only.

### Additional surfaces reviewed

- `packages/strategy_validation/policy.py` and `validators.py` — recursive hard-rule and StrategySpec validation.
- `packages/ai_builder/provider.py` and `service.py` — advisory draft creation, acceptance, and audit save path.
- `packages/adapter_registry/service.py`, `packages/instrument_registry/service.py`, `services/api/routes/market_catalog.py`, `apps/web/lib/api.ts`, and `apps/web/components/market/MarketProfilePanel.tsx` — backend-owned market-profile DTO contract.
- `packages/backtest_jobs/*`, `packages/runtime_events/*`, `services/api/routes/backtest_jobs.py`, and `services/workers/nautilus_backtest_worker.py` — durable job and runtime-event audit seams.
- `packages/backtest_runner/*`, `pyproject.toml`, and `/home/mok/projects/Nautilus-Daedalus/pyproject.toml` — NautilusTrader pin, fixture/injected engine boundary, and Daedalus runtime version parity.
- `packages/promotions/service.py` and `services/api/routes/promotions.py` — shadow/promotion authority and evidence boundaries.
- `packages/workflow_spine/storage_config.py` — warning observed during frontend E2E web-server startup.

### Current structure status

- The previous top findings remain closed at code-contract level: AI drafts are validated before acceptance; forbidden credential/order references are recursively rejected; frontend market-profile requests match the backend validation payload; backtest jobs/runtime events carry audit fields; and Builder records the same `nautilus_trader==1.223.0` pin as Daedalus.
- Daedalus reference confirms the intended runtime split: Daedalus owns `run_gate_engine.py`, `run_execution_lane.py`, `TradeAction`, and execution reports; Builder still has no direct Daedalus import or live-order authority path in `packages/`, `services/`, or `apps/web` outside negative guards/tests.
- The backtest runner is still a fixture/injected boundary, not a concrete NautilusTrader `BacktestEngine` smoke. This is now correctly labeled in artifacts, but it remains a structural WATCH item before Builder can claim NautilusTrader backtest readiness.
- Local default Python is not aligned with the recorded pin: `python3` imports `nautilus_trader` from `/home/mok/.local/lib/python3.12/site-packages` at version `1.222.0`, while Builder and Daedalus both record `1.223.0`. This means current passing tests prove Builder contracts, not the installed NautilusTrader runtime.
- No `uv.lock`, requirements lock, or install-time check exists in Builder yet; dependency reproducibility depends only on `pyproject.toml` until a lock/sync policy is added.

### Fresh verification evidence

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 197 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed

python3 - <<'PY'
import importlib.metadata as md
import nautilus_trader
print(getattr(nautilus_trader, "__version__", "unknown"), md.version("nautilus_trader"))
PY
# 1.222.0 1.222.0
```

### Architectural status

**Status:** `WATCH` for NautilusTrader readiness.
Builder is safe as a contract/MVP scaffold with no live order authority, but it should not be described as a real NautilusTrader backtest runtime until the active environment is pinned/synced to Daedalus and at least one concrete NautilusTrader engine smoke exists.

## Production-readiness closure pass — 2026-05-24

**Status:** completed with segment reconciliation and master verification.

### Segment A — runtime dependency truth

Files added/changed:

- `packages/backtest_runner/runtime_check.py` — compares installed `nautilus_trader` distribution to `NAUTILUS_TRADER_VERSION`.
- `tests/backtest_runner/test_runtime_dependency_check.py` — locks mismatch, match, and active-environment checks.
- `uv.lock` — captures the Builder dependency graph with `nautilus-trader==1.223.0`.

Reconciliation:

- Builder and read-only Daedalus both record `nautilus_trader==1.223.0`.
- Active `python3` now imports `nautilus_trader` `1.223.0`, so local tests prove the pinned runtime instead of the older `1.222.0` package.

### Segment B — real NautilusTrader engine smoke

Files added/changed:

- `packages/backtest_runner/real_engine_smoke.py` — runs a minimal real `BacktestEngine` lifecycle with quiet logging, no data, no strategies, no adapters, no credentials, and no execution authority.
- `tests/backtest_runner/test_real_nautilus_engine_smoke.py` — verifies `real_nautilus_engine_smoke` remains separate from `fixture` and `injected_engine` evidence modes.

Reconciliation:

- Fixture and injected-engine seams remain explicit contract modes.
- The new smoke proves pinned NautilusTrader engine initialization/run/disposal, not a full catalog-backed strategy replay.

### Segment C — promotion evidence and FastAPI parity

Files changed:

- `packages/promotions/models.py` and `service.py` — require explicit validation, backtest, no-lookahead, gate, runtime-boundary, and risk evidence refs before shadow/final candidate readiness.
- `services/api/routes/promotions.py` — `/api/promotions/shadow` now rejects missing evidence with `422` and returns `201` only for explicit strategy/version identity, non-empty correctly typed evidence, and boolean gate compatibility.
- `services/api/app.py` and `services/api/fastapi_app.py` — lightweight and FastAPI bootstraps both route through the hardened promotion payload helper.
- `tests/promotions/test_shadow_evidence_contract.py`, `tests/api/test_route_mounts.py`, and existing promotion tests — lock missing-evidence rejection and explicit-evidence success.

Reconciliation:

- RED evidence: `rtk pytest tests/api/test_fastapi_app.py -q` failed 4 tests because FastAPI still imported the removed fabricated helper.
- GREEN evidence: `rtk pytest tests/api/test_fastapi_app.py tests/api/test_route_mounts.py tests/promotions -q` passed with 25 tests.

### Segment D — StrategySpec executable docs/schema alignment

Files changed:

- `packages/strategy_spec/models.py` and generated `strategy_spec.schema.json` — executable schema now accepts documented safe indicator blocks: `EMA`, `SMA`, `RSI`, `MACD`, `ATR`, `BollingerBands`, and `VWAP`; comparison operators now include `gte`, `lte`, and `eq`.
- `doc/nautilus_builder_hardguards.md` — clarifies `all`/`any` as executable combinators and explicitly excludes direct `not` from the MVP schema.
- `apps/web/lib/strategySpec.ts` — frontend allowed block list mirrors the executable schema.
- `tests/strategy_spec/test_allowed_block_alignment.py` — locks doc/schema alignment.

Reconciliation:

- Documented v1 block names no longer exceed executable schema truth except for explicitly excluded direct `not`.

### Segment E — readiness hygiene

Files changed:

- `README.md` — current limitations now reflect existing `pyproject.toml`, `services/api/fastapi_app.py`, `services/api/dev_server.py`, Next.js shell, and remaining production-integration gaps.
- `packages/workflow_spine/storage_config.py` — `BuilderPostgresConfig.schema` renamed to `db_schema` with backwards-compatible `schema` alias input.
- `tests/workflow_spine/test_storage_config.py` and `tests/integration/test_readme_readiness_hygiene.py` — lock warning-free naming and README reality.

Reconciliation:

- The avoidable Pydantic `schema` shadow warning is removed from the model contract.

### Master verification evidence

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 215 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# tsc --noEmit passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed
```

Authority grep found only guard tables, negative assertions, denied booleans, credential rejection tests/config, and documentation references for `submit_order`, `TradeAction`, credential/order tokens, and Daedalus runtime names. No Builder path gained live order authority.

## Catalog-backed replay closure start — 2026-05-24

Planning artifacts added for the remaining NautilusTrader readiness blocker: `docs/superpowers/specs/2026-05-24-catalog-backed-nautilus-replay-design.md` and `docs/superpowers/plans/2026-05-24-catalog-backed-nautilus-replay-implementation-plan.md`. The chosen design is a deterministic ParquetDataCatalog + BacktestNode replay using an official no-order SubscribeStrategy, preserving Builder's no-live-order boundary.

## Catalog-backed replay Segment 1 — real catalog/data/strategy smoke

**Completed:** 2026-05-24

Files changed:

- `packages/backtest_runner/catalog_replay_smoke.py` — writes deterministic quote ticks to a Nautilus `ParquetDataCatalog` and runs `BacktestNode` with the official no-order `SubscribeStrategy`.
- `packages/backtest_runner/__init__.py` — exports `CATALOG_BACKED_REPLAY_SMOKE_MODE` and `run_catalog_backed_nautilus_replay_smoke`.
- `tests/backtest_runner/test_catalog_backed_nautilus_replay_smoke.py` — proves catalog-backed data replay, strategy path, metrics sections, zero orders/positions, and no credentials/authority.

Reconciliation:

- Empty lifecycle smoke remains `real_nautilus_engine_smoke`.
- Catalog-backed replay is a distinct `catalog_backed_replay_smoke` evidence mode.
- The new smoke proves historical data from a catalog is replayed through Nautilus' high-level backtest path with result metrics, while still avoiding live venues and order submission.

Evidence:

```bash
rtk pytest tests/backtest_runner/test_catalog_backed_nautilus_replay_smoke.py -q
# RED: 0 passed, 1 failed because catalog-backed replay smoke function was missing
# GREEN: Pytest: 1 passed

rtk pytest tests/backtest_runner -q
# Pytest: 15 passed
```

## Catalog-backed replay Segment 2 — readiness wording

**Completed:** 2026-05-24

Files changed:

- `README.md` — now lists `packages/backtest_runner/catalog_replay_smoke.py` and describes the catalog-backed Nautilus replay smoke over synthetic historical quote ticks.
- `tests/integration/test_readme_readiness_hygiene.py` — locks the README against regressing to the old empty-lifecycle wording or overclaiming production-scale StrategySpec replay.

Evidence:

```bash
rtk pytest tests/integration/test_readme_readiness_hygiene.py -q
# RED: 1 passed, 1 failed because README still described only empty lifecycle smoke
# GREEN: Pytest: 2 passed

rtk pytest tests/backtest_runner tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 17 passed
```

## Master reconciliation — catalog-backed Nautilus replay

**Status:** completed on 2026-05-24.

The remaining NautilusTrader readiness blocker is closed at smoke-evidence level. Builder now records three separate real/contract backtest evidence lanes:

- `fixture` — contract fixture result normalization.
- `injected_engine` — injected engine protocol boundary.
- `real_nautilus_engine_smoke` — empty real BacktestEngine lifecycle initialization/run/disposal.
- `catalog_backed_replay_smoke` — real catalog-backed Nautilus replay over synthetic historical quote ticks using an official no-order SubscribeStrategy.

This is not full trading-production readiness. The next maturity step is a durable worker that loads user-selected catalog data and compiled StrategySpec-generated strategies, persists artifacts, and runs under production authz/CI/deployment controls.

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

Added `packages/artifact_store/` as a durable local JSON artifact seam for Builder-owned evidence. The store writes deterministic scoped refs in the form `artifact://builder/{project_id}/{user_id}/{artifact_type}/{artifact_id}`, persists JSON payloads under the configured root, records SHA-256 checksums, and enforces `UserProjectContext` scope on reads.

Files added:

- `packages/artifact_store/models.py`
- `packages/artifact_store/service.py`
- `packages/artifact_store/__init__.py`
- `tests/artifact_store/test_local_json_artifact_store.py`

Evidence:

```bash
rtk pytest tests/artifact_store/test_local_json_artifact_store.py -q
# RED: missing packages.artifact_store import
# GREEN: Pytest: 3 passed
```

## Production runtime readiness Segment 2 — user-selected catalog datasets

**Status:** completed on 2026-05-24.

Added `packages/catalog_datasets/` as the user-selected Nautilus catalog dataset seam. Datasets are registered with user/project identity, adapter/instrument/data type/timeframe/market/date-range fields, and a local `catalog_path`. Selection validates every backtest-profile field and rejects cross-project access through the existing auth scope policy. `BacktestJob` now records `user_id`, `project_id`, `dataset_id`, and `catalog_path` while preserving legacy job creation defaults.

Files added/changed:

- `packages/catalog_datasets/models.py`
- `packages/catalog_datasets/service.py`
- `packages/catalog_datasets/__init__.py`
- `packages/backtest_jobs/models.py`
- `packages/backtest_jobs/service.py`
- `tests/catalog_datasets/test_catalog_dataset_registry.py`
- `tests/backtest_jobs/test_dataset_scope_fields.py`

Evidence:

```bash
rtk pytest tests/catalog_datasets/test_catalog_dataset_registry.py tests/backtest_jobs/test_dataset_scope_fields.py -q
# RED: missing packages.catalog_datasets import
# GREEN: Pytest: 4 passed

rtk pytest tests/catalog_datasets tests/backtest_jobs -q
# Pytest: 8 passed
```

## Production runtime readiness Segment 3 — StrategySpec-generated catalog replay

**Status:** completed on 2026-05-24.

Added Builder's first real StrategySpec-generated Nautilus replay path. `packages.nautilus_rule_graph.strategy:RuleGraphBacktestStrategy` is now an importable no-order Nautilus `Strategy` that subscribes to quote ticks and carries the serialized Builder StrategySpec and compile hash in its config. `packages/backtest_runner/strategy_spec_replay.py` validates and compiles a StrategySpec, checks it against the selected catalog dataset, writes deterministic local quote-tick data into `ParquetDataCatalog`, runs `BacktestNode`, and returns evidence with `engine_mode="strategy_spec_catalog_replay"`. The worker can now run that replay path and persist the evidence through `LocalJsonArtifactStore`.

Files added/changed:

- `packages/nautilus_rule_graph/strategy.py`
- `packages/backtest_runner/strategy_spec_replay.py`
- `packages/backtest_runner/__init__.py`
- `services/workers/nautilus_backtest_worker.py`
- `tests/backtest_runner/test_strategy_spec_catalog_replay.py`
- `tests/backtest_runner/test_worker_integration.py`

Evidence:

```bash
rtk pytest tests/backtest_runner/test_strategy_spec_catalog_replay.py -q
# RED: missing STRATEGY_SPEC_CATALOG_REPLAY_MODE export
# GREEN: Pytest: 1 passed

rtk pytest tests/backtest_runner/test_worker_integration.py::test_worker_can_run_strategy_spec_catalog_replay_and_persist_artifact -q
# RED: run_backtest_job lacked context/artifact/dataset args
# GREEN: Pytest: 1 passed

rtk pytest tests/backtest_runner -q
# Pytest: 17 passed
```

## Production runtime readiness Segment 4 — backtest job authz/tenant controls

**Status:** completed on 2026-05-24.

Backtest job service/API now support user/project scoped access checks. `BacktestJobService.get_job()`, `request_cancel()`, and `transition_job()` accept an optional `UserProjectContext` and enforce the job's `scoped_artifact` through the shared auth policy. The lightweight API route accepts scoped `user_id`/`project_id` query values for read/cancel and returns `403 forbidden` for cross-project access. Job responses expose `user_id`, `project_id`, `dataset_id`, and `catalog_path` so downstream operators can audit tenant/dataset ownership.

Files changed:

- `packages/backtest_jobs/service.py`
- `packages/backtest_jobs/models.py`
- `services/api/routes/backtest_jobs.py`
- `services/api/app.py`
- `tests/backtest_jobs/test_job_scope_authorization.py`
- `tests/api/test_backtest_job_routes.py`

Evidence:

```bash
rtk pytest tests/backtest_jobs/test_job_scope_authorization.py tests/api/test_backtest_job_routes.py::test_backtest_job_routes_enforce_user_project_scope_when_supplied -q
# RED: BacktestJobService lacked context arg and API route did not handle scope query
# GREEN: Pytest: 3 passed

rtk pytest tests/auth tests/backtest_jobs tests/api/test_backtest_job_routes.py -q
# Pytest: 21 passed
```

## Production runtime readiness Segment 5 — CI/deployment evidence

**Status:** completed on 2026-05-24.

CI and deployment evidence now enumerate the production-readiness checks needed for the new seams. The CI template includes Python compile checks, the pinned NautilusTrader runtime check, the expanded contract test suite including `tests/artifact_store` and `tests/catalog_datasets`, and frontend type/unit/build/e2e checks. `infra/deployment/production-readiness-evidence.md` records closed seams and remaining deployment boundaries.

Files changed/added:

- `infra/ci/github-actions-test.yml`
- `infra/deployment/production-readiness-evidence.md`
- `README.md`
- `tests/integration/test_operability_baseline.py`
- `tests/integration/test_readme_readiness_hygiene.py`

Evidence:

```bash
rtk pytest tests/integration/test_operability_baseline.py::test_ci_template_covers_runtime_replay_frontend_and_new_storage_suites tests/integration/test_operability_baseline.py::test_deployment_readiness_evidence_documents_remaining_authority_boundaries tests/integration/test_readme_readiness_hygiene.py::test_readme_mentions_new_production_readiness_closure_boundaries -q
# RED: CI/deployment/README evidence missing
# GREEN: Pytest: 3 passed

rtk pytest tests/integration/test_operability_baseline.py tests/integration/test_readme_readiness_hygiene.py -q
# Pytest: 8 passed
```

## Master reconciliation — production runtime readiness closure

**Status:** completed on 2026-05-24.

The broader production-readiness blockers have been closed at Builder repository-contract level:

1. durable local artifact storage with scoped refs and checksums;
2. user/project-scoped catalog dataset selection;
3. StrategySpec-generated catalog replay through a real Nautilus `BacktestNode` and Builder no-order rule-graph strategy;
4. package/API/worker tenant scope checks for backtest jobs and artifacts;
5. CI/deployment evidence templates covering Python, Nautilus runtime, artifact/dataset suites, and frontend checks.

Master reconciliation also caught and fixed one review issue: worker execution now checks the supplied `UserProjectContext` against the job scope before RUNNING/SUCCEEDED transitions, preventing a cross-project worker context from mutating a job.

Master evidence:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api tests/artifact_store tests/catalog_datasets -q
# Pytest: 234 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed

python3 - <<'PY'
from packages.backtest_runner.runtime_check import check_nautilus_runtime_version
status = check_nautilus_runtime_version()
print(status.message)
assert status.is_match
PY
# nautilus_trader runtime matches pinned version 1.223.0

git diff --check
# passed
```

Authority grep for live-order/credential/Daedalus execution terms found only guard tables, denial tests, false authority booleans, runtime-version function names, and credential-rejection paths. No Builder live-order path was introduced.

## Deep review refresh — 2026-05-25 inventory-first semantic legacy/deprecation closure

**Status:** reviewed and documented on 2026-05-25. This pass used `superpowers:code-review` with NautilusTrader routing through `nt-review` plus `nt-architect`, `nt-adapters`, `nt-live`, and `nt-testing`. `aiogram-dialog-menus` was loaded; Builder has no Telegram/aiogram implementation surface, so that lens is only a negative-inventory check.

### Authoritative reference baseline refreshed

- NautilusTrader upstream `develop` was refreshed to `e43ecef` (`Add Plugin custom data callbacks`); installed Builder runtime still matches the repo pin `nautilus_trader==1.223.0`.
- NautilusTrader developer guide facts used for this pass:
  - adapter work is phased Rust core → instruments → market data → order execution → advanced features → config/factories → testing/docs;
  - new Rust-backed PyO3/live-adapter examples should prefer `nautilus_trader.live.LiveNode`; `TradingNode` is legacy v1/Cython/older-example territory;
  - DataTester/ExecTester evidence is required before claiming adapter data/execution compatibility;
  - adapter runtime code must use Nautilus' global runtime seam rather than raw `tokio::spawn()` from Python-driven paths.
- AI reference repos were refreshed/verified at: EvoMap/evolver `3d5386c`, LangChain `33875fd`, and LangGraph `d1e2ff0`. Builder has no direct LangChain/LangGraph/EvoMap package dependency or source import in `packages/`, `services/`, or `apps/web`.
- Daedalus reference repo remains read-only for this review. Its relevant boundary is still: Builder can author/validate/backtest/promote observational evidence, while Daedalus owns signal/gate/execution lanes and Telegram remains downstream-only.

### Current structure inventory after refresh

| Surface | Current state | Review note |
| --- | --- | --- |
| StrategySpec / validation | Strict Pydantic schema, recursive forbidden-token scan, JSON schema export | Good guard baseline; date-range/profile consistency is still distributed across separate services. |
| Adapter/instrument registry | Static Builder registry with disabled live execution modes | Registry says `BINANCE_PERP` supports quote ticks at adapter level, while the `BTCUSDT-PERP` instrument omits quote ticks even though StrategySpec replay requires them. |
| Backtest runner | Fixture runner, real empty engine smoke, catalog-backed subscribe smoke, and StrategySpec no-order `BacktestNode` replay | Stronger than earlier scaffold, but the StrategySpec replay writes synthetic test-kit quote ticks into the selected catalog path instead of consuming existing user-selected catalog data. |
| Artifact/dataset storage | Scoped local JSON artifact store plus in-memory dataset registry | Artifact store is rooted and checksum-backed; catalog dataset paths are not rooted/allowlisted and can point anywhere the worker can write. |
| API routes | Thin `ApiApp` and FastAPI adapters over package services | Route-level scope can be supplied by payload/query; real token/middleware propagation is not wired into FastAPI. |
| Worker | Backend-owned worker entrypoint enforces supplied context and persists StrategySpec replay artifacts | Good context enforcement when a context is supplied; production path still depends on caller providing a real context and safe dataset object. |
| Promotions | Shape-checked evidence refs, no live-order booleans, final manual approval guard | Evidence refs are not resolved against scoped artifact storage/checksums; several examples still use legacy unscoped artifact schemes. |
| Frontend | Next.js operator MVP with no order controls | Type/unit/build/e2e passed; UI remains observational and does not own runtime authority. |
| AI / EvoMap / LangChain / LangGraph | Advisory AI drafting only; no direct external framework imports | Alignment is positive: no direct advisory-to-execution coupling found. |
| aiogram / Telegram | No Builder implementation surface | Alignment is positive: no Builder aiogram-dialog runtime exists; Daedalus Telegram remains outside Builder. |

### Inventory-first semantic closure results

Source-only inventory over `packages/`, `services/`, and `apps/web` found no Builder source imports of `nautilus_brain`, `nautilus_runtime`, `langchain`, `langgraph`, `EvoMap`, `evolver`, `TradingNode`, `LiveNode`, `DataTesterConfig`, `ExecTesterConfig`, `tokio::spawn`, or `Arc<PyObject>`. Live-order terms appear in guard tables, negative tests, or false authority booleans only.

Legacy/deprecation inventory items that remain intentionally present but must stay fenced:

- `dataset_id="unspecified"` and unscoped fixture artifacts are compatibility/dev defaults, not production evidence.
- `artifact://backtests/...` and `artifact://validation/...` promotion examples are legacy/unscoped evidence shapes until promotion checks resolve scoped `artifact://builder/...` refs.
- `backtest_order_intent` in the backtest compile artifact is a semantic legacy label; it should not be reused for no-order StrategySpec replay readiness.
- Synthetic `TestDataStubs` catalog writes are smoke-test evidence only, not proof of user-selected dataset ingestion.

### Architectural status

**Architectural status: WATCH / production-readiness request changes.** The local contract suite is green and the no-live-order Builder/Daedalus split remains intact. The remaining risks are not ordinary unit failures; they are evidence-boundary and production-integration risks around catalog data provenance, path trust, real auth propagation, promotion evidence resolution, and registry/replay semantic drift.

### Fresh verification evidence

```bash
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

## Findings closure Segment 1 — catalog trust and read-only user replay

**Status:** completed on 2026-05-25.

Segment 1 split StrategySpec catalog evidence into explicit synthetic smoke vs read-only user-catalog replay. `strategy_spec_synthetic_catalog_smoke` remains the only path that writes deterministic Nautilus test-kit quote ticks, and it labels evidence as `dataset_source=synthetic_test_kit`. `strategy_spec_catalog_replay` now requires a configured `catalog_root`, validates the selected catalog path through `CatalogPathPolicy`, reads only pre-existing matching quote ticks, records catalog manifest checksum/file-count evidence, and fails closed for missing/empty catalogs.

Changed surfaces:

- `packages/catalog_datasets/service.py` — safe-root `CatalogPathPolicy`, symlink traversal rejection, corrected mismatch diagnostics.
- `packages/backtest_runner/strategy_spec_replay.py` — synthetic/user replay split, user-catalog read-only checks, manifest evidence.
- `services/workers/nautilus_backtest_worker.py` — StrategySpec replay passes/requires `catalog_root`.
- `tests/catalog_datasets/test_catalog_dataset_registry.py`
- `tests/backtest_runner/test_strategy_spec_catalog_replay.py`
- `tests/backtest_runner/test_worker_integration.py`

Evidence:

```bash
rtk pytest tests/catalog_datasets/test_catalog_dataset_registry.py tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/backtest_runner/test_worker_integration.py -q
# RED: missing synthetic replay helper / missing safe-root policy, then GREEN: Pytest: 13 passed

rtk pytest tests/catalog_datasets tests/backtest_runner -q
# Pytest: 26 passed
```

## Findings closure Segment 2 — auth-derived API scope and validated backtest job creation

**Status:** completed on 2026-05-25.

Segment 2 added strict API seams that derive `UserProjectContext` from verified bearer tokens, ignore spoofed `user_id`/`project_id` body/query fields, and validate backtest profile plus catalog dataset selection before creating jobs. The lightweight in-process `ApiApp` keeps dev/test compatibility, while FastAPI backtest job routes now require auth-derived context and pass strict validation inputs.

Changed surfaces:

- `services/api/routes/backtest_jobs.py` — strict context-derived create/read/cancel, 401/422/403 route responses, profile/dataset validation.
- `services/api/fastapi_app.py` — bearer-token auth helper and catalog dataset registry injection for strict routes.
- `packages/backtest_jobs/models.py` and `packages/backtest_jobs/service.py` — persisted `data_type`, `timeframe`, and `market_type` audit fields.
- `tests/api/test_backtest_job_routes.py`
- `tests/api/test_fastapi_app.py`
- `tests/backtest_jobs/*`

Evidence:

```bash
rtk pytest tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py tests/backtest_jobs -q
# RED: strict context/dataset args missing, then GREEN: Pytest: 21 passed

rtk pytest tests/auth tests/api tests/backtest_jobs tests/catalog_datasets -q
# Pytest: 59 passed
```

## Findings closure Segment 3 — scoped promotion evidence resolution

**Status:** completed on 2026-05-25.

Segment 3 added strict promotion evidence resolution. `PromotionService` can now be constructed with a `LocalJsonArtifactStore` plus auth context and will require scoped `artifact://builder/{project_id}/{user_id}/{artifact_type}/{artifact_id}` refs, resolve each artifact, enforce artifact type matches the evidence key, and carry checksum evidence into `PromotionRequest.evidence_checksums`. Legacy unscoped refs remain available only through explicit fixture/dev compatibility.

Changed surfaces:

- `packages/promotions/models.py` — `PromotionRequest.evidence_checksums`.
- `packages/promotions/service.py` — strict artifact-backed evidence verification.
- `services/api/routes/promotions.py` — strict route helper mode with scoped store/context.
- `tests/promotions/test_shadow_evidence_contract.py`
- `tests/artifact_store/test_local_json_artifact_store.py` (reused checksum/scope contract)

Evidence:

```bash
rtk pytest tests/promotions/test_shadow_evidence_contract.py -q
# RED: PromotionService lacked artifact/context strict mode, then GREEN: Pytest: 16 passed

rtk pytest tests/promotions tests/artifact_store tests/api -q
# Pytest: 65 passed
```

## Findings closure Segment 4 — registry/replay semantics and no-order output naming

**Status:** completed on 2026-05-25.

Segment 4 aligned the market catalog with StrategySpec replay by making `quote_ticks` visible and valid for `BTCUSDT-PERP`, while adding an instrument-level data-type guard so adapter-supported but instrument-unsupported modes are rejected. The backtest compile artifact now uses `output_mode=backtest_signal_observation`, and source-truth docs no longer use `BacktestOrderIntent` for Builder no-order artifacts.

Changed surfaces:

- `packages/instrument_registry/service.py` — `quote_ticks` availability and instrument data-type validation.
- `packages/strategy_compiler/compiler.py` — no-order backtest output mode renamed to `backtest_signal_observation`.
- `doc/nautilus_builder_hardguards.md`
- `doc/nautilus_builder_implementation_plan.md`
- `doc/nautilus_builder_implementation_prompts.md`
- `tests/instrument_registry/test_supported_instruments.py`
- `tests/strategy_compiler/test_compile_valid_spec.py`
- `tests/integration/test_semantic_legacy_closure.py`

Evidence:

```bash
rtk pytest tests/instrument_registry tests/strategy_compiler tests/integration/test_semantic_legacy_closure.py -q
# RED: quote_ticks missing / legacy output wording present, then GREEN: Pytest: 9 passed

rtk pytest tests/instrument_registry tests/strategy_compiler tests/api tests/backtest_runner tests/integration/test_semantic_legacy_closure.py -q
# Pytest: 67 passed
```

## Master reconciliation — 2026-05-25 findings closure

**Status:** completed on 2026-05-25.

The 2026-05-25 review findings are closed at repo-contract level:

1. StrategySpec user-catalog replay is read-only, root-validated, manifest-recorded, and split from synthetic smoke evidence.
2. Strict FastAPI backtest job routes derive scope from bearer auth and validate market profile plus scoped catalog dataset before job creation.
3. Strict shadow promotion resolves scoped Builder artifact refs through checksum/scope/type verification and carries evidence checksums.
4. Market catalog and StrategySpec replay agree on `quote_ticks` for `BTCUSDT-PERP`.
5. Builder no-order backtest artifacts use `backtest_signal_observation` / `BacktestSignalObservation` wording.

Additional reconciliation corrected FastAPI shadow-promotion wiring so strict promotion routes also require bearer auth and resolve scoped artifact evidence when an artifact store is configured.

Master evidence:

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

# Source authority grep over packages/services/apps source only found guard/negative-test/false-authority hits only.
git diff --check
# passed
```
