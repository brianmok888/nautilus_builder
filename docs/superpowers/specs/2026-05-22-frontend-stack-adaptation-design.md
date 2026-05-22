# Frontend Stack and Daedalus Adaptation Design

**Date:** 2026-05-22  
**Status:** approved stack direction  
**Scope:** define the Next.js + React + TypeScript frontend direction for Nautilus Builder while using `brokermr810/QuantDinger-Vue` as a pattern donor only.

## 1. Current Builder stack

Nautilus Builder currently has a real backend/domain foundation, but not a real browser application.

Current implemented stack:

- Python domain packages under `packages/*`.
- Thin API adapter/bootstrap under `services/api/*`.
- Minimal auth/project-scope package under `packages/auth/*`.
- Worker and runtime scaffolding under `services/workers/*` and backend packages.
- Pytest contract suite under `tests/*`.
- Placeholder TSX components under `apps/web/components/*`.

Current missing frontend implementation:

- no `apps/web/package.json`;
- no Next.js app shell;
- no frontend router;
- no frontend request client;
- no frontend auth provider/store;
- no frontend build or test toolchain.

The frontend stack decision is now **Next.js + React + TypeScript**. The existing TSX files are placeholders that should be migrated into a real Next.js app structure later, not treated as a runnable frontend today.

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

## 3. Stack decision

Nautilus Builder will use **Next.js + React + TypeScript** for the real frontend runtime.

This decision means:

- QuantDinger-Vue remains a pattern donor, not a framework donor;
- frontend contracts should be shaped for typed React/Next clients;
- future app scaffolding should use a Next.js app shell rather than Vue or plain Vite;
- frontend routing/auth/session decisions should use Next.js-native patterns while preserving the same backend authority boundaries.

## 4. Alternatives considered

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

### Option B — React/TSX + Vite or Next.js

Preserve the current TSX direction and adapt QuantDinger-Vue concepts into React architecture.

Pros:

- aligns with existing placeholder file type;
- strong TypeScript and AI-assisted UI ecosystem;
- good fit for typed API client and contract-first frontend work;
- Next.js adds a more complete app/routing/deployment framework than plain Vite;
- avoids Vue 2 legacy drag.

Cons:

- less direct reuse from QuantDinger-Vue;
- dashboard shell and route/store patterns need React-native design.

Decision: choose **Next.js + React + TypeScript**, not plain Vite, as the target React stack.

### Option C — Contract-first before scaffolding

Define frontend contracts before scaffolding the selected framework.

Pros:

- safest architecture;
- keeps UI framework independent from Daedalus and backend contracts;
- matches current repo maturity, because API/auth just became real;
- reduces risk of copying the wrong donor surface.

Cons:

- slower visible UI progress;
- still delays visible app scaffolding.

## 5. Recommendation

Use contract-first work immediately, with **Next.js + React + TypeScript** as the selected implementation stack.

Recommended sequence:

1. Define frontend contracts and hardguards first.
2. Treat QuantDinger-Vue as a pattern donor, not a framework mandate.
3. Scaffold a real Next.js + React + TypeScript app only after the frontend contracts are implemented.
4. Keep the Daedalus boundary backend-contract-only.

Why:

- Builder already has TSX placeholders but no actual frontend runtime.
- The newly merged API/auth foundation should drive frontend integration shape.
- QuantDinger-Vue is valuable, but its stack is Vue 2.7 and product-specific.
- Next.js gives Builder a full frontend application framework without adopting Vue 2 legacy.
- Daedalus adaptation depends on backend payloads, not UI framework choice.

## 6. Target frontend architecture

The frontend should be organized around stable boundaries:

```text
Next.js Frontend App
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

## 7. Forbidden frontend surfaces

Do not copy or build these QuantDinger-Vue surfaces into Builder without a separate approved design:

- quick-trade UI;
- live order entry UI;
- broker credential management UI;
- billing/credits UI;
- Daedalus control panel;
- live execution dashboard;
- browser-side Python execution / Pyodide strategy execution.

## 8. Daedalus adaptation model

Nautilus-Daedalus should adapt well if integration stays contract-only.

Daedalus should care about:

- promotion request payloads;
- signal-preview outputs;
- readiness evidence;
- approval-state semantics;
- externally stable schemas.

Daedalus should not care about:

- Next.js vs Vue;
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

## 9. First follow-on implementation slice

Before choosing the final frontend framework, implement or plan a small contract-first slice:

- document frontend API client contract;
- document auth/session frontend flow;
- define route guard rules;
- map safe Builder feature surfaces to existing backend endpoints;
- list forbidden QuantDinger-Vue screens explicitly.

Only after that should Builder scaffold the real Next.js app.

## 10. Success criteria

This design succeeds if:

- QuantDinger-Vue informs Builder frontend structure without forcing Vue adoption;
- Next.js + React + TypeScript is the explicit target stack for future frontend scaffolding;
- Builder's API/auth foundation remains the integration source of truth;
- Daedalus remains UI-framework independent;
- forbidden live-trading and credential-management UI surfaces stay out of scope;
- the next implementation plan can decide frontend scaffolding without weakening Builder hardguards.
