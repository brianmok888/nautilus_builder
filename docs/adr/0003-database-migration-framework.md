# ADR 0003: Database migration framework (Alembic)

- **Status:** Accepted (Phase 1: baseline)
- **Date:** 2026-06-22
- **Adoption Report reference:** §3.4

## Context

The repo used a custom versioned raw-SQL migration runner
(`packages/postgres/migrations.py`) with 7 migrations. As schema evolution
accelerates, a custom runner becomes a maintenance liability (no downgrade
support, no offline SQL generation, no branching/merge semantics).

## Decision

Adopt Alembic for future schema migrations. Phase 1 introduces a stamp-only
baseline representing the current schema state, alongside the existing custom
runner (dual-run).

## Guardrails (non-negotiable)

- **No SQLAlchemy ORM swap.** Raw SQL/psycopg repositories remain the authority.
  Alembic is for migrations only, not ORM model authority.
- Migrations are raw SQL via `op.execute()`, reviewed as code — not
  autogenerate-first.
- The custom runner remains available for existing deployments during the
  transition window.
- Production startup continues to refuse unknown schema state.

## Phases

- **Phase 1 (done):** Add `alembic.ini` + `migrations/env.py` + baseline
  revision. Existing deployments `alembic stamp head`. Custom runner unchanged.
- **Phase 2:** New migrations are Alembic revisions. CI runs
  `alembic upgrade head` on fresh Postgres. Dual-run maintained.
- **Phase 3:** Mark custom runner deprecated with owner/expiry. Remove after
  confidence window.

## Verification

5 smoke tests in `tests/postgres/test_alembic_baseline.py`. Offline SQL
generation produces correct `alembic_version` table + stamp. Custom runner
present and unchanged.
