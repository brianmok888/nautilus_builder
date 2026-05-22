# Strategy Test Workflow and Event Spine Design

**Date:** 2026-05-22  
**Status:** approved simplified direction  
**Scope:** define the core Builder workflow for strategy loading/building, parameterized testing, result output, and async AI/ND/notification sidecars using Postgres plus Redis.

## 1. Goal

Simplify Nautilus Builder around one user-facing workflow:

1. UI loads or builds a strategy.
2. User selects test parameters.
3. Backend saves and versions the strategy.
4. Backend validates and compiles the version.
5. Backend enqueues the selected test.
6. Worker executes the test.
7. Backend stores the result.
8. UI displays result output and advisory suggestions.

AI, Nautilus-Daedalus, evomap, LangChain/LangGraph, RAG, and notifications are sidecar lanes that observe workflow events and publish suggestions/reports. They do not replace the core workflow.

## 2. Product workflow

```text
Next.js UI
  load/build strategy
  select params:
    - test type
    - instrument
    - data source
    - period/date range
    - timeframe
    - risk/test settings
        |
        v
Builder API
  save strategy
  create immutable strategy version
  validate
  compile
  enqueue selected test
        |
        v
Worker
  execute test
  store result
  emit completion event
        |
        v
UI output
  metrics
  charts/artifacts
  logs/events
  AI/ND suggestions
```

## 3. Core principle

The core workflow must be backend-owned and headless-capable.

The same task contract should be usable by:

- Next.js UI;
- backend workers;
- scheduled jobs;
- future MCP/agent gateway;
- AI advisory workers;
- ND advisory bridge.

The frontend is a client of backend contracts, not the place where strategy/test logic lives.

## 4. Storage roles

### Postgres is source of truth

Postgres stores durable records:

- users/projects;
- strategy drafts;
- strategy lineage records;
- strategy versions;
- selected test parameters;
- validation reports;
- compile artifacts;
- test jobs;
- test results;
- signal outputs;
- gated signal records;
- AI suggestions;
- ND advisory reports;
- notification preferences;
- notification event logs.

AI lane also uses Postgres for:

- RAG document metadata;
- RAG retrieval traces;
- conversation/task traces;
- LangGraph checkpoints;
- evomap recommendations;
- advisory history;
- feedback records.

Redis events should carry IDs that point back to Postgres records.

Example event payload:

```json
{
  "event": "test.completed",
  "project_id": "project_001",
  "strategy_version_id": "sv_123",
  "test_job_id": "job_456",
  "result_id": "res_789"
}
```

## 4.1 Strategy identity and AI continuity

AI lane continuity must not depend on a shared display name.

Display names can change, differ between lanes, or be rewritten by AI. Continuity must use stable identity keys:

- `strategy_id` — stable logical strategy identity;
- `strategy_lineage_id` — stable family/thread across forks/imports/AI revisions;
- `strategy_version_id` — immutable version being tested;
- `source_ref` — optional external source such as ND strategy reference;
- `parent_version_id` — previous version when AI/backend creates a revision;
- `revision_reason` — why a new version exists;
- `ai_thread_id` — advisory conversation/workflow thread;
- `improvement_cycle_id` — grouped optimize/test/review loop.

Recommended continuity model:

```text
StrategyLineage
  └── Strategy
        ├── Version 1
        ├── Version 2
        └── Version 3

AIThread
  -> linked to strategy_lineage_id
  -> suggestions linked to strategy_version_id and result_id
```

When execution moves from frontend-initiated to backend/worker execution, the UI and AI lane continue the same improvement loop by passing IDs, not names.

Example event payload:

```json
{
  "event": "ai.revision.proposed",
  "project_id": "project_001",
  "strategy_id": "strat_123",
  "strategy_lineage_id": "lineage_abc",
  "parent_version_id": "sv_123",
  "proposed_version_id": "sv_124",
  "ai_thread_id": "ai_thread_789",
  "improvement_cycle_id": "cycle_456",
  "result_id": "res_789"
}
```

Rules:

- names are labels only;
- all AI suggestions must attach to stable IDs;
- backend execution must create or reuse the same `strategy_lineage_id`;
- imported ND strategies get a Builder `strategy_lineage_id` plus `source_ref` to ND;
- AI/evomap/LangGraph state uses `ai_thread_id` and `improvement_cycle_id` to continue after backend jobs complete;
- UI displays names, but API calls and events carry IDs.

This is how Builder can continue improving the same strategy even when execution moves to backend workers and AI lane names differ.

### Redis is movement, not truth

Redis is used for:

- async job/event coordination;
- worker consumer groups;
- progress updates;
- sidecar fanout;
- UI live-update fanout through API/SSE.

Redis must not be the only durable location for strategy versions, results, suggestions, or notifications.

## 5. Redis model

Use **both** Redis Streams and Pub/Sub/SSE style fanout.

### Redis Streams

Use streams for durable backend workflow events and jobs.

Builder-owned streams:

```text
builder:workflow:events
builder:test:jobs
builder:test:progress
builder:ai:requests
builder:ai:suggestions
builder:nd:advisory
builder:nd:reports
builder:notifications
```

Use consumer groups for workers and sidecars.

### Pub/Sub or SSE

Use Pub/Sub/SSE for live UI progress fanout.

The UI must not connect directly to Redis.

Recommended path:

```text
Redis Stream event
  -> Builder API event fanout
  -> SSE or WebSocket
  -> Next.js UI
```

## 6. Redis sharing with Nautilus-Daedalus

Builder may use the same Redis infrastructure as Nautilus-Daedalus, but only with strict namespace separation.

```text
Same Redis instance
  ├── nd:*        # ND-owned streams/keys
  └── builder:*   # Builder-owned streams/keys
```

Rules:

- Builder owns `builder:*`.
- ND owns `nd:*`.
- Builder must not write to ND internal streams.
- ND must not write to Builder internal streams except through explicit bridge contracts.
- Shared Redis does not imply shared authority.
- Cross-system events must use documented bridge stream names and payload schemas.

If ND exposes public integration streams later, Builder can write to those only after a separate approved integration design.

## 7. ND advisory bridge

ND integration should initially be advisory and bridge-based.

Recommended flow:

```text
Builder publishes builder:nd:advisory event
ND bridge reads Builder event + ND context
ND bridge writes builder:nd:reports
Builder stores ND report in Postgres
UI reads ND report through Builder API
```

ND bridge may report:

- compatibility notes;
- strategy similarity/difference;
- promotion-system context;
- gate-readiness feedback;
- notification-routing suggestions;
- warnings about existing ND strategies.

ND bridge must not directly mutate Builder strategy versions unless a later explicit command contract is approved.

## 8. AI advisory lane

AI lane components are sidecars.

They may include:

- RAG retrieval worker;
- LangChain workflow worker;
- LangGraph stateful review worker;
- evomap advisory worker;
- model-specific evaluator workers.

They consume events such as:

- `strategy.versioned`;
- `validation.completed`;
- `compile.completed`;
- `test.completed`;
- `signal.generated`;
- `gate.checked`.

They publish suggestions such as:

- `ai.suggestion.created`;
- `ai.revision.proposed`;
- `risk.warning.created`;
- `evomap.recommendation.created`.

Suggestions are stored in Postgres and linked to strategy version, test job, result, and project.

Suggestions must also link to `strategy_lineage_id`, `ai_thread_id`, and optionally `improvement_cycle_id` so advisory loops continue across frontend edits, backend executions, imports, and forks.

## 9. Notification lane

Notification lane consumes normalized events and sends adjustable notifications.

Events may include:

- strategy saved;
- validation failed/passed;
- test started/completed/failed;
- signal candidate generated;
- AI suggestion ready;
- ND advisory report ready.

Rules:

- notifications are outputs, not commands;
- notification messages must not contain secrets;
- notification workers must not mutate strategy/test state;
- user/project notification preferences live in Postgres.

## 10. Test types

The initial workflow should model test type explicitly.

Supported test type candidates:

- `backtest`;
- `forward_test`;
- `signal_preview`;
- `gated_signal_test`.

Each test type uses the same high-level workflow:

```text
save/version -> validate -> compile -> enqueue -> execute -> store result -> emit events
```

Different test types may use different worker implementations later.

## 11. API shape

The UI should eventually call API operations such as:

- `POST /api/strategies` — save/load strategy draft;
- `POST /api/strategies/{id}/versions` — create immutable version;
- `POST /api/tests` — create test job from version + params;
- `GET /api/tests/{job_id}` — read test job status;
- `GET /api/results/{result_id}` — read output result;
- `GET /api/results/{result_id}/suggestions` — read AI/ND suggestions;
- `GET /api/events/{job_id}/stream` — SSE progress stream.

These are target operations. Exact route names can be finalized in implementation planning.

## 12. Authority rules

Core Builder workflow produces official Builder records:

- strategy versions;
- validation reports;
- compile artifacts;
- test jobs;
- test results;
- signal outputs.

AI/ND lanes produce advisory suggestions/reports by default.

Later gate/promotion designs may decide when an advisory output can become an approved action.

## 13. What this replaces

This simplified workflow/event-spine design supersedes the overcomplicated dual-lane product architecture idea.

Keep the useful parts:

- frontend/backend parity;
- ND awareness;
- AI lane;
- notifications;
- Builder hardguards.

Drop the heavy upfront lane-authority model.

## 14. First implementation recommendation

Start with a small workflow contract slice:

1. `StrategyTestParams` model;
2. `StrategyVersionRecord` model;
3. `TestJobRecord` model;
4. `WorkflowEvent` model;
5. in-memory Postgres-like repository interface for tests;
6. Redis stream publisher interface with fake/in-memory implementation;
7. tests proving save/version/validate/compile/enqueue emits events and stores IDs.

Do not connect to real Redis/Postgres in the first slice unless explicitly requested. Define interfaces first, then swap implementations.

## 15. Success criteria

This design succeeds if:

- the user workflow is simple and visible;
- backend remains source of truth;
- Redis coordinates async work but is not truth;
- Postgres stores AI lane and core records;
- same Redis infrastructure as ND can be reused safely through namespaces;
- AI/ND/notification lanes are sidecars, not blockers;
- Next.js UI remains a client of backend contracts;
- implementation can proceed in small TDD slices.
