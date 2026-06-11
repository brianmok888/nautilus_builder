# Nautilus Builder — Capability Readiness Matrix

**Last updated:** 2026-06-11 (v4 closure)
**Builder version:** 0.5.0
**Status convention:** Ready = fully implemented and tested; Partial = implemented but incomplete; Out of scope = not owned by Builder; Blocked = requires external work.

| Capability | Status | Blocking segments | Evidence required |
|---|---|---|---|
| Strategy authoring | Ready (dev-demo) | — | StrategySpec validation tests |
| Strategy validation | Ready (dev-demo) | — | Validation suite, forbidden-authority scan |
| Strategy compiler | Partial | Deterministic IR bundle completeness | Deterministic hash tests, artifact bundle |
| Synthetic backtest | Ready (dev-demo) | — | Local replay evidence, BacktestNode smoke |
| Real dataset replay | Blocked | Real Parquet fixtures, production-scale replay harness | Dataset manifest, Parquet/DuckDB contracts |
| Promotion contracts | Partial | Catalog backtest requirement | Typed evidence refs, evidence ledger |
| Live execution | **Out of scope** | Builder must not own live execution | Daedalus/DataTester/ExecTester/reconciliation |
| ND runtime changes | **Out of scope** | Builder must not edit Daedalus runtime | N/A |
| AI advisory drafts | Ready (advisory only) | — | Prompt audit store, validation gate, secret redaction |
| Production deployment | Partial | CI security/docker workflows, startup fail-closed validation | Auth enforcement, object store, service supervision |

## Machine-Readable Status

See `doc/readiness_status.json` for the JSON export of this matrix.

## Key Definitions

- **Ready (dev-demo):** Works for local development and demo scenarios. Not production-live-trading ready.
- **Ready (advisory only):** AI outputs are suggestions, not execution authority.
- **Partial:** Core implementation exists but needs additional work.
- **Blocked:** Requires external work or new infrastructure.
- **Out of scope:** Not owned by Builder. Belongs to Nautilus-Daedalus or external systems.

## Production/Live-Trading Status

**Nautilus Builder is not production-ready and is not live-trading ready.**

Builder produces strategy specs, validation results, compile artifacts, backtest evidence, and promotion requests. It does not execute live orders, hold venue credentials, or create authoritative TradeAction objects.

Live execution requires:
- NautilusTrader DataTester evidence
- ExecTester evidence
- Adapter reconciliation reports
- Daedalus execution-boundary confirmation
- Manual operator approval
