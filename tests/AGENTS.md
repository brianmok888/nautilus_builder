# Test knowledge base

## OVERVIEW
Feature-mirrored Python contract enforcement; score 11, separate from the frontend test runners.

## STRUCTURE
- Domain slices mirror packages: strategy_spec, strategy_validation, strategy_compiler.
- Workflow/evidence slices include workflow_spine, promotions and evidence_ledger.
- Runtime contract slices include execution_lane, backtest_runner and replay.
- Transport/storage slices include api, auth, postgres and artifact_store.
- TradeHUD has tradehud_contracts, tradehud_redis and shared fixtures.
- web/ checks Python/source UI contracts; integration/ composes backend seams.
- Hygiene and CI slices check repository/deployment boundaries.

## WHERE TO LOOK
| Task | Location | Surface exercised |
|---|---|---|
| Import setup | conftest.py | Adds repository root to sys.path |
| HTTP behavior | api/ | FastAPI, auth, SSE and OpenAPI |
| TradeHUD payloads | tradehud_contracts/, tradehud_redis/ | Normalization and adapter contracts |
| Storage behavior | postgres/ | Repository and migration contracts |
| Browser behavior | ../apps/web/e2e/ | Separate Playwright runner |
| React and TS behavior | ../apps/web/**/*.test.ts* | Separate Vitest runner |

## CONVENTIONS
- Use behavior-first test_<rule>.py names and packages.* or services.* imports.
- Run python3 -m pytest tests/<seam>/ -q for the affected contract first.
- Root pyproject.toml configures asyncio auto mode and coverage for packages/services.
- Inspect each fixture before inferring whether it uses fakes, SQLite or an external service.
- Python web tests do not execute TSX; frontend builds and test runners now exist independently.

## ANTI-PATTERNS
- Do not claim deployed E2E coverage from an in-process integration or source-text assertion.
- Do not require live credentials or imports from the Daedalus source tree.
- Do not substitute browser tests for backend policy contracts, or vice versa.
