# Builder Production Blocker Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close Nautilus Builder's documented production/security blockers without adding live execution authority.

**Architecture:** Implement five isolated TDD segments: Docker/credential safety, API/rate-limit/audit hardening, artifact/LLM persistence, frontend runtime-action ownership removal, and safety/docs reconciliation. Each segment starts with failing tests, lands the minimal code, updates review docs, and runs targeted verification before the next segment.

**Tech Stack:** Python 3.12, FastAPI, Pydantic v2, pytest, Next.js 15, React 19, Vitest, Ant Design, NautilusTrader boundary contracts.

---

## File map

- `.dockerignore`: new Docker context exclusions.
- `Dockerfile.api`: remove local env copy pattern.
- `tests/test_dockerfile_safety.py`: Docker context and env-copy regression tests.
- `apps/web/app/config/page.tsx`: remove browser credential bootstrap.
- `apps/web/components/config/CredentialSlotBootstrap.tsx`: delete or decommission browser raw credential component.
- `apps/web/components/config/ExecutionLaneFeaturePanel.tsx`: remove raw credential inputs and browser runtime-action composition.
- `apps/web/components/config/ExecutionLaneFeaturePanel.test.tsx`: frontend safety regressions.
- `apps/web/lib/api.ts`, `apps/web/lib/types.ts`: remove browser credential-slot helper if unused.
- `services/api/routes/execution_lane.py`, `services/api/fastapi_app.py`: reject credential-slot HTTP writes and harden runtime endpoints.
- `pyproject.toml`, `services/api/fastapi_cli.py`, `services/api/dev_server.py`: authenticated API entrypoint and dev-server guard.
- `packages/auth/redis_rate_limit.py`, `packages/auth/audit_middleware.py`: limiter/audit hardening.
- `packages/postgres/migrations.py`, `packages/postgres/audit_event_repository.py`: project-aware audit persistence if needed.
- `packages/artifact_store/factory.py`, `services/api/fastapi_app.py`: artifact-store startup/readiness wiring.
- `services/api/routes/llm_config.py`: Postgres config persistence path.
- `scripts/check_forbidden_authority.sh`: scan production directories by default.
- `structure.md`, `findings.md`, `handguard.md`: continuously updated reconciliation ledger.

## Segment 1: Credential and Docker packaging safety

- [ ] **Step 1: Write RED Docker tests**

Add assertions to `tests/test_dockerfile_safety.py` proving `.dockerignore` exists, excludes `.env*`, and `Dockerfile.api` does not copy `.env.execution.local`.

- [ ] **Step 2: Run RED Docker tests**

Run: `python3 -m pytest tests/test_dockerfile_safety.py -q`
Expected: FAIL because `.dockerignore` is missing and Dockerfile copies `.env.execution.local`.

- [ ] **Step 3: Implement Docker safety**

Create `.dockerignore` and remove env-file copy/touch from `Dockerfile.api`.

- [ ] **Step 4: Write RED browser credential tests**

Update API/web tests to expect no browser credential UI and credential-slot HTTP POST rejection.

- [ ] **Step 5: Run RED browser credential tests**

Run targeted pytest and Vitest tests. Expected: FAIL while UI/API still allow raw credentials.

- [ ] **Step 6: Implement browser credential removal**

Remove Settings credential bootstrap, remove raw credential form in Execution Lane, and reject `/api/execution-lane/credential-slots` browser/API submissions.

- [ ] **Step 7: Verify Segment 1 GREEN**

Run Docker, API, web contract, and targeted Vitest tests.

- [ ] **Step 8: Reconcile docs**

Update `structure.md`, `findings.md`, `handguard.md` with Segment 1 CLOSED evidence.

## Segment 2: API exposure, rate-limit enforcement, audit attribution

- [ ] **Step 1: Write RED entrypoint/rate-limit/audit tests**

Tests should prove packaged CLI is authenticated FastAPI, dev server rejects non-loopback without unsafe flag, protected `/api/*` routes enforce rate limiting, and audit events include actor/project.

- [ ] **Step 2: Verify RED**

Run targeted API/auth tests. Expected: FAIL on current implementation.

- [ ] **Step 3: Implement minimal hardening**

Add FastAPI CLI entrypoint, dev-server unsafe guard, rate-limit middleware, Redis redaction/fail-closed policy, and request-state auth context for audit.

- [ ] **Step 4: Verify GREEN and reconcile docs**

Run targeted tests and update docs with Segment 2 evidence.

## Segment 3: Artifact readiness and LLM config persistence

- [ ] **Step 1: Write RED artifact/LLM tests**

Tests should prove `BUILDER_ARTIFACT_ROOT` is honored by default app startup and Postgres LLM config saves persist.

- [ ] **Step 2: Verify RED**

Run targeted API tests. Expected: FAIL because app ignores artifact factory and resets `_pg_config_repo`.

- [ ] **Step 3: Implement minimal wiring**

Create artifact store from env when not injected, report real readiness, preserve `_pg_config_repo`.

- [ ] **Step 4: Verify GREEN and reconcile docs**

Run targeted tests and update docs.

## Segment 4: Frontend runtime-action ownership

- [ ] **Step 1: Write RED frontend action-ownership tests**

Tests should prove frontend source does not construct `order_intent`, `risk_decision.status="approved"`, or expose worker/session control buttons.

- [ ] **Step 2: Verify RED**

Run targeted web tests. Expected: FAIL because current panel constructs commands and actions.

- [ ] **Step 3: Implement observation-only UI**

Remove command/worker/session actions from frontend; keep backend profile/runtime status display.

- [ ] **Step 4: Verify GREEN and reconcile docs**

Run targeted web tests and update docs.

## Segment 5: Safety scan and master reconciliation

- [ ] **Step 1: Write RED safety scan tests**

Tests should prove production directories are scanned and forbidden authority is not allowlisted wholesale.

- [ ] **Step 2: Verify RED**

Run safety scan tests. Expected: FAIL on allowlisted production dirs.

- [ ] **Step 3: Implement safety scan inversion**

Update scan to include production dirs by default and maintain explicit false-positive filtering.

- [ ] **Step 4: Master verification**

Run backend tests, frontend typecheck/tests/build, safety grep, `git diff --check`, and final review.

- [ ] **Step 5: Lore commit and push**

Commit with Lore trailers, `git pull --ff-only origin master`, then push `origin master`.

## Plan self-review

- Spec coverage: all eight blockers map to segments.
- Placeholder scan: no TBD/TODO placeholders.
- Type consistency: plan uses existing route/service/component names.
- Scope control: no Daedalus mutation, no live trading authority, no new dependencies.
