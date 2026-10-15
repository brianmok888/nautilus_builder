# PROJECT KNOWLEDGE BASE

**Generated:** 2026-10-15
**Commit:** 0c5459e8 (working tree carries local modifications; knowledge reflects the scanned filesystem state)
**Branch:** master

## OVERVIEW
Nautilus Builder combines Python strategy/workflow domain packages and API adapters with a Next.js 15, React 19 and Ant Design 6 operator app. TradeHUD observes Nautilus-Daedalus (ND); Builder does not own its live trading runtime.

## STRUCTURE
```text
nautilus_builder/
|-- doc/             # Primary product policy and runtime boundaries
|-- docs/            # ADRs, operations, TradeHUD runbooks and derived plans
|-- packages/        # Canonical domain logic, contracts and repositories
|-- services/        # API adapters, application factories and workers
|-- apps/web/        # Operator app and read-only TradeHUD presentation
|-- tests/           # Feature-mirrored Python contracts; not frontend execution
|-- scripts/         # Direct development, seed and verification entrypoints
|-- infra/migrations/ # Raw baseline SQL
`-- migrations/      # Alembic migration surface; baseline SQL still exists
```

## WHERE TO LOOK
| Task | Location | Routing note |
|---|---|---|
| Product identity and hardguards | `doc/README.md`, `doc/nautilus_builder_{spec,hardguards}.md` | Read before derived plans. |
| Strategy contracts and validation | `packages/strategy_spec/`, `packages/strategy_validation/` | Domain contracts precede API/UI projections. |
| Backtest behavior and engine modes | `packages/backtest_runner/` | Local `engine_contract.py` defines engine assumptions. |
| Session planning and command lifecycle | `packages/execution_lane/`, `packages/workflow_spine/` | Planning is not execution evidence. |
| Persistent Builder state | `packages/postgres/`, `migrations/`, `infra/migrations/` | Distinguish repositories from migration mechanisms. |
| HTTP composition and API tests | `services/api/`, `tests/api/` | In-process and ASGI factories differ. |
| Ordinary frontend API access | `apps/web/lib/api.ts`, `apps/web/middleware.ts` | Client access and server proxy/auth have separate owners. |
| ND payload contracts | `packages/tradehud_contracts/`, `tests/tradehud_contracts/` | Python contract authority; UI consumes normalized data. |
| TradeHUD feeds and panels | `apps/web/lib/tradehud/`, `apps/web/components/tradehud/` | Follow their local guides for display behavior. |
| Web routes and shared components | `apps/web/app/`, `apps/web/components/`, `apps/web/lib/` | Local guides own route, component and helper conventions. |
| Redis contract enforcement | `tests/tradehud_redis/`, `docs/tradehud-*.md` | Separate wire contracts from runbook claims. |

## CODE MAP
Digest-supplied symbol evidence only; reference counts were not measured.

| Symbol | Type | Location | Refs | Role |
|---|---|---|---|---|
| `create_app` | Factory | `services.api` | Unmeasured | Returns the in-process `BuilderApiApp`. |
| `create_fastapi_app` | Factory | `services/api/fastapi_app.py` | Unmeasured | Actual ASGI composition; `app_factory.py` delegates. |
| `SqliteWorkflowRepository` | Repository | `packages/workflow_spine/postgres_repository.py` | Unmeasured | SQLite despite the historical filename. |

## CONVENTIONS
- `doc/` defines product/runtime policy; implementation and executable contracts establish current code behavior. Derived `docs/superpowers/` plans are not runtime authority.
- Domain rules belong in `packages/`; HTTP routes adapt them and frontend code projects their outputs.
- Builder = product; Strategy Builder = module; NautilusTrader = engine; ND = live control system; TradeHUD = observational UI.
- `tests/web/` is a Python/source contract slice. Browser and React execution checks run separately inside `apps/web/`.
- Consult the nearest child `AGENTS.md` for domain details; this file routes cross-subtree work rather than repeating those guides.

## ANTI-PATTERNS
- Never give Builder/TradeHUD ND live-order authority. UI commands, session plans and approved intent do not prove submission or execution.
- Never move ND contract truth into TSX or treat this checkout as authority to modify Nautilus-Daedalus.
- Never collapse missing data into true zero, discard source provenance or expose unsanitized connection URLs.
- Never send API bearer tokens to the browser; proxy injection is server-side and limited to explicitly local environments.
- Do not claim `TradeHudService` provides Redis integration: it is mock-only; FastAPI selects Redis separately.
- Do not infer implemented `src/`, `crates/`, `configs/` or `tools/` trees from target-architecture documents.
- Do not import the adjacent Nautilus-Daedalus engine version or runtime assumptions into Builder backtests.

## UNIQUE STYLES
- Redis defaults to the `builder` namespace, rejects `nd`, and uses colon-delimited stream names rather than `builder.*`.
- `PostgresWorkflowRepository` is a deprecated name for the SQLite workflow seam; actual PostgreSQL repositories live in `packages/postgres/`.
- TradeHUD SSE implementation lives in `replay-feed.ts`; `sse-feed.test.ts` does not imply an `sse-feed.ts` implementation.
- The ordinary web client is `api.ts`; `apiClient.ts` is absent. `middleware.ts` owns same-origin proxy/no-store behavior.
- Both baseline SQL and Alembic exist; ADR 0003 is context, not proof that either migration runner replaced the other.

## COMMANDS
Run from the repository root unless a subshell changes directory.

```bash
python3 -m pytest tests/<seam>/ -q
(cd apps/web && npm run typecheck)
(cd apps/web && npm run test)
(cd apps/web && npm run build)
(cd apps/web && npm run test:e2e)
scripts/e2e_webui.sh
```

## NOTES
- Root Ruff and basedpyright configuration is scoped; inspect its inclusion rules before describing results as repository-wide coverage.
- Root `vitest.config.ts` is a placeholder, not the frontend test entrypoint.
- `services/api/fastapi_cli.py` is the CLI factory surface; stale `app_factory.py` refactor prose does not supersede the actual ASGI implementation.
- Existing code includes real domain/API/UI surfaces; old docs describing them as planned-only are stale. Presence alone does not establish production readiness.
- This digest-only update does not establish current Git commit or branch; metadata above records that evidence limit explicitly.
