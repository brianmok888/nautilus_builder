# Nautilus Builder Production-Readiness Closure Design

**Date:** 2026-05-24  
**Workflow:** `superpowers:brainstorming` design, then segment-by-segment `$autopilot`-style TDD loops.  
**Target repo:** `/home/mok/projects/nautilus_builder`  
**Reference repos/docs:** official NautilusTrader docs/repo, EvoMap/evolver, LangChain, LangGraph, and read-only `/home/mok/projects/Nautilus-Daedalus`.

## Goal

Close the remaining production-readiness blockers recorded in `findings.md` while preserving Nautilus Builder's authority boundary: Builder may author, validate, backtest/smoke, observe, and request shadow/signal-preview promotion, but it must not own Daedalus live order authority.

## Design choices

### Approach selected: segment-gated hardening

Use five isolated segments with TDD red/green/refactor and a reconciliation after each segment. This keeps runtime/dependency work, Nautilus smoke evidence, promotion evidence, schema/docs alignment, and hygiene changes independently reviewable.

Rejected alternatives:

- **One broad production rewrite:** too risky for a repo whose existing strengths are narrow contract seams.
- **Docs-only closure:** would not close the runtime mismatch or promotion evidence weakness.
- **Adopt EvoMap/LangChain/LangGraph now:** out of scope; these remain reference/advisory ecosystems, not Builder runtime dependencies in this pass.

## Segment design

### Segment 1 — Runtime dependency truth

Add a Builder-owned runtime check that compares the installed `nautilus_trader` distribution to `packages.backtest_runner.engine_contract.NAUTILUS_TRADER_VERSION`. Add an actual environment test and document that production verification must run in the synced environment. Generate/keep lock evidence where possible and update local environment evidence.

Acceptance:

- A test fails on a version mismatch and passes when the installed package matches `1.223.0`.
- `structure.md`, `findings.md`, and `handguard.md` record the dependency-check evidence.

### Segment 2 — Real NautilusTrader BacktestEngine smoke

Add a minimal concrete NautilusTrader `BacktestEngine` lifecycle smoke that imports `BacktestEngine`, constructs it with quiet logging, runs an empty deterministic backtest lifecycle, disposes it, and returns an explicit `real_nautilus_engine_smoke` evidence mode. This does not replace fixture/injected result semantics; it proves the pinned engine can initialize/run in the local environment.

Acceptance:

- Fixture evidence remains labeled `fixture`.
- Injected evidence remains labeled `injected_engine`.
- Real smoke evidence is labeled separately and includes installed/runtime version.
- No live credentials, adapters, `TradeAction`, or live order authority are introduced.

### Segment 3 — Promotion evidence hardening

Make `/api/promotions/shadow` evidence-backed instead of fabricated. Require explicit evidence refs and gate compatibility input; reject missing required evidence with a 422. Keep `/api/promotions/request` as the safe user-facing manual-approval path.

Acceptance:

- Missing evidence for `/api/promotions/shadow` fails.
- Complete evidence succeeds and does not fabricate refs.
- Promotion payload remains `signal_preview_only`, `may_submit_order=False`, and `may_create_trade_action=False`.

### Segment 4 — StrategySpec docs/schema alignment

Close drift between `doc/nautilus_builder_hardguards.md` and `packages/strategy_spec/models.py`. Extend the executable schema for the documented indicator/comparison subset where cheap and safe, and clarify docs for logical combinators that are represented by `all`/`any` blocks rather than direct runtime operators.

Acceptance:

- Tests prove documented executable indicator/operator names are accepted.
- Unknown indicators/operators remain rejected.
- Docs state the executable schema truth unambiguously.

### Segment 5 — Readiness hygiene

Refresh README limitations and remove the Pydantic warning caused by `BuilderPostgresConfig.schema` shadowing `BaseModel.schema`.

Acceptance:

- README reflects current package/API/frontend/E2E reality and remaining production gaps.
- Storage config uses `db_schema` internally while accepting the old `schema` input alias.
- Tests assert the new field and table naming behavior.
- E2E startup no longer emits the avoidable schema-field warning.

## Verification plan

Each segment runs focused failing tests first, implements minimal changes, then runs focused green tests and updates `structure.md`, `findings.md`, and `handguard.md`.

Master reconciliation runs:

```bash
python3 -m compileall -q packages services tests
rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/workflow_spine tests/auth tests/api -q
cd apps/web && npm run typecheck && npm test && npm run build && npm run test:e2e
```

Authority grep must confirm no new Builder live-order path.
