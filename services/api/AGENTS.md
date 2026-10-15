# API knowledge base

## OVERVIEW
Builder HTTP and in-process adapters over packages; score 9, a distinct transport boundary.

## WHERE TO LOOK
| Task | Location | Role |
|---|---|---|
| In-process service facade | app.py | BuilderApiApp and create_app |
| HTTP app construction | fastapi_app.py | create_fastapi_app and lifespan wiring |
| Canonical HTTP wrapper | app_factory.py | Delegates to create_fastapi_app |
| ASGI startup command | fastapi_cli.py | Environment-driven factory |
| Endpoint adapters | routes/ | Narrow package calls |
| Configuration and dependencies | settings.py, _app_env.py, dependencies.py | Backend wiring |
| Startup validation | startup_policy.py | Deployment policy checks |
| Errors and request behavior | errors.py, middleware.py | Transport translation |
| Event transport | sse.py, routes/tradehud_sse.py | SSE response handling |

## CONVENTIONS
- Distinguish services.api.create_app (in-process facade) from the ASGI factory.
- Keep actual HTTP registration and lifespan behavior in fastapi_app.py.
- app_factory.py is a thin wrapper; its docstring is not a second implementation.
- Route modules delegate to domain services and serialize Pydantic results with model_dump(mode="json").
- Keep replay, AI draft, registry and promotion provenance explicit in responses.
- Auth and deployment policy belong in backend wiring, not browser configuration.
- Test route behavior through tests/api/; OpenAPI has a tracked snapshot there.

## ANTI-PATTERNS
- Do not make a route the only enforcement point for a domain rule.
- Do not give endpoint adapters shell access or direct Daedalus coupling.
- Do not mistake a mock TradeHUD HTTP stream for a connected ND runtime.
- Do not collapse facade tests and actual FastAPI tests into one claimed guarantee.
