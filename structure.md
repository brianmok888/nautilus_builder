# Nautilus Builder Structure Review

**Review date:** 2026-05-29 (updated — full deep review v2)
**Target repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus`
**Review mode:** `$superpowers:code-review` routed through `$superpowers:nt-review` (primary) with `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing`, `$superpowers:aiogram-dialog-menus` supporting checks.

## Authoritative references

- NautilusTrader: `nautilus_trader==1.227.0` (pinned in pyproject.toml, aligned with Daedalus)
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
├── packages/                # Canonical Python domain layer (113 files)
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
│   ├── ui_contracts/        # Python-backed executable UI contract helpers
│   └── postgres/            # Postgres connection pool, migrations, repositories
├── services/api/            # FastAPI + thin ApiApp routes over packages/* (21 files)
├── services/workers/        # Backend-owned worker entrypoint stubs
├── apps/web/                # Next.js 15 + Ant Design v6 app shell (~86 TSX/TS files)
│   ├── app/                 # Next.js App Router pages (strategies, backtests, results, builder, execution)
│   ├── components/          # AntD components (shell, strategies, backtests, results, config, dashboard, etc.)
│   └── lib/                 # API client (api.ts), types, strategy spec helpers
├── tests/                   # 442 pytest tests across 20+ test directories (135+ files)
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
- `execution_lane/nautilus_runtime.py` — `Literal[False]` on `browser_credentials_allowed`, `credential_inputs_allowed`, `strategy_lane_coupled`.
- `strategy_validation/policy.py` — `FORBIDDEN_REFERENCES` dict blocks `submit_order`, `modify_order`, `cancel_order`, `close_position`, `api_key`, `secret_key`, `credential`, `TradeAction`.
- `strategy_validation/policy.py` — `RAW_CODE_PATTERNS` set blocks `eval`, `exec`, `import`, `subprocess`, `socket`, `requests`, `os.`, `sys.`, `__import__`.

## NT version alignment status

| Repo | nautilus_trader | Status |
|------|----------------|--------|
| Builder | 1.227.0 | **Aligned** with Daedalus |
| Daedalus | 1.227.0 | Current |

**Deprecation gap analysis (1.223.0 → 1.227.0):**
- `fill_limit_at_touch` → `fill_limit_inside_spread` (v1.224.0) — Builder uses `trade_execution: False` (no fill model), so not directly affected
- Coinbase International adapter (`COINBASE_INTX`) removed (v1.224.0) — no references found in Builder
- `InstrumentProvider.load_ids_async`/`load_async` now have defaults (v1.224.0) — Builder uses `load_ids` via `BinanceInstrumentProviderConfig`, compatible
- Binance Ed25519 env vars now raise `ValueError` (v1.224.0) — Builder reads from credential slots, not env vars directly
- dYdX v3 adapter removed (v1.223.0) — no references in Builder
- `Quantity - Quantity` returns `Quantity`, not `Decimal` (v1.223.0) — no arithmetic on NT types in Builder
- Binance adapter config builder now uses `environment` instead of deprecated `testnet` param

**Assessment:** Builder is fully aligned with Daedalus at 1.227.0. No breaking deprecations hit Builder's current usage patterns.

## Frontend architecture

- **Next.js 15** with App Router, server components for data fetching
- **Ant Design v6** for UI components (Table, Descriptions, Statistic, Tag, Card)
- **API proxy** via Next.js rewrites → `BUILDER_API_BASE_URL`
- **Auth**: Bearer token from `BUILDER_API_TOKEN` / `NEXT_PUBLIC_BUILDER_API_TOKEN` env vars
- **44 vitest component tests**, 442 pytest backend tests
- **Docker** ready: `docker-compose up` brings full stack (postgres, api, web)

## Security posture

- No hardcoded secrets in production code (confirmed via AST scan)
- No `eval()`, `exec()`, `subprocess`, `os.system`, `time.sleep` in packages/ or services/
- All user inputs validated through Pydantic models with `extra="forbid"`
- SQL injection prevented via parameterized queries in Postgres repository (table names use `safe_storage_identifier()`)
- Artifact URIs are path-traversal-safe (`_SAFE_IDENTIFIER` regex on all artifact refs)
- API token auth on all routes; 401 handled gracefully with action guidance
- `.env.execution.local` gitignored; venue credentials use prefixed keys only
- Credential model forbids bare key names via `_FORBIDDEN_KEYS` set
- AI provider endpoint URL is operator-configured via env vars, never derived from model output
- LLM output always validated through `validate_strategy_spec()` before acceptance

## Security concerns identified (new in this review)

1. **No CORS middleware** — API has no CORS configuration. In Docker deployment, Next.js SSR proxies bypass this, but direct browser access from other origins is blocked. Acceptable for VM deployment; add CORS if browser SPA access is needed.
2. **Default dev token in docker-compose** — `BUILDER_API_TOKEN: ${BUILDER_API_TOKEN:-dev-token}` provides a fallback that is trivially guessable. Production deployments must override this.
3. **No API rate limiting** — No rate limiting middleware (slowapi/throttling). Low risk for operator-only tool, but should be added if exposed to wider network.
4. **No request body size limits** — FastAPI defaults apply but no explicit max body size is configured for API routes.
5. **`NEXT_PUBLIC_BUILDER_API_TOKEN` exposed to client** — Token is sent to browser in `NEXT_PUBLIC_*` env var. This is standard for Next.js but means the token is visible in client-side JS bundles.

## Daedalus alignment

Daedalus (`nautilus_trader==1.227.0`) is the execution authority. Builder produces compile artifacts, validation reports, and backtest results. Adapter test evidence (DataTester/ExecTester/reconciliation) comes from Daedalus or adapter test suites.

Key Daedalus components reviewed for alignment:
- `nautilus_runtime/live/execution_lane.py` — consumes TradeAction from Redis, submits orders via NT strategy
- `nautilus_runtime/live/telegram_gateway/ui_dialogs.py` — aiogram-dialog menu system for signal delivery
- `crates/adapters/` — 11 custom DEX adapters (apex_omni, paradex, ethereal, etc.) with Rust core
- `nautilus_brain/` — ML signal pipeline, genome evolution, graph-based strategy construction

## Previously applied fixes (still valid)

### S1: Master reconciliation text + H2 fixture fallback gate
- `workflow_result_payload` gates fixture fallback behind `BUILDER_ALLOW_FIXTURE_FALLBACK` env var (defaults to off).
- Tests updated: 3 existing tests set the env flag explicitly; 2 new tests verify 404 when off, 200 when on.

### S2: H3 adapter config builder credential safety
- `generic_client_config_builder` now raises `ValueError` when no venue-prefixed credentials are found.
- Added `_require_non_blank_credentials()` helper that checks for `{VENUE}_*` prefixed keys with non-empty values.

### S3: H1 NT version upgrade + M3 runtime_label extensibility
- Upgraded `nautilus_trader` from 1.223.0 to 1.227.0 in `pyproject.toml` and `engine_contract.py`.
- Replaced deprecated `testnet` param with `environment` in Binance adapter config builder.

### S4: M1 list_results pagination + M2 created_at timestamp
- Added `limit` and `offset` parameters to `list_results()` in InMemory and SQLite repos.
- Added `created_at: str` field to `WorkflowResultRecord` with ISO datetime default factory.

## Master reconciliation — catalog-backed Nautilus replay

- `catalog_backed_replay_smoke` runs synthetic historical quote ticks through the full BacktestNode pipeline.
- This is a wiring and data-flow check — not full trading-production readiness.
- Supports `CATALOG_BACKED_REPLAY_SMOKE_MODE` env variable for smoke test gating.

## Verification gate (current)

```bash
python3 -m compileall -q packages services tests  # Clean
python3 -m pytest tests/ -q --tb=line             # 459 passed
```

## Segments applied (this session)

### S5: H4+M10+M11 — Docker-compose production safety
- `_UNSAFE_DEV_TOKENS` set rejects dev tokens in production.
- Postgres port bound to `127.0.0.1:5432:5432` (localhost only).
- Password uses `${POSTGRES_PASSWORD:-builder_dev}` env var.
- 5 new tests.

### S6: M5 — API route pagination
- `list_results_payload` accepts `limit`/`offset` params.
- New `GET /api/results` route with pagination query params.
- 3 new tests.

### S7: M6 — Adapter fallback warning
- `_client_configs` logs warning when adapter not in registry.
- 1 new test.

### S8: M8 — PostgresWorkflowRepository deprecation
- `__getattr__`-based deprecation warning for alias.
- Tests use `SqliteWorkflowRepository` directly.
- 1 new test.

### S9: M9 — Dockerfile safety
- `RUN touch .env.execution.local` before COPY.
- 2 new tests.

### S10: L6 — `__import__` anti-pattern
- Module-level `datetime` import replaces `__import__` call.

### S11: L7+L8 — Rate limiting + CORS
- `InMemoryRateLimiter` for zero-dependency rate limiting.
- CORS middleware via `BUILDER_CORS_ORIGINS` env var.
- 5 new tests.

## Segments applied — QuantDinger fluidity gap (2026-05-30)

### S12: .env.example + scripts/run_dev.sh + scripts/run_tests.sh
- `.env.example` documents all configurable env vars with safe defaults.
- `scripts/run_dev.sh` starts API + frontend with `--api-only`, `--web-only`, `--full` modes.
- `scripts/run_tests.sh` runs verification gate with `--quick`, `--full`, `--frontend` modes.
- 13 new tests in `tests/onboarding/test_env_and_scripts.py`.

### S13: DEVELOPMENT.md
- Full onboarding guide: prerequisites, 5-command quickstart, local dev, testing, troubleshooting.
- Documents all environment variables with defaults and descriptions.
- Architecture boundaries section: what Builder owns and doesn't own.

### S14: docs/examples/ with runnable demos
- `docs/examples/demo_strategy_basic.py` — spec → validate → compile.
- `docs/examples/demo_strategy_backtest.py` — full pipeline through backtest config.
- `docs/examples/demo_adapter_discovery.py` — adapter registry exploration.
- 11 new tests in `tests/examples/test_demo_scripts.py`.

### S15: Strategy development guide
- `doc/strategy_dev_guide.md` — write indicator → save → backtest → promote.
- Full indicator reference, rule operators, risk parameters.
- Safety boundaries and lifecycle stages documented.
- 9 new tests in `tests/onboarding/test_dev_guide_references.py`.

### S16: Adapter auto-discovery factory pattern
- `packages/adapter_registry/discovery.py` — `AdapterFactory` base class with `@register_adapter` decorator.
- `discover_adapter()`, `adapter_factory()`, `list_discovered_adapters()` API.
- Drop-in pattern: new adapters register via decorator, no manual wiring.
- 8 new tests in `tests/adapter_registry/test_discovery.py`.

### S17: # @param convention for AI Builder
- `packages/ai_builder/param_parser.py` — parses `# @param name:type:default desc` comments.
- `# @strategy name="..." adapter="..."` header parsing.
- `ParseResult` and `ParamDecl` Pydantic models.
- 14 new tests in `tests/ai_builder/test_param_parser.py`.

### S18: Zero-config docker compose
- `docker-compose.yml` — API healthcheck, web depends on API healthy, postgres localhost-only.
- `.env.example` covers all docker-compose env vars.
- 12 new tests in `tests/onboarding/test_docker_zero_config.py`.

### S19: Open findings closure
- M4: Frontend tests use vi.fn() mocks (verified).
- L1: storage_config.py has deprecation deadline (verified).
- L2: Backtest legacy_hash documented (verified).
- L3: Frontend selectors mitigated with mocks (verified).
- L4: All packages have __all__ exports (verified).
- L9: Token exposure documented in .env.example (verified).
- L10: InMemory stores documented with Postgres migration note (verified).
- 10 new tests in `tests/onboarding/test_open_findings.py`.

## Verification gate (current)

```bash
python3 -m compileall -q packages services tests  # Clean
python3 -m pytest tests/ -q --tb=line             # 536 passed
```

## Master reconciliation — QuantDinger fluidity gap

All 7 QuantDinger improvements implemented and verified:
1. `.env.example` + `scripts/` operational tooling
2. `DEVELOPMENT.md` onboarding guide
3. 3 runnable example strategy demos
4. Strategy development guide
5. Adapter auto-discovery factory pattern
6. `# @param` convention for AI Builder
7. Zero-config `docker compose up -d` experience

All open findings (M4, L1-L4, L9, L10) resolved or documented.

**Test evidence:** 536 passed (77 new), 0 compilation errors, all handguards intact.

## Segments applied — End-to-end pipeline and spec files (2026-05-30)

### S20: Example JSON spec files
- `docs/examples/specs/dual_ma.json` — EMA crossover strategy spec.
- `docs/examples/specs/rsi_reversal.json` — RSI mean reversion strategy spec.
- Both validate as StrategySpec and exercise the full validation pipeline.
- 8 new tests in `tests/examples/test_spec_files.py`.

### S21: scripts/run_backtest.py — End-to-end chained pipeline
- Chains all seams: load JSON → validate → compile → backtest → result.
- CLI args: `--spec`, `--profile`, `--output`, `--json`.
- Human-readable report by default, JSON output with `--json`.
- Writes result artifacts to file with `--output`.
- Execution authority always False. No venue connection required.
- 11 new tests in `tests/examples/test_run_backtest.py`.

### S22: Strategy dev guide updated
- `doc/strategy_dev_guide.md` now includes "Running the End-to-End Pipeline" section.
- Documents `scripts/run_backtest.py` usage with examples and output.

## Verification gate (current)

```bash
python3 -m compileall -q packages services tests  # Clean
python3 -m pytest tests/ -q --tb=line             # 555 passed
```

## Hardening Sprint — 2026-06-07

### Segment H1: Repo Hygiene
- Removed committed `node_modules/.vite/vitest/.../results.json`.
- Expanded `.gitignore` with comprehensive entries (`__pycache__/`, `node_modules/`, `.vite/`, `.vitest/`, `.next/`, `.ruff_cache/`, `.mypy_cache/`, `.venv/`).
- Created `scripts/check_repo_hygiene.sh` — scans git-tracked files for forbidden artifacts.
- Created `scripts/check_forbidden_authority.sh` — scans for authority-granting patterns.
- 10 new tests in `tests/hygiene/`.

### Segment H2: CI + Security
- Expanded `infra/ci/github-actions-test.yml` with `repo-hygiene` job, branch gating.
- `BUILDER_ENV` validation: `local|staging|production` with `BuilderEnvironment` enum.
- Production token enforcement: rejects missing, dev, short (<32), and NEXT_PUBLIC tokens.
- CORS validation: rejects wildcard and empty origins in staging/production.
- Structured error codes: `ErrorCode` enum (12 codes), `StructuredError` exception, `error_response()` helper.
- 20 new tests in `tests/api/test_security_hardening.py`.

### Segment H3: Persistence & Evidence
- Migration v2: `compiler_runs`, `replay_runs`, `promotion_ledger`, `audit_events` tables.
- `AllowedPromotionMode` enum: `shadow_only`, `signal_preview_only`, `paper_replay_candidate`.
- `ForbiddenPromotionMode` exception for live authority modes.
- Immutable `PromotionLedgerEntry` with `execution_authority=False` via `Literal[False]`.
- Immutable `AuditEvent` model with `frozen=True`.
- 19 new tests across `tests/postgres/`, `tests/promotions/`, `tests/api/`.

### Segment H4: Replay + Spec + Release
- `ReplayFixtureType` enum: bars, trades, quotes, order_book_snapshots, funding_rates, liquidations.
- `FailureModeFixture` and `ReplayFixtureConfig` for failure-mode fixtures.
- `scan_generated_artifact()` static scan for forbidden references in generated code.
- Health endpoints: `/health/live`, `/health/ready`, `/health/build`.
- `CHANGELOG.md` with v0.4.0 entry.
- `docs/deployment_guide.md` with environment profiles, rollback, backup/restore.
- 12 new tests in `tests/replay/`, `tests/strategy_compiler/`, `tests/api/`.

## Verification gate (current)

```bash
python3 -m compileall -q packages services tests  # Clean
python3 -m pytest tests/ -q --tb=line             # 645 passed
bash scripts/check_repo_hygiene.sh                # PASSED
bash scripts/check_forbidden_authority.sh         # PASSED
```

## P1 Segments — 2026-06-07

### P1-1: Wire Promotion Ledger Service into Postgres

**Status: DONE**

Created `packages/postgres/promotion_ledger_repository.py`:
- `record_compiler_run()` — writes to `compiler_runs` table with required evidence fields
- `record_replay_run()` — writes to `replay_runs` table, linked to compiler run
- `record_promotion()` — evidence-gated transaction: validate → write ledger → write audit event → return
  - Fails closed on missing compiler evidence, replay evidence, artifact hash
  - Fails on forbidden promotion modes (live_trade_authority, etc.)
  - Requires approved_by for paper_replay_candidate mode
  - All results enforce `execution_authority=False`
- `get_promotion()` — read by promotion ID
- `list_promotions()` — list all promotions

20 new tests in `tests/postgres/test_promotion_ledger_repository.py`.

### P1-2: Add S3/MinIO Artifact Backend

**Status: DONE**

Created:
- `packages/artifact_store/interface.py` — `ArtifactStoreProtocol` with `put()` and `get()` methods
- `packages/artifact_store/s3_store.py` — S3-compatible backend:
  - Content-addressed immutable keys: `artifacts/{type}/{sha256}/{filename}`
  - Checksum verification after write and before read
  - `execution_authority=false` in all artifact metadata
  - Never exposes S3 secrets to frontend
- `packages/artifact_store/factory.py` — creates correct backend from env:
  - `BUILDER_ARTIFACT_BACKEND=local` (default) → LocalJsonArtifactStore
  - `BUILDER_ARTIFACT_BACKEND=s3` → S3ArtifactStore
  - Env vars: BUILDER_S3_BUCKET, BUILDER_S3_REGION, BUILDER_S3_ENDPOINT_URL, BUILDER_S3_ACCESS_KEY_ID, BUILDER_S3_SECRET_ACCESS_KEY
- Updated `packages/artifact_store/__init__.py` exports

13 new tests in `tests/artifact_store/test_s3_artifact_store.py`.

### Verification gate (current)

```bash
python3 -m compileall -q packages services tests  # Clean
python3 -m pytest tests/ -q --tb=line             # 743 passed
```

### Segment P1-3: Replay Deterministic Loader (v0.6.0)

**Status: DONE**

Created `packages/backtest_runner/replay_loader.py`:
- `FixtureSpec` — specification for generating deterministic fixtures from seed
- `generate_fixture()` — deterministic fixture generation for all 10 dataset types (bars, trades, quotes, order_book_snapshots, funding_rates, liquidations, bad_data, stale_data, etc.)
- `generate_dataset_report()` — full dataset report with determinism proof (generates twice, compares hashes)
- `validate_ohlc_consistency()` — OHLC cross-validation for bar fixtures (low ≤ open/close ≤ high)
- `ReplayDatasetReport` — safety contract with `credentials_used=False`, `live_trading_enabled=False`, `execution_authority=False`

27 new tests in `tests/replay/test_replay_loader.py`.

### Segment P1-4: StrategySpecMicrostructureV1 (v0.6.0)

**Status: DONE**

Created `packages/strategy_spec/microstructure.py`:
- `MicrostructureFeature` enum: 26 features (OBI, spread_bps, top_depth_usd, CVD, CVD_divergence, absorption, aggressive_buy/sell_volume, heatmap_liquidity, liquidity_walls, SVP POC/VAH/VAL, HVN/LVN, funding_rate, funding_z_score, liquidation_imbalance, liquidation_clusters, VWAP_session, anchored_VWAP, VPIN_toxicity, book_resilience, liquidity_replenishment)
- `FeatureSourceHealth` — source health tracking per feature (source_available, stale, missing, true_zero, synthetic_fallback_used)
- `MicrostructureFeatureRef` — feature reference with required/optional, max_staleness_ms, fail_closed_on_missing
- `MicrostructureSignalRule` — signal rule combining feature references
- `StrategySpecMicrostructureV1` — full spec with `output_mode=signal_preview_only`, `execution_authority=Literal[False]`
- Source health validation: `validate_source_health()` checks required features for stale/missing/synthetic

30 new tests in `tests/strategy_spec/test_microstructure_spec.py`.

### Segment P2-1: Release/Deployment Posture (v0.6.0)

**Status: DONE**

Created:
- `RELEASE.md` — version scheme, release checklist, rollback procedure, hotfix process
- `docker-compose.staging.yml` — Postgres + Redis + MinIO, CORS locked, strong tokens required
- `docker-compose.production.yml` — all guards, password-required env vars, restart policies, network isolation

Updated:
- `CHANGELOG.md` — v0.6.0 entry

25 new tests in `tests/integration/test_docker_compose_profiles.py`.

### Segment P2-2: Postgres Audit Event Writer (v0.6.0)

**Status: DONE**

Created `packages/postgres/audit_event_repository.py`:
- `PostgresAuditEventRepository` — async write/query to `builder.audit_events` table
- `make_audit_writer_from_pool()` — factory creating a sync callable compatible with `AuditMiddleware`
- Fire-and-forget scheduling for non-blocking middleware writes
- Graceful handling of missing pool (dev mode) and missing event loop

14 new tests in `tests/postgres/test_audit_event_repository.py`.

### Verification gate (v0.6.0)

```bash
python3 -m compileall -q packages services tests  # Clean
python3 -m pytest tests/ -q --tb=line             # 852 passed
bash scripts/check_repo_hygiene.sh                # PASSED
bash scripts/check_forbidden_authority.sh         # PASSED
```
