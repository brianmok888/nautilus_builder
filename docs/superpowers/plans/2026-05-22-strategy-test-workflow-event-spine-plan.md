# Strategy Test Workflow Event Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax and are intended to be completed in order. Do not skip verification steps. Do not broaden scope. Keep all work inside the Nautilus Builder repository or an isolated worktree created from it.

## Goal

Implement the first in-memory slice of the strategy/test workflow event spine from the approved design.

This slice defines backend contracts for strategy lineage, versioning, selected test parameters, workflow events, and in-memory repository/stream interfaces. It does **not** connect to real Postgres or Redis yet.

## Source Spec

- `docs/superpowers/specs/2026-05-22-strategy-test-workflow-event-spine-design.md`

## Hard Scope Constraints

- No real Postgres connection in this slice.
- No real Redis connection in this slice.
- No frontend scaffold.
- No Nautilus-Daedalus source access or mutation.
- No live execution authority.
- No AI framework implementation yet.
- Tests first for every behavior.

## File Structure Map

### New package

- `packages/workflow_spine/__init__.py`
  - Public exports.
- `packages/workflow_spine/models.py`
  - Pydantic models for lineage, versions, test params, jobs, results, events, AI continuity IDs.
- `packages/workflow_spine/repository.py`
  - In-memory repository interface used as a fake Postgres stand-in.
- `packages/workflow_spine/event_stream.py`
  - In-memory Redis Stream-like publisher with namespace validation.
- `packages/workflow_spine/service.py`
  - Orchestrates save/version/validate/compile/enqueue test workflow using existing package services where practical.

### Tests

- `tests/workflow_spine/__init__.py`
- `tests/workflow_spine/test_lineage_identity.py`
- `tests/workflow_spine/test_workflow_event_payloads.py`
- `tests/workflow_spine/test_strategy_test_workflow.py`
- `tests/workflow_spine/test_redis_namespace_policy.py`

## Tasks

### Task 1 — Red tests: lineage continuity

- [ ] Create `tests/workflow_spine/__init__.py`.
- [ ] Create `tests/workflow_spine/test_lineage_identity.py`.
- [ ] Write failing tests proving names are labels only and continuity uses:
  - `strategy_id`;
  - `strategy_lineage_id`;
  - `strategy_version_id`;
  - `parent_version_id`;
  - `ai_thread_id`;
  - `improvement_cycle_id`.
- [ ] Run `rtk pytest tests/workflow_spine/test_lineage_identity.py` and confirm RED.

### Task 2 — Implement lineage models

- [ ] Create `packages/workflow_spine/__init__.py`.
- [ ] Create `packages/workflow_spine/models.py`.
- [ ] Implement strict Pydantic models for strategy lineage/version identity.
- [ ] Run lineage tests and confirm GREEN.

### Task 3 — Red tests: event payload IDs and namespace policy

- [ ] Create `tests/workflow_spine/test_workflow_event_payloads.py`.
- [ ] Create `tests/workflow_spine/test_redis_namespace_policy.py`.
- [ ] Write failing tests for workflow events carrying Postgres IDs, not only names.
- [ ] Write failing tests that Builder streams must start with `builder:` and ND streams are rejected unless explicit bridge streams.
- [ ] Run focused tests and confirm RED.

### Task 4 — Implement event stream contracts

- [ ] Create `packages/workflow_spine/event_stream.py`.
- [ ] Implement `WorkflowEvent` model if not already in `models.py`.
- [ ] Implement in-memory stream publisher that stores event payloads by stream name.
- [ ] Enforce `builder:*` namespace and explicit bridge names such as `builder:nd:advisory` / `builder:nd:reports`.
- [ ] Run event payload and namespace tests and confirm GREEN.

### Task 5 — Red tests: core strategy/test workflow

- [ ] Create `tests/workflow_spine/test_strategy_test_workflow.py`.
- [ ] Write failing test for complete in-memory flow:
  - create strategy draft label;
  - create immutable version;
  - attach selected params;
  - create test job;
  - publish `strategy.versioned` and `test.enqueued` events;
  - preserve AI continuity IDs;
  - store records in repository.
- [ ] Run test and confirm RED.

### Task 6 — Implement repository and workflow service

- [ ] Create `packages/workflow_spine/repository.py`.
- [ ] Create `packages/workflow_spine/service.py`.
- [ ] Implement in-memory repository for records.
- [ ] Implement service orchestration for save/version/enqueue.
- [ ] Keep validation/compile as explicit recorded phases or references to existing services; do not overbuild real execution.
- [ ] Run workflow spine tests and confirm GREEN.

### Task 7 — Verification

- [ ] Run focused workflow suite:
  - `rtk pytest tests/workflow_spine`
- [ ] Run broader suite:
  - `rtk pytest tests/workflow_spine tests/api tests/auth tests/backtest_jobs tests/runtime_events tests/strategy_compiler`
- [ ] Run full suite if budget permits:
  - `rtk pytest tests/strategy_spec tests/strategy_validation tests/adapter_registry tests/instrument_registry tests/strategy_compiler tests/backtest_jobs tests/runtime_events tests/backtest_runner tests/lifecycle tests/strategy_registry tests/promotions tests/web tests/ai_builder tests/integration tests/api tests/auth tests/frontend_contracts tests/workflow_spine`
- [ ] Search changed files for forbidden strings:
  - `submit_order`
  - `TradeAction`
  - `nd:` direct writes
  - real Redis/Postgres connection strings.

### Task 8 — Commits

- [ ] Commit plan as `plan strategy test event spine`.
- [ ] Commit implementation/tests as `add workflow event spine contracts` or split if more than one coherent unit.

## Verification Commands

Focused:

```bash
rtk pytest tests/workflow_spine
```

Broader:

```bash
rtk pytest tests/workflow_spine tests/api tests/auth tests/backtest_jobs tests/runtime_events tests/strategy_compiler
```

## Success Criteria

- Strategy improvement continuity uses stable IDs, not display names.
- In-memory repository records strategy lineage/version/test job data.
- In-memory event stream emits namespaced Builder workflow events.
- ND sharing is represented only through explicit Builder-owned bridge streams.
- No real Redis/Postgres integration is introduced yet.

## Completion Reconciliation

Status: **completed and merged to `origin/master`**.

Implementation evidence:

- `packages/workflow_spine/models.py` defines lineage/version/job/result/event records with stable IDs.
- `packages/workflow_spine/repository.py` provides the in-memory repository contract.
- `packages/workflow_spine/event_stream.py` enforces Builder-owned stream namespaces.
- `packages/workflow_spine/service.py` publishes `strategy.versioned`, `test.enqueued`, `result.completed`, and `suggestion.created` workflow events.
- `packages/workflow_spine/storage_interfaces.py` keeps fake Postgres/Redis adapters dependency-free and rejects network-shaped configuration.
- `packages/workflow_spine/nd_compat.py` maps Builder events to the explicit `builder:nd:advisory` bridge without importing or mutating Nautilus-Daedalus.

Commit evidence on `master`:

- `df954f0 add workflow storage interfaces`
- `86ca3d8 add workflow storage interface tests`
- `2bae3ef add workflow storage config skeletons`
- `a8d5a63 add workflow storage config tests`
- `19ed112 add workflow result API routes`
- `9a996e0 add workflow result API tests`
- `33d95c4 add workflow completion events`
- `bbcbe68 guard workflow adapter boundaries`

Verification evidence:

```bash
rtk pytest tests/workflow_spine tests/api tests/auth tests/backtest_jobs tests/runtime_events tests/strategy_compiler
# Pytest: 51 passed
```

## Follow-on Slice: ND AI Pipeline Compatibility Mapping

Goal: add a small contract adapter that maps Builder workflow identity/events to ND-facing advisory bridge payloads without importing ND internals or writing to ND-owned streams.

### Additional files

- `packages/workflow_spine/nd_compat.py`
  - Builder-owned mapping models for ND AI pipeline compatibility.
  - Converts Builder workflow events into ND advisory request/report payloads.
- `tests/workflow_spine/test_nd_ai_compatibility.py`
  - Verifies ID mapping, stream names, and no direct ND mutation assumptions.

### Additional tasks

- [ ] Write red tests for ND AI compatibility mapping:
  - Builder event maps to `builder:nd:advisory` payload;
  - payload preserves `strategy_lineage_id`, `strategy_version_id`, `ai_thread_id`, `improvement_cycle_id`, and `source_ref` when present;
  - mapper rejects `nd:*` output streams;
  - mapper does not require a shared display name.
- [ ] Implement `nd_compat.py` minimally.
- [ ] Run `rtk pytest tests/workflow_spine/test_nd_ai_compatibility.py`.
- [ ] Run `rtk pytest tests/workflow_spine`.
- [ ] Commit as `add ND AI compatibility mapping`.

Follow-on status: **implemented before this reconciliation** in `packages/workflow_spine/nd_compat.py` and `tests/workflow_spine/test_nd_ai_compatibility.py`.
