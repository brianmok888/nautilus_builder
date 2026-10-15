# Frontend library knowledge base

## OVERVIEW
Typed HTTP access, view projections and pure helpers; score 9, separate from feature components.

## WHERE TO LOOK
| Task | Module | Role |
|---|---|---|
| Builder requests | api.ts | Base URL selection, errors and typed endpoints |
| Shared responses | types.ts | Backend-aligned interfaces |
| Strategy editing helpers | strategySpec.ts | Spec transformations |
| Lifecycle projection | lifecycle/ | State/evidence/audit derivation |
| TradeHUD data flow | tradehud/ | Local guide for feeds, types and reducer |
| Unit coverage | *.test.ts and nested tests | Vitest contracts |

## CONVENTIONS
- api.ts is the ordinary Builder HTTP surface; no apiClient.ts module exists.
- Browser requests default to same-origin paths; server reads use BUILDER_API_BASE_URL.
- Keep error status, URL and response detail available through ApiError.
- Match shared types to backend Pydantic payloads rather than UI guesses.
- Lifecycle helpers derive display state from backend records; they do not advance runtime state.
- TradeHUD owns a separate normalized event path under its child guide.
- Keep pure helpers free of component state and rendering concerns.
- Run npm run test -- lib from apps/web for the relevant unit slice.

## ANTI-PATTERNS
- Do not create a competing generic API client next to api.ts.
- Do not hide auth tokens in NEXT_PUBLIC configuration or log them in request errors.
- Do not promote a display-derived lifecycle state into backend approval authority.
- Do not replace absent backend evidence with optimistic success defaults.
- Do not put ND Redis parsing in browser helpers.
