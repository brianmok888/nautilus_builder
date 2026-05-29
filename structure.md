# Nautilus Builder Structure Review

**Review date:** 2026-05-29 (deep review, post-ultragoal)
**Target repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus`
**Review mode:** `$superpowers:code-review` routed through `$superpowers:nt-review` (primary) with `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing`, `$superpowers:aiogram-dialog-menus` supporting checks.

## Authoritative references

- NautilusTrader: `nautilus_trader==1.223.0` (pinned in pyproject.toml)
- https://github.com/nautechsystems/nautilus_trader
- https://nautilustrader.io/docs/latest/developer_guide
- https://nautilustrader.io/docs/latest/developer_guide/adapters/
- https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/
- Daedalus reference: `/home/mok/projects/Nautilus-Daedalus` (`nautilus_trader==1.227.0`)
- EvoMap: https://github.com/EvoMap/evolver
- LangChain: https://github.com/langchain-ai/langchain
- LangGraph: https://github.com/langchain-ai/langgraph
- aiogram-dialog: https://github.com/Tishka17/aiogram_dialog (v2.x, used in Daedalus Telegram gateway)

## Repository shape

```text
nautilus_builder/
├── packages/                # Canonical Python domain layer (113 files, ~8,194 LOC)
│   ├── strategy_spec/       # Pydantic StrategySpec schema, in-memory repository
│   ├── strategy_validation/ # Hard-rule checks, forbidden refs, raw-code detection
│   ├── strategy_compiler/   # StrategySpec -> compile artifact/profile metadata
│   ├── ai_builder/          # Advisory AI draft provider (fixture + OpenAI-compatible), audit store
│   ├── backtest_runner/     # NT backtest config builder, engine boundary, result normalization
│   ├── backtest_jobs/       # Durable backtest job lifecycle service
│   ├── execution_lane/      # TradingNode runtime plan, credential slots, paper strategy
│   ├── lifecycle/           # Draft->Testing->Beta->Final state machine
│   ├── promotions/          # Shadow/evidence-backed promotion contracts
│   ├── workflow_spine/      # Strategy/test workflow lineage, Postgres/Redis persistence
│   ├── runtime_events/      # In-memory, SQLite, Redis event stream seams
│   ├── adapter_registry/    # Backend-approved adapter profiles
│   ├── instrument_registry/ # Backend-approved instruments, data/timeframe/date checks
│   ├── catalog_datasets/    # Parquet dataset registry
│   ├── auth/                # In-memory test token/project-scope model
│   ├── artifact_store/      # Local JSON artifact persistence
│   ├── backend_runtime/     # Backend runtime readiness checks
│   ├── llm_config/          # OpenAI-compatible model configuration
│   ├── nautilus_rule_graph/ # Placeholder NT strategy classes/profiles
│   ├── research_jobs/       # Durable research-job contracts
│   ├── strategy_registry/   # Read-only external strategy registry/import-as-draft
│   ├── system_verification/ # Composed MVP verification report
│   └── ui_contracts/        # Python-backed executable UI contract helpers
├── services/api/            # FastAPI + thin ApiApp routes over packages/* (21 files, ~2,200 LOC)
├── services/workers/        # Backend-owned worker entrypoint stubs
├── apps/web/                # Next.js 15 + Ant Design v6 app shell (~86 TSX/TS files, ~8,598 LOC)
│   ├── app/                 # Next.js App Router pages (strategies, backtests, results, builder, execution)
│   ├── components/          # AntD components (shell, strategies, backtests, results, config, dashboard, etc.)
│   └── lib/                 # API client (api.ts), types, strategy spec helpers
├── tests/                   # 429 pytest tests across 20+ test directories (~8,856 LOC)
├── docker-compose.yml       # Full-stack Docker (postgres:16-alpine, FastAPI, Next.js)
├── Dockerfile.api           # FastAPI container
├── apps/web/Dockerfile      # Next.js container
├── pyproject.toml           # Python packaging/test manifest
└── DESIGN.md               # UI design source of truth
```

## Builder authority boundary

The product boundary is enforced at multiple layers:

- **Strategy Builder** — authoring, drafting, validation. No venue credentials or runtime handles.
- **Backtest Center** — backend-owned BacktestNode historical replay only.
- **Execution Lane** — backend-owned TradingNode paper/live lifecycle; server-side credential slots; manual/risk gates.
- **Daedalus gate** — external live authority; Builder never holds `submit_order`.

Code-level enforcement:
- `compiler.py` sets `execution_authority=False` for both `backtest` and `signal_preview_only` profiles.
- `promotions/service.py` returns `may_submit_order=False`, `may_create_trade_action=False`.
- `lifecycle/models.py` exposes `live_trading_authority=False`.
- `execution_lane/nautilus_runtime.py` — `NautilusTradingNodeRuntimePlan` uses `Literal[False]` guards for `browser_credentials_allowed`, `credential_inputs_allowed`, `strategy_lane_coupled`.
- `execution_lane/credentials.py` — venue-prefixed env keys only; forbidden bare key names; file restricted to owner read/write.
- `execution_lane/models.py` — `_SECRET_KEYS` set recursively rejects credential leakage in profiles, commands, and reports.
- `strategy_validation/policy.py` — `FORBIDDEN_REFERENCES` dict blocks `submit_order`, `modify_order`, `cancel_order`, `close_position`, `api_key`, `secret_key`, `credential`, `TradeAction`.
- `strategy_validation/policy.py` — `RAW_CODE_PATTERNS` set blocks `eval`, `exec`, `import`, `subprocess`, `socket`, `requests`, `os.`, `sys.`, `__import__`.

## NT version alignment status

| Repo | nautilus_trader | Status |
|------|----------------|--------|
| Builder | 1.223.0 | Pinned — 4 versions behind Daedalus |
| Daedalus | 1.227.0 | Current |

**Deprecation gap analysis (1.223.0 → 1.227.0):**
- `fill_limit_at_touch` → `fill_limit_inside_spread` (v1.224.0) — Builder uses `trade_execution: False` (no fill model), so not directly affected
- Coinbase International adapter (`COINBASE_INTX`) removed (v1.224.0) — no references found in Builder
- `InstrumentProvider.load_ids_async`/`load_async` now have defaults (v1.224.0) — Builder uses `load_ids` via `BinanceInstrumentProviderConfig`, compatible
- Binance Ed25519 env vars now raise `ValueError` (v1.224.0) — Builder reads from credential slots, not env vars directly
- dYdX v3 adapter removed (v1.223.0) — no references in Builder
- `Quantity - Quantity` returns `Quantity`, not `Decimal` (v1.223.0) — no arithmetic on NT types in Builder

**Assessment:** Builder is compatible with 1.223.0 but should plan upgrade to 1.227.0 for Daedalus alignment. No breaking deprecations hit Builder's current usage patterns.

## Frontend architecture

- **Next.js 15** with App Router, server components for data fetching
- **Ant Design v6** for UI components (Table, Descriptions, Statistic, Tag, Card)
- **API proxy** via Next.js rewrites → `BUILDER_API_BASE_URL`
- **Auth**: Bearer token from `BUILDER_API_TOKEN` / `NEXT_PUBLIC_BUILDER_API_TOKEN` env vars
- **44 vitest component tests**, 429 pytest backend tests
- **Docker** ready: `docker-compose up` brings full stack (postgres, api, web)

## Security posture

- No hardcoded secrets in production code (confirmed via AST scan)
- No `eval()`, `exec()`, `subprocess`, `os.system`, `time.sleep` in packages/ or services/
- All user inputs validated through Pydantic models with `extra="forbid"`
- SQL injection prevented via parameterized queries in Postgres repository
- Artifact URIs are path-traversal-safe
- API token auth on all routes; 401 handled gracefully with action guidance
- `.env.execution.local` gitignored; venue credentials use prefixed keys only

## Daedalus alignment

Daedalus (`nautilus_trader==1.227.0`) is the execution authority. Builder produces compile artifacts, validation reports, and backtest results. Adapter test evidence (DataTester/ExecTester/reconciliation) comes from Daedalus or adapter test suites.

Key Daedalus components reviewed for alignment:
- `nautilus_runtime/live/execution_lane.py` — consumes TradeAction from Redis, submits orders via NT strategy
- `nautilus_runtime/live/telegram_gateway/ui_dialogs.py` — aiogram-dialog menu system for signal delivery
- `crates/adapters/` — 11 custom DEX adapters (apex_omni, paradex, ethereal, etc.) with Rust core
- `nautilus_brain/` — ML signal pipeline, genome evolution, graph-based strategy construction
