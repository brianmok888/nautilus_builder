# Nautilus Builder Hardening Sprint — Implementation Design

**Date:** 2026-06-07
**Status:** APPROVED FOR EXECUTION
**Scope:** Top 10 fixes from validation summary, staged into 4 implementation phases

## Current Baseline

- 571 pytest tests passing, 0 compilation errors
- PostgreSQL migrations exist (v1: strategies, adapters, instruments)
- CI exists (GitHub Actions: python-contracts + frontend-operator-shell)
- Auth fail-closed for production environment
- Rate limiting and CORS middleware in place
- LocalJsonArtifactStore with SHA-256 checksums
- PromotionService with evidence binding and artifact validation
- StrategySpec has schema_version, Pydantic strict validation
- execution_authority=False enforced at compile time

## Gap Analysis (Already Done vs Needed)

### Already Done
1. ✅ `.gitignore` covers `__pycache__/`, `.pytest_cache/` (but missing some entries)
2. ✅ CI exists with Python + Frontend jobs
3. ✅ Production auth fail-closed (rejects dev-token in production)
4. ✅ PostgreSQL persistence layer exists with migrations
5. ✅ Artifact store with SHA-256 hashes
6. ✅ PromotionService with evidence refs and checksums
7. ✅ StrategySpec semantic validation (Pydantic strict model)
8. ✅ Rate limiting and CORS middleware
9. ✅ Docker compose with health checks
10. ✅ DEVELOPMENT.md onboarding guide

### Still Needed (Mapped to 10 Findings)

1. **Repo Hygiene**: Remove committed `node_modules/.vite/vitest/.../results.json`, tighten `.gitignore`, add guard script
2. **CI Verification Gate**: Expand CI with ruff, forbidden authority scan, repo hygiene scan, structured error model tests
3. **Production Auth Fail-Closed**: Extend to reject short tokens, NEXT_PUBLIC tokens in production, wildcard CORS in production, add explicit BUILDER_ENV mode
4. **Persistence Layer**: Add promotion_ledger, audit_events, compiler_runs, replay_runs tables (migration v2)
5. **Evidence Ledger**: Immutable promotion ledger with full hash chain linking
6. **Replay Upgrade**: Add replay fixture types beyond synthetic quotes (bars, trades, order books, failure modes)
7. **StrategySpec Hardening**: Add indicator-specific param validation, warmup requirements, NaN behavior, output mode enforcement, generated artifact static scan
8. **API Hardening**: Add request IDs, structured error model with stable codes, idempotency keys for mutations, audit logging for all mutations
9. **Supply Chain**: Add dependency locking verification, SBOM generation script
10. **Release Posture**: Add CHANGELOG.md, health/live+ready+build endpoints, deployment docs, rollback guide

## Implementation Segments

### Segment 1: Repo Hygiene (Phase 0-1)
- Remove committed `node_modules/.vite/vitest/.../results.json`
- Expand `.gitignore` with comprehensive entries
- Create `scripts/check_repo_hygiene.sh`
- Create `scripts/check_forbidden_authority.sh`
- Add tests for hygiene and forbidden authority

### Segment 2: CI Expansion + Security Hardening (Phase 1)
- Expand GitHub Actions: add ruff lint/format, forbidden authority scan, repo hygiene job
- Add explicit BUILDER_ENV validation (local|staging|production)
- Extend production auth: reject short tokens, reject NEXT_PUBLIC tokens, reject wildcard CORS
- Add structured error codes enum
- Add request ID middleware
- Add tests for all new security checks

### Segment 3: Persistence & Evidence Ledger (Phase 2)
- Migration v2: promotion_ledger, audit_events, compiler_runs, replay_runs tables
- PostgresPromotionLedgerRepository
- PostgresAuditEventRepository
- Audit logging for mutations
- Idempotency key support for mutation endpoints
- Tests for persistence and ledger

### Segment 4: API Hardening + Replay + Release (Phase 3)
- Structured error responses with stable codes
- API contract tests (OpenAPI export)
- Replay fixture types (bars, trades, order books, failure modes)
- StrategySpec semantic hardening (indicator params, warmup, NaN, static scan)
- CHANGELOG.md, health endpoints, deployment/rollback docs
- Supply chain: SBOM script, dependency lock verification
- Final verification and master reconciliation

## Hard Rules (Invariant)

- `execution_authority = False` always
- `may_submit_order = False` always
- No `submit_order`, `TradeAction`, live credentials in generated artifacts
- Promotion modes limited to: `shadow_only`, `signal_preview_only`, `paper_replay_candidate`
- Production must fail closed on auth, CORS, persistence
