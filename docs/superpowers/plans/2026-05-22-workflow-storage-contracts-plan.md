# Workflow Storage Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax and are intended to be completed in order. Do not skip verification steps. Do not broaden scope. Keep all work inside the Nautilus Builder repository or an isolated worktree created from it.

## Goal

Add the next in-memory workflow-spine storage slice: result records and AI suggestion records linked by stable strategy lineage/version/job/result IDs.

This prepares the future real Postgres interface while keeping this slice dependency-free and testable.

## Scope

- Extend `packages/workflow_spine` models and repository.
- Add tests under `tests/workflow_spine`.
- Do not connect to real Postgres.
- Do not connect to real Redis.
- Do not implement AI frameworks.
- Do not touch Nautilus-Daedalus.

## Tasks

1. Write failing tests for storing and reading `TestResultRecord` by `result_id` and `test_job_id`.
2. Write failing tests for storing and reading `AiSuggestionRecord` by `strategy_lineage_id`, `strategy_version_id`, `result_id`, and `ai_thread_id`.
3. Implement strict models in `packages/workflow_spine/models.py`.
4. Extend `InMemoryWorkflowRepository` with result/suggestion methods.
5. Verify `rtk pytest tests/workflow_spine`.
6. Verify broader workflow-related suite.
7. Commit as `add workflow result suggestion storage`.

## Success Criteria

- Results are durable repository records, not Redis-only messages.
- AI suggestions attach to stable IDs and do not depend on display names.
- Repository can query suggestions by lineage and result.
- No real database or external service dependency is introduced.

## Completion Reconciliation

Status: **completed and merged to `origin/master`**.

Implementation evidence:

- `packages/workflow_spine/models.py` defines strict `TestResultRecord` and `AiSuggestionRecord` models.
- `packages/workflow_spine/repository.py` stores results by `result_id` / `test_job_id` and suggestions by lineage, result, and AI thread.
- `tests/workflow_spine/test_result_suggestion_storage.py` covers durable result/suggestion storage and display-name independence.
- Commit evidence includes `05d8c09 add workflow result suggestion storage` on `master`.

Verification evidence from the downstream workflow-spine tranche:

```bash
rtk pytest tests/workflow_spine tests/api tests/auth tests/backtest_jobs tests/runtime_events tests/strategy_compiler
# Pytest: 51 passed
```
