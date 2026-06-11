# Nautilus Builder Readiness Matrix

**Last updated:** 2026-06-11

## Capability Status

| Capability | Status | Notes |
|---|---|---|
| Strategy authoring | Ready (dev-demo) | StrategySpec v1/v2, validation, forbidden-authority scan |
| StrategySpec validation | Ready (dev-demo) | v1 classic + v2 microstructure, authority rules, source health |
| Deterministic compile bundle | Ready (dev-demo) | Normalized IR, risk contract, artifact bundle, deterministic hash |
| Synthetic replay smoke | Ready (dev-demo) | Catalog-backed BacktestNode smoke, synthetic ticks |
| Real catalog replay | Partial | Dataset manifest + Parquet/DuckDB contracts exist; production-scale replay pending |
| Evidence ledger | Partial | Typed evidence model, verifier, hash check; production artifact storage pending |
| Promotion gate | Ready (dev-demo) | Evidence-based promotion with blocking reasons; shadow/signal-preview only |
| CI enforcement | Ready | GitHub Actions CI with backend/safety/frontend/docker gates |
| Version metadata | Ready | Single source of truth from `packages/builder_metadata` |
| Production auth/RBAC | Partial | Token auth, project scope, rate limiting, audit; full RBAC pending |
| Production object storage | Partial | S3/MinIO compose config; production provisioning pending |
| Worker/job supervision | Partial | Worker entrypoints exist; full job queue pending |
| NT/Daedalus compatibility | Contract only | Compatibility report; no direct Daedalus imports |
| **Live trading** | **Out of scope** | Builder must not submit orders or claim live readiness |
| **Order submission** | **Forbidden** | `submit_order` must never appear in Builder production code |

## Key Definitions

- **Ready (dev-demo):** Works for local development and demo scenarios
- **Partial:** Core implementation exists, needs additional work for production
- **Contract only:** Interfaces and evidence contracts exist; no runtime coupling
- **Out of scope:** Not owned by Builder; belongs to Nautilus-Daedalus or external systems
- **Forbidden:** Builder must never implement this capability

## Production/Live-Trading Status

**Nautilus Builder is not production-ready and is not live-trading ready.**

Live execution requires:
- NautilusTrader DataTester evidence
- ExecTester evidence
- Adapter reconciliation reports
- Daedalus execution-boundary confirmation
- Manual operator approval

None of these are within Builder authority.
