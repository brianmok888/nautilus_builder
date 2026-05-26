# Standalone Builder Platform Design

**Date:** 2026-05-26
**Repo:** `/home/mok/projects/nautilus_builder`
**Segment:** PLATFORM-1 — clean-room Builder control-plane schema for AI, backtest, research, paper/live, and Telegram lanes

## Context

The product direction has changed: Nautilus Builder should become the standalone open-source AI strategy builder and NautilusTrader platform. Nautilus-Daedalus remains a private/reference system only. Builder may adopt proven ND architecture patterns, but must not import ND code, require an ND repo at runtime, or copy ND schema names into an open-source product.

The official NautilusTrader source and docs remain the engine authority for adapters, data catalog/backtest behavior, testing evidence, live runtime/reconciliation, and strategy execution boundaries:

- `https://github.com/nautechsystems/nautilus_trader`
- `https://nautilustrader.io/docs/latest/developer_guide/`
- `https://nautilustrader.io/docs/latest/developer_guide/adapters/`
- `https://nautilustrader.io/docs/latest/developer_guide/spec_exec_testing/`

AI/reference systems are advisory only. LangChain/LangGraph/EvoMap can inspire provider orchestration, graph workflows, and continuous-improvement loops, but this segment adds no new runtime dependency on them.

## Recommended approach

Use a Builder-owned PostgreSQL control-plane schema first. This gives later implementation segments a stable durable contract before expanding services, UI, Telegram, paper, or live runtime code.

### Architecture

```text
builder_core       StrategySpec, validation, compiler, lifecycle
builder_ai         prompt -> StrategySpec, audit, review, improvement cycles
builder_data       catalog roots, dataset manifests, artifact refs
builder_backtest   Nautilus backtest jobs, run manifests, report artifacts
builder_research   optimizer jobs, trials, candidate ranking
builder_runtime    authoring/backtest/research/paper/live runtime profiles
builder_gate       risk/manual activation checks before paper/live authority
builder_execution  Nautilus paper/live execution records, disabled by default
builder_telegram   notifications, approval prompts, delivery audit
builder_api/web    FastAPI + Next.js surfaces over these contracts
```

### Runtime modes

Persist mode explicitly instead of inferring authority from a job/table name:

| Mode | Authority |
| --- | --- |
| `authoring` | draft StrategySpec only |
| `backtest` | historical replay only |
| `research` / `optimizer` | offline experiments only |
| `paper` | simulated execution only |
| `live` | disabled by default; allowed only with explicit profile activation, server-side credentials, risk profile, reconciliation, and audit |

The existing UI/backtest/promotion contracts keep `may_submit_order=false`. PLATFORM-1 only adds schema space for future paper/live lanes and makes the dangerous fields default false. Actual order-submission code remains a later segment and must be gated by dedicated tests.

### Data persistence split

- PostgreSQL: control-plane metadata, strategy versions, AI audit, run manifests, promotion approvals, runtime profile activation, Telegram delivery audit, execution reports.
- Parquet/catalog/artifact store: market data, Nautilus catalog data, orders/fills/positions/equity curves, large result frames.
- Redis/event streams: runtime fan-out and status transport, not permanent truth.

### NautilusTrader compatibility fields

Schema records must keep the fields needed to prove NT compatibility later:

- `instrument_id`, `venue`, `bar_type`, `data_type`, `data_cls`, `catalog_path`, time range
- `strategy_class_path`, `config_class_path`, `compile_hash`, `strategy_lineage_id`, `strategy_version_id`
- `engine_mode`, `runtime_mode`, `nautilus_trader_version`
- artifact refs/checksums for orders, fills, positions, reports, and manifests

## Rejected approaches

- **Depend on Nautilus-Daedalus runtime:** rejected because Builder is now the open-source standalone product and ND is private/personal reference only.
- **Copy ND migrations as-is:** rejected because ND has private schema names and live-system assumptions. Builder needs a clean-room `builder.*` schema with open-source naming.
- **Add live execution code now:** rejected because schema alignment must land before paper/live services, risk gates, credentials, and reconciliation code.
- **Store market data/backtest frames in PostgreSQL:** rejected because heavy market/result data belongs in Parquet/catalog/artifact storage; PostgreSQL is metadata/control-plane.

## Acceptance criteria

- Add a new migration `infra/migrations/002_builder_standalone_platform.sql` under only the `builder` schema.
- Cover StrategySpec/versioning, dataset manifests, backtest/research artifacts, AI continuous-improvement audit, promotion packages/approvals, runtime profiles, paper/live run metadata, execution reports, Telegram delivery, and runtime event enrichment.
- Dangerous live flags (`live_trading_enabled`, `execution_authority`, `may_submit_order`) default false.
- Any enabled live authority requires `runtime_mode='live'`, profile activation, manual review, reconciliation, a risk profile, activation identity, activation timestamp, and a config checksum.
- Paper/live records do not store credentials; they reference server-side credential slots/profile IDs only.
- Artifact/catalog references reject traversal and require checksums/media types where relevant.
- Tests assert the schema inventory and safety constraints before implementation and pass after implementation.

## Segment reconciliation rule

After PLATFORM-1, update `structure.md`, `findings.md`, and `handguard.md` with:

- the standalone Builder platform decision;
- the ND decoupling rule;
- the new mode-gated paper/live safety boundary;
- verification evidence;
- remaining implementation segments for AI service persistence, backtest/research persistence, paper runtime scaffold, Telegram menus, live runtime scaffold, and execution lifecycle.
