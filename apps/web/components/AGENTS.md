# Component knowledge base

## OVERVIEW
Interactive feature views, shared shell and display panels; score 11, not a directory of placeholder stubs.

## STRUCTURE
- strategy-builder/, strategies/, ai-builder/: strategy editing and draft review.
- backtests/, results/, evidence/: jobs and inspectable result artifacts.
- config/, execution/, llm-config/: backend configuration and session views.
- pipeline/, market/, lineage/: workflow and market-data context.
- shell/, dashboard/, ui/, theme/: navigation, overview and shared presentation.
- lifecycle/, promotions/, safety/: explicit state and approval boundaries.
- tradehud/: observational ND panels with their own local guide.
- terminal/: job-oriented terminal presentation.

## WHERE TO LOOK
| Task | Location | Responsibility |
|---|---|---|
| Strategy editing | strategy-builder/ | Builder workspace and validation display |
| AI proposals | ai-builder/ | Draft creation/application UX |
| App navigation | shell/ | Shared shell mounted by routes |
| Dashboard | dashboard/ | Backend summary presentation |
| Pipeline runs | pipeline/ | Run submission and status UI |
| TradeHUD panels | tradehud/ | Reducer-driven read-only display |
| Shared controls | ui/ | Reused component primitives |

## CONVENTIONS
- Pages compose feature components; stateful behavior belongs in its feature seam.
- Use Ant Design primitives and existing shared UI controls.
- Ordinary requests call lib/api.ts and display backend validation/errors.
- Keep Python ui_contracts and tests/web aligned with the actual UI responsibilities.
- Colocated .test.tsx files execute under the app's Vitest/jsdom configuration.

## ANTI-PATTERNS
- Do not infer runtime success from a button click or a submitted command.
- Do not let AI-generated drafts silently cross review/promotion boundaries.
- Do not move shell access, exchange secrets or order authority into React state.
