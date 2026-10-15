# Workflow spine knowledge base

## OVERVIEW
Versioned strategy workflows, events and storage contracts; score 8, a distinct identity/persistence seam.

## WHERE TO LOOK
| Task | Module | Role |
|---|---|---|
| Identity and records | models.py | Strategy/version, jobs, events and results |
| Workflow orchestration | service.py | StrategyTestWorkflowService |
| Event namespace | event_stream.py | In-memory stream and namespace checks |
| In-memory records | repository.py | Reference repository |
| Read projection | projections.py | WorkflowReadModel |
| SQLite persistence | postgres_repository.py | SqliteWorkflowRepository and schema statements |
| PostgreSQL connection | postgres_runtime.py | Builder database connection helper |
| Storage settings | storage_config.py | BuilderPostgresConfig and BuilderRedisConfig |
| Protocol checks | storage_interfaces.py | Repository/stream protocols and fake backends |

## CONVENTIONS
- Import SqliteWorkflowRepository by its real exported name.
- The postgres_repository.py filename is historical; it does not prove PostgreSQL persistence.
- Keep strategy identity separate from strategy-version identity throughout job/result handling.
- Validate storage identifiers; Redis namespaces default to builder and explicitly reject nd.
- Use protocols and their contract checks when introducing a storage implementation.
- AI suggestion records remain proposal/audit records in the workflow.
- Focused checks live in tests/workflow_spine/ and tests/integration/.

## ANTI-PATTERNS
- Do not restore the deprecated PostgresWorkflowRepository facade name.
- Do not present FakePostgresWorkflowRepository or FakeRedisWorkflowStream as real service clients.
- Do not reuse runtime-owned Redis stream namespaces for Builder workflow events.
- Do not bypass validation/version identity when moving from a draft to a tested result.
