# Builder Database Boundary

## Overview

Nautilus Builder owns its own database (`nautilus_builder_db`). This is a hard
architectural boundary — the Builder must never write to the Nautilus-Daedalus
runtime database or any trading system database.

## Database Separation

```
PostgreSQL server / cluster
├── nautilus_builder_db     ← Builder owns this (full read/write)
├── nautilus_daedalus_db    ← ND runtime owns this (Builder has NO access)
└── analytics_db / lake     ← optional research/read-only later
```

## Builder-Owned Tables

All tables live in the `builder` schema of `nautilus_builder_db`:

| Table | Migration | Purpose |
|-------|-----------|---------|
| `strategies` | v1 | Strategy registry (id, lineage, status, latest_spec) |
| `strategy_versions` | v1 | Immutable strategy version snapshots |
| `adapters` | v1 | Market adapter registry |
| `instruments` | v1 | Instrument catalog per adapter |
| `compiler_runs` | v2 | Strategy compiler run records |
| `replay_runs` | v2 | Replay/backtest run records |
| `promotion_ledger` | v2 | Evidence-gated promotion ledger |
| `audit_events` | v2, v3 | Audit trail for all mutations |
| `backtest_jobs` | v4 | Backtest job lifecycle and artifacts |
| `backtest_results` | v4 | Backtest outcomes (metrics, reports) |
| `builder_config` | v4 | Non-secret key-value config |
| `workflow_results` | v4 | Workflow result persistence |

## DB User Boundary

For demo and local development:
- **Database**: `nautilus_builder_db`
- **User**: `builder_app` (or `builder` in docker-compose)
- **Permissions**: Owner/write only on `nautilus_builder_db`

For future runtime separation:
- **Database**: `nautilus_daedalus_db`
- **User**: `nd_runtime`
- **Builder has NO write permission** on this database

## Environment Variable

```
BUILDER_DATABASE_URL=postgresql://builder_app:password@postgres:5432/nautilus_builder_db
```

The Builder only reads `BUILDER_DATABASE_URL`. It never reads:
- `ND_RUNTIME_DATABASE_URL`
- `NAUTILUS_DAEDALUS_DATABASE_URL`
- `TRADING_DATABASE_URL`

## In-Memory Fallback

When `BUILDER_DATABASE_URL` is not set, the Builder falls back to in-memory
repositories for lightweight local development. A warning is logged:

```
WARNING: Running with in-memory Builder repositories. State will not survive restart.
```

Production and demo deployments must always set `BUILDER_DATABASE_URL`.

## Promotion Handoff

The promotion handoff from Builder to runtime is artifact-based:

1. Builder records evidence in `promotion_ledger` (compile hash, replay hash, artifact URI)
2. Builder sets strategy status to `execution_ready`
3. Runtime reads the promotion ledger entry and artifact
4. Runtime re-validates the promoted package independently
5. Builder never grants live execution authority

## Read-Only Access to External Data

Builder may read selected ND/runtime/research data only through:
- Controlled read-only APIs
- Read-only replicas
- Exported artifacts
- Dataset indexes

Builder must never write to runtime DB tables.
