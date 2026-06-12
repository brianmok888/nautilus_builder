# Changelog

## Unreleased

### Changed
- v5 Finding A: CHANGELOG restructured with Unreleased section; version check script hardened.
- v5 Finding B: Compiler handles both classic and microstructure StrategySpec families via resolver.
- v5 Finding C: New `compile_strategy_spec_bundle()` produces 6 deterministic artifacts (IR, feature graph, risk contract, replay manifest, compile report, bundle manifest).
- v5 Finding D: PostgresEvidenceRepository aligned with EvidenceRef model fields (strategy_lineage_id, uri, source_system, VerificationStatus).
- v5 Finding E: Evidence routes use injected repository pattern; production fails on in-memory evidence store.
- v5 Finding F: DatasetDataType enum with 10 ND-grade types; DatasetManifestV1 model for multi-type file entries.
- v5 Finding G: Migration v7 for evidence_refs table with project-scoped indexes.
- v5 Promotion: Forbidden promotion modes enforced; required evidence per mode defined.

### Added
- `packages/strategy_spec/resolver.py` — schema family resolver.
- `packages/evidence_ledger/in_memory_repository.py` — in-memory evidence repository for dev/demo.
- `packages/catalog_datasets/models.py` — DatasetDataType enum and DatasetManifestV1 model.
- `packages/strategy_spec/examples/` — 3 microstructure example spec JSON files.
- 46 new tests across version, evidence, strategy_spec, and strategy_compiler packages.

### Verification
- 1423 Python tests passing.
- Forbidden authority scan passing.
- Version consistency check passing.
- No `submit_order(` or authoritative `TradeAction(` in Builder production code.

## v0.5.0 - 2026-06-11

### Added
- Redis-backed rate limiting (`RedisRateLimiter`) with configurable backend selection.
- Audit middleware logging every mutation request with actor_id, project_id, request_id.
- Request ID middleware: every response includes `X-Request-ID` header.
- BuilderProductionConfig with fail-closed validation for production startup.
- Compatibility contracts package (`packages/compatibility/`) for ND/NT alignment.
- Evidence Postgres repository for persistent evidence storage.
- Startup policy (`services/api/startup_policy.py`) using BuilderProductionConfig.
- CI workflows: `ci.yml`, `security.yml`, `docker.yml`.
- Security scanning: `.gitleaks.toml`, `check_secrets.sh`, `check_release_version.py`.
- Production smoke test script (`scripts/smoke_production.sh`).
- Machine-readable readiness matrix (`doc/readiness_status.json`).
- Full builder journey integration test (7 steps).
- Version consistency tests across `pyproject.toml`, `RELEASE.md`, and `/health/build`.
- Deterministic replay fixture generator for all 10 dataset types.
- `StrategySpecMicrostructureV1` schema with 26 microstructure feature references.
- Source health semantics with stale/missing/true_zero/synthetic_fallback tracking.
- `StrategySpecClassicV1` alias for backward compatibility.
- `RELEASE.md` with version scheme, release checklist, rollback procedure.
- `docker-compose.staging.yml` and `docker-compose.production.yml` with guards.
- Promotion modes: `AllowedPromotionMode` enum for safe-only modes.
- Immutable promotion ledger: `PromotionLedgerEntry` with `execution_authority=False`.
- Health endpoints: `/health/live`, `/health/ready`, `/health/build`.
- Deterministic compiler IR (`CompiledStrategyIR`).
- Feature dependency graph, risk contract, artifact bundle models.
- Evidence ledger with typed `EvidenceRef` model and verifier.
- Canonical version source in `packages/builder_metadata/version.py`.
- UX traceability components (`StrategyJourney`, `BlockingReasonPanel`).
- Structured audit events with 15 required event types.
- Builder metrics with 7 canonical metric names.
- Local CI parity script (`scripts/verify_all.sh`).

### Changed
- FastAPI creates default artifact store from `BUILDER_ARTIFACT_BACKEND`/`BUILDER_ARTIFACT_ROOT`.
- `/health/ready` reports artifact-store factory failures instead of unconditional readiness.
- Postgres-backed LLM config saves persist through the config repository.
- Frontend execution lane panel is observe/request-only; no command construction.
- Forbidden authority safety scan covers production paths by default.
- Frontend uses canonical `apiFetch` from `api.ts`; `apiClient.ts` deprecated.
- AI prompt audit storage redacts secrets before persistence.
- All legacy items removed (no env escapes remain).
- Capabilities upgraded to v4 names with role-based sets.

### Security
- Docker builds never copy `.env*` files into images.
- Browser/API credential entry disabled; backend-only provisioning required.
- Installed `nautilus-builder-api` uses authenticated FastAPI entrypoint.
- Rate limiting enforced on all protected routes after auth.
- Mutation audit carries authenticated actor/project attribution.
- `NEXT_PUBLIC_BUILDER_API_TOKEN` forbidden in staging/production.
- CORS wildcard/empty rejected in staging/production.
- Production config fails closed on missing/invalid settings.

### Verification
- 1377 Python tests passing, 138 frontend tests passing.
- Forbidden authority scan passing.
- Secret scanning passing.
- Frontend typecheck and build passing.
- No `submit_order(` or authoritative `TradeAction(` in Builder production code.

## v0.4.0 - 2026-06-07

### Added
- Repo hygiene: removed committed `.vite/vitest` cache, tightened `.gitignore`.
- Security: `BUILDER_ENV` validation, production token enforcement, CORS validation.
- Structured error codes: `ErrorCode` enum with 12 stable codes.
- Persistence: migration v2 with compiler_runs, replay_runs, promotion_ledger, audit_events.
- Promotion modes: `AllowedPromotionMode`, `ForbiddenPromotionMode`.
- Immutable ledger: `PromotionLedgerEntry` with `execution_authority=False`.
- Replay fixtures: `ReplayFixtureType` enum, `FailureModeFixture`, `ReplayFixtureConfig`.
- Static scan: `scan_generated_artifact()` for forbidden references.

### Changed
- CI runs on `master/main` push.
- Production mode rejects `dev-token`.
- Promotion models enforce allowed modes via Pydantic validator.

### Verification
- 641 tests passing, 0 compilation errors.

