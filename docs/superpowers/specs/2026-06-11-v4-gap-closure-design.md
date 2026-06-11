# V4 Gap Closure Design — Nautilus Builder

**Date:** 2026-06-11
**Status:** Approved (direct user instruction)
**Scope:** Close all remaining gaps from the Reworked Review v4 master prompt

## Design Summary

This design closes the remaining v4 gaps across 20 segments (A-U), organized into 11 sequential PRs. Prior gap closures v1-v3 already established the foundation: readiness matrix, version metadata, CI, StrategySpec v2, compiler IR, evidence ledger, artifact store, catalog datasets, promotion gate, UI traceability, runtime events, and audit. The v4 closure deepens existing implementations, fills missing pieces, and adds production hardening.

## Non-Negotiable Rules

1. Builder-only boundary: no `submit_order(`, no `TradeAction(`, no live execution authority
2. AI remains advisory only
3. No hidden production shortcuts
4. No legacy dumping
5. Determinism is product behavior

## Segment Gap Analysis

### Already Complete (from v1/v2/v3, deepening only needed)
- A: Readiness matrix — add `readiness_status.json`, v4 statuses
- B: Version — fix RELEASE.md drift (0.1.0 vs v0.5.0)
- F: API modularization — already done
- G: StrategySpec v2 — exists, add microstructure features
- H: Compiler IR — exists, ensure deterministic bundle completeness
- I: Evidence ledger — exists, add postgres repository + full verifiers
- J: Artifact store — exists with S3, add production hardening
- K: Catalog datasets — exists, deepen Parquet/DuckDB
- M: Promotion gate — exists, add full lifecycle policy
- O: UI traceability — components exist, may need deepening
- P: Runtime events — exists, add health endpoints
- Q: Postgres migrations — exists, add completeness

### Needs New Implementation
- C: CI hardening — add security.yml, docker.yml, version check scripts
- D: Production Config — add `BuilderProductionConfig`, `startup_policy.py`
- E: Auth RBAC — add full audit middleware, route-level enforcement
- L: Backtest Result Normalization — add metrics model
- N: ND Compatibility Contracts — add `packages/compatibility/`
- R: Deployment/Smoke — add smoke scripts, runbooks
- S: Security Scanning — add `.gitleaks.toml`, `check_secrets.sh`
- T: Docs Cleanup — update all docs
- U: Full-System Verification — complete journey test

## PR Sequence

### PR 1: Readiness v4 + Version Fix (Segments A, B)
- Fix RELEASE.md drift: make version 0.5.0 canonical
- Update `pyproject.toml` to 0.5.0
- Add `doc/readiness_status.json`
- Add readiness tests that verify no live-readiness claims
- Tests: version consistency, readiness matrix completeness

### PR 2: CI + Security (Segments C, S)
- Add `.github/workflows/security.yml`
- Add `.github/workflows/docker.yml`
- Add `scripts/ci_backend.sh`, `ci_frontend.sh`, `ci_security.sh`
- Add `scripts/check_secrets.sh`
- Add `.gitleaks.toml`
- Add version drift check to CI
- Tests: CI script structure, security scan completeness

### PR 3: Production Config Fail-Closed (Segments D, E)
- Add `packages/config/production.py` with `BuilderProductionConfig`
- Add `services/api/startup_policy.py`
- Deepen auth RBAC with full audit middleware
- Add route-level capability checks
- Tests: startup rejection for each missing/invalid config

### PR 4: API Modularization Verification (Segment F)
- Verify app_factory is thin
- Add OpenAPI snapshot test
- Add import isolation test
- Tests: app factory, dependency wiring

### PR 5: Evidence + Artifact Hardening (Segments I, J)
- Add evidence postgres repository
- Add full verifier implementations
- Add artifact store immutability, lifecycle, listing
- Add S3 contract tests
- Tests: evidence CRUD, hash verification, artifact immutability

### PR 6: StrategySpec v2 + Compiler (Segments G, H, N)
- Deepen StrategySpec v2 with v4 feature list
- Ensure compiler bundle completeness
- Add compatibility contracts package
- Tests: v2 validation, deterministic hash, compatibility matrix

### PR 7: Dataset Replay + Metrics (Segments K, L)
- Deepen Parquet/DuckDB loader
- Add backtest result normalizer with full metrics
- Tests: dataset manifest, result normalization, metrics

### PR 8: Promotion Gate + Lifecycle (Segment M)
- Add full lifecycle policy (DRAFT→TESTING→BETA→FINAL)
- Add evidence requirements per stage
- Tests: promotion blocking, stage transitions

### PR 9: UI + Runtime Events (Segments O, P)
- Deepen UI traceability views
- Add full health endpoints (live, ready, build, policy)
- Tests: health endpoint coverage, UI component rendering

### PR 10: Migrations + Deployment (Segments Q, R)
- Complete migration suite
- Add smoke scripts
- Add deployment runbooks
- Tests: migration idempotency, smoke script structure

### PR 11: Docs + Full Verification (Segments T, U)
- Update all docs
- Complete full journey test
- Add `scripts/verify_all.sh` enhancements
- Tests: full builder journey, production fail-closed

## Success Criteria

All 20 Definition of Done items from the v4 spec must be true.
