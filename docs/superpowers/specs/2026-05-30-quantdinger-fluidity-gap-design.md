# QuantDinger Fluidity Gap — Implementation Design

**Date:** 2026-05-30
**Status:** Approved for execution
**Scope:** 7 QuantDinger improvements + open findings closure
**Constraints:** Zero new dependencies, preserve all handguards, TDD per segment

## Problem

Nautilus Builder has architecturally superior domain boundaries vs QuantDinger, but developer/operator onboarding friction is high. An operator cannot go from clone to running app in under 5 minutes. There are no runnable examples, no onboarding doc, no operational scripts, and no strategy development guide.

## Success Criteria

1. `git clone` → `docker compose up -d` → working app in <5 min
2. New developer reads `DEVELOPMENT.md` and can run local dev in <10 min
3. `docs/examples/` contains 2-3 runnable strategy demo scripts
4. `doc/strategy_dev_guide.md` walks: indicator → strategy → backtest → promote
5. Adapter registry supports drop-in discovery pattern
6. AI Builder can parse `# @param` structured comments into StrategySpec params
7. All open findings (M4, L1-L4, L9, L10) resolved
8. 459+ tests still passing, handguards intact

## Segments

### S12: .env.example + scripts/run_dev.sh (P0, Small)
- Create `.env.example` with all configurable env vars documented
- Create `scripts/run_dev.sh` — starts API + frontend + watches tests
- Create `scripts/run_tests.sh` — runs full verification gate
- Tests: script execution tests, env var presence checks

### S13: DEVELOPMENT.md (P0, Small)
- Prerequisites (Python 3.12+, Node.js, Docker)
- Quick start (5 commands to running app)
- Local development (API only, frontend only, full stack)
- Testing (unit, integration, frontend, E2E)
- Troubleshooting (common issues and fixes)
- No code tests needed — documentation only

### S14: docs/examples/ with runnable demos (P1, Medium)
- `docs/examples/demo_strategy_basic.py` — simplest StrategySpec → validate → compile
- `docs/examples/demo_strategy_backtest.py` — full pipeline with catalog replay
- `docs/examples/demo_adapter_discovery.py` — adapter registration + lookup
- Tests: each example script runs without error in test environment

### S15: Strategy development guide (P1, Medium)
- `doc/strategy_dev_guide.md` — write indicator → save as strategy → run backtest → promote to live
- Tied to actual Builder seams (StrategySpec, validators, compiler, backtest_runner)
- Tests: documentation cross-reference test (all mentioned modules exist)

### S16: Auto-discovery factory for adapters (P2, Medium)
- `packages/adapter_registry/discovery.py` — `AdapterFactory` base + registration
- Drop-in pattern: new adapter module registers itself via decorator
- `adapter_registry/__init__.py` auto-imports registered adapters
- Tests: registration, lookup, duplicate detection, missing adapter handling

### S17: # @param convention for AI Builder (P2, Medium)
- `packages/ai_builder/param_parser.py` — parse structured comments
- Convention: `# @param name:type:default description`
- `# @strategy name="MyStrategy" timeframe="5-MINUTE"`
- Integration with existing `validate_strategy_spec()`
- Tests: parsing, type coercion, missing params, invalid syntax

### S18: Zero-config docker compose (P3, Med-High)
- Seed data script for initial DB population
- Improve Dockerfile.api with proper layer caching
- Frontend Dockerfile optimization
- Docker health checks already exist; verify end-to-end
- Tests: docker compose config validation, seed data verification

### S19: Open findings fixes (Medium)
- M4: Frontend `api.test.ts` — mock all fetch calls with `vi.fn()`
- L1: `storage_config.py` — add migration path comment + deprecation deadline
- L2: Backtest `legacy_hash` — document migration plan
- L3: Frontend test selectors — use data-testid
- L4: `__all__` exports — complete for all packages
- L9: Token exposure — document server-side proxy recommendation
- L10: InMemory dicts — add maxlen documentation + TODO for Postgres migration
- Tests: per-fix regression tests

## Execution Protocol

Each segment follows TDD autopilot:
1. RED: Write failing tests
2. GREEN: Implement minimal code
3. REFACTOR: Clean up
4. Reconcile: Full test suite + update structure.md/findings.md/handguard.md

After all segments:
- Master reconciliation
- Update all three review docs
- Commit, merge, push to origin/master

## Constraints

- Zero new dependencies (superpowers is zero-dep by design)
- No `submit_order`/`TradeAction` in Builder code
- No aiogram/aiogram-dialog imports in Builder
- No weakening of `execution_authority=False`
- All handguards preserved
- NautilusTrader 1.227.0 pinned

## References

- NautilusTrader: https://github.com/nautechsystems/nautilus_trader
- Daedalus: /home/mok/projects/Nautilus-Daedalus
- EvoMap: https://github.com/EvoMap/evolver
- LangChain: https://github.com/langchain-ai/langchain
- LangGraph: https://github.com/langchain-ai/langgraph
