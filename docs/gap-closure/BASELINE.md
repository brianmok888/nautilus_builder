# Baseline Audit — Gap Closure v1

**Date:** 2026-06-11
**Branch:** master (will create `feat/close-builder-gaps-v1`)
**Commit:** 8b229d7

## Commands Run

```bash
git status --short                              # clean working tree
git rev-parse --short HEAD                      # 8b229d7
python3 -m compileall -q packages services tests scripts  # EXIT: 0
python3 -m pytest tests/ -q --tb=line           # 979 passed, 1 skipped, 1 warning
bash scripts/check_forbidden_authority.sh       # PASSED
cd apps/web && npm run typecheck                # 2 TS6053 for .next types (pre-existing, non-blocking)
cd apps/web && npm test                         # 131 passed, 4 skipped (33 test files)
cd apps/web && npm run build                    # passed
```

## Test Status

- **Backend:** 979 passed, 1 skipped, 1 warning (StarletteDeprecationWarning from testclient)
- **Frontend:** 131 passed, 4 skipped (33 test files passed, 1 skipped)
- **Build:** succeeds with Middleware output
- **Authority scan:** PASSED
- **Compile check:** clean

## Known Pre-existing Issues

1. `apps/web` typecheck shows 2x TS6053 for `.next/types/cache-life.d.ts` — these are generated-file references that resolve after `npm run build`.
2. StarletteDeprecationWarning about `httpx` vs `httpx2` in testclient — non-blocking.

## Builder Version Values

- `pyproject.toml`: `version = "0.1.0"`
- No `packages/builder_metadata/` module exists yet
- No `/health/build` route discovered yet in API routes
- `CHANGELOG.md` last updated 2026-06-07
- `RELEASE.md` last updated 2026-06-07

## Prior Segment Closure (2026-06-08)

Segments 1–5 of the prior review round closed:
1. Docker credential packaging / browser credential entry
2. Packaged API exposure, rate-limit enforcement, audit attribution
3. Artifact readiness, LLM config persistence
4. Frontend runtime-action ownership
5. Forbidden-authority safety-scan hardening
