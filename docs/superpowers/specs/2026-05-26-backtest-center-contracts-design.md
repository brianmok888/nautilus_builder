# Backtest Center Contracts Design

**Date:** 2026-05-26
**Repo:** `/home/mok/projects/nautilus_builder`
**Segment:** BT-1 — PMBT-inspired / NautilusTrader-aligned backtest runner contracts and artifact/report policy

## Context

The next adoption slice takes useful architecture ideas from `evan-kolberg/prediction-market-backtesting` without copying its source: explicit replay/run contracts, artifact policy, report metadata, dataset provenance, and optimizer-ready result summaries. Builder must keep the existing NautilusTrader boundary: authoring/backtest/shadow-review only, no live order authority, no credentials, no `TradeAction`, and manual promotion only.

QuantDinger/QuantDinger-Vue remains UI information-architecture inspiration only. This segment is backend contract first; rich UI charts are downstream once reports have stable payloads.

## Recommended approach

Implement a narrow Builder-owned contract module instead of importing PMBT abstractions:

1. Add `packages/backtest_runner/contracts.py` with Pydantic models for:
   - `BacktestRunRequest`
   - `BacktestDatasetProvenance`
   - `BacktestArtifactRef`
   - `BacktestReportSummary`
   - `BacktestRunManifest`
2. Add small pure functions to build deterministic run IDs, checksums, report summaries, and run manifests.
3. Wire `normalize_backtest_result()` to include a report summary and manifest-ready artifact metadata while preserving existing output fields.
4. Keep the implementation independent of live Nautilus nodes/adapters and independent of AI provider secrets.

## Rejected approaches

- **Copy PMBT runner/result code:** rejected because PMBT contains prediction-market-specific assumptions and LGPL-derived Nautilus code; Builder needs clean-room contracts.
- **Add charting dependencies now:** rejected because the backend report contract should stabilize before UI chart libraries are introduced.
- **Expose optimizer execution now:** rejected because optimizer/research jobs require their own offline-only policy segment.

## Acceptance criteria

- Run manifest binds strategy lineage/version, compile hash, dataset ID, catalog/source mode, requested data type, engine mode, run timestamps, and report/artifact metadata.
- Artifact refs require safe Builder/fixture URI schemes, checksum, media type, and scope; path traversal and missing checksums are rejected.
- Report summary exposes trade/fill counts and equity-derived metrics/sections without claiming live execution authority.
- Builder run contracts preserve `orders=0`, `positions=0`, `credentials_used=false`, `live_trading_enabled=false`, and `execution_authority=false` for no-order Builder replay.
- Focused tests fail before implementation and pass after implementation.

## Segment reconciliation rule

After BT-1, update `structure.md`, `findings.md`, and `handguard.md` with the implemented contract, test evidence, and remaining segments: dataset/source modes, safe strategy module registry, offline optimizer jobs, and richer result UI.
