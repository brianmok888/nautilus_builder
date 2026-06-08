# Nautilus Builder Handguard

**Review date:** 2026-06-08
**Purpose:** Runtime and review invariants for Nautilus Builder. These are hard boundaries, not suggestions.
**Current state:** REQUEST CHANGES until the auth/project-scope gates below are implemented.

## 1. Authority boundary — Builder never owns live order submission

Builder production code must not call `submit_order(`, construct authoritative `TradeAction(`, hold direct exchange execution credentials in browser/UI state, or directly couple to Daedalus runtime internals.

Required false/blocked values in Builder-owned production paths:

```python
execution_authority = False
may_submit_order = False
live_trading_authority = False
advisory_only = True
browser_credentials_allowed = False
credential_inputs_allowed = False
strategy_lane_coupled = False
```

Current enforcement surfaces:

- `packages/strategy_validation/policy.py` blocks `submit_order`, `modify_order`, `cancel_order`, `close_position`, `TradeAction`, and credential terms in StrategySpec inputs.
- `packages/backtest_runner/config_builder.py` rejects live credentials in backtest config.
- `packages/backtest_runner/contracts.py` uses `Literal[False]` for backtest execution authority and credential usage.
- `packages/execution_lane/models.py` rejects paper-mode live authority and requires multiple gates for any live authority fields.
- `packages/execution_lane/sessions.py` keeps paper session configs `execution_authority=False` and `may_submit_order=False`.

Guard: reject any PR that adds a Builder-side production `submit_order(` path or authoritative `TradeAction(` construction.

## 2. API auth and project-scope gate — currently BLOCKING

Every `/api/*` FastAPI route except health/build liveness endpoints must do all of the following:

1. Accept bearer authorization.
2. Call `require_context(authorization)`.
3. Return `401` when auth is absent/invalid.
4. Pass `UserProjectContext` into package/repository calls that read or mutate scoped data.
5. Return `403` or an empty scoped list for wrong-project access.

Known gaps as of 2026-06-08:

- `GET /api/strategies` does not validate auth or pass context.
- `POST /api/strategies/{strategy_id}/approve` authenticates but does not pass context into repository mutation.
- `POST /api/strategies/{strategy_id}/clone` authenticates but does not pass context into repository clone.
- Several read-only `/api` catalog/config routes have an auth parameter but do not validate it; explicitly allowlist them only if the product decision is public metadata.
- Static auth tests are insufficient because they check for an `authorization` parameter rather than runtime behavior.

Guard: no production-readiness claim until runtime tests prove missing-token and wrong-project requests fail for every protected `/api` route.

## 3. Production environment policy gate — currently not fully wired

`packages/auth/policy.py` defines the required policy:

- `BUILDER_ENV` must be `local`, `staging`, or `production`.
- In `staging` or `production`, `BUILDER_API_TOKEN` must exist, be at least 32 chars, and not be a known dev token.
- `NEXT_PUBLIC_BUILDER_API_TOKEN` is forbidden in staging/production.
- CORS origins must not be empty or wildcard in staging/production.

Guard: `services/api/fastapi_app.py` must call `validate_builder_env()`, `validate_production_token()`, and `validate_cors_config()` during startup. Do not rely only on `_register_env_dev_token()`.

## 4. Strategy repository scope gate

All strategy repositories must preserve and enforce `user_id`/`project_id` scope for:

- save/create
- list
- detail
- update draft
- create version
- approve/update status
- clone

Guard: Postgres strategy storage must include scope columns or equivalent scoped ownership metadata. In-memory and Postgres repositories must have the same context semantics.

## 5. NautilusTrader evidence gate

Builder may produce and store:

- StrategySpec drafts and versions
- validation reports
- compile metadata/artifacts
- backtest jobs/results/manifests
- evidence refs and promotion gate decisions

Builder must not claim it produces adapter-compliance evidence unless an actual adapter suite produced it. For NT adapter readiness claims, require:

- DataTester evidence for claimed data adapter behavior.
- ExecTester evidence for claimed execution adapter behavior.
- Reconciliation reports for claimed live execution readiness.
- Adapter guide capability matrix for venue-specific behavior.

Guard: UI/docs must distinguish `passed_inferred` from artifact-backed evidence. Do not mark compile/replay/promotion as production-ready from lifecycle status alone.

## 6. TradingNode / LiveNode wording gate

- Python `nautilus_trader.live.node.TradingNode` examples in Builder are integration-specific/paper sandbox contracts.
- Rust-backed `nautilus_trader.live.LiveNode` is the current/future Rust v2 path for new Rust-backed PyO3 adapter work.
- Builder does not currently run Rust `LiveNode`.

Guard: reject docs that present Builder's Python TradingNode contract as universal Nautilus live production readiness.

## 7. Daedalus boundary gate

Daedalus is the execution authority and owns:

- approved-intent `TradeAction` generation/handling
- order submission surface
- `ExecutionReport` source of execution truth
- Telegram delivery runtime
- EvoMap/LangChain/LangGraph decision/advisory lanes
- custom adapter runtime evidence

Builder may reference Daedalus only through documented handoff/evidence contracts. Builder must not import or edit Daedalus internals from this repo.

Guard: no direct `Nautilus-Daedalus` runtime imports in Builder packages/services.

## 8. aiogram-dialog / Telegram gate

Builder must not add `aiogram` or `aiogram-dialog` dependencies. Telegram dialog/menu ownership remains in Daedalus (`nautilus_runtime/live/telegram_gateway/`). Builder may emit/record notification configuration contracts only after explicit design and tests.

Guard: reject Builder-side aiogram/aiogram-dialog runtime dependencies.

## 9. AI advisory gate

Builder AI output is advisory-only:

- Provider endpoint comes from operator env/config, never model output.
- LLM output must pass StrategySpec validation before acceptance.
- No AI output may auto-apply live strategy rules or execution authority.
- Prompt/audit persistence must redact secrets before production use.

Guard: treat all model output and user prompt text as untrusted input.

## 10. Postgres identifier gate

Every schema/table identifier interpolated into SQL must be validated with a strict identifier helper before use. Parameter binding protects values, not identifiers.

Guard: constructors and migrations must reject unsafe schema/table names. Do not interpolate operator-controlled identifiers raw.

## 11. Fixture/demo evidence gate

Fixture and demo data are allowed only when explicitly labelled and disabled by default in production:

- `BUILDER_ALLOW_FIXTURE_FALLBACK` must remain off by default.
- `res_001` fallback must be fixture/dev-only.
- Demo compile hashes must not be presented as real artifact checksums.
- Seed scripts must not hide unexpected failures.

Guard: reject any PR that silently converts demo/fixture evidence into production evidence.

## 12. Worker isolation gate

Native Nautilus runners must not run from the API event loop. They belong in backend worker processes or explicit CLI/operator paths.

Guard: `services/api/` must not directly start a native `TradingNode`; worker entrypoints own runtime lifecycle.

## 13. Verification gate before readiness claims

Minimum backend gate:

```bash
python3 -m compileall -q packages services tests scripts
python3 -m pytest tests/ -q --tb=line
```

Frontend readiness gate when UI claims change:

```bash
cd apps/web && npx tsc --noEmit
cd apps/web && npx vitest run
cd apps/web && npm run build
```

Runtime/live-readiness claims also require NT evidence refs (DataTester/ExecTester/reconciliation) and Daedalus execution-boundary confirmation.

## 14. Legacy/deprecation closure schedule

| Item | Status on 2026-06-08 | Deadline | Guard |
|---|---|---:|---|
| `storage_config.py` legacy schema alias | OPEN | 2026-07-01 | Remove after cutoff; no new callers. |
| `PostgresWorkflowRepository` alias | OPEN | 2026-07-01 | Prefer `SqliteWorkflowRepository`; remove alias after cutoff. |
| Backtest legacy hash derivation | OPEN | 2026-07-01 | Keep disabled by default; remove env escape after cutoff. |
| `allow_legacy_fixture_refs` | OPEN | 2026-07-01 | Strict evidence for non-dev promotions. |
| `res_001` fixture fallback | WATCH | 2026-07-01 | Production flag must stay off. |
| `NEXT_PUBLIC_BUILDER_API_TOKEN` local mode | WATCH | n/a | Forbid in staging/production startup. |

## 15. Current review blockers

Do not claim merge-ready/production-ready until these are fixed:

1. H-01: strategy list auth/project leak.
2. H-02: approve/clone cross-project mutation.
3. H-03: production auth/CORS policy not wired into FastAPI startup.
4. H-04: route auth tests are static/insufficient.

See `findings.md` for file/line evidence and concrete fixes.

## 16. Master reconciliation — catalog-backed Nautilus replay

`CATALOG_BACKED_REPLAY_SMOKE_MODE` / `catalog_backed_replay_smoke` must remain a smoke-only gate. It writes synthetic historical quote ticks into a catalog and exercises NautilusTrader BacktestNode replay wiring. It is **not full trading-production readiness**, and it does not satisfy DataTester, ExecTester, adapter reconciliation, or live execution evidence requirements.
