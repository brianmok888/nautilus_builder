# Nautilus Builder Production Blocker Closure Design

**Date:** 2026-06-08
**Repository:** `/home/mok/projects/nautilus_builder`
**Reference repository:** `/home/mok/projects/Nautilus-Daedalus` (read-only)
**Requested skills:** `superpowers:brainstorming`, `superpowers:test-driven-development`, `superpowers:nt-review`, `superpowers:nt-architect`, `superpowers:nt-adapters`, `superpowers:nt-live`, `superpowers:nt-testing`, `superpowers:aiogram-dialog-menus` negative-boundary lens.

## Goal

Close the documented production/security blockers while preserving Nautilus Builder as a Builder-only, evidence-only system: no browser-held venue credentials, no Builder live order authority, no Daedalus mutation, and no frontend ownership of runtime action composition.

## Non-goals and hard boundaries

- Do not add `submit_order` paths or authoritative `TradeAction` creation.
- Do not enable live trading from Builder.
- Do not expose `NEXT_PUBLIC_BUILDER_API_TOKEN`.
- Do not add Telegram/aiogram runtime dependencies to Builder; Telegram remains a Daedalus boundary.
- Do not claim NautilusTrader adapter/live readiness without DataTester, ExecTester, reconciliation evidence, and Daedalus execution-boundary approval.
- Do not store raw exchange credentials from browser/UI state.

Allowed posture remains:

```text
Builder-only mode
Backtest evidence
Historical evidence-only
No live order submission
may_submit_order: false
browser_credentials: false
```

## Architecture approach

The closure is split into five reversible, testable segments. Each segment follows RED → GREEN → reconciliation, updates `structure.md`, `findings.md`, and `handguard.md`, then hands off to the next segment only after targeted verification is green. The implementation is intentionally conservative: where a capability violates the Builder boundary, remove or disable the browser/API surface instead of trying to harden it for live use.

## Segment design

### Segment 1 — Credential and Docker packaging safety

**Findings closed:** Docker env credential packaging and browser credential entry.

**Design:**
- Add `.dockerignore` excluding `.env*`, `.git`, caches, local DB/artifact folders, and build outputs.
- Remove `COPY .env.execution.local .env.local` and `RUN touch .env.execution.local` from `Dockerfile.api`.
- Remove Settings-page credential bootstrap UI.
- Remove raw credential value inputs and save action from Execution Lane UI.
- Make HTTP credential-slot creation reject browser/API payloads with a clear error. Preserve backend model code only as an internal seam until a CLI/admin-only design exists.

**Tests:** Dockerfile safety tests, web UI contract tests, frontend component tests, API credential-slot rejection test.

### Segment 2 — API exposure, rate limit enforcement, audit attribution

**Findings closed:** unauthenticated dev API entrypoint, unenforced limiter, missing audit attribution.

**Design:**
- Change `nautilus-builder-api` package script to launch authenticated FastAPI via a new CLI entrypoint.
- Keep dependency-free `dev_server.py` loopback-only unless an explicit unsafe flag is passed.
- Add rate-limit middleware/dependency for protected `/api/*` routes while skipping health/build endpoints.
- Redact Redis URLs in logs and fail closed for Redis limiter outage in production.
- Attach auth actor/project to request state before route handling so `AuditMiddleware` can persist attribution.
- Persist `project_id` in Postgres audit rows and raise/log deterministically for audit failures.

**Tests:** production safety tests, FastAPI route tests, audit middleware tests, Postgres audit repository tests.

### Segment 3 — Artifact store readiness and LLM config persistence

**Findings closed:** artifact-store readiness mismatch and Postgres LLM config persistence bug.

**Design:**
- Build default artifact store from `packages.artifact_store.factory.create_artifact_store()` when none is injected.
- Honor `BUILDER_ARTIFACT_ROOT` for local artifact storage and keep `BUILDER_ARTIFACT_BACKEND` behavior.
- Make `/health/ready` report actual artifact-store initialization status.
- Preserve the Postgres config repository created at startup; do not reset it to `None`.
- Persist sanitized LLM config saves to Postgres and add restart/persistence coverage.

**Tests:** FastAPI ready checks, backtest execution dependency tests, LLM config persistence tests.

### Segment 4 — Frontend runtime-action ownership

**Findings closed:** frontend `order_intent`/risk-approved command and worker/session action ownership.

**Design:**
- Convert Execution Lane UI to observe/request backend profiles and runtime plans only.
- Remove browser construction of `order_intent` and `risk_decision.status="approved"`.
- Remove web buttons for queueing commands, running worker, starting sessions, and stopping sessions.
- Keep status cards and runtime-plan display so operators can see backend-owned readiness.
- Any future command creation must be server-side from approved evidence, not browser-composed.

**Tests:** frontend component tests and web contract grep tests proving no frontend `order_intent` construction or execution control labels.

### Segment 5 — Safety scan and master reconciliation

**Findings closed:** safety scan allowlisting production directories and stale review docs.

**Design:**
- Update `scripts/check_forbidden_authority.sh` to scan production code by default and allow only documented negative/test-policy literals.
- Update `structure.md`, `findings.md`, and `handguard.md` after every segment with CLOSED/remaining evidence.
- Run full targeted backend and frontend verification, plus safety searches.
- Commit using the Lore protocol and push only after `origin/master` fast-forward check.

## NautilusTrader and AI reference alignment

- Official NautilusTrader docs remain authoritative for adapter and live-runtime claims.
- DataTester/ExecTester evidence is mandatory before claiming adapter/data/execution readiness.
- Python `TradingNode` examples must remain integration-specific; Rust-backed `LiveNode` remains the Rust v2/live-node reference path.
- EvoMap, LangChain, and LangGraph stay advisory/downstream references only; Builder will not couple to those runtimes in this closure.

## Error handling and rollback

- Unsafe browser credential submissions return explicit 4xx responses and do not persist values.
- Rate-limit failures in production are treated as deny/closed rather than allow/open.
- Artifact-store factory errors surface in readiness and startup-dependent tests.
- Each segment is small enough to revert independently.

## Verification plan

Per segment:

1. Write failing tests.
2. Verify RED failures.
3. Implement minimal code.
4. Verify targeted tests pass.
5. Update review docs.
6. Run segment reconciliation.

Master reconciliation:

```bash
git diff --check
python3 -m pytest tests/ -q --tb=short
cd apps/web && npm run typecheck && npm test && npm run build
bash scripts/check_forbidden_authority.sh
grep -R "submit_order\|Start live trading\|live trading enabled\|Auto execute\|Guaranteed profit" apps/web --exclude-dir=.next --exclude-dir=node_modules || true
grep -R "?tab=\|tab=strategy\|tab=backtest\|tab=execution" apps/web --exclude-dir=.next --exclude-dir=node_modules || true
```

## Spec self-review

- Placeholder scan: no TBD/TODO placeholders remain.
- Scope check: five independent segments, each with concrete tests and rollback boundaries.
- Ambiguity check: browser credential entry is rejected rather than partially hardened; frontend action ownership is removed rather than renamed.
- Consistency check: production/security readiness is not claimed until all blockers close and review passes.
