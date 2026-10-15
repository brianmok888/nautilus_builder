# Backtest runner knowledge base

## OVERVIEW
Builder backtest contracts, fixture replay and explicit engine adapters; score 8, a distinct evidence boundary.

## WHERE TO LOOK
| Task | Module | Role |
|---|---|---|
| Runtime version/modes | engine_contract.py | Version pin and fixture/injected-engine labels |
| Run request/report models | contracts.py | Backtest request and output contracts |
| Configuration | config_builder.py | Validation report and engine-mode requirements |
| Execution entry | runner.py | Fixture and engine execution paths |
| Official engine adapter | nautilus_engine.py | NautilusTrader engine integration |
| Result normalization | result_normalizer.py | Engine output shaping |
| Artifacts | artifacts.py | Persistable backtest evidence |
| Replay inputs | replay_loader.py, replay_fixtures.py | Recorded data inputs |
| Spec replay | strategy_spec_replay.py | StrategySpec replay handling |
| Smoke checks | real_engine_smoke.py, catalog_replay_smoke.py | Explicit engine/catalog evidence |
| Availability check | runtime_check.py | Engine runtime readiness probe |

## CONVENTIONS
- engine_contract.py is the local version/mode authority; do not infer it from nearby projects.
- build_backtest_config requires a validation_report_id argument and rejects live credentials.
- Preserve fixture versus injected_engine distinctions in configuration and results.
- Keep compile hashes, worker image and spec version attached to run evidence.
- Use the __init__.py facade for the supported runner surface.
- Focused checks live in tests/backtest_runner/ and tests/replay/.

## ANTI-PATTERNS
- Do not label fixture execution as a successful official-engine run.
- Do not remove validation requirements to make a run configuration acceptable.
- Do not infer runtime availability from the existence of a version constant.
- Do not turn backtest evidence into production trading authority.
