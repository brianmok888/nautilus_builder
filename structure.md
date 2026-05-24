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
