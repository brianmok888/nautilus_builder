# AGENTS

## Scope
- `tests/` is feature-mirrored contract enforcement.
- Tests define what the repo actually guarantees today.

## Conventions
- Mirror feature/package names: `tests/<domain>/test_<behavior>.py`.
- Use behavior-first names that describe the rule being preserved.
- Keep tests small and boundary-oriented: forbidden behavior, lifecycle gates, replay, contract payloads, deterministic hashing.
- Use `tests/conftest.py` repo-root path insertion; imports should come from `packages.*` or `services.*` directly.

## Current harness reality
- Lightweight pytest only; no fixture-heavy framework, DB harness, or frontend runner.
- `tests/web/` validates Python-backed UI contracts, not actual TSX execution.
- `tests/integration/` is still a minimal verification harness, not a full deployed E2E stack.

## Do not
- Do not add tests that assume a real frontend build pipeline exists.
- Do not couple tests to Nautilus-Daedalus source or live credentials.
- Do not turn contract tests into broad end-to-end simulations without real runtime support.

## Verification
- Run focused slices while changing one seam.
- Use the full suite only after seam-local tests are green.
