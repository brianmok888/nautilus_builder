# ADR 0002: Python static analysis baseline (basedpyright)

- **Status:** Accepted
- **Date:** 2026-06-22
- **Adoption Report reference:** §3.2

## Context

The CI had ruff (lint) and compileall but no static type checking. This meant
import errors, wrong-constructor calls, and dead-code attribute accesses could
reach runtime undetected.

## Decision

Adopt `basedpyright` in scoped `standard` mode, expanding gradually. The initial
include list is 7 packages: ai_builder, auth, pipeline, promotions,
strategy_compiler, strategy_validation, services/api.

Two rules are set to `"none"` for the current codebase's auth-correlation
pattern (`require_context()` returns `tuple[Context | None, Error | None]`;
pyright cannot correlate the two tuple members). These are tracked for a future
optional-narrowing hardening pass.

## Guardrails

- Type checker is CI/dev tooling only; no runtime behavior change.
- `strict` mode only after `standard` is green across all packages.
- Expand the include list incrementally; do not enable repo-wide strict in one pass.

## Outcome

basedpyright found and this adoption fixed 4 real bugs:
1. `services/api/middleware.py`: broken import (`request_id` → `audit_middleware`)
2. `strategy_compiler`: dead unreachable microstructure risk branch accessing
   non-existent `RiskBlock` attributes
3. `fastapi_app`: `ApiResponse(error=...)` → `ApiResponse({...})` (2 sites)
4. `_PgWorkflowAdapter`: incomplete — missing 4 delegating methods routes call

Also added `pip-audit` (supply-chain vulnerability scanning) and `pre-commit`
(local hook enforcement: ruff + file hygiene + private-key detection +
forbidden-authority scan). All kept FAST (no full pytest in pre-commit).

## Verification

basedpyright: 0 errors, 0 warnings. pip-audit: no known vulnerabilities.
CI `static-analysis` job added.
