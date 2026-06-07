# Changelog

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
- Repo hygiene scan passes.
- Forbidden authority scan passes.
