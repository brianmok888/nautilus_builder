# Changelog

## v0.1.0 - 2026-06-11

### Changed
- Canonical version source: `packages/builder_metadata/version.py` now the single source of truth.
- `/health/build` and FastAPI app.version read from canonical source.
- RELEASE.md updated to reference current version.

## v0.6.0 - 2026-06-07

### Added
- Deterministic replay fixture generator (`packages/backtest_runner/replay_loader.py`): generates reproducible fixtures from seed for all 10 dataset types.
- Dataset report with determinism proof: same spec always produces same hash.
- OHLC consistency validation for bar fixtures.
- `StrategySpecMicrostructureV1` schema with 26 microstructure feature references (OBI, CVD, spread_bps, VPIN, etc.).
- Source health semantics: `FeatureSourceHealth` with stale/missing/true_zero/synthetic_fallback tracking.
- Fail-closed source health validation: missing or stale required features block spec compilation.
- `StrategySpecClassicV1` alias for backward compatibility.
- `RELEASE.md` with version scheme, release checklist, rollback procedure, hotfix process.
- `docker-compose.staging.yml` with Postgres, Redis, MinIO, CORS locked.
- `docker-compose.production.yml` with all guards, password-required env vars, restart policies.
- CI workflow updated with per-suite runs (strategy_spec, workflow_spine, artifact_store, catalog_datasets).
- Updated `handguard.md` with microstructure spec gate (Section 34), replay loader gate (Section 35).

### Changed
- Classic `StrategySpec` unchanged — all existing tests continue to pass.
- CI workflow now runs individual test suites for better failure isolation.

### Security
- Microstructure spec enforces `output_mode=signal_preview_only` and `execution_authority=False`.
- No execution authority introduced in any new code.

### Verification
- 811 tests passing, 0 compilation errors.
- Repo hygiene scan passes.
- Forbidden authority scan passes.

## v0.5.0 - 2026-06-07

### Added
- Redis-backed rate limiting (`RedisRateLimiter`) with configurable backend selection (`BUILDER_RATE_LIMIT_BACKEND=memory|redis`).
- In-memory rate limiter retained as default for local development.
- Audit middleware (`AuditMiddleware`) that logs every mutation request (POST, PUT, DELETE, PATCH) with actor_id, project_id, request_id, route, method, status_code.
- Request ID middleware: every response includes `X-Request-ID` header (UUID).
- Audit middleware writes to Postgres `audit_events` table when Postgres is configured.
- Redis rate limiter fails open (allows request, logs warning) when Redis is unavailable.
- Expanded deployment guide with required env vars table, forbidden production defaults, Postgres/S3/MinIO setup steps, health checks, migration commands, backup/restore commands, release checklist, and rollback checklist.
- New operations guide (`docs/operations.md`) covering monitoring, incident response, backup/restore, environment profiles, rate limiting architecture, and audit trail queries.
- Production environment example (`.env.production.example`) updated with rate limiting and audit configuration vars.
- `audit_events` migration v3 adds `project_id` column and index for project-scoped audit queries.

### Changed
- FastAPI app selects rate limiter backend based on `BUILDER_RATE_LIMIT_BACKEND` env var.
- `packages/auth/__init__.py` exports `InMemoryRateLimiter` and `RedisRateLimiter`.

### Fixed
- Production mode no longer relies solely on in-memory rate limiting.

### Security
- Audit trail now covers all mutation routes in production.
- Request IDs enable end-to-end trace correlation.

## v0.4.0 - 2026-06-07

### Added
- Repo hygiene: removed committed `.vite/vitest` cache, tightened `.gitignore`, added `scripts/check_repo_hygiene.sh` and `scripts/check_forbidden_authority.sh`.
- CI: expanded GitHub Actions with `repo-hygiene` job, branch gating on `master/main`.
- Security: `BUILDER_ENV` validation (`local|staging|production`), production token enforcement (rejects short/dev/public tokens), CORS validation (rejects wildcard/empty in production).
- Structured error codes: `ErrorCode` enum with 12 stable codes, `StructuredError` exception, `error_response()` helper.
- Persistence: migration v2 with `compiler_runs`, `replay_runs`, `promotion_ledger`, `audit_events` tables.
- Promotion modes: `AllowedPromotionMode` enum (`shadow_only`, `signal_preview_only`, `paper_replay_candidate`), `ForbiddenPromotionMode` for live authority modes.
- Immutable ledger: `PromotionLedgerEntry` with `execution_authority=False` enforced via `Literal[False]`.
- Audit events: immutable `AuditEvent` model with `frozen=True`, `audit_event_from_mutation()` helper.
- Replay fixtures: `ReplayFixtureType` enum (bars, trades, quotes, order book snapshots, funding rates, liquidations), `FailureModeFixture`, `ReplayFixtureConfig`.
- Static scan: `scan_generated_artifact()` for forbidden references in generated strategy code.
- Health endpoints: `/health/live`, `/health/ready`, `/health/build`.

### Changed
- CI runs on `master/main` push (not all pushes).
- Production mode rejects `dev-token` via both `BUILDER_API_TOKEN` and `BUILDER_DEV_AUTH_TOKEN`.
- Promotion models now enforce allowed modes via Pydantic validator.

### Fixed
- Removed committed `node_modules/.vite/vitest/.../results.json`.

### Security
- Production startup validates token length (≥32 chars), rejects `NEXT_PUBLIC_*` tokens.
- Wildcard CORS rejected in staging/production.

### Verification
- 641 tests passing, 0 compilation errors.
