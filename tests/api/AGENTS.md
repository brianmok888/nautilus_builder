# API test knowledge base

## OVERVIEW
HTTP/facade behavior, OpenAPI and transport policy checks; score 9, distinct from package unit contracts.

## WHERE TO LOOK
| Task | Location | Surface |
|---|---|---|
| App construction and HTTP behavior | test_fastapi_app.py | FastAPI client and application wiring |
| API schema | openapi_snapshot.json | Tracked OpenAPI contract |
| Feature handlers | test_*.py | Route/facade-specific expectations |
| Fixture payloads | Local JSON files | Stable contract inputs |
| Implementation | ../../services/api/ | Factories, routes and middleware |

## CONVENTIONS
- Inspect whether a test calls BuilderApiApp directly or goes through the FastAPI client.
- Keep the in-process facade factory distinct from create_fastapi_app.
- Exercise authentication and project scoping at the actual HTTP boundary where asserted.
- Keep package business-rule assertions in the owning tests/<domain>/ slice.
- Review OpenAPI changes as public API changes, not incidental snapshot churn.
- JSON payload assertions must preserve the backend's explicit provenance and state vocabulary.
- SSE response checks belong to the transport contract, not runtime execution evidence.
- Root pytest configuration supplies asyncio mode and package/service coverage.
- Run python3 -m pytest tests/api/ -q for this slice.

## ANTI-PATTERNS
- Do not claim a facade-only assertion covers HTTP auth or serialization.
- Do not update the OpenAPI snapshot without reviewing the schema difference.
- Do not use fixture/mock response success as proof of ND connectivity.
- Do not hide domain policy exclusively in a route to satisfy a transport test.
- Do not add real credentials or production service dependencies to in-process tests.
