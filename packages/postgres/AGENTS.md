# PostgreSQL persistence knowledge base

## OVERVIEW
Builder-owned PostgreSQL repositories and SQL migration runner; score 8, distinct from workflow SQLite storage.

## WHERE TO LOOK
| Task | Module | Role |
|---|---|---|
| Connections | connection.py | DSN, direct connection and pool helpers |
| Migration ledger | migrations.py | Apply, version and rollback |
| Strategy records | strategy_repository.py | PostgreSQL strategy storage |
| Adapters | adapter_repository.py | Adapter persistence |
| Backtest jobs | backtest_job_repository.py | Job repository |
| Workflow results | workflow_result_repository.py | Result repository |
| Promotion evidence | promotion_ledger_repository.py | Promotion ledger validation/storage |
| Configuration | config_repository.py | Builder configuration persistence |
| Audit | audit_event_repository.py | Audit event records |
| SQL identifiers | identifiers.py | Safe identifier handling |
| Defaults | seed.py | Builder market-data seed records |

## CONVENTIONS
- Keep this storage on Builder's database, not the runtime/trading database.
- Use the connection helpers rather than embedding database URLs in callers.
- Raw baseline SQL lives in infra/migrations/; root migrations/ is the Alembic surface.
- Consult docs/adr/0003-database-migration-framework.md before changing migration ownership.
- workflow_spine/postgres_repository.py is a SQLite implementation despite its filename.
- tests/postgres/ covers this seam; inspect its connection doubles before claiming integration evidence.
- Preserve safe identifier handling and repository transaction boundaries.

## ANTI-PATTERNS
- Do not interpolate unvalidated schema/table identifiers into SQL.
- Do not confuse fake/SQLite repository tests with a verified PostgreSQL deployment.
- Do not silently replace the baseline migration path with an unrelated framework.
- Do not let Builder migrations or seeds write to ND runtime-owned databases.
