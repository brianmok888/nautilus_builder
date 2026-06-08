# Nautilus Builder 2026-06-08 Review Findings Closure Design

**Date:** 2026-06-08
**Status:** Executed and reconciled on 2026-06-08; final commit/push gated by fresh verification and review
**Target repo:** `/home/mok/projects/nautilus_builder`
**Read-only reference repo:** `/home/mok/projects/Nautilus-Daedalus`
**Primary route:** `superpowers:nt-review`
**Supporting routes:** `nt-architect`, `nt-adapters`, `nt-live`, `nt-testing`, `aiogram-dialog-menus` as a negative Telegram boundary lens

## Goal

Close the active findings in `findings.md` without adding Builder live order authority, Daedalus runtime imports, Telegram/aiogram runtime dependencies, or LangChain/LangGraph/EvoMap execution coupling.

## Scope decision

The current repo instructions and prior approved specs say Nautilus-Daedalus is read-only from this Builder repo. The appended Nautilus-Daedalus order-flow robustness document is therefore treated as an authoritative boundary/reference input, not as a Builder implementation target. Builder may model evidence and handoff contracts, but must not implement Daedalus profile state machines or live execution internals here.

## References used

- Local source truth: `doc/nautilus_builder_spec.md`, `doc/nautilus_builder_hardguards.md`, `AGENTS.md`, `structure.md`, `findings.md`, `handguard.md`.
- NautilusTrader official docs/repo are authoritative for adapter/testing/live wording. Builder must not claim adapter/live readiness without DataTester, ExecTester, and reconciliation evidence.
- EvoMap/LangChain/LangGraph remain advisory ecosystem references only. No runtime dependency is added in this closure.
- aiogram-dialog menus remain Daedalus/Telegram boundary knowledge only. Builder must not add aiogram dependencies.

## Architecture

The closure is split into four TDD segments plus master reconciliation:

1. **API auth and strategy scope** — require auth for protected `/api` routes, enforce `UserProjectContext` in strategy list/detail/mutations, and update tests so public strategy leakage is impossible.
2. **Production startup policy** — wire `packages.auth.policy` into FastAPI startup so production/staging reject short tokens, public browser tokens, and wildcard/empty CORS.
3. **Storage/evidence hardening** — validate Postgres schema identifiers, preserve strategy scope in Postgres rows, delegate Postgres backtest job strategy queries, and distinguish artifact-backed vs inferred compile evidence.
4. **Runtime route coverage and demo hygiene** — replace static auth-confidence tests with runtime missing-auth checks, keep demo evidence labeled as demo-only, and stop seed scripts from swallowing unexpected errors.

## Data flow

```text
HTTP request
  -> FastAPI route
  -> require_context(authorization)
  -> UserProjectContext
  -> package/repository scoped read or mutation
  -> JSON payload or deterministic 401/403/404/422
```

Strategy ownership is preserved in memory and Postgres:

```text
create StrategySpec with context
  -> row/version carries user_id + project_id
  -> list/detail/mutation predicates check same context
  -> clone preserves caller scope while copying source spec only after source access is authorized
```

## Error handling

- Missing or invalid auth returns `401` with existing auth error payloads.
- Wrong-project detail/mutation returns `404` for resource hiding unless an existing route already uses `403` for policy denial.
- Production/staging startup invalid config raises `RuntimeError`/`ValueError` before app accepts traffic.
- Unsafe schema names raise `ValueError("unsafe postgres identifier: ...")` at construction/migration time.
- Demo seed idempotency handles only expected existing-row conflicts; unexpected exceptions fail loudly.

## Testing strategy

Every segment follows RED -> GREEN -> refactor:

1. Write focused failing tests for one behavior.
2. Run the focused command and confirm the expected failure.
3. Implement the smallest production change.
4. Run the focused command to green.
5. Run a segment slice.
6. Update `structure.md`, `findings.md`, and `handguard.md` with reconciliation evidence.

## Acceptance criteria

- `/api/strategies` requires auth and filters by `UserProjectContext`.
- Strategy approve/clone/status mutations cannot cross project boundaries in memory or Postgres mode.
- Production/staging app creation rejects weak tokens, public tokens, and wildcard/empty CORS.
- Runtime route tests prove protected `/api` endpoints reject missing auth.
- Postgres schema identifiers are validated before interpolation.
- Evidence summary does not present inferred compile status as artifact-backed evidence.
- Demo/fixture evidence remains clearly labeled and disabled by default in production.
- `structure.md`, `findings.md`, and `handguard.md` record each segment and final verification.
