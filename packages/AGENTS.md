# Packages knowledge base

## OVERVIEW
Canonical Python domain layer; score 13, with bounded packages and explicit public facades.

## STRUCTURE
- Contracts and checks: strategy_spec, strategy_validation, evidence_ledger, lifecycle.
- Compilation and research: strategy_compiler, backtest_runner, backtest_jobs, research_jobs.
- Registries and storage: strategy_registry, adapter_registry, catalog_datasets, postgres.
- Workflows and operations: workflow_spine, pipeline, execution_lane, config, auth.
- Display contracts: tradehud_contracts and ui_contracts; neither is a browser runtime.
- Small support seams include errors, audit, observability, common and compatibility.

## WHERE TO LOOK
| Task | Location | Contract |
|---|---|---|
| Spec and hard validation | strategy_spec/, strategy_validation/ | Schema plus policy |
| Generated strategy bundles | strategy_compiler/ | Deterministic artifacts |
| Backtest engines and replay | backtest_runner/ | Fixture versus engine evidence |
| Read-only ND normalization | tradehud_contracts/ | Python payload authority |
| Jobs and workflow identity | workflow_spine/, backtest_jobs/ | Versioned workflow records |
| Persistence | postgres/, artifact_store/ | Builder-owned storage |
| Local execution sessions | execution_lane/ | Explicit runner and credential boundaries |

## CONVENTIONS
- Keep each seam bounded; expose intended imports through its __init__.py.
- Prefer strict Pydantic contracts and explicit enums/booleans over loose dictionaries.
- Keep transport wiring in services; domain decisions belong here.
- system_verification is a composed check harness, not production orchestration.
- Verify a seam with tests/<seam>/ before expanding the test slice.
- Preserve stable hashes, artifact names and explicit error values.

## ANTI-PATTERNS
- Do not import Nautilus-Daedalus internals or create production order authority.
- Do not put validation, lifecycle or promotion rules only in route/UI adapters.
- Do not bypass package-level checks when adding a new caller.
