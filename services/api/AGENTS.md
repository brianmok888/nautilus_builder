# AGENTS

## Scope
- `services/api/` is the thin adapter layer over `packages/*`.
- Route files should translate package outputs to JSON-ish payloads and nothing more.

## Conventions
- Keep route modules narrow: import one package service, call it, `model_dump(mode="json")` if needed.
- Preserve backend-owned truth; routes should not invent lifecycle, validation, or promotion policy.
- Keep runtime replay, AI draft, registry, and promotion boundaries explicit in payload names.

## Do not
- Do not embed real business rules here if they belong in `packages/`.
- Do not give routes shell access, order authority, or direct Daedalus coupling.
- Do not let route code become the only place a policy is enforced.

## Current reality
- `fastapi_app.py` provides the real FastAPI bootstrap when FastAPI is installed.
- `app.py` keeps the lightweight in-process `ApiApp` for dependency-free contract tests.
- `services/workers/` is separate and should stay backend-only.
