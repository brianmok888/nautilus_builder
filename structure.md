# Nautilus Builder Structure Review

**Review date:** 2026-06-08
**Target repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus`
**Review mode:** `$superpowers:code-review` routed through `$superpowers:nt-review` (primary) with `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing`, and `aiogram-dialog-menus` as supporting boundary lenses.
**Current verdict:** **REQUEST CHANGES** — architecture status **BLOCK** until auth/project-scope gaps are closed.

## Authoritative references checked

- NautilusTrader official repo: <https://github.com/nautechsystems/nautilus_trader>
- NautilusTrader Developer Guide: <https://nautilustrader.io/docs/latest/developer_guide>
- NautilusTrader Adapters guide: <https://nautilustrader.io/docs/latest/developer_guide/adapters/>
- NautilusTrader Data Testing Spec: <https://nautilustrader.io/docs/latest/developer_guide/spec_data_testing/>
- NautilusTrader Execution Testing Spec: <https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/>
- EvoMap Evolver: <https://github.com/EvoMap/evolver>
- LangChain: <https://github.com/langchain-ai/langchain>
- LangGraph: <https://github.com/langchain-ai/langgraph>
- Daedalus local reference: `/home/mok/projects/Nautilus-Daedalus`

## Repository shape (current tracked surface)

`git ls-files packages services apps/web tests scripts doc docs` reports **542 tracked files** across the review surface:

| Area | Tracked files | Role |
|---|---:|---|
| `packages/` | 136 | Canonical Python domain layer: strategy specs, validation, compiler, backtests, execution lane, auth, AI builder, stores, Postgres seams. |
| `services/` | 25 | FastAPI and lightweight API adapter layers plus backend worker stubs. |
| `apps/web/` | 121 | Next.js 15 / React 19 / Ant Design 6 operator UI. Must remain observational and backend-driven. |
| `tests/` | 178 | Contract and regression suite. Several tests currently encode known auth-scope gaps. |
| `scripts/` | 8 | Local/dev/demo orchestration and seed scripts. |
| `doc/` | 13 | Product/runtime source truth. |
| `docs/` | 61 | Derived runbooks, implementation artifacts, deployment/verification docs. |

## Boundary model

| Boundary | Current status | Evidence / notes |
|---|---|---|
| Builder vs live order authority | **Aligned** | `packages/strategy_validation/policy.py` blocks `submit_order`, `TradeAction`, credential terms; `packages/backtest_runner/config_builder.py` rejects credentials; execution lane payloads keep `may_submit_order=False` in paper paths. |
| Builder vs Daedalus | **Aligned but needs wording discipline** | Daedalus owns live execution, TradeAction intent, ExecutionReport, Telegram delivery, EvoMap/LangGraph decision lanes. Builder must only produce specs, validation/compile/backtest evidence, and reviewed handoff artifacts. |
| NautilusTrader version | **Aligned** | Builder `pyproject.toml` pins `nautilus_trader==1.227.0`; Daedalus `pyproject.toml` also pins `1.227.0`. |
| NT adapter readiness claims | **WATCH** | Official adapter docs require Rust/Python adapter layers and DataTester/ExecTester evidence. Builder can gate on evidence refs but must not claim it produces adapter compliance evidence. |
| Python `TradingNode` / Rust `LiveNode` wording | **WATCH** | Builder uses Python `TradingNode` as an integration-specific paper/runtime contract; docs should not present it as the universal current live runtime. Rust-backed `LiveNode` remains the future/current Rust v2 path. |
| AI/EvoMap/LangChain/LangGraph | **Aligned** | Builder does not depend on EvoMap/LangChain/LangGraph in `packages/`, `services/`, or `pyproject.toml`; it uses an OpenAI-compatible advisory provider and validates outputs before acceptance. |
| aiogram-dialog / Telegram | **Aligned** | Builder has no aiogram/aiogram-dialog dependency. Daedalus owns Telegram dialog/runtime paths; Builder docs may reference this only as an external downstream notification boundary. |
| Frontend vs runtime authority | **Aligned with caveats** | UI carries API token handling for local VM mode and no direct order authority; browser must never collect exchange credentials or own worker/runtime handles. |
| API project scoping | **BLOCK** | Strategy list and mutation routes do not consistently require context or pass context into repository methods; see `findings.md` H-01/H-02. |

## High-level architecture map

```text
nautilus_builder/
├── doc/                         # Product/runtime source truth
├── docs/                        # Derived runbooks, verification, deployment docs
├── packages/
│   ├── strategy_spec/           # StrategySpec schema, repositories, demo seed data
│   ├── strategy_validation/     # Builder hard-rule validation and forbidden references
│   ├── strategy_compiler/       # StrategySpec -> compile artifacts/profiles
│   ├── ai_builder/              # Advisory AI draft generation + audit storage
│   ├── backtest_runner/         # NT BacktestEngine/BacktestNode smoke and run contracts
│   ├── backtest_jobs/           # Backtest job lifecycle service
│   ├── execution_lane/          # Backend-owned TradingNode paper/live contract models
│   ├── workflow_spine/          # Workflow lineage/result storage seams
│   ├── runtime_events/          # Runtime event stream seams
│   ├── adapter_registry/        # Builder-approved adapter profiles
│   ├── auth/                    # Token, project scope, policy, audit/rate-limit helpers
│   └── postgres/                # Postgres migrations/repositories
├── services/api/                # FastAPI route adapter layer over packages/*
├── services/workers/            # Backend-only worker entrypoints
├── apps/web/                    # Observational operator UI
├── scripts/                     # Local/dev seed and run helpers
└── tests/                       # Contract-first regression suite
```

## Current changed-diff assessment

The current uncommitted diff adds demo-evidence seeding and replaces private `_jobs_by_id` access in `services/api/routes/evidence_summary.py` with public `list_jobs_for_strategy()` methods.

| Diff area | Assessment |
|---|---|
| `services/api/routes/evidence_summary.py` | Directionally good: avoids private backtest service internals. Still inherits evidence-semantics risks: compile can be marked passed from status without a hash, and any non-empty `compile_hash` is accepted. |
| `packages/backtest_jobs/service.py` | In-memory public query methods are small and coherent. |
| `packages/backtest_jobs/postgres_service.py` | Works functionally but refreshes/scans all jobs instead of using `PostgresBacktestJobRepository.list_by_strategy_version()`. |
| `scripts/seed_builder_demo_data.py` | Useful demo flow, but broad `except Exception: pass` can hide seed failures. Demo hashes are intentionally fake and must stay labelled demo-only. |
| `tests/api/test_evidence_summary.py` | Good coverage for public methods/status mapping. Does not cover Postgres query-path efficiency or compile-hash validation. |
| Demo/verification docs | Useful runbook updates. Need current review artifacts to state that demo evidence is not production evidence. |

No direct `submit_order(` or authoritative `TradeAction(` call was found in production Builder code during the review scan. `TradeAction`/`submit_order` references are expected in docs/tests/policy text and Daedalus boundary references.

## Verification evidence collected during this review

```bash
python3 -m compileall -q packages services tests scripts
# pass

python3 -m pytest tests/api/test_evidence_summary.py -q
# 15 passed

python3 -m pytest tests/ -q --tb=line
# 906 passed, 1 skipped, 1 warning

cd apps/web && npm run typecheck
# pass

cd apps/web && npm run build
# pass

cd apps/web && npm run test
# failed: 1 dashboard layout test exceeded the default 5000 ms Vitest timeout under full-suite load

cd apps/web && npx vitest run --config vitest.config.mts --testTimeout=10000
# 115 passed, 4 skipped

python3 -m pytest \
  tests/api/test_fastapi_app.py::test_fastapi_strategy_routes_require_auth_and_filter_by_project \
  tests/api/test_route_auth_scope.py::TestRouteAuthScope::test_all_api_routes_require_auth -q
# 2 passed, but this is a false sense of safety: the tests currently encode/permit public list access.
```

Additional manual probes:

- `GET /api/strategies` with **no token** returned `200` and included an alpha user's strategy.
- `GET /api/strategies` with a **different beta token** returned `200` and included the alpha user's strategy.
- `POST /api/strategies/{strategy_id}/approve` with a beta token successfully approved an alpha-owned strategy.
- Production startup accepted a short token when `BUILDER_AI_AUDIT_SQLITE_PATH` was configured, because `validate_production_token()` is not wired into FastAPI startup.

## Stop condition for this review

This review is complete when `structure.md`, `findings.md`, and `handguard.md` reflect the current 2026-06-08 risk state and verification evidence. The repo is **not** merge-ready for production claims until the high-priority auth/scope findings in `findings.md` are fixed and covered by failing-then-passing regression tests.

## Master reconciliation — catalog-backed Nautilus replay

`catalog_backed_replay_smoke` writes synthetic historical quote ticks into a `ParquetDataCatalog` and runs NautilusTrader `BacktestNode` with the official no-order subscribe strategy. This is Builder evidence that the pinned Nautilus runtime can replay catalog data through the backtest data path; it is **not full trading-production readiness** and does not replace DataTester/ExecTester/reconciliation evidence for adapters or live execution.
