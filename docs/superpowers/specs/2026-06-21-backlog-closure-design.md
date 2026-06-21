# 2026-06-21 Backlog Closure Design

Generated: 2026-06-21
Scope: Close the production-readiness backlog (`findings.md` + the 2026-06-21 fix
backlog P0–P4) across `packages/`, `services/`, `tests/`, and `apps/web/`.
Reference posture: NautilusTrader (v1.227.0 pinned) is execution/backtest/live
authority; AI/LangChain/LangGraph/EvoMap lanes are advisory-only.

## Goal / success criteria

- Every P0 and P1 item closed with a regression test that fails before the fix
  and passes after.
- `pytest -q` is green on the full suite (currently OpenAPI + 11 web tests fail).
- No new dependencies (zero-dep contract preserved).
- No `as any` / `@ts-ignore`; no weakened tests; no deleted failing tests.
- TradeHUD / AI lanes remain read-only / advisory: cannot submit orders, cannot
  collect credentials, cannot bypass promotion/evidence gates.
- `structure.md`, `findings.md`, `handguard.md` updated with closure evidence.

## Design decisions

1. **Auth pattern reuse.** Every `/api/*` route already follows
   `context, auth_error = require_context(authorization)` -> early return on
   error. TradeHUD routes adopt the identical closure. The SSE route performs the
   auth check *before* constructing `StreamingResponse` so a stream never starts
   on an unauthenticated request.

2. **Redaction helper placement.** Add `packages/pipeline/redaction.py` with
   `_redact_error_message` (API keys, bearer tokens, redis URLs, credential-like
   substrings). `PipelineStep` gains optional `detail` and `error_type` (default
   `None`, `extra="forbid"` preserved). Default-None keeps all existing callers
   and serialized snapshots valid.

3. **RedisRateLimiter fail-closed default.** Flip constructor default to
   `fail_closed=True`; existing local/dev tests that need fail-open must pass
   `fail_closed=False` explicitly. Docstring rewritten: fail-open is local/dev
   only. `create_fastapi_app` already passes the correct value so production is
   unaffected; the change removes the footgun of bare construction.

4. **lifespan migration.** Move `_revalidate_evidence_storage()` from
   `@app.on_event("startup")` to an `@asynccontextmanager` lifespan, preserving
   identical fail-closed behavior. Drop the `hasattr(app,"on_event")` guard.

5. **NativeTradingNodeSessionRunner.stop idempotency.** `pop(session_id, None)`;
   `NOT_FOUND` result for unknown/double stop; `STOP_TIMEOUT` lifecycle event +
   skip `dispose()` if the thread is still alive after `join(timeout=5.0)`.

6. **Web contract fix.** Restore a thin root `apps/web/app/page.tsx` that
   re-exports the builder shell page. This matches what the contract tests assert
   and keeps the standalone-merge intent (TradeHUD decoupled from builder shell)
   intact without rewriting 11 tests. (Chosen over rewriting tests because the
   root page is the intended public landing surface.)

7. **Evidence factory guard (P2-1).** Add
   `create_evidence_ledger_service(repo, *, environment)` in
   `packages/evidence_ledger/` that raises outside LOCAL when given an in-memory
   repo. `create_fastapi_app` continues to use its inline guard; the factory adds
   defense-in-depth for direct construction.

8. **Paper strategy (P2-6/P2-7).** Add lifecycle logging (on_start/on_stop/
   on_reset, instrument-not-found branch) and `request_bars` warmup before
   `subscribe_bars` (bar mode only). Tick mode unchanged.

9. **LLM transport (P2-5).** Replace `urllib.request.urlopen` in
   `packages/ai_builder/provider.py` with `httpx.Client(timeout=..., verify=True)`
   if `httpx` is already a transitive dependency; otherwise construct an explicit
   `ssl.SSLContext` and pass it to `urlopen` (no new dependency). Keep S310
   suppression removed where possible.

10. **Legacy stream map (P3-1).** Add owner / expiry / removal-criteria constants
    in `packages/tradehud_contracts/config.py`; require explicit env for legacy
    namespace; add expiry test.

11. **Small cleanups (P3-2/P3-3/P3-4/P4-1/P4-2/P4-3/P4-4).** Historical doc
    banners, Rust LiveNode "not implemented" label kept, AI advisory static
    guard test, duplicate status field documentation/narrowing, narrow the
    `except` in `_installed_nautilus_version`, rename demo token, add `py.typed`.

## Segment execution order (TDD per segment)

- S1: P0-2 evidence context bug.
- S2: P0-1 TradeHUD route auth + SSE.
- S3: P0-3 pipeline error preservation + redaction.
- S4: P1-1 OpenAPI snapshot + P1-2 root page.
- S5: P1-3 redis fail-closed default + P1-4 lifespan + P1-5 session stop.
- S6: P2/P3/P4 subset (evidence guard, paper strategy, LLM transport, legacy
  stream map, AI advisory static test, small cleanups).

Reconciliation after each segment (run the segment's tests + full pytest, update
ledgers, commit). Master reconciliation + ledger update + merge/push at the end.

## Out of scope (explicit)

- The full execution_lane module split (P2-2) and the full tradehud Redis adapter
  module split (P2-3): these are large refactors behind a green test gate. The
  backlog lists them as "after behavior is locked by tests". This cycle locks the
  behavior; the split itself is a follow-up. A boundary/LOC test note will record
  the deferral.
- Production Redis SSE fallback policy (P2-4): implemented as part of S2 where
  cheap (emit degraded event in production when configured-but-unavailable), full
  UI provenance surfacing left to frontend work.
