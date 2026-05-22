# Frontend Stack and Daedalus Adaptation Design

**Date:** 2026-05-22  
**Status:** draft for review  
**Scope:** choose the next frontend direction for Nautilus Builder while using `brokermr810/QuantDinger-Vue` as a pattern donor only.

## 1. Current Builder stack

Nautilus Builder currently has a real backend/domain foundation, but not a real browser application.

Current implemented stack:

- Python domain packages under `packages/*`.
- Thin API adapter/bootstrap under `services/api/*`.
- Minimal auth/project-scope package under `packages/auth/*`.
- Worker and runtime scaffolding under `services/workers/*` and backend packages.
- Pytest contract suite under `tests/*`.
- Placeholder TSX components under `apps/web/components/*`.

Current missing frontend stack:

- no `apps/web/package.json`;
- no `App.tsx` or app shell;
- no frontend router;
- no frontend request client;
- no frontend auth provider/store;
- no frontend build or test toolchain.

Therefore the frontend framework is not truly chosen yet. The existing TSX files are placeholders, not a committed React runtime.

## 2. QuantDinger-Vue donor role

`brokermr810/QuantDinger-Vue` is a separate frontend-only repository from `brokermr810/QuantDinger`.

Confirmed donor stack:

- Vue 2.7;
- Vite;
- Ant Design Vue;
- Vue Router 3;
- Vuex 3;
- Axios request wrapper;
- ECharts / KLineCharts;
- CodeMirror;
- vue-i18n;
- frontend deployment assets.

Useful donor areas:

- `src/api/*` API-client separation;
- `src/utils/request.js` centralized request handling;
- `src/permission.js` route guard pattern;
- `src/store/modules/user.js` auth/user session state pattern;
- reusable component grouping;
- dashboard/workspace layout concepts;
- chart/result surface organization;
- public/assets/deploy separation.

Not useful as direct code:

- Vue 2 implementation details;
- QuantDinger-specific trading, quick-trade, broker credential, billing, or SaaS UI;
- live-execution UI affordances;
- product branding/copy.

## 3. Stack options

### Option A — Vue 3 + Vite

Use QuantDinger-Vue as a strong frontend pattern donor, but implement with Vue 3 rather than Vue 2.

Pros:

- closest conceptual match to QuantDinger-Vue;
- dashboard/auth/router/store patterns translate naturally;
- good fit for admin-style trading research workspaces.

Cons:

- current Builder placeholders are TSX;
- QuantDinger-Vue is Vue 2, so code is still pattern-only;
- requires choosing Vue UI/store/testing conventions from scratch.

### Option B — React/TSX + Vite

Preserve the current TSX direction and adapt QuantDinger-Vue concepts into React architecture.

Pros:

- aligns with existing placeholder file type;
- strong TypeScript and AI-assisted UI ecosystem;
- good fit for typed API client and contract-first frontend work;
- avoids Vue 2 legacy drag.

Cons:

- less direct reuse from QuantDinger-Vue;
- dashboard shell and route/store patterns need React-native design.

### Option C — Contract-first, framework decision later

Define frontend contracts before final framework choice.

Pros:

- safest architecture;
- keeps UI framework independent from Daedalus and backend contracts;
- matches current repo maturity, because API/auth just became real;
- reduces risk of copying the wrong donor surface.

Cons:

- slower visible UI progress;
- still needs a later Vue vs React decision.

## 4. Recommendation

Use Option C immediately, with Option B as the likely implementation default.

Recommended sequence:

1. Define frontend contracts and hardguards first.
2. Treat QuantDinger-Vue as a pattern donor, not a framework mandate.
3. Default future implementation to React/TSX + Vite unless the user explicitly chooses Vue 3.
4. Keep the Daedalus boundary backend-contract-only.

Why:

- Builder already has TSX placeholders but no actual frontend runtime.
- The newly merged API/auth foundation should drive frontend integration shape.
- QuantDinger-Vue is valuable, but its stack is Vue 2.7 and product-specific.
- Daedalus adaptation depends on backend payloads, not UI framework choice.

## 5. Target frontend architecture

The frontend should be organized around stable boundaries:

```text
Frontend App
  -> API Client
  -> Auth Session State
  -> Route Guards
  -> Builder Feature Surfaces
  -> Backend API/Auth
  -> Builder Domain Packages
  -> Daedalus-facing contracts only
```

### API client layer

Purpose:

- centralize browser-to-backend calls;
- attach auth/session context;
- handle unauthorized responses;
- preserve typed request/response boundaries.

Initial client groups:

- auth/session;
- strategy specs;
- validation;
- backtest jobs;
- runtime events/replay;
- AI drafts;
- promotion readiness.

### Auth/session state

Purpose:

- track current user/project context;
- expose login/logout/session refresh flow;
- clear local state on backend unauthorized responses.

Rules:

- frontend may hide/show affordances;
- backend remains authorization authority;
- frontend must not invent permissions that backend does not enforce.

### Route guards

Purpose:

- block unauthenticated workspace routes;
- redirect unauthenticated users to login;
- prevent navigation to unsupported or forbidden Builder capabilities.

Rules:

- route guards are UX safety rails only;
- backend hardguards remain authoritative.

### Builder feature surfaces

Initial safe surfaces:

- Strategy Builder;
- Validation Report;
- Backtest Job Console;
- Runtime Event Terminal;
- AI Draft Panel;
- Promotion Readiness View.

All feature surfaces must call the API client and must not import backend package internals.

## 6. Forbidden frontend surfaces

Do not copy or build these QuantDinger-Vue surfaces into Builder without a separate approved design:

- quick-trade UI;
- live order entry UI;
- broker credential management UI;
- billing/credits UI;
- Daedalus control panel;
- live execution dashboard;
- browser-side Python execution / Pyodide strategy execution.

## 7. Daedalus adaptation model

Nautilus-Daedalus should adapt well if integration stays contract-only.

Daedalus should care about:

- promotion request payloads;
- signal-preview outputs;
- readiness evidence;
- approval-state semantics;
- externally stable schemas.

Daedalus should not care about:

- React vs Vue;
- frontend route guards;
- frontend auth store;
- UI component state;
- dashboard layout.

Safe boundary:

```text
Builder backend contracts
  -> promotion request / signal-preview / readiness evidence
  -> external Daedalus boundary
```

## 8. First follow-on implementation slice

Before choosing the final frontend framework, implement or plan a small contract-first slice:

- document frontend API client contract;
- document auth/session frontend flow;
- define route guard rules;
- map safe Builder feature surfaces to existing backend endpoints;
- list forbidden QuantDinger-Vue screens explicitly.

Only after that should Builder scaffold a real frontend app.

## 9. Success criteria

This design succeeds if:

- QuantDinger-Vue informs Builder frontend structure without forcing Vue 2 adoption;
- Builder's API/auth foundation remains the integration source of truth;
- Daedalus remains UI-framework independent;
- forbidden live-trading and credential-management UI surfaces stay out of scope;
- the next implementation plan can decide frontend scaffolding without weakening Builder hardguards.
