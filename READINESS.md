# Nautilus Builder — Capability Readiness Matrix

**Last updated:** 2026-06-11
**Status convention:** Ready = fully implemented and tested; Partial = implemented but incomplete or not fully tested; Out of scope = not owned by Builder.

| Capability | Status | Evidence required | Owner |
|---|---|---|---|
| Strategy authoring | Ready (dev-demo) | StrategySpec validation tests | Builder |
| Strategy validation | Ready (dev-demo) | Validation suite, forbidden-authority scan | Builder |
| Compile artifact | Ready (dev-demo) | Deterministic IR tests (Segment 5) | Builder |
| Synthetic replay | Ready (dev-demo) | Local replay evidence, BacktestNode smoke | Builder |
| Real catalog replay | Partial | Dataset manifest + replay hash (Segment 6) | Builder |
| Promotion request | Shadow/signal-preview only | Typed evidence refs (Segments 7-8) | Builder |
| Live execution | **Out of scope** | Daedalus/DataTester/ExecTester/reconciliation | Daedalus/external |
| Order submission | **Forbidden** | N/A — Builder must not submit orders | Daedalus only |
| AI advisory drafts | Ready (advisory only) | Prompt audit store, validation gate | Builder |
| Evidence ledger | Partial | Typed evidence model and verifier (Segment 7) | Builder |
| Production deployment | Partial | Docker compose profiles, auth hardening (Segments 10, 12) | Builder |

## Key Definitions

- **Ready (dev-demo):** Works for local development and demo scenarios. Not production-live-trading ready.
- **Ready (advisory only):** AI outputs are suggestions, not execution authority. Must pass deterministic validation before acceptance.
- **Partial:** Core implementation exists but needs additional segments to close gaps.
- **Out of scope:** This capability is intentionally not owned by Builder. It belongs to Nautilus-Daedalus or external systems.
- **Forbidden:** Builder must never implement this capability. It violates the fundamental Builder authority boundary.

## Production/Live-Trading Status

**Nautilus Builder is not production-ready and is not live-trading ready.**

Builder produces strategy specs, validation results, compile artifacts, backtest evidence, and promotion requests. It does not execute live orders, hold venue credentials, or create authoritative TradeAction objects.

Live execution requires:
- NautilusTrader DataTester evidence
- ExecTester evidence  
- Adapter reconciliation reports
- Daedalus execution-boundary confirmation
- Manual operator approval

None of these are within Builder's authority to produce or claim.
