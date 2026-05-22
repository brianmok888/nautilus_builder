# QuantDinger Donor-Adoption Design for Nautilus Builder

**Date:** 2026-05-22  
**Status:** draft for review  
**Scope:** use `brokermr810/QuantDinger` as a reference and selective feature donor for `nautilus_builder`

## 1. Goal

Use QuantDinger as a source of proven infrastructure patterns while keeping Nautilus Builder's product identity, safety boundaries, and repository ownership intact.

This is not a merge plan. It is a Builder-native adoption design.

## 2. Non-negotiable Builder boundaries

Every borrowed pattern must preserve these rules:

- Nautilus Builder remains a Builder-side repository.
- Do not edit or depend on Nautilus-Daedalus source code.
- Builder must not own live order execution.
- Builder must not create `TradeAction` or call `submit_order`.
- UX remains authoring and observational only.
- AI remains advisory only and must produce validated Draft-stage outputs.
- Backend-owned durable state remains the runtime truth.
- MCP and agent surfaces must never become policy owners.

## 3. Evidence from QuantDinger

The revised research found that QuantDinger's most useful reusable pattern is not its full product scope. It is the ordered infrastructure stack around a real backend.

### 3.1 Backend/API structure

Relevant QuantDinger files and docs:

- `backend_api_python/run.py`
- `backend_api_python/app/__init__.py`
- `backend_api_python/app/routes/*`
- `backend_api_python/app/services/*`
- `backend_api_python/app/utils/*`
- `backend_api_python/gunicorn_config.py`
- `backend_api_python/docker-entrypoint.sh`
- `backend_api_python/start.sh`

Observed pattern:

- backend has an app/bootstrap layer;
- route modules are mounted under URL prefixes;
- routes delegate to service classes;
- services own domain behavior;
- deployment is built around a real API process rather than standalone helper functions.

Builder relevance:

- current Builder has `services/api/routes/*.py`, but they are route-shaped helper functions, not mounted endpoints;
- current Builder has no real API app bootstrap.

### 3.2 Auth and multi-user structure

Relevant QuantDinger evidence:

- `backend_api_python/app/utils/auth.py`
- docs for multi-user, billing, credits, and agent auth
- schema references to `qd_users` as the tenant anchor

Observed pattern:

- JWT bearer tokens;
- `generate_token(user_id, username, role, token_version)`;
- `verify_token(token)`;
- `login_required`, `admin_required`, `manager_required`, and `permission_required` decorators;
- request identity stored in request context;
- `token_version` used to invalidate older sessions;
- user-owned state and authorization are central to the backend.

Builder relevance:

- Builder currently has no auth/session package;
- Builder docs require user/project authorization for artifacts;
- Builder should adopt minimal request identity and artifact scoping, not QuantDinger's full SaaS/billing/admin surface.

### 3.3 Agent gateway

Relevant QuantDinger files/docs:

- `backend_api_python/app/routes/agent_v1/*`
- `backend_api_python/migrations/v3_1_0_agent_gateway.sql`
- `backend_api_python/tests/test_agent_v1.py`
- `backend_api_python/tests/test_agent_v1_saas_guard.py`
- `backend_api_python/tests/test_agent_jobs_progress.py`
- `docs/agent/AI_INTEGRATION_DESIGN.md`
- `docs/agent/AGENT_ENVIRONMENT_DESIGN.md`
- `docs/agent/AGENT_QUICKSTART.md`
- `docs/agent/agent-openapi.json`

Observed pattern:

- machine access is separate from human session APIs;
- agent gateway lives under `/api/agent/v1`;
- agent tokens are scoped by capability class;
- gateway adds identity, authorization, throttling, idempotency, audit, and job progress;
- long-running jobs can stream progress via SSE;
- trading-class access is constrained by server-side policy.

Builder relevance:

- Builder should eventually expose a Builder-safe agent gateway;
- the gateway should only expose read, validate, compile, backtest, replay, and promotion-readiness actions;
- no Builder agent token may grant live execution authority.

### 3.4 MCP wrapper

Relevant QuantDinger files:

- `mcp_server/src/quantdinger_mcp/server.py`
- `mcp_server/README.md`
- `mcp_server/pyproject.toml`
- `mcp_server/tests/test_transport_resolution.py`
- `docs/agent/cursor-mcp.example.json`

Observed pattern:

- MCP is a thin wrapper over the Agent Gateway;
- REST remains the source of truth;
- MCP exposes a curated tool subset;
- server-side tokens/scopes still gate every call;
- transports include stdio, SSE, and streamable HTTP;
- environment variables configure base URL, token, timeout, host, port, and transport.

Builder relevance:

- Builder MCP should be implemented only after API/auth/agent gateway exist;
- MCP must not duplicate policy or bypass backend authorization;
- MCP tools should be Builder-safe only.

### 3.5 Notifications and ops

Relevant QuantDinger evidence:

- notification docs for Telegram, email, SMS, and webhook-style channels;
- service names such as `email_service.py` and `signal_notifier.py`;
- docs that tie notifications to users, strategy events, and authorization.

Observed pattern:

- notifications consume backend state and user configuration;
- notifications are operational outputs, not control-plane inputs;
- per-user notification autonomy exists in the broader platform.

Builder relevance:

- Builder can later add event-driven notifications for backend state transitions;
- notifications should never expose secrets, worker internals, or execution controls.

### 3.6 Deployment

Relevant QuantDinger files:

- `docker-compose.yml`
- `backend_api_python/Dockerfile`
- `frontend/Dockerfile`
- `backend_api_python/env.example`
- `backend_api_python/gunicorn_config.py`
- `backend_api_python/docker-entrypoint.sh`

Observed pattern:

- Docker Compose bundles API, frontend delivery, Postgres, Redis, and workers;
- `.env` drives runtime configuration;
- `SECRET_KEY`, DB, Redis, LLM, OAuth, workers, billing, notifications, and agent gateway settings are explicit;
- deployment docs distinguish local and cloud concerns.

Builder relevance:

- Builder should borrow environment/config discipline and API/worker separation;
- Builder should not copy QuantDinger's full `.env` breadth before the corresponding features exist.

## 4. Evidence from Nautilus Builder

Current Builder repo has:

- domain packages under `packages/*`;
- route-shaped helper files under `services/api/routes/*`;
- a worker stub under `services/workers/`;
- placeholder TSX components under `apps/web/components/*`;
- Python-backed UI contracts under `packages/ui_contracts/*`;
- contract/policy tests under `tests/*`;
- source docs under `doc/`;
- derived execution docs under `docs/superpowers/`.

Current Builder repo lacks:

- real API server bootstrap;
- auth/session package;
- user/project ownership model;
- MCP package/server;
- notification package;
- deployment/Docker/CI configuration;
- real frontend app shell;
- frontend API client.

## 5. Adoption strategy

QuantDinger should be used as a donor of infrastructure patterns, not product identity.

### Adopt

- thin route layer over services;
- API app bootstrap;
- request identity/auth boundary;
- user/project artifact scoping;
- dedicated agent gateway;
- scoped machine tokens;
- audit/idempotency/rate-limit concepts;
- MCP as thin wrapper over agent gateway;
- event-driven notifications;
- Docker/env deployment discipline.

### Adapt

- JWT/session concepts into a minimal Builder auth model;
- tenant ownership into Builder user/project ownership;
- QuantDinger agent scopes into Builder-safe scopes;
- job streaming into Builder runtime-event replay/progress;
- notification channels into backend-state-only notifications;
- deployment topology into Builder API/worker/storage units.

### Reject

- live execution authority;
- QuantDinger trading-class agent scope;
- billing/credits/SaaS breadth as an early dependency;
- QuantDinger-specific route names, branding, and product semantics;
- MCP tools that submit live orders or control Daedalus;
- notification commands that mutate runtime state;
- full QuantDinger `.env` complexity before features exist.

## 6. Recommended adoption order

### Phase 1 — `API-01`: real API bootstrap

Goal:

- convert Builder route stubs into mounted, testable endpoints.

Includes:

- backend app entrypoint;
- health endpoint;
- mounted adapters for existing route helper modules;
- request/response payload tests;
- preserved thin-route discipline.

Excludes:

- full auth;
- frontend app shell;
- database persistence;
- MCP;
- notifications.

Acceptance:

- tests can call existing route payloads through an app/test client;
- route layer delegates to `packages/*`;
- no endpoint grants runtime or live execution authority.

### Phase 2 — `AUTH-01`: minimal auth/session and artifact scoping

Goal:

- add the smallest Builder identity boundary needed for real API use.

Includes:

- request identity context;
- user/project identifier model;
- authorization helper;
- artifact-scope interfaces for specs, jobs, results, events, and promotion requests;
- tests for unauthorized access and project isolation.

Excludes:

- billing;
- credits;
- full RBAC admin console;
- OAuth;
- production-grade session management.

Acceptance:

- API boundary can resolve user/project context;
- artifacts can be associated with user/project ownership;
- unauthorized cross-project access is rejected in tests.

### Phase 3 — `AGENT-01`: Builder-safe agent gateway

Goal:

- add a machine-client surface analogous to QuantDinger's Agent Gateway, but restricted to Builder-safe actions.

Includes:

- `/api/agent/v1` route namespace;
- scoped Builder agent token model;
- audit-log model;
- idempotency support for job creation;
- safe endpoints for read, validate, compile, backtest, replay, and promotion readiness.

Excludes:

- trading scope;
- live execution toggles;
- Daedalus control;
- broad marketplace/SaaS semantics.

Acceptance:

- agent calls are scoped, auditable, and denied when outside allowed capabilities;
- no agent endpoint can submit live orders.

### Phase 4 — `MCP-01`: thin MCP wrapper

Goal:

- expose Builder-safe agent gateway calls as MCP tools.

Includes:

- separate MCP package or server module;
- environment-based base URL and token config;
- stdio transport first;
- optional HTTP/SSE transport later;
- curated tool subset.

Excludes:

- policy decisions inside MCP;
- direct package-service calls that bypass API auth;
- live execution tools.

Acceptance:

- MCP tools call the agent gateway;
- server-side auth/scopes remain authoritative;
- MCP has no broader power than the configured token.

### Phase 5 — `NOTIFY-01`: event-driven notifications

Goal:

- add downstream notifications for Builder state changes.

Includes:

- notification preference model;
- backend-state event triggers;
- safe message payloads;
- initial channel abstraction.

Excludes:

- notification-triggered runtime mutation;
- secrets in notification payloads;
- full multi-channel production integrations unless separately planned.

Acceptance:

- notifications report state transitions only;
- messages cannot control jobs or promotion state.

### Phase 6 — `DEPLOY-01`: deployment and configuration scaffold

Goal:

- make Builder runnable as separated API/worker units once API/auth seams exist.

Includes:

- `.env.example`;
- API container scaffold;
- worker container scaffold;
- local compose file when storage dependencies are introduced;
- docs for local dev startup.

Excludes:

- copying QuantDinger's full configuration matrix;
- production cloud hardening;
- live trading infrastructure.

Acceptance:

- local deployment docs match implemented components;
- config variables correspond to real Builder features.

## 7. First implementation recommendation

Start with `API-01`.

Reason:

- Builder's current biggest gap is that UI/API/auth/MCP cannot connect to a real backend process;
- QuantDinger's MCP and agent gateway patterns depend on REST/API being the source of truth;
- API bootstrap is the smallest high-leverage slice that unlocks auth, agent gateway, MCP, notifications, and frontend integration later;
- API bootstrap does not require violating Builder's no-live-execution and no-Daedalus-coupling boundaries.

## 8. Open implementation decisions for planning

These should be resolved during planning, not inside this design:

1. API framework choice for Builder bootstrap.
   - likely FastAPI or Flask;
   - choose based on minimal dependency and testability.
2. Whether `AUTH-01` uses JWT immediately or a minimal bearer-token/request-context model first.
3. Whether agent gateway persistence is in-memory first or backed by a real DB seam.
4. Whether MCP lives under `mcp_server/` or `packages/mcp_gateway/`.
5. Whether deployment scaffolding waits for DB/Redis persistence or starts with API-only local run.

## 9. Success criteria for this donor strategy

The adoption succeeds if Builder gains real operational structure while remaining Builder-specific:

- API becomes real without moving domain logic out of `packages/*`;
- auth scopes artifacts without broad SaaS sprawl;
- agent/MCP access remains bounded and auditable;
- notifications consume backend state but never control runtime;
- deployment matches implemented reality;
- Daedalus remains external;
- live execution remains outside Builder authority.
