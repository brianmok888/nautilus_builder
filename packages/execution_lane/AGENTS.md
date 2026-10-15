# Execution lane knowledge base

## OVERVIEW
Builder session planning, command lifecycle and explicit session runners; score 8, a separate operational contract.

## WHERE TO LOOK
| Task | Module | Role |
|---|---|---|
| Profiles, commands, reports | models.py | Typed lane/session contracts |
| Command lifecycle | service.py | Profile registration, claim, run, reports |
| Runtime plan | nautilus_runtime.py | TradingNode plan construction |
| Contract/native runners | sessions.py | Selected session execution implementation |
| Adapter configuration | adapter_config_builders.py | Venue-specific client configuration |
| Credential slots | credentials.py | Environment-backed secret resolution |
| Native strategy wiring | paper_strategy.py | Strategy implementation |
| Worker integration | ../../services/workers/execution_lane_worker.py | Command processing boundary |
| Public API | __init__.py | Exported lane surface |

## CONVENTIONS
- Treat a queued/claimed command, a session and its report as different records.
- Preserve project scoping on profile and command access.
- Keep native versus contract runner selection explicit in construction.
- Credential-slot references cross the API; raw secret values stay backend-side.
- Keep runtime-plan construction distinct from starting a session.
- Preserve command idempotency and the service's bounded reports/session history.
- Tests live in tests/execution_lane/; HTTP wrappers live in services/api/routes/.

## ANTI-PATTERNS
- Do not equate a runtime plan or contract runner with observed venue execution.
- Do not put environment secrets in serialized profiles or browser state.
- Do not bypass project checks or command lifecycle when adding a worker caller.
- Do not infer production permission from the existence of a native runner.
