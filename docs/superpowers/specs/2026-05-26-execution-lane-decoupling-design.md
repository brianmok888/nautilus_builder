# Execution Lane Decoupling Design

**Date:** 2026-05-26
**Repo:** `/home/mok/projects/nautilus_builder`
**Segment:** EXEC-1 — standalone execution lane contracts and scaffold

## Context

Builder now owns the standalone platform control plane. The next user need is to run an execution lane independently from strategy authoring/research work, so an already-approved paper/live lane can keep processing execution commands while the operator iterates on other strategies.

NautilusTrader remains the engine authority. The lane design follows the same high-level separation used by live trading systems: strategy/signal work produces reviewed intent, while an execution lane owns order lifecycle, reconciliation, execution reports, and runtime status. This segment does not implement broker order submission; it creates the Builder-owned lane contract, queue/service, API surface, worker scaffold, and DB migration needed for a later Nautilus `LiveNode` / adapter-backed implementation.

## Approach

Add an explicit `execution_lane` package and migration:

1. `ExecutionLaneProfile` — mode-gated runtime profile for `paper` or `live` lanes. It is always `strategy_lane_coupled=false` and can be started/stopped independently.
2. `ExecutionLaneCommand` — queue item produced from a gate/manual approval path, not from a live strategy process. It carries idempotency, strategy lineage/version, risk decision, order intent, and authority flags.
3. `ExecutionLaneReport` — lane-owned execution outcome record; this is execution evidence, not strategy evidence.
4. `ExecutionLaneService` — in-memory contract service for registration, enqueue, claim, and report flows. It enforces tenant/project/profile isolation and idempotency.
5. `services/workers/execution_lane_worker.py` — backend-only worker entrypoint scaffold, with no strategy imports.
6. API routes under `/api/execution-lane/*` for status/profile/command contract tests.
7. `infra/migrations/003_builder_execution_lane.sql` for durable execution lane runs, commands, reports, and heartbeats.

## Authority rules

- `paper` mode is simulated execution only: `may_submit_order=false`, `live_trading_enabled=false`, no live credentials.
- `live` mode is disabled by default. A command may represent submit authority only when the profile and command both include live mode, manual approval, risk profile, credential slot ref, reconciliation, activation identity/time, config checksum, and approved risk decision.
- Commands must not include browser secrets or strategy process coupling fields.
- Strategy authoring/backtest/research can continue while execution lane queue/worker state changes because the lane consumes explicit commands and does not import strategy-lane runtime objects.

## Rejected approaches

- **Let strategies call execution directly:** rejected because it couples authoring/research to order lifecycle and prevents independent lane operation.
- **Add real broker submission now:** rejected because Nautilus adapter credentials, reconciliation, and live-node integration need a dedicated risk-tested segment.
- **Use browser controls as execution authority:** rejected because runtime authority must stay backend-owned and audited.

## Acceptance criteria

- Tests prove paper lane commands can be enqueued, claimed, and reported without strategy-lane coupling.
- Tests reject strategy process IDs, secrets, missing live gates, and mismatched runtime profiles.
- API exposes lane status/profile/command contracts without inventing business rules outside `packages.execution_lane`.
- Migration 003 applies after migrations 001 and 002 in PostgreSQL 16.
- Existing authoring/backtest/research tests continue to pass.
