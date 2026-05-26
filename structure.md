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

## Deep review refresh — 2026-05-25 post-closure inventory review

**Status:** review completed on 2026-05-25. **Recommendation:** REQUEST CHANGES before any stronger production-readiness or promotion-readiness claim. **Architectural Status:** BLOCK for production exposure and strict promotion evidence semantics; CLEAR remains for the no-live-order-authority boundary.

### Authoritative reference baseline refreshed

- NautilusTrader official repo HEAD: `develop @ 107b9c707cae70bb8ea8580df86235b305754ceb`.
- EvoMap/evolver official repo HEAD: `main @ 3d5386cfe16660de05ef8ff5cbe9749b032e782c`.
- LangChain official repo HEAD: `master @ 33875fde2acf6ffb717915a895638274a6098ec2`.
- LangGraph official repo HEAD: `main @ d1e2ff0561a8b0b09212d0795c9d7b390a5de23a`.
- Nautilus docs checked: developer guide, adapter guide, execution testing spec, data testing spec, and backtesting concepts. The relevant alignment points remain: use `BacktestNode`/`ParquetDataCatalog` for catalog-backed backtest evidence, use DataTester/ExecTester evidence before adapter/execution compatibility claims, and do not label fixture or method-presence checks as production adapter readiness.
- LangChain/LangGraph docs checked as advisory context only: durable execution / human-in-the-loop / persistence patterns are references for future AI workflow design, not Builder runtime dependencies.

### Current structure inventory after refresh

- `packages/backtest_runner/strategy_spec_replay.py` is the key Nautilus alignment surface. It uses `ParquetDataCatalog` plus `BacktestNode`, but its catalog manifest helper currently hashes every `Path.rglob()` file and follows symlinked files inside an otherwise allowed catalog directory.
- `packages/promotions/service.py` and `packages/artifact_store/service.py` are the strict promotion-evidence surfaces. They verify Builder artifact ref shape, scope, type, and checksum, but missing scoped artifacts currently bubble as `FileNotFoundError`, and valid evidence artifacts are not semantically bound to the requested `compile_hash` / `strategy_version`.
- `services/api/fastapi_app.py` has strict auth-derived scope for backtest job create/read/cancel and strict shadow-promotion evidence, but strategy, AI draft/apply, workflow result, suggestion, lineage, runtime-event, and promotion-request routes remain unauthenticated and unscoped.
- `packages/workflow_spine/*` carries `project_id` on workflow results/suggestions, but repository/API lookups are by `result_id`, `strategy_lineage_id`, or `ai_thread_id` only. There is no `UserProjectContext` boundary for these reads.
- `packages/catalog_datasets/service.py` has a safe-root policy, but `CatalogDatasetRegistryService(catalog_root=None)` is still valid and allows absolute catalog paths to pass registration/selection unrooted. Strict callers must therefore prove they injected a root-policy registry before claiming catalog path allowlisting.
- `packages/ai_builder/*` remains direct-dependency-free with no LangChain/LangGraph/EvoMap imports. However, the API apply path accepts blank AI/provenance IDs and constructs a fresh in-memory audit store per request, so advisory lineage durability is weaker than the AI ecosystem references imply.
- No aiogram/Telegram runtime surface exists in Builder source. The loaded aiogram skill remains a negative-inventory lens only.

### Inventory-first semantic closure results

- `backtest_order_intent` / `BacktestOrderIntent`: absent from Builder no-order source truth; remaining hits are historical closure-plan text and negative tests only.
- Live/order authority source grep over `packages`, `services`, and `apps/web` found only guard/negative/false-authority surfaces (`may_submit_order: false`, forbidden validator strings, no credentials). No Builder source imports Daedalus execution or calls `submit_order`.
- AI/Telegram runtime import grep over executable Builder source found no `langchain`, `langgraph`, `EvoMap`, `evolver`, `aiogram`, or Telegram imports.
- Nautilus runtime source grep confirms current real-engine evidence is backtest/catalog only (`BacktestNode`, `ParquetDataCatalog`). There are no adapter `DataTesterConfig`/`ExecTesterConfig` implementations, so adapter/live compatibility must remain a future claim unless added explicitly.

### Architectural status

- **BLOCK:** strict promotion evidence can accept stale/wrong-compile artifacts and can 500 on missing artifacts; user-catalog manifests can follow nested symlinks; tenant/project scoping is incomplete for non-backtest routes.
- **WATCH:** catalog root policy is optional by construction; storage schema/namespace identifiers are not restricted to safe identifier shapes; AI apply/audit provenance is not durable at route level.
- **CLEAR:** Builder still has no live order authority, no Daedalus execution import, no aiogram runtime, and no LangChain/LangGraph/EvoMap runtime coupling.

### Fresh verification evidence

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
# WATCH: Vitest still emits Vite CJS Node API deprecation warning; Playwright web server still emits NO_COLOR/FORCE_COLOR warning.

# Semantic inventories: no live-order authority, no AI/Telegram runtime imports, no active order-intent source-truth term.
```

## R2 Implementation Segment 1 — promotion evidence lineage binding

**Status:** completed on 2026-05-25.

Segment 1 tightened strict promotion evidence so scoped Builder artifact refs are not only shape/scope/checksum verified, but also semantically bound to the promotion request. Strict shadow/final evidence now requires matching `compile_hash` and `strategy_version` / `strategy_version_id` in artifact payload or metadata. Missing/corrupt artifact reads are converted to typed domain `ValueError`s so API routes can return 4xx responses instead of leaking `FileNotFoundError`.

Changed surfaces:

- `packages/artifact_store/service.py` — typed missing/invalid artifact envelope errors.
- `packages/promotions/service.py` — evidence binding to requested compile hash and strategy version.
- `tests/promotions/test_shadow_evidence_contract.py`
- `tests/api/test_fastapi_app.py`

Evidence:

```bash
rtk pytest tests/promotions/test_shadow_evidence_contract.py -q
# RED: missing artifact / wrong compile hash / wrong strategy version accepted or leaked, then GREEN: Pytest: 19 passed

rtk pytest tests/promotions tests/artifact_store tests/api/test_fastapi_app.py -q
# Pytest: 37 passed

python3 -m compileall -q packages/artifact_store packages/promotions services/api/routes/promotions.py tests/promotions tests/artifact_store tests/api/test_fastapi_app.py
# compileall passed
```

## R2 Implementation Segment 2 — catalog traversal and strict root policy

**Status:** completed on 2026-05-25.

Segment 2 closed the nested catalog symlink and optional-root strict-path gaps. Catalog manifest generation now rejects symlinked files/directories before reading and verifies every resolved manifest candidate remains under the selected catalog root. `CatalogDatasetRegistryService` now exposes root-policy state and strict root-policy guards, and strict backtest job creation requires a root-policy registry before accepting dataset selection.

Changed surfaces:

- `packages/backtest_runner/strategy_spec_replay.py` — safe manifest traversal.
- `packages/catalog_datasets/service.py` — `has_root_policy`, `require_root_policy()`, and strict registration/selection flags.
- `services/api/routes/backtest_jobs.py` — strict job creation requires rooted catalog registry selection.
- `tests/backtest_runner/test_strategy_spec_catalog_replay.py`
- `tests/catalog_datasets/test_catalog_dataset_registry.py`
- `tests/api/test_backtest_job_routes.py`

Evidence:

```bash
rtk pytest tests/catalog_datasets/test_catalog_dataset_registry.py tests/backtest_runner/test_strategy_spec_catalog_replay.py tests/api/test_backtest_job_routes.py -q
# RED: manifest followed symlinks / strict registry accepted unrooted policy, then GREEN: Pytest: 22 passed

rtk pytest tests/catalog_datasets tests/backtest_runner tests/api/test_backtest_job_routes.py tests/api/test_fastapi_app.py -q
# Pytest: 46 passed

python3 -m compileall -q packages/catalog_datasets packages/backtest_runner services/api/routes/backtest_jobs.py tests/catalog_datasets tests/backtest_runner tests/api/test_backtest_job_routes.py
# compileall passed
```

## R2 Implementation Segment 3 — tenant/project FastAPI scoping

**Status:** completed on 2026-05-25.

Segment 3 extended strict FastAPI auth-derived scoping beyond backtest jobs and strict shadow promotion. Strategy create/list/detail/draft/version, runtime-event replay, AI draft, promotion-request, workflow result, workflow suggestion, and lineage status routes now require bearer auth in the FastAPI bootstrap. Strategy records carry user/project ownership when created through strict routes, and workflow repository reads now enforce project scope for results and suggestions. The lightweight `ApiApp` remains dependency-free fixture/dev compatibility.

Changed surfaces:

- `services/api/fastapi_app.py` — consistent bearer-context gate for production-facing non-backtest routes.
- `packages/strategy_spec/repository.py` and `services/api/routes/strategies.py` — scoped strategy ownership and route responses.
- `packages/workflow_spine/repository.py` and `services/api/routes/workflow_results.py` — scoped result/suggestion/lineage reads.
- `tests/api/test_fastapi_app.py`

Evidence:

```bash
rtk pytest tests/api/test_fastapi_app.py -q
# RED: routes accepted calls without auth / leaked cross-project data, then GREEN: Pytest: 9 passed

rtk pytest tests/api tests/workflow_spine tests/strategy_spec tests/runtime_events -q
# Pytest: 98 passed

python3 -m compileall -q packages/strategy_spec packages/workflow_spine services/api/routes/strategies.py services/api/routes/workflow_results.py services/api/fastapi_app.py tests/api tests/workflow_spine
# compileall passed
```

## R2 Implementation Segment 4 — storage identifiers and AI provenance/audit

**Status:** completed on 2026-05-25.

Segment 4 constrained Builder-owned storage identifiers and made AI apply provenance executable. SQL schema/table identifiers and Redis namespaces now use a strict safe identifier policy before interpolation into table names or stream prefixes. AI draft apply now rejects blank provenance IDs, and FastAPI mounts `/api/ai-builder/apply` with the app-level AI Builder service so injected audit stores persist route-level apply records across calls.

Changed surfaces:

- `packages/workflow_spine/storage_config.py` — shared safe storage identifier validator for Postgres/Redis config.
- `packages/workflow_spine/postgres_repository.py` and `packages/runtime_events/stream.py` — schema identifiers validated before SQL construction.
- `packages/ai_builder/service.py` and `services/api/routes/ai_builder.py` — non-empty apply provenance and typed route errors.
- `services/api/fastapi_app.py` — injected/reused AI audit store and strict `/api/ai-builder/apply` route.
- `tests/workflow_spine/test_storage_config.py`
- `tests/runtime_events/test_durable_stream.py`
- `tests/ai_builder/test_persistent_audit_store.py`
- `tests/api/test_fastapi_app.py`

Evidence:

```bash
rtk pytest tests/workflow_spine/test_storage_config.py tests/runtime_events/test_durable_stream.py tests/ai_builder/test_persistent_audit_store.py tests/api/test_fastapi_app.py -q
# RED: unsafe identifiers/blank provenance/ephemeral apply route allowed, then GREEN: Pytest: 24 passed

rtk pytest tests/workflow_spine tests/runtime_events tests/ai_builder tests/api -q
# Pytest: 101 passed

python3 -m compileall -q packages/workflow_spine packages/runtime_events packages/ai_builder services/api/routes/ai_builder.py services/api/fastapi_app.py tests/workflow_spine tests/runtime_events tests/ai_builder tests/api
# compileall passed
```

## R2 Implementation Segment 5 — fixture evidence labeling and frontend warning cleanup

**Status:** completed on 2026-05-25.

Segment 5 made fixture evidence explicit and removed the observed frontend verification warning paths. Fixture backtest normalization now emits `fixture://` refs with `fixture_evidence_only=true`, and workflow dashboard compatibility fallback now labels payloads as `evidence_mode=fixture_dev_only`. Strict FastAPI result routes already deny fallback fixture exposure unless a repository-owned result exists. Frontend Vitest config now uses an ESM `.mts` config, and the Playwright web server unsets conflicting color env vars before launching API/Next.

Changed surfaces:

- `packages/backtest_runner/result_normalizer.py` — fixture-only result refs and labels.
- `services/api/routes/workflow_results.py` — fixture/dev fallback label and production repository-result distinction.
- `apps/web/vitest.config.mts`, `apps/web/package.json`, `apps/web/playwright.config.ts` — verification warning cleanup.
- `tests/backtest_runner/test_result_normalizer.py`, `tests/backtest_runner/test_runner_dummy_data.py`
- `tests/api/test_workflow_results.py`, `tests/api/test_fastapi_app.py`
- `tests/web/test_frontend_infrastructure.py`

Evidence:

```bash
rtk pytest tests/backtest_runner/test_result_normalizer.py tests/backtest_runner/test_runner_dummy_data.py tests/api/test_workflow_results.py tests/api/test_fastapi_app.py tests/web/test_frontend_infrastructure.py tests/integration/test_browser_e2e_contract.py -q
# RED: fixture refs unlabeled and frontend config still warned, then GREEN: Pytest: 29 passed

rtk pytest tests/backtest_runner tests/api tests/web tests/integration -q
# Pytest: 121 passed

cd apps/web && npm test -- --run
# Vitest: 8 files / 12 tests passed with no Vite CJS warning observed
```

## Master reconciliation — 2026-05-25 R2 findings closure

**Status:** completed on 2026-05-25.

All named R2 findings are closed at repo-contract level:

1. Strict promotion evidence is scoped, checksummed, type-checked, and bound to requested `compile_hash` plus strategy lineage.
2. User-catalog manifest traversal rejects nested symlinks and strict catalog selection requires a configured root policy.
3. FastAPI production-facing strategy, workflow, runtime, AI, and promotion routes derive scope from bearer auth instead of client-supplied scope.
4. Storage schema/table/namespace identifiers are constrained to safe shapes before SQL/stream interpolation.
5. AI apply requires non-empty thread/cycle/lineage/version provenance and uses a reusable/injected FastAPI audit store.
6. Fixture evidence is visibly `fixture://` / `fixture_dev_only`, while strict FastAPI result reads require repository-owned results.
7. Frontend verification uses ESM Vitest config and the Playwright web server no longer exports conflicting color env vars.

Master evidence:

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
# typecheck passed; Vitest: 8 files / 12 tests passed; Next build passed; Playwright: 4 passed

git diff --check
# passed
```

Remaining watch items are deployment/integration concerns, not open repo-contract findings: production token issuer integration, production object-store deployment, catalog ingestion/curation operations, and downstream Daedalus consumption of strict promotion artifacts.

## Implementation progress — Segment UI-1 API JSON/proxy hardening

**Completed:** 2026-05-25

Files changed:

- `apps/web/lib/api.test.ts` — added Vitest coverage for JSON success, non-JSON proxy/HTTP failures, empty error bodies, and network failures.
- `apps/web/lib/api.ts` — `apiFetch()` now reads the response body once, parses JSON only for JSON content types, wraps network failures, and raises `ApiError` with status, URL, content type, and payload/snippet diagnostics.

Verification:

```bash
cd apps/web && npm test -- --run lib/api.test.ts
# Result: 5 passed
```

## Implementation progress — Segment UI-2 no-dependency polished shell

**Completed:** 2026-05-25

Files changed:

- `apps/web/app/globals.css` — added dependency-free Builder design tokens, dashboard layout, cards, panels, forms, status badges, terminal styling, and responsive rules.
- `apps/web/app/layout.tsx` — imports the global operator shell styles.
- `apps/web/app/page.tsx` and selected route/component TSX files — added semantic class names around existing Builder-only, observational/advisory surfaces.
- `tests/web/test_app_shell_contract.py` — locks the global CSS import and visual shell tokens.
- `tests/web/test_frontend_infrastructure.py` — locks the no-Tailwind/no-UI-library dependency boundary and required visual shell classes.

Verification:

```bash
rtk pytest tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py -q
# Result: 9 passed

cd apps/web && npm test -- --run lib/api.test.ts components/market/MarketProfilePanel.test.tsx components/strategies/StrategyListClient.test.tsx components/strategies/StrategyDetailClient.test.tsx
# Result: 9 passed
```

## Master reconciliation — VM frontend UI/API readiness pass

**Completed:** 2026-05-25

Segments reconciled:

1. API JSON/proxy hardening — closed `JSON.parse` failures from HTML/text/empty/proxy responses by centralizing safe parsing in `apps/web/lib/api.ts`.
2. No-dependency visual shell — closed plain-text VM demo presentation by importing global CSS and styling the operator dashboard without adding frontend dependencies.
3. Verification — frontend unit/type/build and Python contract suites passed after the changes.

Verification evidence:

```bash
rtk pytest tests/web tests/integration -q
# Result: 54 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Result: 271 passed

cd apps/web && npm run typecheck
# Result: passed

cd apps/web && npm test
# Result: 9 files / 17 tests passed

cd apps/web && npm run build
# Result: Next.js production build passed
```

Remaining watch item: Playwright browser execution was not rerun in this pass; previous repo guard still requires a provisioned browser before claiming full frontend E2E readiness.

## Post-implementation review — frontend UI/API hardening

**Completed:** 2026-05-25

Review verdict: **APPROVE / CLEAR** for the local diff. The review found no open critical/high/medium findings after adding the JSON error-payload regression. The implementation remains limited to frontend API diagnostics, no-dependency visual shell styling, tests, and review artifacts.

Review evidence is recorded in `findings.md` under `Post-implementation code review — 2026-05-25 frontend UI/API hardening`.

## Brainstorming implementation plan — Segment DEP-1 PyYAML test-extra closure

**Completed:** 2026-05-25

Context: VM02 reproduced two FastAPI contract-test failures after `uv sync --extra test` because `tests/api/test_fastapi_app.py` imports `make_valid_spec` from `tests/strategy_spec/test_schema_valid.py`, and that module imports `yaml` to validate the packaged StrategySpec YAML example. The repo manifest did not declare PyYAML in the test extra or lockfile, so a fresh synced VM environment could miss the parser.

Approaches considered:

1. **Recommended / implemented — declare PyYAML in the test extra and lock it.** This keeps YAML parsing a test/development dependency, matches the actual usage surface, and makes `uv sync --extra test` reproducible.
2. Add PyYAML to runtime dependencies. Rejected because production API/runtime code does not import `yaml`; only tests do.
3. Install PyYAML manually on VM02. Rejected because it would leave the repo manifest/lock unreproducible and fail on the next clean VM or CI sync.

Segment plan and outcome:

1. Inventory dependency surface — `rg` confirmed only `tests/strategy_spec/test_schema_valid.py` imports `yaml`; `pyproject.toml`/`uv.lock` had no PyYAML declaration.
2. TDD RED — added an operability manifest assertion that the test extra declares PyYAML, then confirmed it failed before the manifest change.
3. GREEN — added `PyYAML>=6.0` to `[project.optional-dependencies].test` and regenerated `uv.lock`, resolving `pyyaml==6.0.3`.
4. Reconciliation — verified fresh `uv sync --extra test`, targeted FastAPI/YAML tests, full Python contract suite, and frontend type/unit/build checks.

Files changed:

- `pyproject.toml` — declares `PyYAML>=6.0` under the test extra only.
- `uv.lock` — locks `pyyaml==6.0.3` for reproducible VM/CI test syncs.
- `tests/integration/test_operability_baseline.py` — guards the dependency contract so future clean environments keep YAML example tests installable.

Verification:

```bash
rtk pytest tests/integration/test_operability_baseline.py::test_python_project_declares_runtime_and_test_dependencies -q
# RED before manifest change: missing PyYAML assertion failed

uv sync --extra test
# Installed pyyaml==6.0.3 with the test extra

rtk pytest tests/integration/test_operability_baseline.py::test_python_project_declares_runtime_and_test_dependencies tests/api/test_fastapi_app.py::test_fastapi_bootstrap_reuses_strategy_repository_helpers tests/api/test_fastapi_app.py::test_fastapi_strategy_routes_require_auth_and_filter_by_project tests/strategy_spec/test_schema_valid.py::test_example_yaml_loads_as_valid_strategy_spec -q
# Pytest: 4 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 271 passed

cd apps/web && npm run typecheck && npm test && npm run build
# typecheck passed; Vitest: 9 files / 17 tests passed; Next build passed
```

Master reconciliation: the VM02 `ModuleNotFoundError: No module named 'yaml'` deployment-test finding is closed at repo manifest/lock level without changing Builder runtime authority, NautilusTrader pinning, frontend behavior, or Daedalus boundaries.

## Brainstorming implementation plan — Segment AI-2 OpenAI-compatible StrategySpec draft provider

**Started:** 2026-05-25

Context: the product workflow is user words -> AI draft -> strict Builder `StrategySpec` -> validation -> backtest -> manual promotion. The current `AdvisoryDraftProvider` is deterministic fixture-like scaffolding only, so this segment adds an optional OpenAI-compatible chat-completions provider without changing Builder's no-live-order boundary.

Approaches considered:

1. **Recommended / implementing — stdlib HTTP OpenAI-compatible provider behind env.** Use `OPENAI_API_KEY`, `OPENAI_BASE_URL`, and `OPENAI_MODEL` to opt into a provider that calls `/v1/chat/completions`, requests JSON output, parses the model content as strict JSON, and relies on `validate_strategy_spec()` before acceptance. This avoids a new SDK dependency and keeps provider activation explicit.
2. Add the OpenAI Python SDK. Rejected for this segment because the repo already avoids unnecessary dependencies, the user requested an OpenAI-compatible URL/API rather than OpenAI-only SDK coupling, and stdlib HTTP is enough for the provider seam.
3. Replace the advisory provider globally. Rejected because local/dev/test environments must keep deterministic behavior when OpenAI env vars are absent.

Segment plan:

1. TDD RED: add provider tests proving env activation, chat-completions payload shape, strict JSON parsing, audit metadata redaction, and validation rejection for forbidden model output.
2. GREEN: implement `OpenAICompatibleProviderConfig`, `OpenAICompatibleDraftProvider`, env-based provider selection, prompt/response metadata capture, and service audit wiring.
3. Reconciliation: verify the new AI provider tests plus existing AI/API contract tests; confirm no API key is stored and no live order/`TradeAction` authority is introduced.
4. Review: run a focused post-implementation code review for security, boundary, maintainability, and Nautilus Builder hardguard alignment.

Expected files:

- `packages/ai_builder/provider.py`
- `packages/ai_builder/service.py`
- `packages/ai_builder/__init__.py`
- `tests/ai_builder/test_openai_compatible_provider.py`
- `structure.md`, `findings.md`, `handguard.md`

## Implementation progress — Segment AI-2 OpenAI-compatible StrategySpec draft provider

**Completed:** 2026-05-25

Files changed:

- `packages/ai_builder/provider.py` — added `OpenAICompatibleProviderConfig`, `OpenAICompatibleDraftProvider`, env-based provider selection, stdlib chat-completions transport, strict JSON content parsing, response metadata capture, and advisory-provider metadata.
- `packages/ai_builder/service.py` — added `AiBuilderService.from_env()`, provider-error handling, prompt/metadata/validation audit records, and credential-prompt rejection before audit persistence.
- `services/api/fastapi_app.py` — FastAPI bootstrap now builds the AI service from env, so `OPENAI_API_KEY` + `OPENAI_BASE_URL` + `OPENAI_MODEL` opt into the OpenAI-compatible provider while missing env falls back to advisory mode.
- `packages/ai_builder/__init__.py` — exports the OpenAI-compatible provider/config and provider-builder helper.
- `tests/ai_builder/test_openai_compatible_provider.py` — locks env activation, payload shape, metadata redaction, malformed JSON rejection, validation of forbidden model output, and credential-prompt rejection.

Reconciliation:

- The provider remains advisory-only and returns only StrategySpec JSON for validation.
- No OpenAI SDK or frontend dependency was added; stdlib `urllib` keeps the dependency surface narrow.
- API keys are used only in the outbound `Authorization` header and are not persisted in audit records.
- `validate_strategy_spec()` remains the acceptance gate, so `submit_order`, `TradeAction`, credential references, malformed JSON, and missing fields are not accepted.
- Backtest and promotion flow remains unchanged: generated drafts still require validation/backtest evidence and manual promotion.

Verification:

```bash
rtk pytest tests/ai_builder/test_openai_compatible_provider.py -q
# RED before implementation: ImportError for missing OpenAICompatibleDraftProvider
# GREEN after implementation: Pytest: 7 passed

rtk pytest tests/ai_builder -q
# Pytest: 17 passed

rtk pytest tests/api/test_fastapi_app.py tests/api/test_route_mounts.py -q
# Pytest: 18 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 278 passed

cd apps/web && npm run typecheck && npm test && npm run build
# typecheck passed; Vitest: 9 files / 17 tests passed; Next build passed
```

## Brainstorming implementation plan — Segment VM-API-1 and CONFIG-1 live UI/config closure

**Started:** 2026-05-25

Context: VM02 showed the web shell at `http://192.168.4.82:3000`, but browser calls through the Next proxy returned `500 Internal Server Error` for `/api/adapters` and `/api/strategies` while the API itself returned JSON on `http://192.168.4.82:8000`. The user also requested a UI-based configuration section with multiple tabs for configuring multiple LLM/model roles.

Approaches considered:

1. **Recommended / implemented — fix server-side proxy precedence and add a frontend-only config section.** Make `next.config.mjs` rewrites prefer `BUILDER_API_BASE_URL` over `NEXT_PUBLIC_API_BASE_URL`, preserving browser-direct mode as optional. Add `/config` with multiple tabs for Providers, Models, Guardrails, and Audit. This addresses the VM proxy failure and gives operators a visible LLM config workspace without adding backend persistence or browser-side secrets.
2. Use `NEXT_PUBLIC_API_BASE_URL` for all VM traffic. Rejected because browser-direct cross-origin calls are more fragile and can require CORS/firewall changes; the existing app is designed to use Next rewrites when possible.
3. Build backend-persistent config management immediately. Rejected for this segment because it would require auth/scoped storage, secret handling, and API policy decisions beyond the reported UI/config need.

Segment plan:

1. TDD RED for proxy: add a regression proving Next rewrites prefer `BUILDER_API_BASE_URL` for server-side proxying.
2. GREEN proxy: update `apps/web/next.config.mjs` and prove local `next start` can proxy `/api/adapters` and `/api/strategies` to the VM API.
3. TDD RED for config UI: add component and contract tests for a multiple-tab LLM config section with no browser-side API key input.
4. GREEN config UI: add `/config`, `ModelConfigTabs`, home nav link, and no-dependency styles.
5. Reconciliation: run frontend type/unit/build/e2e, Python contract suite, `git diff --check`, and a local production proxy smoke.

## Implementation progress — Segment VM-API-1 live web/API proxy fix

**Completed:** 2026-05-25

Files changed:

- `apps/web/next.config.mjs` — rewrites now use `process.env.BUILDER_API_BASE_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"` so VM/server-side proxy config wins over browser-public config.
- `tests/web/test_frontend_infrastructure.py` — added a regression locking the server-side proxy precedence.

Verification:

```bash
rtk pytest tests/web/test_frontend_infrastructure.py::test_next_rewrites_use_server_api_base_before_browser_public_base -q
# RED before config change: missing BUILDER_API_BASE_URL assertion failed
# GREEN after config change: Pytest: 1 passed

BUILDER_API_BASE_URL=http://192.168.4.82:8000 npm run build
BUILDER_API_BASE_URL=http://192.168.4.82:8000 npm run start -- --hostname 127.0.0.1 --port 3100
curl -i http://127.0.0.1:3100/api/adapters
# HTTP/1.1 200 OK; JSON adapter list proxied from VM API
curl -i http://127.0.0.1:3100/api/strategies
# HTTP/1.1 200 OK; [] JSON proxied from VM API
```

Deployment note: this repo fix must still be pulled/rebuilt/restarted on VM02 before `http://192.168.4.82:3000/api/*` changes from the currently observed 500s.

## Implementation progress — Segment CONFIG-1 multiple-tab LLM config UI

**Completed:** 2026-05-25

Files changed:

- `apps/web/app/config/page.tsx` — added a Builder configuration route.
- `apps/web/components/config/ModelConfigTabs.tsx` — added a client-side tabbed configuration workspace for Providers, Models, Guardrails, and Audit.
- `apps/web/app/page.tsx` — added a `Config` navigation link.
- `apps/web/app/globals.css` — added dependency-free config tab/panel styling.
- `apps/web/components/config/ModelConfigTabs.test.tsx` — covers tab navigation, model editing, guardrails, audit copy, and no API-key input.
- `tests/web/test_config_ui_contract.py` — locks route mounting, env labels, guardrail copy, and no browser-side secret field.
- `apps/web/app/backtests/[jobId]/page.tsx` and `apps/web/components/promotions/PromotionRequestPanel.tsx` — restored exact E2E-visible guard text for allowed cancel and manual approval state.

Reconciliation:

- Config UI is frontend-only draft configuration. It does not persist secrets, does not write backend env, and does not grant live trading authority.
- LLM provider options are OpenAI-compatible, local OpenAI-compatible gateway, and offline advisory fixture; no LangChain/LangGraph/EvoMap runtime dependency was added.
- Guardrails tab repeats `validate_strategy_spec()`, `signal_preview_only`, no credentials, no `submit_order` / `TradeAction`, and manual promotion requirements.

Verification:

```bash
cd apps/web && npm test -- --run components/config/ModelConfigTabs.test.tsx
# RED before component: import failed for missing ModelConfigTabs
# GREEN after component: 1 passed

rtk pytest tests/web/test_config_ui_contract.py -q
# Pytest: 1 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 280 passed

cd apps/web && npm run typecheck && npm test && BUILDER_API_BASE_URL=http://192.168.4.82:8000 npm run build && npm run test:e2e
# typecheck passed; Vitest: 10 files / 18 tests passed; Next build passed with /config route; Playwright: 4 passed
```

## Brainstorming implementation plan — Segment UI-ANTD-1 Ant Design operator console

**Started:** 2026-05-26

Context: the current web UI was visually closer to a scaffold/contract demo than a user-friendly trading-builder console. The user compared it unfavorably with QuantDinger / QuantDinger-Vue and approved the practical React stack: `antd` and `@ant-design/icons`.

Approaches considered:

1. **Recommended / implemented — Ant Design React on the existing Next.js app.** Keep the current React/Next architecture, add `antd` + `@ant-design/icons`, and rebuild the shell/dashboard/config surfaces with AntD Layout, Cards, Statistics, Steps, Tabs, Forms, Selects, Alerts, and Badges. This gives a product-grade admin/trading console without a Vue migration.
2. Vue / Ant Design Vue migration. Rejected because Nautilus Builder is already Next.js/React; migrating to Vue would expand scope, duplicate frontend foundations, and delay the AI → StrategySpec → backtest workflow.
3. Continue custom CSS only. Rejected for the polished UI segment because it is slower, more brittle, and less user-friendly than a mature component system now that the user explicitly approved a pre-built UI kit.

Segment plan:

1. TDD RED: add source-contract tests requiring the approved AntD React stack, an AntD operator shell, AntD dashboard workflow surface, and AntD config UI with no browser-side secrets.
2. GREEN: install `antd` and `@ant-design/icons`, mount AntD reset CSS, wrap pages with `OperatorAppShell`, add a sidebar/topbar/safety status shell, add `BuilderDashboard`, and convert LLM config tabs to AntD forms/cards/tabs.
3. Reconciliation: preserve no-live-authority guardrails, no Vue migration, no browser API-key input, existing API proxy behavior, and existing Playwright user journey.
4. Verification: run focused Python UI contracts, TypeScript, Vitest, Next build, Playwright, full Python contract suite, diff/audit checks.

## Implementation progress — Segment UI-ANTD-1 Ant Design operator console

**Completed locally:** 2026-05-26

Files changed:

- `apps/web/package.json` and `apps/web/package-lock.json` — added approved React UI dependencies `antd` and `@ant-design/icons`.
- `apps/web/app/layout.tsx` — imports AntD reset CSS and mounts `OperatorAppShell` around all pages.
- `apps/web/components/shell/OperatorAppShell.tsx` — adds sidebar navigation, top health/status bar, and always-visible advisory/no-live-authority guard badges.
- `apps/web/components/dashboard/BuilderDashboard.tsx` — adds AntD KPI cards, AI-to-backtest `Steps`, visible workflow surface cards, and tabbed operator workspaces for strategy drafting, runtime observation, AI drafting, and manual promotion.
- `apps/web/components/config/ModelConfigTabs.tsx` — converts the LLM provider/model/guardrail/audit config surface to AntD `Tabs`, `Form`, `Select`, `Input`, `Alert`, `Badge`, and `Card` components while keeping secrets backend-only.
- `apps/web/app/page.tsx` — now renders `BuilderDashboard` in the app shell.
- `apps/web/app/globals.css` — adds AntD shell/dashboard polish while retaining the no-live-order-authority styling boundary.
- `apps/web/vitest.setup.ts` — adds deterministic test polyfills for AntD `ResizeObserver` and `matchMedia` usage.
- `tests/web/test_antd_operator_ui_contract.py`, `tests/web/test_app_shell_contract.py`, `tests/web/test_frontend_infrastructure.py`, and `tests/web/test_config_ui_contract.py` — lock the AntD stack, no Vue migration, shell mounting, no-secret config UI, and no live authority.

Reconciliation:

- The redesign is frontend-only; it does not change the FastAPI API, backtest runner, Nautilus replay contracts, AI provider acceptance gate, or promotion authority.
- The app remains React/Next; QuantDinger-Vue remains UX inspiration only, not copied code or a Vue migration.
- UI strings still state advisory-only / observational-only / manual promotion and do not introduce `submit_order` or `TradeAction` authority in page entry points.
- Browser config still does not collect provider API keys or secret fields.
- AntD warnings encountered during TDD were closed by replacing deprecated `Space direction`, `Alert message`, `List`, and `Steps.description` usage.

Verification:

```bash
rtk pytest tests/web/test_antd_operator_ui_contract.py -q
# RED before implementation: 4 failed for missing antd deps/shell/dashboard/Form usage
# GREEN after implementation: included in focused suite below

rtk pytest tests/web/test_antd_operator_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py -q
# Pytest: 15 passed

cd apps/web && npm run typecheck && npm test
# typecheck passed; Vitest: 10 files / 18 tests passed

cd apps/web && npm run test:e2e
# Playwright: 4 passed

cd apps/web && npm run build
# Next build passed; / route first-load JS 249 kB, /config first-load JS 280 kB after AntD
```

### Final reconciliation refresh — Segment UI-ANTD-1

**Refreshed:** 2026-05-26 after cleanup before commit/push.

- Removed a stale unused AntD icon import from `OperatorAppShell`.
- Cleaned generated `__pycache__`, Playwright test-results, and ignored TypeScript build-info artifacts after verification.
- Reconfirmed the segment remains frontend/UI scoped: no FastAPI contract changes, no live trading authority, no browser-side provider secret inputs, no Vue migration, and no Daedalus execution coupling.

Fresh verification evidence:

```bash
git diff --check
# passed

rtk pytest tests/web/test_antd_operator_ui_contract.py tests/web/test_app_shell_contract.py tests/web/test_frontend_infrastructure.py tests/web/test_config_ui_contract.py -q
# Pytest: 15 passed

python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# Pytest: 284 passed

cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest: 10 files / 18 tests passed; Next build passed; Playwright: 4 passed

cd apps/web && npm audit --omit=dev --audit-level=high
# exit 0; only moderate next/postcss advisory remains, with a breaking force-fix path
```

## Brainstorming implementation plan — Segment AI-UI-1 prompt-to-StrategySpec UI and compact workflow

**Started:** 2026-05-26

Context: after the AntD operator shell landed, the natural-language Builder workflow was still incomplete: the backend AI draft/apply endpoints and frontend API wrappers existed, but `AiStrategyCopilot` did not provide a user text input, result preview, validation status, or real apply action. The dashboard also exposed too many equal-weight surfaces before the user reached the actual prompt-first workflow.

Design approved by user direction:

1. Add a compact AntD prompt panel where the operator describes the strategy in plain text.
2. Call `generateAiDraft()` with durable `ai_thread_id` / `improvement_cycle_id` audit IDs and show accepted/rejected status, validation errors, explanation, and strict StrategySpec JSON preview.
3. Enable `Apply to Builder` only after the generated draft is accepted; send lineage/version IDs to `applyAiDraftToBuilder()`.
4. Make the dashboard prompt-first and smaller: compact AntD provider sizing, default the main workspace tab to AI prompt, reduce card/body/font weight, and keep StrategySpec/backtest/promotion as downstream tabs.
5. Preserve hardguards: advisory-only, draft lifecycle only, no live order controls, no browser LLM secrets, no automatic backtest/promotion.

## Implementation progress — Segment AI-UI-1 prompt-to-StrategySpec UI and compact workflow

**Completed locally:** 2026-05-26

Files changed:

- `apps/web/components/ai-builder/AiStrategyCopilot.tsx` — replaced placeholder text/button with a real compact AntD flow: strategy prompt textarea, audit/lineage inputs, Generate StrategySpec action, accepted/rejected result panel, JSON preview, validation errors, and Apply to Builder action gated by accepted drafts.
- `apps/web/components/ai-builder/AiStrategyCopilot.test.tsx` — added Vitest coverage for successful prompt → draft → apply and rejected draft guard behavior.
- `apps/web/components/dashboard/BuilderDashboard.tsx` — moved the operator workspace to prompt-first (`defaultActiveKey="ai"`), compacted steps/cards, and made downstream workflow tabs numbered.
- `apps/web/components/shell/OperatorAppShell.tsx` — set AntD `componentSize="small"` and smaller theme tokens.
- `apps/web/app/globals.css` — added compact dashboard, compact workflow, compact AI copilot, and compact spec preview sizing rules.
- `tests/web/test_ai_copilot_frontend.py` — locks the prompt input, generate/apply wiring, accepted-gated apply behavior, and compact prompt-first dashboard contract.

TDD evidence:

```bash
cd apps/web && npm test -- --run components/ai-builder/AiStrategyCopilot.test.tsx
# RED before implementation: 2 failed; missing Strategy prompt label and flow UI
# GREEN after implementation: 1 file / 2 tests passed

pytest tests/web/test_ai_copilot_frontend.py -q
# RED before implementation: 3 failed for missing prompt, accepted-gated apply, and compact workflow
# GREEN after implementation: 3 passed
```

Reconciliation:

- The frontend now performs the intended user workflow: user words → AI draft endpoint → accepted StrategySpec preview → apply endpoint with provenance IDs.
- Apply remains disabled until the backend reports `accepted: true`; rejected drafts display validation errors and cannot be applied from the UI.
- This segment does not create a backtest job, promotion request, live order action, or browser-side provider secret input.
- If a staged FastAPI deployment requires bearer auth, the UI will surface the API error through the existing safe `apiFetch()` error path; auth/session UX remains a separate segment.

## Reference UI architecture review — QuantDinger / QuantDinger-Vue

**Checked:** 2026-05-26

Sources reviewed:

- `https://github.com/brianmok888/QuantDinger/blob/main/docs/screenshots/architecture.png`
- `https://github.com/brokermr810/QuantDinger-Vue`

Reference takeaways:

- QuantDinger presents the product as a full AI quant operating system: client/agent access, market/user/news inputs, gateway/auth, engine layers for indicator/signal/strategy/backtesting/AI analysis, optional execution/output, multi-agent workflow, infrastructure, safety/compliance, and a closed-loop AI workflow.
- QuantDinger-Vue groups user-facing pages into clear product areas: analysis/research, strategy/IDE/backtesting, execution/portfolio, and billing/community/user settings.
- Its frontend structure separates API modules, shared components, config, app bootstrap/core, layouts, router, state store, utilities, i18n, and page-level views.
- The stack is Vue 2 / Ant Design Vue / charting / CodeMirror / Axios / vue-i18n, but Nautilus Builder remains Next.js/React/AntD React by prior decision.

Nautilus Builder mapping:

| QuantDinger reference area | Nautilus Builder equivalent | Boundary |
| --- | --- | --- |
| AI analysis / dashboard / indicator analysis | `AiStrategyCopilot`, dashboard, future market-research pages | Advisory-only; no execution authority. |
| Indicator IDE / backtest center / trading assistant / trading bot | StrategySpec builder, backtest jobs, results | StrategySpec and Nautilus replay evidence only. |
| QuickTradePanel / portfolio / exchange account modal | Not a Builder feature | Do not add quick trade, exchange credentials, or portfolio execution controls. |
| Billing / community / profile / user / settings | `/config` today; future user/settings only if auth/session UX is added | No browser-side model/exchange secrets. |
| `src/api`, `layouts`, `router`, `store`, `views` | `apps/web/lib/api.ts`, `components/shell`, Next `app/`, local component state | Keep Next app router; do not migrate to Vue. |

Current segment alignment:

- The new prompt-first AI tab now matches the reference's closed-loop shape at UI level: idea/prompt → StrategySpec draft → validation → later backtest → later manual promotion.
- The dashboard was compacted to reduce the scaffold feel and make the first user action obvious.
- The Builder scope intentionally omits reference execution widgets such as quick trade and exchange account binding.

Final verification summary for Segment AI-UI-1:

- `pytest tests/web/test_ai_copilot_frontend.py -q` — 3 passed.
- `cd apps/web && npm test -- --run components/ai-builder/AiStrategyCopilot.test.tsx` — 2 passed.
- Full targeted Python suite — 285 passed after `compileall`.
- Frontend gates — typecheck, Vitest 20 tests, Next build, and Playwright 4 tests passed.
- `npm audit --omit=dev --audit-level=high` exited 0 with only the existing moderate Next/PostCSS advisory.

## Implementation plan — Segment BT-1 backtest center contracts

**Started:** 2026-05-26 10:05:52Z

Using the requested brainstorming/autopilot/TDD workflow, the next implementation segment adopts the safest reusable parts of `prediction-market-backtesting` as clean-room Builder contracts:

1. Add explicit backtest run request/manifest models.
2. Add artifact/report policy models with checksum, media type, and scope checks.
3. Add dataset/source provenance fields that can support later catalog/cache/source-mode work.
4. Add equity/metrics/report section summaries for later rich result UI.
5. Preserve Builder hardguards: no credentials, no live trading authority, no `TradeAction`, no `submit_order`, manual promotion only.

Design spec: `docs/superpowers/specs/2026-05-26-backtest-center-contracts-design.md`.

## Implementation completion — PMBT/QuantDinger adoption slice

**Completed:** 2026-05-26 10:27:08Z

Segments completed in this slice:

1. **BT-1 Backtest runner contracts and report policy**
   - Added `packages/backtest_runner/contracts.py` with `BacktestRunRequest`, `BacktestRunManifest`, `BacktestArtifactRef`, `BacktestDatasetProvenance`, and `BacktestReportSummary`.
   - `normalize_backtest_result()` now carries report-summary metadata while preserving existing artifact/result fields.
2. **BT-2 Dataset/cache/source modes**
   - Added catalog source/cache mode policy to `CatalogDataset` for `catalog`, `local_fixture`, `external_mirror_manifest`, `user_fetched_manifest`, and `synthetic_test_kit` modes.
   - Manifest-backed modes require Builder artifact manifest refs; fixture modes are explicitly fixture-cache only.
3. **BT-3 Strategy module registry**
   - Added metadata-only `StrategyModuleRegistryService` for safe StrategySpec-derived modules.
   - The registry does not import or execute module paths and rejects non-allowlisted module paths.
4. **BT-4 Offline research/optimizer jobs**
   - Added `packages/research_jobs` with offline-only parameter-search job contracts.
   - Jobs require manual promotion and expose no live/order authority.
5. **UI-RESULTS Rich result metadata**
   - Results API and dashboard now expose/render `report_summary` sections, chart metadata, and explicit no-execution authority labeling.

This implements the practical shared core of the PMBT ideas while staying Nautilus Builder-owned and preserving the Builder/Daedalus/NautilusTrader boundary.

Verification evidence:

```bash
git diff --check
python3 -m compileall -q packages services tests
rtk pytest tests/backtest_runner tests/catalog_datasets tests/strategy_registry tests/research_jobs tests/api/test_workflow_results.py -q
# 60 passed
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/catalog_datasets tests/research_jobs tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
# 310 passed
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
# typecheck passed; Vitest 11 files / 21 tests passed; Next build passed; Playwright 4 passed
```

Remaining future segments:

- Persist run manifests/artifact refs into the job worker output store for non-fixture runs.
- Add a dedicated Research Center API/UI for `research_jobs`.
- Add a chart library only when equity/drawdown payloads are stable enough to justify the dependency.
- Keep NautilusTrader real-engine smoke separate from fixture/injected evidence.

## Standalone platform pivot — Builder decouples from Nautilus-Daedalus

**Started:** 2026-05-26

Context: product direction changed from "Builder as a companion for Nautilus-Daedalus" to "Builder as the standalone open-source AI strategy builder + NautilusTrader platform." Nautilus-Daedalus is now a private/personal reference only. Builder may adopt clean-room architectural patterns from ND, but it must not depend on ND at runtime, import ND internals, copy private schema names, or require an ND checkout.

Design/spec written:

- `docs/superpowers/specs/2026-05-26-standalone-builder-platform-design.md`

Segment PLATFORM-1 implementation:

- Added `infra/migrations/002_builder_standalone_platform.sql` as a Builder-owned PostgreSQL control-plane migration under only the `builder` schema.
- Added `tests/infrastructure/test_builder_standalone_platform_migration.py` to lock the migration inventory and safety constraints.
- Updated `doc/nautilus_builder_hardguards.md` authority boundary so future paper/live support is explicit and mode-gated instead of Daedalus-owned.

New standalone control-plane areas:

1. Strategy/versioning: `builder.strategy_specs`, `builder.strategy_param_versions`, `builder.active_strategy_params`.
2. Data/catalog: `builder.dataset_manifests` with catalog root, source/cache mode, Nautilus data class/type, instrument, venue, bar type, time range, and traversal guard.
3. Backtest/report: `builder.backtest_jobs`, `builder.backtest_run_manifests`, `builder.backtest_artifacts` with lineage/version/compile hash/checksum/media type binding.
4. Research/optimizer: `builder.research_jobs`, `builder.optimizer_trials` as offline/manual-promotion-only records.
5. AI continuous improvement: `builder.ai_threads`, `builder.ai_draft_audits`, `builder.ai_result_reviews`, `builder.ai_improvement_suggestions`, `builder.ai_experiment_cycles`, `builder.ai_candidate_rankings`, `builder.ai_feedback_memory`.
6. Promotion: `builder.promotion_candidate_packages`, `builder.promotion_approvals`.
7. Runtime: `builder.runtime_profiles`, `builder.paper_runs`, `builder.live_runs`, `builder.trade_actions`, `builder.execution_reports`, and enriched `builder.runtime_events` metadata.
8. Telegram: `builder.telegram_users`, `builder.telegram_subscriptions`, `builder.telegram_delivery_log` as notification-only records.

Authority reconciliation:

- Existing web/backtest/promotion surfaces still remain no-live-authority and keep `may_submit_order=false`.
- The migration only creates durable space for future paper/live lanes; it does not add order-submission code, exchange credentials, broker adapters, or browser-side authority.
- Dangerous flags default false: `paper_trading_enabled`, `live_trading_enabled`, `execution_authority`, and `may_submit_order`.
- Live authority can only be represented when `runtime_mode='live'`, profile is enabled, manual review is required, reconciliation is required, a risk profile exists, a credential slot reference exists, activation identity/time exist, and config checksum is present.

Remaining segments after PLATFORM-1:

- Persist AI draft/review/improvement cycles into the new DB tables.
- Persist real backtest/research run manifests and artifacts into the control plane.
- Add paper runtime profile scaffolding with simulated execution only.
- Add Telegram notification/menu scaffolding using aiogram-dialog patterns.
- Add live runtime scaffolding last, behind risk/reconciliation/credential-slot gates.
- Add execution lifecycle services only after paper and live runtime guards are test-proven.

### PLATFORM-1 final verification

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

PostgreSQL syntax verification also applied `001_builder_workflow_storage.sql` plus `002_builder_standalone_platform.sql` successfully in a disposable `postgres:16-alpine` container using `psql -v ON_ERROR_STOP=1`.

## Execution lane decoupling — standalone lane scaffold

**Started:** 2026-05-26

Context: after PLATFORM-1 established the standalone Builder control plane, the next required runtime split is an execution lane that can run independently while the operator continues creating/researching other strategies. The lane must consume explicit execution commands, not live strategy-process objects, so strategy authoring/backtest/research work can continue without owning order lifecycle.

Design/spec written:

- `docs/superpowers/specs/2026-05-26-execution-lane-decoupling-design.md`

Segment EXEC-1 implementation:

- Added `packages/execution_lane/` with strict Pydantic contracts for `ExecutionLaneProfile`, `ExecutionLaneCommand`, `ExecutionLaneReport`, status enums, and `ExecutionLaneService`.
- Added `services/workers/execution_lane_worker.py` as a backend-only worker scaffold. It imports the execution-lane package only and reports `strategy_lane_coupled=false`.
- Added API contract routes under `/api/execution-lane/status`, `/api/execution-lane/profiles`, and `/api/execution-lane/commands` in both lightweight `ApiApp` and FastAPI bootstrap.
- Added `infra/migrations/003_builder_execution_lane.sql` for lane runs, command queue, reports, and worker heartbeats.
- Added TDD coverage in `tests/execution_lane/`, `tests/api/test_execution_lane_routes.py`, and `tests/infrastructure/test_builder_execution_lane_migration.py`.

Runtime separation:

- Strategy/AI/backtest/research lanes produce drafts, evidence, and candidate approvals.
- Gate/manual approval path produces an execution command with lineage/version, risk decision, order intent, and idempotency key.
- Execution lane worker claims commands from its own lane queue and emits lane-owned reports.
- Existing strategy work can continue because command processing does not import strategy modules or depend on browser/session lifetime.

Authority reconciliation:

- Paper lane is simulated only and keeps `may_submit_order=false`.
- Live lane remains disabled unless both profile and command carry explicit live authority plus risk profile, credential slot ref, reconciliation, approval, activation identity/time, and approved risk decision.
- This segment does not submit real broker orders. Nautilus `LiveNode`/adapter-backed submission remains a later segment behind the EXEC-1 contracts.

### EXEC-1 final verification

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
